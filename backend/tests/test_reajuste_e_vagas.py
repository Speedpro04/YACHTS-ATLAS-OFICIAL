"""
Regressão do preço da fundadora: os 12 meses e a vaga que pode não existir.

Duas coisas acontecem no mesmo instante do pagamento de US$ 200:

  • se HÁ vaga, a Stripe recebe o cronograma que sobe para US$ 250 no 13º mês;
  • se NÃO há, alguém pagou preço de fundadora sem vaga para honrar — e isso
    precisa chegar no Telegram, porque é uma recorrência a menos US$ 50/mês
    para sempre se passar batido.

O link de US$ 200 é uma URL pública e estática: o segundo caso não é hipótese
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
            StripeService, "_agendar_correcao_do_13o_mes",
            lambda self, sub_id: chamadas["agendou"].append(sub_id),
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
        amount_total=settings.LAUNCH_PRICE_MONTHLY * 100,
        currency="usd",
        mode="subscription",
        payment_intent=None,
        subscription="sub_123",
        customer="cus_1",
        customer_email="marina@exemplo.com",
        customer_details={"email": "marina@exemplo.com"},
    )


def test_fundadora_com_vaga_agenda_o_reajuste(cenario):
    chamadas = cenario({"modo": "fundadora", "slot": 1, "uf": "SC"})

    StripeService()._handle_checkout_completed(_checkout_fundadora())

    assert chamadas["agendou"] == ["sub_123"]
    assert chamadas["avisou"] == []


def test_pagou_200_sem_vaga_dispara_alerta_e_nao_agenda(cenario):
    """Sem vaga ela não é fundadora — agendar o reajuste seria fingir que é."""
    chamadas = cenario({"modo": "tradicional", "motivo": "vagas_do_estado_esgotadas"})

    StripeService()._handle_checkout_completed(_checkout_fundadora("cs_sem_vaga"))

    assert chamadas["avisou"] == ["marina@exemplo.com"]
    assert chamadas["agendou"] == []


def test_pagamento_oficial_nao_mexe_em_vaga_nem_em_reajuste(cenario):
    """Quem paga $250 já está na tabela oficial — não há o que agendar."""
    chamadas = cenario({"modo": "fundadora"})
    sessao = _checkout_fundadora("cs_oficial")
    sessao.amount_total = settings.TRADITIONAL_PRICE_MONTHLY * 100

    StripeService()._handle_checkout_completed(sessao)

    assert chamadas["agendou"] == []
    assert chamadas["avisou"] == []
