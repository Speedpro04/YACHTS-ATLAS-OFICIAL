"""
Regressão do acesso pago — quem entra, quem é barrado e quem volta sozinho.

Duas regras de negócio estão sob teste aqui:

  • ninguém usa o Atlas antes do pagamento cair na Stripe;
  • 20 dias de inadimplência cortam o acesso, e pagar religa automaticamente.

O grupo mais importante é o do fim: as contas que NUNCA podem ser bloqueadas
(manutenção, admin, marinas do piloto gratuito). Um erro ali tranca o dono da
plataforma para fora do próprio sistema — e é o tipo de bug que só aparece na
pior hora possível.
"""
import os
import types
from datetime import datetime, timedelta, timezone

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

import app.core.supabase as sb
from app.core.acesso import avaliar_acesso
from app.core.config import settings
from app.services.stripe_service import StripeService


def _dias_atras(dias: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()


# --------------------------------------------------------------------------
# Regra 1 — só entra depois do pagamento
# --------------------------------------------------------------------------

def test_pagamento_pendente_e_barrado():
    bloqueio = avaliar_acesso({"pagamento": "pendente"})
    assert bloqueio is not None
    assert bloqueio.motivo == "pagamento_pendente"


def test_pagamento_confirmado_entra():
    assert avaliar_acesso({"pagamento": "pago"}) is None


def test_assinatura_cancelada_e_barrada():
    bloqueio = avaliar_acesso({"pagamento": "cancelado"})
    assert bloqueio is not None
    assert bloqueio.motivo == "assinatura_cancelada"


def test_link_do_bloqueio_e_o_preco_que_a_marina_contratou():
    """Mandar a fundadora para o link de $250 cobraria a mais de quem não deve."""
    fundadora = avaliar_acesso({"pagamento": "pendente", "oferta": "fundadora"})
    oficial = avaliar_acesso({"pagamento": "pendente", "oferta": "oficial"})

    assert fundadora.link_pagamento
    assert oficial.link_pagamento
    assert fundadora.link_pagamento != oficial.link_pagamento


def test_link_do_bloqueio_sai_na_moeda_da_marina():
    """
    Marina bloqueada querendo voltar não pode topar com uma cobrança em dólar
    que o cartão dela recusa: ela já está sem acesso, e essa é a única porta.
    """
    br = avaliar_acesso({"pagamento": "pendente", "oferta": "oficial", "uf": "SC"})
    assert br.link_pagamento == settings.STRIPE_LINK_MARINA_OFICIAL_BRL


# --------------------------------------------------------------------------
# Regra 2 — 20 dias de inadimplência
# --------------------------------------------------------------------------

def test_dentro_do_prazo_continua_usando():
    """O prazo existe para a marina trocar o cartão sem perder o acesso."""
    meta = {"pagamento": "pago", "inadimplente_desde": _dias_atras(19)}
    assert avaliar_acesso(meta) is None


def test_no_vigesimo_dia_corta():
    meta = {"pagamento": "pago", "inadimplente_desde": _dias_atras(20)}
    bloqueio = avaliar_acesso(meta)
    assert bloqueio is not None
    assert bloqueio.motivo == "inadimplente"
    assert bloqueio.dias_em_atraso == 20


def test_bloqueio_por_atraso_aponta_para_a_fatura():
    """Link genérico de checkout criaria uma segunda assinatura, não quitaria a dívida."""
    meta = {
        "pagamento": "pago",
        "inadimplente_desde": _dias_atras(30),
        "fatura_url": "https://invoice.stripe.com/i/abc",
    }
    assert avaliar_acesso(meta).link_pagamento == "https://invoice.stripe.com/i/abc"


def test_data_corrompida_nao_bloqueia_ninguem():
    """Fail-open: metadata estragado não pode virar bloqueio inexplicável."""
    for lixo in ("", "ontem", None, 12345, "2026-13-45"):
        assert avaliar_acesso({"pagamento": "pago", "inadimplente_desde": lixo}) is None


# --------------------------------------------------------------------------
# Quem NUNCA pode ser bloqueado
# --------------------------------------------------------------------------

@pytest.mark.parametrize("metadata", [
    None,
    {},
    {"nome": "Fundador"},
    {"programa": "fundador_brinde"},                      # piloto gratuito
    {"programa": "fundador_brinde", "nome": "Marina 1"},
    {"user_role": "admin"},
    {"pagamento": "valor_que_ainda_nao_existe"},          # fail-open
])
def test_conta_sem_marca_de_cobranca_nunca_e_bloqueada(metadata):
    """
    O bloqueio é fail-open: barra só quem está explicitamente marcado.

    Manutenção e admin nem chegam aqui (saem antes, em security.get_current_user),
    mas mesmo que chegassem passariam — é a rede de segurança que impede o
    sistema de trancar o próprio dono para fora.
    """
    assert avaliar_acesso(metadata) is None


# --------------------------------------------------------------------------
# Webhook: marcar, preservar e limpar a inadimplência
# --------------------------------------------------------------------------

class _AuthAdmin:
    """Dublê do Auth admin do Supabase, que guarda o metadata em memória."""

    def __init__(self, metadata):
        self.metadata = dict(metadata)

    def get_user_by_id(self, uid):
        return types.SimpleNamespace(
            user=types.SimpleNamespace(user_metadata=dict(self.metadata))
        )

    def update_user_by_id(self, uid, dados):
        self.metadata = dict(dados["user_metadata"])


class _AdminComMetadata:
    """Service-role falso: Auth em memória e `payments` devolvendo o dono."""

    def __init__(self, metadata, usuario_id="user-uuid-1"):
        self.auth_admin = _AuthAdmin(metadata)
        self.auth = types.SimpleNamespace(admin=self.auth_admin)
        self._usuario_id = usuario_id
        self.inserts = []

    def table(self, nome):
        return _QueryPayments(self, nome)


class _QueryPayments:
    def __init__(self, admin, tabela):
        self._admin = admin
        self._tabela = tabela
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
        if self._payload is not None:
            self._admin.inserts.append((self._tabela, self._payload))
            return types.SimpleNamespace(data=[])
        return types.SimpleNamespace(
            data=[{"usuario_id": self._admin._usuario_id,
                   "plan_type": "marina",
                   "payment_type": "subscription"}]
        )


@pytest.fixture
def acesso_falso(monkeypatch):
    def instalar(metadata):
        admin = _AdminComMetadata(metadata)
        monkeypatch.setattr(sb, "get_supabase_admin", lambda: admin)
        return admin

    return instalar


def _invoice(invoice_id="in_1", billing_reason="subscription_cycle"):
    return types.SimpleNamespace(
        id=invoice_id,
        customer="cus_1",
        amount_paid=25000,
        currency="usd",
        billing_reason=billing_reason,
        subscription="sub_123",
        attempt_count=1,
        hosted_invoice_url="https://invoice.stripe.com/i/abc",
    )


def test_cobranca_recusada_comeca_a_contar_o_prazo(acesso_falso):
    admin = acesso_falso({"pagamento": "pago", "nome": "Marina Teste"})

    StripeService()._handle_invoice_payment_failed(_invoice())

    meta = admin.auth_admin.metadata
    assert meta["inadimplente_desde"]
    assert meta["fatura_url"] == "https://invoice.stripe.com/i/abc"
    # O resto do metadata não pode ser perdido: o update do Auth troca o objeto
    # inteiro, e já apagou nome e telefone de marina uma vez.
    assert meta["nome"] == "Marina Teste"


def test_segunda_recusa_nao_reinicia_o_prazo(acesso_falso):
    """O Stripe tenta várias vezes; se cada tentativa zerasse, nunca cortaria."""
    primeira = _dias_atras(10)
    admin = acesso_falso({"pagamento": "pago", "inadimplente_desde": primeira})

    StripeService()._handle_invoice_payment_failed(_invoice("in_2"))

    assert admin.auth_admin.metadata["inadimplente_desde"] == primeira


def test_pagar_religa_o_acesso_sozinho(acesso_falso):
    admin = acesso_falso({
        "pagamento": "pago",
        "inadimplente_desde": _dias_atras(25),
        "fatura_url": "https://invoice.stripe.com/i/abc",
    })

    StripeService()._handle_invoice_paid(_invoice("in_3"))

    meta = admin.auth_admin.metadata
    assert meta["pagamento"] == "pago"
    assert "inadimplente_desde" not in meta
    assert "fatura_url" not in meta
    assert avaliar_acesso(meta) is None


def test_assinatura_cancelada_revoga_o_acesso(acesso_falso):
    admin = acesso_falso({"pagamento": "pago"})

    StripeService()._handle_subscription_deleted(
        types.SimpleNamespace(id="sub_123", metadata={}, status="canceled")
    )

    assert admin.auth_admin.metadata["pagamento"] == "cancelado"
    assert avaliar_acesso(admin.auth_admin.metadata).motivo == "assinatura_cancelada"
