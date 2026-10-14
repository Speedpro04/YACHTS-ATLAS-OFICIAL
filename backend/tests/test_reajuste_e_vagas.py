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


def _cadastrou_vaga():
    """Quem o webhook cadastrou como fundadora, pelo nome da RPC que ele chama."""
    return [p.get("p_email") for nome, p in _RPCS_CHAMADAS
            if nome == "cadastrar_marina_fundadora"]


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
        _RPCS_CHAMADAS.append((nome, params))
        return _Query(retorno=self._resposta_rpc)


_RPCS_CHAMADAS: list = []


@pytest.fixture
def cenario(monkeypatch):
    """Instala o banco falso e espiões nos três efeitos que importam."""
    _RPCS_CHAMADAS.clear()
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


def _checkout_marina(session_id="cs_marina", programa=None):
    """Checkout de marina no nosso preço.

    `programa="marina_fundadora"` é a PROVA EXPLÍCITA que, desde a suspensão
    do programa (14/10/2026), é a única coisa que ainda concede vaga — e que
    só existe se alguém marcar o Payment Link no painel ou preencher
    STRIPE_LINK_MARINA_FUNDADORA. O cadastro não produz mais nenhuma das duas.
    """
    metadata = {"plan_type": "marina", "uf": "SC"}
    if programa:
        metadata["programa"] = programa
    return types.SimpleNamespace(
        id=session_id,
        metadata=metadata,
        amount_total=settings.PRECO_MENSAL_USD * 100,
        currency="usd",
        mode="subscription",
        payment_intent=None,
        subscription="sub_123",
        customer="cus_1",
        customer_email="marina@exemplo.com",
        customer_details={"email": "marina@exemplo.com"},
    )


def test_marina_comum_registra_o_reajuste_e_nao_ocupa_vaga(cenario):
    """O caminho de TODA marina desde a suspensão.

    Ela paga o nosso preço, o sistema reconhece a assinatura e grava os 12
    meses travados. A vaga, não: o dublê devolveria "fundadora" se fosse
    perguntado, e justamente por isso o teste prova que ninguém perguntou.
    """
    chamadas = cenario({"modo": "fundadora", "slot": 1, "uf": "SC"})

    StripeService()._handle_checkout_completed(_checkout_marina())

    assert chamadas["agendou"] == ["sub_123"]
    assert chamadas["avisou"] == []
    assert _cadastrou_vaga() == [], "sem prova explícita, não ocupa vaga"


def test_prova_explicita_ainda_concede_vaga(cenario):
    """O programa está suspenso, não demolido.

    Marcar `programa: marina_fundadora` no Payment Link continua funcionando —
    é assim que o fundador religa o lado do pagamento sem deploy. Se este
    teste quebrar, religar passou a exigir mexer em código.
    """
    chamadas = cenario({"modo": "fundadora", "slot": 1, "uf": "SC"})

    StripeService()._handle_checkout_completed(
        _checkout_marina("cs_explicita", programa="marina_fundadora")
    )

    assert _cadastrou_vaga() == ["marina@exemplo.com"]
    assert chamadas["agendou"] == ["sub_123"]
    assert chamadas["avisou"] == []


def test_prova_explicita_sem_vaga_no_estado_chama_o_humano(cenario):
    """O alerta continua de pé para o caso de religar com os 5 estados cheios."""
    chamadas = cenario({"modo": "tradicional", "motivo": "vagas_do_estado_esgotadas"})

    StripeService()._handle_checkout_completed(
        _checkout_marina("cs_sem_vaga", programa="marina_fundadora")
    )

    assert chamadas["avisou"] == ["marina@exemplo.com"]
    # Ela paga o mesmo que todas: os 12 meses travados são dela de qualquer jeito.
    assert chamadas["agendou"] == ["sub_123"]


def test_assinatura_de_outro_valor_nao_mexe_em_nada(cenario):
    """Outro produto da casa no mesmo webhook não é marina.

    Sem o nosso valor, nem link, nem metadata, não há prova de nada: nem vaga,
    nem régua de reajuste.
    """
    chamadas = cenario({"modo": "fundadora"})
    sessao = _checkout_marina("cs_outro")
    sessao.amount_total = 25000

    StripeService()._handle_checkout_completed(sessao)

    assert chamadas["agendou"] == []
    assert chamadas["avisou"] == []
    assert _cadastrou_vaga() == []
