# -*- coding: utf-8 -*-
"""
O reajuste do 13º mês: REGISTRADO, não agendado — e dito na moeda da marina.

A HISTÓRIA. Enquanto havia dois preços, o 13º mês era um degrau fixo agendado
na Stripe: 12 meses no preço de fundadora e, depois, o oficial. Dava para
agendar porque o valor da segunda fase já se conhecia no dia da venda. Houve um
defeito famoso nesse arranjo (achado em 14/09/2026): a segunda fase saía fixa
em DÓLAR, a fundadora brasileira assina em REAL, a Stripe recusa cronograma com
duas moedas, e o reajuste simplesmente nunca era agendado — cada fundadora
ficaria em R$ 1.000 para sempre, sem erro nenhum aparecendo.

O QUE MUDOU EM 13/10/2026. Preço único de US$ 140 (R$ 697,00) e correção por
IPCA + 15% no 13º mês. IPCA do período não existe no dia da venda, então não há
o que agendar: cronograma com valor inventado cobraria o errado com a
autoridade de um automatismo, e um degrau de US$ 140 para US$ 140 só fingiria
que a regra está implementada.

O que o sistema faz é guardar a REGRA e a DATA — no acesso da marina e, quando
é fundadora, na linha dela — e avisar o fundador. É o que estes testes
protegem, incluindo a lição que sobrou do defeito antigo: o aviso fala na moeda
que a marina paga, não numa que ela nunca viu.
"""
import os
import types
from datetime import datetime, timezone

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

import app.core.supabase as supa
import app.services.stripe_service as modulo
from app.core.config import settings
from app.services.stripe_service import StripeService


# 1º de março de 2026, 12:00 UTC — data de início da assinatura nos testes.
INICIO = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


class _TabelaFalsa:
    """Imita table().update().eq().execute() do supabase-py."""

    def __init__(self, registro):
        self._registro = registro
        self._payload = None

    def update(self, payload):
        self._payload = payload
        return self

    def eq(self, coluna, valor):
        self._registro["eq"] = (coluna, valor)
        return self

    def execute(self):
        self._registro["updates"].append(self._payload)
        return types.SimpleNamespace(data=[])


@pytest.fixture
def cenario(monkeypatch):
    """Instala a Stripe falsa e espiões em tudo que o registro escreve."""

    def instalar(moeda="brl", inicio=INICIO, subscription_quebra=False):
        registro = {
            "metadata": [],
            "updates": [],
            "avisos": [],
            "agendas": [],
            "eq": None,
        }

        class Subscription:
            @staticmethod
            def retrieve(sub_id):
                if subscription_quebra:
                    raise RuntimeError("stripe fora do ar")
                return types.SimpleNamespace(
                    id=sub_id,
                    currency=moeda,
                    start_date=int(inicio.timestamp()) if inicio else None,
                )

        class SubscriptionSchedule:
            """Nada aqui pode ser chamado — é o ponto do teste."""

            @staticmethod
            def create(**kw):
                registro["agendas"].append(kw)
                raise AssertionError("não pode agendar degrau fixo: a correção é por índice")

            @staticmethod
            def modify(*a, **kw):
                registro["agendas"].append(kw)
                raise AssertionError("não pode agendar degrau fixo: a correção é por índice")

        monkeypatch.setattr(modulo.stripe, "Subscription", Subscription)
        monkeypatch.setattr(modulo.stripe, "SubscriptionSchedule", SubscriptionSchedule)
        monkeypatch.setattr(
            StripeService, "_atualizar_metadata",
            staticmethod(lambda uid, mudancas, preservar=(): registro["metadata"].append((uid, mudancas))),
        )
        monkeypatch.setattr(
            supa, "get_supabase_admin",
            lambda: types.SimpleNamespace(table=lambda nome: _TabelaFalsa(registro)),
        )
        import app.services.notify_service as notify
        monkeypatch.setattr(
            notify, "notificar_fundador",
            lambda titulo, texto: registro["avisos"].append((titulo, texto)),
        )
        return registro

    return instalar


def _servico():
    return StripeService.__new__(StripeService)


# ------------------------------------------------- o que fica guardado

def test_grava_a_data_de_vencimento_do_preco_travado(cenario):
    registro = cenario()

    _servico()._registrar_reajuste_do_13o_mes(
        "sub_br", usuario_id="user-1", email="marina@exemplo.com"
    )

    (uid, regra), = registro["metadata"]
    assert uid == "user-1"
    # 12 meses depois de 01/03/2026 é 01/03/2027 — o aniversário da marina,
    # não uma data de calendário nossa.
    assert regra["preco_travado_ate"].startswith("2027-03-01")
    assert regra["reajuste_indice"] == settings.REAJUSTE_INDICE
    assert regra["reajuste_percentual"] == settings.REAJUSTE_PERCENTUAL
    assert registro["avisos"] == [], "registrou certo: não pode avisar falha"


def test_grava_tambem_na_linha_da_fundadora(cenario):
    """É onde o comercial olha para montar a carta de reajuste."""
    registro = cenario()

    _servico()._registrar_reajuste_do_13o_mes(
        "sub_br", usuario_id="user-1", email="Marina@Exemplo.com "
    )

    gravado, = registro["updates"]
    assert gravado["preco_travado_ate"].startswith("2027-03-01")
    assert gravado["reajuste_indice"] == "ipca"
    assert gravado["reajuste_percentual"] == 15
    # A tabela é chaveada por e-mail minúsculo e sem espaço.
    assert registro["eq"] == ("email", "marina@exemplo.com")


def test_nao_agenda_degrau_fixo_na_stripe(cenario):
    """O ponto da mudança.

    Agendar exigiria saber hoje o IPCA de um ano que não acabou. O dublê da
    Stripe levanta se alguém tentar — se este teste falhar, voltou a existir um
    valor inventado cobrado automaticamente.
    """
    registro = cenario()

    _servico()._registrar_reajuste_do_13o_mes("sub_br", usuario_id="user-1")

    assert registro["agendas"] == []
    assert registro["avisos"] == []


def test_sem_usuario_e_sem_email_nao_quebra(cenario):
    """O webhook não pode cair por não ter conseguido identificar a marina."""
    registro = cenario()

    _servico()._registrar_reajuste_do_13o_mes("sub_br")

    assert registro["metadata"] == []
    assert registro["updates"] == []
    assert registro["avisos"] == []


def test_assinatura_sem_data_conta_de_hoje(cenario):
    """Melhor uma data aproximada e registrada que nenhuma data."""
    registro = cenario(inicio=None)

    _servico()._registrar_reajuste_do_13o_mes("sub_br", usuario_id="user-1")

    (_, regra), = registro["metadata"]
    vence = datetime.fromisoformat(regra["preco_travado_ate"])
    assert vence.year == datetime.now(timezone.utc).year + 1


# ------------------------------------------------- a moeda do aviso

def test_o_aviso_de_falha_fala_na_moeda_da_marina(cenario):
    """A lição do defeito de 14/09/2026, que continua valendo.

    O fundador lê "R$ 697 corrigido por IPCA + 15%", não um valor em dólar que
    a Marina brasileira nunca pagou.
    """
    registro = cenario(moeda="brl", subscription_quebra=True)

    _servico()._registrar_reajuste_do_13o_mes("sub_br", usuario_id="user-1")

    titulo, texto = registro["avisos"][0]
    assert "não registrado" in titulo
    assert "IPCA + 15%" in texto


def test_rotulo_em_dolar_para_quem_paga_em_dolar():
    rotulo = StripeService._rotulo_do_reajuste("usd")
    assert str(settings.PRECO_MENSAL_USD) in rotulo
    assert "US$" in rotulo
    assert "IPCA + 15%" in rotulo


def test_rotulo_em_real_para_quem_paga_em_real():
    rotulo = StripeService._rotulo_do_reajuste("brl")
    assert "R$ 697" in rotulo
    assert "IPCA + 15%" in rotulo


def test_moeda_desconhecida_nao_cai_no_dolar():
    """Dizer "R$ 697" a quem paga em euro é o mesmo defeito com outra roupa."""
    rotulo = StripeService._rotulo_do_reajuste("eur")
    assert rotulo == "IPCA + 15%"
    with pytest.raises(ValueError):
        StripeService._preco_na_moeda("eur")


# ------------------------------------------------- a conta dos meses

@pytest.mark.parametrize(
    "inicio, esperado",
    [
        (datetime(2026, 3, 1, tzinfo=timezone.utc), "2027-03-01"),
        (datetime(2026, 12, 31, tzinfo=timezone.utc), "2027-12-31"),
        # 29/02 de ano bissexto: 2027 não tem dia 29, cai no último do mês —
        # é como a própria Stripe trata o aniversário da assinatura.
        (datetime(2028, 2, 29, tzinfo=timezone.utc), "2029-02-28"),
    ],
)
def test_doze_meses_depois(inicio, esperado):
    vence = StripeService._mais_meses(inicio, settings.PRECO_TRAVADO_MESES)
    assert vence.date().isoformat() == esperado


def test_o_prazo_travado_e_de_doze_meses():
    """Se alguém mudar isto, a home e o contrato param de dizer a verdade."""
    assert settings.PRECO_TRAVADO_MESES == 12
