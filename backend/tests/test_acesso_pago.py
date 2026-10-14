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


@pytest.fixture(autouse=True)
def links_em_real(monkeypatch):
    """Põe os links em real que o config não tem mais.

    Desde 13/10/2026 os quatro links estão vazios na configuração: o preço
    virou US$ 140 / R$ 697,00 e os antigos continuam vivos na Stripe cobrando
    a tabela velha. Estes testes verificam QUAL porta a marina bloqueada
    recebe, não o estado de hoje da configuração — sem isto falhariam por um
    motivo que não é o deles. Ver test_checkout_por_uf.py.
    """
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_FUNDADORA_BRL", "https://buy.stripe.com/brl-fundadora")
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_OFICIAL_BRL", "https://buy.stripe.com/brl-oficial")


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
    """Cada oferta tem a sua porta.

    O preço é o mesmo nas duas desde 13/10/2026, mas os links continuam sendo
    dois: é por eles que o webhook sabe se a marina veio da campanha (e ocupa
    vaga) ou do site. Mandar uma para a porta da outra embaralha o programa de
    quem pagou.
    """
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

    def __init__(self, metadata, email="marina@exemplo.com"):
        self.metadata = dict(metadata)
        self.email = email

    def get_user_by_id(self, uid):
        return types.SimpleNamespace(
            user=types.SimpleNamespace(
                user_metadata=dict(self.metadata),
                # `marinas_fundadoras` e chaveada por e-mail, entao o duble
                # precisa ter um para a devolucao da vaga chegar a acontecer.
                email=self.email,
            )
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
        self.updates = []

    def table(self, nome):
        return _QueryPayments(self, nome)


class _QueryPayments:
    def __init__(self, admin, tabela):
        self._admin = admin
        self._tabela = tabela
        self._payload = None
        self._update = None
        self._filtros = []

    def insert(self, payload):
        self._payload = payload
        return self

    def update(self, payload):
        self._update = payload
        return self

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        self._filtros.append(a)
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        if self._update is not None:
            self._admin.updates.append((self._tabela, self._update, self._filtros))
            return types.SimpleNamespace(data=[])
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


# --------------------------------------------------------------------------
# Cancelar é um movimento de três partes
# --------------------------------------------------------------------------
# A condição de fundadora vale ENQUANTO a assinatura estiver ativa (regra do
# Marcos, 15/09/2026). Por muito tempo só a primeira parte acontecia: o acesso
# caía, mas a vaga continuava ocupada e a conta continuava marcada como
# fundadora — então quem saía voltava pagando o preço de lançamento por uma
# vaga que ela mesma havia liberado.

def test_cancelar_derruba_a_condicao_de_fundadora(acesso_falso):
    """Saiu, perdeu o lugar: voltando, entra pela porta normal."""
    admin = acesso_falso({
        "pagamento": "pago", "oferta": "fundadora",
        "preco_mensal": 140, "uf": "SP", "nome": "Marina Teste",
    })

    StripeService()._handle_subscription_deleted(
        types.SimpleNamespace(id="sub_123", metadata={}, status="canceled")
    )

    meta = admin.auth_admin.metadata
    assert meta["oferta"] == "oficial"
    # O preço não muda ao cancelar — é o mesmo para as duas ofertas. O que ela
    # perde é a vaga e o bônus de fundadora.
    assert meta["preco_mensal"] == settings.PRECO_MENSAL_USD == 140
    # E o que não é da assinatura continua lá — o update do Auth troca o
    # objeto inteiro, e já apagou nome de marina uma vez.
    assert meta["nome"] == "Marina Teste"


def test_a_porta_de_volta_e_a_oficial(acesso_falso):
    """O botão "Assinar novamente" lê o metadata. Se `oferta` continuasse
    "fundadora", ele devolveria o link da campanha para quem cancelou — e ela
    voltaria ocupando uma das 4 vagas do estado que ela mesma liberou."""
    from app.core.acesso import avaliar_acesso
    from app.core.precos import link_de_checkout

    admin = acesso_falso({"pagamento": "pago", "oferta": "fundadora", "uf": "SP"})

    StripeService()._handle_subscription_deleted(
        types.SimpleNamespace(id="sub_123", metadata={}, status="canceled")
    )

    bloqueio = avaliar_acesso(admin.auth_admin.metadata)
    oficial, _ = link_de_checkout(fundadora=False, uf="SP")
    fundadora, _ = link_de_checkout(fundadora=True, uf="SP")
    assert bloqueio.link_pagamento == oficial
    assert bloqueio.link_pagamento != fundadora


def test_cancelar_devolve_a_vaga_para_o_estado(acesso_falso):
    """São 4 por estado e elas são o argumento da campanha. Vaga que não volta
    é venda que some do estoque sem ninguém notar."""
    admin = acesso_falso({"pagamento": "pago", "oferta": "fundadora", "uf": "SP"})

    StripeService()._handle_subscription_deleted(
        types.SimpleNamespace(id="sub_123", metadata={}, status="canceled")
    )

    vagas = [u for u in admin.updates if u[0] == "marinas_fundadoras"]
    assert len(vagas) == 1, "a vaga fundadora não foi devolvida"
    _, mudanca, filtros = vagas[0]
    assert mudanca["status"] == "cancelado"
    # Só a linha desta marina, e só se ela ainda estiver ativa.
    assert ("email", "marina@exemplo.com") in filtros
    assert ("status", "ativo") in filtros


def test_sem_email_a_vaga_nao_e_tocada(acesso_falso):
    """Falha de leitura não pode virar UPDATE sem filtro — seria cancelar a
    vaga de todo mundo."""
    admin = acesso_falso({"pagamento": "pago", "oferta": "fundadora"})
    admin.auth_admin.email = ""

    StripeService()._handle_subscription_deleted(
        types.SimpleNamespace(id="sub_123", metadata={}, status="canceled")
    )

    assert [u for u in admin.updates if u[0] == "marinas_fundadoras"] == []
    # O acesso cai do mesmo jeito: a vaga é o acessório, o acesso é o essencial.
    assert admin.auth_admin.metadata["pagamento"] == "cancelado"

