"""
Regressão do webhook de pagamento — a parte do sistema que mexe em dinheiro.

Cada teste aqui corresponde a uma falha que já esteve em produção em silêncio:
vaga fundadora que nunca era ocupada, renovação mensal que nunca era gravada e
reentrega do Stripe que reprocessava o mesmo pagamento.

O Supabase é substituído por um dublê — nenhum teste toca no banco real.
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
    """Dublê do query builder do supabase-py."""

    def __init__(self, tabela, registro, erro=None, retorno=None):
        self._tabela = tabela
        self._registro = registro
        self._erro = erro
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
        if self._payload is not None:
            self._registro["inserts"].append((self._tabela, self._payload))
            if self._erro:
                raise Exception(self._erro)
        return types.SimpleNamespace(data=self._retorno or [])


class _Admin:
    """Dublê do cliente service-role."""

    def __init__(self, registro, erro_insert=None, origem=None):
        self._registro = registro
        self._erro_insert = erro_insert
        self._origem = origem
        self.auth = types.SimpleNamespace(
            admin=types.SimpleNamespace(
                get_user_by_id=lambda uid: types.SimpleNamespace(
                    user=types.SimpleNamespace(user_metadata={"nome": "Marina Teste"})
                ),
                update_user_by_id=lambda uid, dados: None,
            )
        )

    def table(self, nome):
        return _Query(nome, self._registro, erro=self._erro_insert, retorno=self._origem)

    def rpc(self, nome, params):
        self._registro["rpcs"].append((nome, params))
        return _Query("rpc", self._registro, retorno={"modo": "fundadora", "slot": 1})


@pytest.fixture
def supabase_falso(monkeypatch):
    """Devolve uma fábrica: instala o dublê e entrega o registro das chamadas."""
    registro = {"inserts": [], "rpcs": []}

    def instalar(erro_insert=None, origem=None):
        admin = _Admin(registro, erro_insert=erro_insert, origem=origem)
        monkeypatch.setattr(sb, "get_supabase_admin", lambda: admin)
        monkeypatch.setattr(
            sb, "buscar_usuario_por_email",
            lambda email: types.SimpleNamespace(id="user-uuid-1"),
        )
        return registro

    return instalar


def _sessao(valor_cents, metadata, session_id="cs_test_1", mode="subscription"):
    assinatura = mode == "subscription"
    return types.SimpleNamespace(
        id=session_id,
        metadata=metadata,
        amount_total=valor_cents,
        currency="usd",
        mode=mode,
        payment_intent=None if assinatura else "pi_1",
        subscription="sub_123" if assinatura else None,
        customer="cus_1",
        customer_email="marina@exemplo.com",
        customer_details={"email": "marina@exemplo.com"},
    )


def _invoice(invoice_id, billing_reason, valor_cents=25000):
    return types.SimpleNamespace(
        id=invoice_id,
        customer="cus_1",
        amount_paid=valor_cents,
        currency="usd",
        billing_reason=billing_reason,
        subscription="sub_123",
        attempt_count=1,
    )


def _ocupou_vaga(registro):
    return any(nome == "cadastrar_marina_fundadora" for nome, _ in registro["rpcs"])


def test_pagamento_de_200_ocupa_vaga_mesmo_sem_metadata(supabase_falso):
    """O Payment Link pode não ter metadata.programa configurado no painel.

    Se a vaga não fosse ocupada, marinas_fundadoras ficaria em zero para sempre
    e toda marina seguinte continuaria recebendo o link de US$ 200.
    """
    registro = supabase_falso()
    preco_fundadora = settings.LAUNCH_PRICE_MONTHLY * 100

    StripeService()._handle_checkout_completed(
        _sessao(preco_fundadora, {"plan_type": "marina"})
    )

    assert _ocupou_vaga(registro)
    assert any(tabela == "payments" for tabela, _ in registro["inserts"])


def test_pagamento_oficial_nao_ocupa_vaga_fundadora(supabase_falso):
    registro = supabase_falso()
    preco_oficial = settings.TRADITIONAL_PRICE_MONTHLY * 100

    StripeService()._handle_checkout_completed(
        _sessao(preco_oficial, {"plan_type": "marina"})
    )

    assert not _ocupou_vaga(registro)


def test_dossie_de_200_nao_ocupa_vaga_fundadora(supabase_falso):
    """A faixa de 36-45 pés do dossiê custa os mesmos US$ 200 da fundadora.

    O dossiê é vendido por Payment Link próprio, sem metadata, e é pagamento
    avulso — não pode ocupar vaga nem liberar acesso de marina.
    """
    registro = supabase_falso()
    preco_fundadora = settings.LAUNCH_PRICE_MONTHLY * 100

    StripeService()._handle_checkout_completed(
        _sessao(preco_fundadora, {}, session_id="cs_dossie", mode="payment")
    )

    # O pagamento é gravado normalmente: prova que o fluxo rodou até o fim e
    # que a vaga ficou de fora por decisão, não por erro no meio do caminho.
    assert any(tabela == "payments" for tabela, _ in registro["inserts"])
    assert not _ocupou_vaga(registro)


def test_metadata_explicito_continua_valendo(supabase_falso):
    registro = supabase_falso()

    StripeService()._handle_checkout_completed(
        _sessao(settings.TRADITIONAL_PRICE_MONTHLY * 100,
                {"programa": "marina_fundadora"})
    )

    assert _ocupou_vaga(registro)


def test_reentrega_do_mesmo_checkout_nao_reprocessa(supabase_falso):
    """O Stripe reentrega o evento quando não recebe 200 — não pode contar duas vezes."""
    registro = supabase_falso(
        erro_insert='duplicate key value violates unique constraint (23505)'
    )

    resultado = StripeService()._handle_checkout_completed(
        _sessao(settings.LAUNCH_PRICE_MONTHLY * 100, {"programa": "marina_fundadora"})
    )

    assert resultado["status"] == "duplicate"
    assert registro["rpcs"] == []


def test_primeira_fatura_nao_duplica_o_dinheiro(supabase_falso):
    """A fatura de criação da assinatura já entrou via checkout.session.completed."""
    registro = supabase_falso(
        origem=[{"usuario_id": "user-uuid-1", "plan_type": "marina",
                 "payment_type": "subscription"}]
    )

    StripeService()._handle_invoice_paid(_invoice("in_1", "subscription_create"))

    assert registro["inserts"] == []


def test_renovacao_mensal_e_registrada(supabase_falso):
    """Recorrência é o produto: sem isto a base só conhece o primeiro mês."""
    registro = supabase_falso(
        origem=[{"usuario_id": "user-uuid-1", "plan_type": "marina",
                 "payment_type": "subscription"}]
    )

    StripeService()._handle_invoice_paid(_invoice("in_2", "subscription_cycle"))

    gravados = [p for tabela, p in registro["inserts"] if tabela == "payments"]
    assert len(gravados) == 1
    assert gravados[0]["amount"] == float(settings.TRADITIONAL_PRICE_MONTHLY)
    assert gravados[0]["stripe_invoice_id"] == "in_2"
    assert gravados[0]["usuario_id"] == "user-uuid-1"


def test_lookup_key_separa_precos_diferentes():
    """Foi a busca por valor que quebrou todo checkout criado pela API."""
    chave = StripeService._lookup_key
    assert chave(20000, "usd", True) != chave(25000, "usd", True)
    assert chave(20000, "usd", True) != chave(20000, "usd", False)
    assert chave(25000, "USD", True) == chave(25000, "usd", True)
