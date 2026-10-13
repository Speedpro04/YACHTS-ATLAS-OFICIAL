"""
Regressão do pagamento da marina: os 12 meses travados e a vaga que pode não
existir.

Duas coisas acontecem no mesmo instante do pagamento:

  • TODA assinatura tem a regra de reajuste registrada — 12 meses travados e,
    depois, IPCA + 15% (ver test_13o_mes_na_moeda.py). Vale para fundadora e
    para quem chega pelo site, porque desde 13/10/2026 o preço é um só;
  • se a marina veio da CAMPANHA e não há vaga no estado, alguém assinou como
    fundadora sem vaga para honrar — e isso precisa chegar no fundador.

O que está em jogo no segundo caso mudou: antes era dinheiro (US$ 200 contra
US$ 250, uma recorrência a menos US$ 50/mês para sempre). Hoje o preço é o
mesmo e o que fica em aberto é o bônus — os 18 meses de dossiê 100% da marina,
que existem para 4 marinas por estado e nada mais.

O link da campanha é uma URL pública e estática: o segundo caso não é hipótese
remota, basta a marina repassar o link para outra.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

import app.core.supabase as sb
from app.core.config import settings
from app.services.stripe_service import StripeService


class _Query:
    def __init__(self, retorno=None):
        self._retorno = retorno
        self._payload = None

    def insert(self, payload):
        self._payload = payload
        return self

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        return types.SimpleNamespace(data=self._retorno if self._retorno is not None else [])


class _Admin:
    """Service-role falso com resposta configurável da RPC de vagas."""

    def __init__(self, resposta_rpc):
        self._resposta_rpc = resposta_rpc
        self.auth = types.SimpleNamespace(
            admin=types.SimpleNamespace(
                get_user_by_id=lambda uid: types.SimpleNamespace(
                    user=types.SimpleNamespace(user_metadata={})
                ),
                update_user_by_id=lambda uid, dados: None,
            )
        )

    def table(self, nome):
        return _Query()

    def rpc(self, nome, params):
        return _Query(retorno=self._resposta_rpc)


@pytest.fixture
def cenario(monkeypatch):
    """Instala o banco falso e espiões nos dois efeitos que importam."""
    chamadas = {"agendou": [], "avisou": []}

    def instalar(resposta_rpc):
        monkeypatch.setattr(sb, "get_supabase_admin", lambda: _Admin(resposta_rpc))
        monkeypatch.setattr(
            sb, "buscar_usuario_por_email",
            lambda email: types.SimpleNamespace(id="user-uuid-1"),
        )
        monkeypatch.setattr(
            StripeService, "_registrar_reajuste_do_13o_mes",
            lambda self, sub_id, usuario_id=None, email=None: chamadas["agendou"].append(sub_id),
        )
        monkeypatch.setattr(
            StripeService, "_avisar_pagamento_sem_vaga",
            staticmethod(lambda email, motivo, checkout: chamadas["avisou"].append(email)),
        )
        return chamadas

    return instalar


def _checkout_fundadora(session_id="cs_fundadora"):
    return types.SimpleNamespace(
        id=session_id,
        metadata={"plan_type": "marina", "uf": "SC"},
        amount_total=settings.PRECO_MENSAL_USD * 100,
        currency="usd",
        mode="subscription",
        payment_intent=None,
        subscription="sub_123",
        customer="cus_1",
        customer_email="marina@exemplo.com",
        customer_details={"email": "marina@exemplo.com"},
    )


def test_fundadora_com_vaga_registra_o_reajuste(cenario):
    chamadas = cenario({"modo": "fundadora", "slot": 1, "uf": "SC"})

    StripeService()._handle_checkout_completed(_checkout_fundadora())

    assert chamadas["agendou"] == ["sub_123"]
    assert chamadas["avisou"] == []


def test_assinou_sem_vaga_dispara_alerta_e_ainda_registra_o_reajuste(cenario):
    """Sem vaga ela não leva o bônus — mas paga o mesmo e tem os 12 meses.

    Antes, não ter vaga significava estar no preço errado, e o reajuste não era
    agendado de propósito. Com preço único ela está no preço certo: os 12 meses
    travados são dela como de qualquer outra, e só o bônus fica para o humano
    decidir.
    """
    chamadas = cenario({"modo": "tradicional", "motivo": "vagas_do_estado_esgotadas"})

    StripeService()._handle_checkout_completed(_checkout_fundadora("cs_sem_vaga"))

    assert chamadas["avisou"] == ["marina@exemplo.com"]
    assert chamadas["agendou"] == ["sub_123"]


def test_assinatura_de_outro_valor_nao_mexe_em_vaga(cenario):
    """Outro produto da casa no mesmo webhook não pode ocupar vaga.

    O reajuste também não é registrado: sem o nosso valor, nem link, nem
    metadata, não há prova de que seja uma marina.
    """
    chamadas = cenario({"modo": "fundadora"})
    sessao = _checkout_fundadora("cs_outro")
    sessao.amount_total = 25000

    StripeService()._handle_checkout_completed(sessao)

    assert chamadas["agendou"] == []
    assert chamadas["avisou"] == []
