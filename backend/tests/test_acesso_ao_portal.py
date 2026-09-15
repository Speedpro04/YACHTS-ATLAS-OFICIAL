# -*- coding: utf-8 -*-
"""
"O dono já entrou no Portal?" — e por que a resposta é nossa, não do Auth.

POR QUE EXISTE (15/09/2026). Depois de salvo, o cadastro do barco não aparecia
em tela nenhuma — nem o e-mail do dono. A Marina não tinha como saber se o
cliente dela usava o Portal, nem por que o código "não chegou".

A PRIMEIRA VERSÃO LIA `auth.users.last_sign_in_at`, e a revisão derrubou por
dois motivos, os dois graves:

  • aquele campo guarda a última VALIDAÇÃO DE CÓDIGO. A sessão do navegador se
    renova sozinha, então o dono podia abrir o Portal todo dia e a Marina
    continuar lendo a data do primeiro acesso — e concluir que o cliente
    abandonou o Portal;
  • para achar a conta era preciso varrer o Auth por e-mail. Como é a MARINA
    quem escolhe o e-mail gravado no próprio barco, ela podia digitar o de
    qualquer pessoa e descobrir se tem conta na plataforma e quando entrou.
    É exatamente o que `/owner/codigo` evita ao responder sempre "enviado".

Agora a visita é registrada por nós, em `portal_acessos`, e a pergunta é por
ATIVO. Estes testes existem para que continue assim.
"""
import inspect
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1 import ativos, owner
from app.api.v1.ativos import _situacao_do_portal


class _Consulta:
    def __init__(self, banco):
        self._banco = banco
        self._filtros = {}

    def select(self, *a, **k):
        return self

    def eq(self, coluna, valor):
        self._filtros[coluna] = valor
        return self

    def execute(self):
        chave = (self._filtros.get("ativo_id"), self._filtros.get("email"))
        self._banco.perguntas.append(chave)
        if self._banco.explode:
            raise RuntimeError("Auth/banco fora do ar")
        return types.SimpleNamespace(data=self._banco.linhas.get(chave, []))


class _Banco:
    def __init__(self, linhas=None, explode=False):
        self.linhas = linhas or {}
        self.explode = explode
        self.perguntas = []

    def table(self, nome):
        assert nome == "portal_acessos", f"consulta inesperada em {nome}"
        return _Consulta(self)


BARCO = "YA-IATE-2015-3A38"


def test_sem_email_nao_consulta_nada():
    banco = _Banco()
    for vazio in (None, "", "   "):
        assert _situacao_do_portal(banco, BARCO, vazio) == {
            "situacao": "sem_email", "ultimo_acesso": None, "visitas": 0,
        }
    assert banco.perguntas == [], "sem e-mail não há o que perguntar"


def test_sem_visita_registrada_e_nunca_entrou():
    banco = _Banco()
    r = _situacao_do_portal(banco, BARCO, "roberto@email.com")
    assert r == {"situacao": "nunca_entrou", "ultimo_acesso": None, "visitas": 0}


def test_visita_registrada_traz_data_e_quantas():
    banco = _Banco({(BARCO, "roberto@email.com"): [
        {"ultimo_acesso": "2026-09-15T13:20:00+00:00", "visitas": 4},
    ]})
    r = _situacao_do_portal(banco, BARCO, "roberto@email.com")
    assert r["situacao"] == "entrou"
    assert r["ultimo_acesso"].startswith("2026-09-15")
    assert r["visitas"] == 4


def test_pergunta_pelo_ativo_e_pelo_email_juntos():
    """Só por e-mail, a Marina veria visita a barco de outra Marina."""
    banco = _Banco()
    _situacao_do_portal(banco, BARCO, "Roberto@Email.COM ")
    assert banco.perguntas == [(BARCO, "roberto@email.com")]


def test_falha_de_banco_nao_vira_nunca_entrou():
    """Mentir para menos faz a Marina cobrar um cliente que já usa o Portal.
    A exceção sobe, o endpoint devolve erro e a tela diz que não verificou."""
    with pytest.raises(Exception):
        _situacao_do_portal(_Banco(explode=True), BARCO, "roberto@email.com")


def test_o_auth_saiu_de_cena():
    """Se `last_sign_in_at` voltar, voltam os dois defeitos de uma vez: data
    congelada e varredura do Auth por e-mail escolhido pela Marina."""
    # Fora da docstring, que explica justamente por que aquele campo saiu.
    corpo = inspect.getsource(ativos._situacao_do_portal).split('"""')[2]
    assert "last_sign_in_at" not in corpo
    assert "buscar_usuario_por_email" not in inspect.getsource(ativos)


def test_so_a_marina_dona_pergunta():
    fonte = inspect.getsource(ativos.acesso_do_proprietario)
    assert 'str(achado.data[0].get("usuario_id")) != str(user_id)' in fonte
    assert "403" in fonte


# --- o registro da visita ---------------------------------------------------

def test_a_visita_nao_aceita_barco_vindo_do_cliente():
    """O ativo sai do E-MAIL DA CONTA. Se o id viesse no corpo, qualquer conta
    logada marcaria visita em barco alheio — e a Marina leria como se o
    cliente dela estivesse usando o Portal."""
    assinatura = inspect.signature(owner.registrar_visita)
    assert list(assinatura.parameters) == ["user_id"]
    fonte = inspect.getsource(owner.registrar_visita)
    assert '.eq("proprietario_email", email)' in fonte


def test_a_visita_ignora_barco_arquivado():
    fonte = inspect.getsource(owner.registrar_visita)
    assert '.is_("arquivado_em", "null")' in fonte


def test_falha_ao_registrar_nao_derruba_o_portal():
    """Medição é secundária: o dono abre o cofre mesmo se a conta não gravar."""
    fonte = inspect.getsource(owner.registrar_visita)
    assert "except Exception" in fonte
