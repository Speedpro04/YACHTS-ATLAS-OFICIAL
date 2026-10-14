"""
O programa fundador está SUSPENSO: ninguém ocupa vaga, venha de onde vier.

Decisão do fundador em 14/10/2026 — *"vamos deixar de lado a página fundadora,
iremos trabalhar só com a oficial nesse novo valor"*. Toda marina que se
cadastra recebe a oferta Oficial a US$ 140/mês, e `reservar_vaga_fundadora`
não é mais chamada por ninguém.

POR QUE ESTE ARQUIVO CONTINUA EXISTINDO, E O QUE ELE PROTEGE AGORA

O programa não foi apagado: as 4 vagas por estado, a reserva com prazo e as
funções do banco continuam de pé, desligadas em `leads._oferta_marina`. Um
arquivo que testava "a vaga é concedida certo" vira, por isso, o arquivo que
testa "a vaga NÃO é concedida" — é o mesmo ponto do código, e é exatamente ali
que um religamento acidental apareceria.

O que estes testes impediriam: alguém reintroduzir a consulta à origem, ou a
chamada à RPC, sem a decisão comercial que a autoriza. Reservar vaga por
engano não se conserta devolvendo dinheiro: não existe 5ª vaga em estado
nenhum, e quem recebeu a promessa já a leu na tela.

O Supabase é substituído por um dublê — nenhum teste toca no banco real.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1.leads import _oferta_marina
from app.core.config import settings


class _SupabaseFalso:
    """Registra qualquer RPC que o cadastro tente chamar.

    Devolve vaga disponível de propósito: é o pior caso: se o código voltasse a
    consultar o banco, encontraria "pode reservar" e os testes abaixo
    quebrariam — que é o que se quer.
    """

    def __init__(self):
        self.chamadas = []

    def rpc(self, nome, params):
        self.chamadas.append((nome, params))
        return types.SimpleNamespace(
            execute=lambda: types.SimpleNamespace(
                data={"modo": "fundadora", "uf": "SC", "vagas_restantes": 3}
            )
        )


@pytest.fixture(autouse=True)
def links_em_real(monkeypatch):
    """Põe os links em real que o config não tem mais (ver test_checkout_por_uf).

    Estes testes afirmam que SAI um checkout; qual URL é assunto de outro
    arquivo. Sem isto eles passariam a falhar por um motivo que não é o deles.
    """
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_OFICIAL_BRL", "https://buy.stripe.com/brl-oficial")
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_FUNDADORA_BRL", "https://buy.stripe.com/brl-fundadora")


def _cadastro(state, origem="lancamento"):
    # Origem da CAMPANHA de propósito: era a única que conseguia vaga. Se a
    # suspensão falhar em algum lugar, falha aqui primeiro.
    return types.SimpleNamespace(
        email="marina@exemplo.com",
        name="Marina Teste",
        phone="47999999999",
        state=state,
        origem=origem,
    )


# ------------------------------------------------- a suspensão, por estado

@pytest.mark.parametrize("uf", ["SC", "SP", "RJ", "ES", "BA"])
def test_os_cinco_estados_do_programa_recebem_a_oficial(uf):
    """Eram os 5 estados com vaga. Hoje entram como qualquer outro."""
    supabase = _SupabaseFalso()

    oferta = _oferta_marina(supabase, _cadastro(uf))

    assert oferta["oferta"] == "oficial"
    assert oferta["preco_mensal"] == settings.PRECO_MENSAL_USD
    assert supabase.chamadas == [], "ninguém pode reservar vaga"


@pytest.mark.parametrize("uf", ["PR", "MG", "AM", None, ""])
def test_estado_fora_do_programa_tambem_recebe_a_oficial(uf):
    supabase = _SupabaseFalso()

    oferta = _oferta_marina(supabase, _cadastro(uf))

    assert oferta["oferta"] == "oficial"
    assert supabase.chamadas == []


def test_nenhuma_reserva_e_criada_em_nenhum_caminho():
    """A prova direta: a RPC de reserva não é chamada, ponto.

    Se este teste quebrar, alguém religou o programa — e isso é decisão
    comercial, não refatoração.
    """
    supabase = _SupabaseFalso()

    for uf in ("SC", "SP", "RJ", "ES", "BA", "PR", None):
        for origem in ("lancamento", "lp-fundadoras", "google", None, ""):
            _oferta_marina(supabase, _cadastro(uf, origem))

    assert supabase.chamadas == []


# ------------------------------------------------- o que a oferta entrega

def test_a_oferta_sai_completa_e_sem_prazo_correndo():
    """Sem vaga, não há relógio: nada de `reserva_expira_em` na resposta."""
    oferta = _oferta_marina(_SupabaseFalso(), _cadastro("SC"))

    assert oferta["checkout_url"]
    assert oferta["moeda_cobranca"] == "brl"   # SC é do Brasil
    assert oferta["reserva_expira_em"] is None
    assert oferta["reserva_minutos"] is None
    assert oferta["vagas_restantes"] is None


def test_o_programa_continua_configurado_para_voltar():
    """A suspensão é de porta, não de demolição.

    As 4 vagas por estado seguem no config. Se alguém apagar isto achando que
    virou lixo, religar a campanha deixa de ser devolver uma função e passa a
    ser redescobrir um número comercial.
    """
    from app.core.config import LAUNCH_STATES

    assert settings.LAUNCH_SLOTS_PER_STATE == 4
    assert settings.LAUNCH_SLOTS == settings.LAUNCH_SLOTS_PER_STATE * len(LAUNCH_STATES)
