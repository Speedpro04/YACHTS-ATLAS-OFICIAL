"""
Regressão do preço único: R$ 897/mês para toda marina, venha de onde vier.

Substitui os testes de vaga fundadora e de preço por origem, encerrados em
05/11/2026. O que importa proteger agora é a tela e o checkout dizerem o mesmo:
valor, moeda e link.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1.leads import _oferta_marina
from app.core.acesso import avaliar_acesso
from app.core.config import settings
from app.core.precos import UFS_DO_BRASIL, link_de_checkout
from app.services.stripe_service import PlanType, StripeService

LINK = "https://buy.stripe.com/link_897"


@pytest.fixture
def com_link(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_BRL", LINK)


def test_o_preco_e_897():
    assert settings.PRECO_MENSAL_BRL == 897


@pytest.mark.parametrize("uf", ["SC", "PR", " sp ", None, "", "FL"])
def test_toda_marina_recebe_a_mesma_oferta(com_link, uf):
    oferta = _oferta_marina(uf)

    assert oferta["oferta"] == "oficial"
    assert oferta["preco_mensal"] == 897
    assert oferta["moeda_cobranca"] == "brl"
    assert oferta["checkout_url"] == LINK


def test_uf_chega_normalizada_no_cadastro(com_link):
    assert _oferta_marina(" sc ")["uf"] == "SC"
    assert _oferta_marina(None)["uf"] is None


def test_sem_o_link_novo_nao_cai_num_link_antigo(monkeypatch):
    """O link antigo cobraria R$ 1.250 de quem viu R$ 897 na tela."""
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_BRL", "   ")
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_OFICIAL_BRL", "https://buy.stripe.com/antigo")
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_OFICIAL", "https://buy.stripe.com/antigo_usd")

    assert link_de_checkout() == ("", "")
    assert _oferta_marina("SC")["checkout_url"] == ""


@pytest.mark.parametrize("oferta", ["fundadora", "oficial", None])
def test_quem_volta_paga_o_mesmo_preco(com_link, oferta):
    bloqueio = avaliar_acesso({"pagamento": "cancelado", "oferta": oferta, "uf": "SP"})

    assert bloqueio.link_pagamento == LINK


def test_valor_e_moeda_andam_juntos():
    """897 lido como dólar cobraria US$ 897 no checkout criado pela API."""
    plano = StripeService.PRICING[PlanType.MARINA]

    assert (plano["monthly"], plano["currency"]) == (897, "brl")


def test_tabela_publica_declara_real():
    planos = StripeService().get_pricing_plans()

    assert planos["currency"] == "BRL"
    assert planos["plans"][PlanType.MARINA.value]["monthly"] == 897


def test_webhook_reconhece_o_link_novo(com_link):
    assert StripeService._programas_por_link()[LINK] == "marina_oficial"


def test_as_27_ufs_estao_na_lista():
    assert len(UFS_DO_BRASIL) == 27
