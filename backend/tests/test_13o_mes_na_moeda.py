# -*- coding: utf-8 -*-
"""
O reajuste do 13º mês sai na MOEDA DA ASSINATURA.

O DEFEITO (achado em 14/09/2026, consertado em 16/09). A fundadora brasileira
assina em real — R$ 1.000 por mês. No pagamento, o sistema pede à Stripe o
cronograma "12 meses assim, depois o preço oficial". A segunda fase saía fixa
em DÓLAR (US$ 250). A Stripe não aceita cronograma que muda de moeda no meio,
recusava, e o reajuste nunca era agendado. Chegou ao fundador como "Reajuste do
13º mês não agendado" no teste de R$ 1,00.

Sem o conserto, cada fundadora ficaria em R$ 1.000 para sempre em vez de
passar a R$ 1.250 — R$ 250 por mês, por Marina, indefinidamente. E a campanha
das 20 vagas é toda brasileira.

A regra, decidida pelo Marcos: 12 meses a R$ 1.000, depois R$ 1.250.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

import app.services.stripe_service as modulo
from app.core.config import settings
from app.services.stripe_service import StripeService


class _StripeFalso:
    """Registra o que foi pedido à Stripe, sem rede."""

    def __init__(self, moeda):
        self.moeda = moeda
        self.fases = None
        self.precos_pedidos = []

        falso = self

        class Subscription:
            @staticmethod
            def retrieve(sub_id):
                return types.SimpleNamespace(id=sub_id, currency=falso.moeda)

        class SubscriptionSchedule:
            @staticmethod
            def create(from_subscription):
                return types.SimpleNamespace(
                    id="sub_sched_1",
                    phases=[{"items": [{"price": "price_fundadora", "quantity": 1}]}],
                )

            @staticmethod
            def modify(agenda_id, **kw):
                falso.fases = kw["phases"]

        self.Subscription = Subscription
        self.SubscriptionSchedule = SubscriptionSchedule


@pytest.fixture
def stripe_com(monkeypatch):
    avisos = []

    def instalar(moeda):
        falso = _StripeFalso(moeda)
        monkeypatch.setattr(modulo.stripe, "Subscription", falso.Subscription)
        monkeypatch.setattr(modulo.stripe, "SubscriptionSchedule", falso.SubscriptionSchedule)

        def preco(self, amount, currency, recurring, product_name):
            falso.precos_pedidos.append((amount, currency))
            return f"price_{currency}_{amount}"

        monkeypatch.setattr(StripeService, "_get_or_create_price", preco)
        import app.services.notify_service as notify
        monkeypatch.setattr(notify, "notificar_fundador", lambda titulo, texto: avisos.append((titulo, texto)))
        falso.avisos = avisos
        return falso

    return instalar


def _servico():
    return StripeService.__new__(StripeService)


def test_fundadora_em_real_vira_para_1250_reais(stripe_com):
    falso = stripe_com("brl")
    _servico()._agendar_correcao_do_13o_mes("sub_br")

    assert falso.precos_pedidos == [(settings.TRADITIONAL_PRICE_MONTHLY_BRL * 100, "brl")]
    assert settings.TRADITIONAL_PRICE_MONTHLY_BRL == 1250
    primeira, segunda = falso.fases
    assert primeira["iterations"] == settings.LAUNCH_PRICE_MONTHS
    assert segunda["items"][0]["price"] == "price_brl_125000"
    assert falso.avisos == [], "agendou certo: não pode avisar falha"


def test_fundadora_em_dolar_continua_indo_para_250_dolares(stripe_com):
    falso = stripe_com("usd")
    _servico()._agendar_correcao_do_13o_mes("sub_us")
    assert falso.precos_pedidos == [(settings.TRADITIONAL_PRICE_MONTHLY * 100, "usd")]


def test_as_duas_fases_ficam_na_mesma_moeda(stripe_com):
    """É exatamente o que a Stripe exige — e o que o código antigo violava."""
    falso = stripe_com("brl")
    _servico()._agendar_correcao_do_13o_mes("sub_br")
    moeda_da_segunda = falso.precos_pedidos[0][1]
    assert moeda_da_segunda == falso.moeda


def test_moeda_desconhecida_nao_cai_no_dolar(stripe_com):
    """Cobrar US$ 250 de quem assinou em outra moeda é o mesmo defeito com
    outra roupa. O certo é falhar e avisar para agendar na mão."""
    falso = stripe_com("eur")
    _servico()._agendar_correcao_do_13o_mes("sub_eu")
    assert falso.fases is None, "não pode agendar em moeda errada"
    assert falso.precos_pedidos == []
    assert falso.avisos and "não agendado" in falso.avisos[0][0]


def test_aviso_de_falha_fala_na_moeda_da_marina(stripe_com, monkeypatch):
    """O fundador lê 'R$ 1.000 → R$ 1.250', não um valor em dólar que a
    Marina nunca pagou."""
    falso = stripe_com("brl")

    def quebra(*a, **k):
        raise RuntimeError("Stripe fora do ar")

    monkeypatch.setattr(falso.SubscriptionSchedule, "create", staticmethod(quebra))
    _servico()._agendar_correcao_do_13o_mes("sub_br")
    assert "R$ 1.000 → R$ 1.250" in falso.avisos[0][1]
