"""
Política de senha: uma fonte, e a checagem de vazamento sem plano Pro.

Até 01/09/2026 as quatro regras (10 caracteres, maiúscula, minúscula, número)
viviam SÓ no `RegistroMarina.tsx`, conferidas no navegador. O backend recebia
`password: str` e mandava direto para o `create_user` do Supabase — quem
postasse direto em `/leads/marina/registrar` cadastrava com "123". E o
`UsuarioCreate` ainda dizia `min_length=8`: três números para o mesmo fato
(site 10, schema 8, Supabase 6).

A proteção contra senha VAZADA existe no Supabase, mas só no plano Pro. Aqui
ela é nossa, contra o mesmo HaveIBeenPwned, por k-anonimato — a senha nunca
sai do servidor e o hash completo também não.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import asyncio

import pytest
from pydantic import ValidationError

from app.core import security
from app.core.security import SENHA_MINIMO, faltas_na_senha, validar_senha


# --- as quatro regras -------------------------------------------------------

def test_senha_boa_nao_tem_falta():
    assert faltas_na_senha("MarinaAtlas2026") == []


@pytest.mark.parametrize(
    "senha, esperado",
    [
        ("Ab1", "pelo menos %d caracteres" % SENHA_MINIMO),
        ("minusculatoda1", "uma letra maiuscula"),
        ("MAIUSCULATODA1", "uma letra minuscula"),
        ("SemNumeroAqui", "um numero"),
    ],
)
def test_cada_regra_aponta_o_que_falta(senha, esperado):
    assert esperado in faltas_na_senha(senha)


def test_senha_vazia_falha_em_tudo():
    assert len(faltas_na_senha("")) == 4
    assert len(faltas_na_senha(None)) == 4


def test_mensagem_de_erro_lista_o_que_falta():
    with pytest.raises(ValueError) as e:
        validar_senha("abc")
    texto = str(e.value)
    assert "pelo menos %d caracteres" % SENHA_MINIMO in texto
    assert "uma letra maiuscula" in texto
    assert "um numero" in texto


# --- a regra vale no modelo, não só na tela ---------------------------------

def test_cadastro_publico_recusa_senha_fraca():
    """O buraco que existia: POST direto no endpoint, sem passar pelo site."""
    from app.api.v1.leads import MarinaRegistroPublico

    with pytest.raises(ValidationError):
        MarinaRegistroPublico(name="Marina X", email="a@b.com", password="123")


def test_cadastro_publico_aceita_senha_forte():
    from app.api.v1.leads import MarinaRegistroPublico

    m = MarinaRegistroPublico(
        name="Marina X", email="a@b.com", password="MarinaAtlas2026"
    )
    assert m.password == "MarinaAtlas2026"


def test_usuario_create_usa_a_mesma_regra():
    """Antes aceitava 8 caracteres sem complexidade nenhuma."""
    from app.schemas.models import UsuarioCreate

    with pytest.raises(ValidationError):
        UsuarioCreate(email="a@b.com", password="12345678", nome="Fulano")


# --- checagem de vazamento (HIBP por k-anonimato) ---------------------------

class _RespostaFalsa:
    def __init__(self, texto):
        self.text = texto

    def raise_for_status(self):
        pass


def _cliente_falso(corpo=None, erro=None):
    class _Cliente:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None):
            if erro:
                raise erro
            _Cliente.url_chamada = url
            return _RespostaFalsa(corpo)

    return _Cliente


def _rodar(coro):
    return asyncio.get_event_loop_policy().new_event_loop().run_until_complete(coro)


def test_hibp_so_recebe_os_cinco_primeiros_do_hash(monkeypatch):
    """K-anonimato: a senha e o hash completo NUNCA saem daqui."""
    import hashlib
    import httpx

    senha = "MarinaAtlas2026"
    sha1 = hashlib.sha1(senha.encode()).hexdigest().upper()

    cliente = _cliente_falso(corpo="AAAA1111AAAA:3")
    monkeypatch.setattr(httpx, "AsyncClient", cliente)
    _rodar(security.senha_vazada(senha))

    url = cliente.url_chamada
    assert url.endswith(sha1[:5])
    assert sha1 not in url
    assert sha1[5:] not in url
    assert senha not in url


def test_reconhece_senha_vazada(monkeypatch):
    import hashlib
    import httpx

    senha = "MarinaAtlas2026"
    sufixo = hashlib.sha1(senha.encode()).hexdigest().upper()[5:]
    corpo = "0000000000000000000000000000000000A:1\n%s:4823" % sufixo

    monkeypatch.setattr(httpx, "AsyncClient", _cliente_falso(corpo=corpo))
    assert _rodar(security.senha_vazada(senha)) is True


def test_sufixo_com_contagem_zero_nao_conta_como_vazada(monkeypatch):
    """O padding do HIBP vem com contagem 0 — é ruído, não vazamento."""
    import hashlib
    import httpx

    senha = "MarinaAtlas2026"
    sufixo = hashlib.sha1(senha.encode()).hexdigest().upper()[5:]

    monkeypatch.setattr(httpx, "AsyncClient", _cliente_falso(corpo="%s:0" % sufixo))
    assert _rodar(security.senha_vazada(senha)) is False


def test_senha_limpa_passa(monkeypatch):
    import httpx

    monkeypatch.setattr(httpx, "AsyncClient", _cliente_falso(corpo="ABC123:9\nDEF456:2"))
    assert _rodar(security.senha_vazada("MarinaAtlas2026")) is False


def test_hibp_fora_do_ar_falha_ABERTO(monkeypatch):
    """Travar o cadastro de uma marina pagante por causa de serviço de
    terceiro seria pior que o problema que isto resolve."""
    import httpx

    monkeypatch.setattr(
        httpx, "AsyncClient", _cliente_falso(erro=RuntimeError("timeout"))
    )
    assert _rodar(security.senha_vazada("MarinaAtlas2026")) is False


def test_senha_vazia_nao_chama_a_rede(monkeypatch):
    import httpx

    def _explode(*a, **k):
        raise AssertionError("não deveria chamar a rede com senha vazia")

    monkeypatch.setattr(httpx, "AsyncClient", _explode)
    assert _rodar(security.senha_vazada("")) is False
