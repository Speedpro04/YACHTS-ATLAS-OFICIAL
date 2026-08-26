"""
Quem comprou o quê — pelo link, não pelo valor.

Existe por causa de um defeito que ia acontecer no lançamento: com a venda em
real, a marina brasileira paga R$ 1.000 e a regra antiga procurava `usd 200`.
Ela entrava no sistema, não ocupava vaga de fundadora e não ganhava os 18 meses
de dossiê — sem erro nenhum aparecendo em lugar algum. Pagou e não recebeu.

O sintoma no banco era visível desde 19/08 e ninguém tinha lido: as duas linhas
de `marinas_fundadoras` com `stripe_checkout` vazio. Nenhuma delas veio de
pagamento.
"""
import pytest

from app.core.config import settings
from app.services.stripe_service import StripeService


class SessaoFalsa:
    """O mínimo que o handler lê de uma checkout.Session."""

    def __init__(self, payment_link=None):
        self.payment_link = payment_link


@pytest.fixture
def servico():
    s = StripeService()
    StripeService._URL_DO_LINK.clear()
    yield s
    StripeService._URL_DO_LINK.clear()


def _com_link(servico, plink_id: str, url: str) -> SessaoFalsa:
    """Semeia o cache para o teste não sair na rede."""
    StripeService._URL_DO_LINK[plink_id] = url
    return SessaoFalsa(payment_link=plink_id)


# ------------------------------------------------- reconhecer pelo link

def test_link_em_dolar_e_fundadora(servico, monkeypatch):
    """
    Os links em dólar estão vazios desde 26/08/2026 (desativados no painel),
    então o teste põe um: o que se verifica é a regra, não o estado de hoje.
    """
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_FUNDADORA", "https://buy.stripe.com/usd-fu")
    s = _com_link(servico, "plink_usd", settings.STRIPE_LINK_MARINA_FUNDADORA)
    assert servico._programa_do_checkout(s, {}) == "marina_fundadora"


def test_link_em_real_tambem_e_fundadora(servico):
    """O defeito. Mesma vaga, moeda diferente."""
    s = _com_link(servico, "plink_brl", settings.STRIPE_LINK_MARINA_FUNDADORA_BRL)
    assert servico._programa_do_checkout(s, {}) == "marina_fundadora"


def test_link_do_oficial_nao_e_fundadora(servico):
    s = _com_link(servico, "plink_of", settings.STRIPE_LINK_MARINA_OFICIAL_BRL)
    assert servico._programa_do_checkout(s, {}) == "marina_oficial"


def test_link_desconhecido_nao_vira_programa(servico):
    """Outro produto da casa no mesmo webhook não pode virar marina."""
    s = _com_link(servico, "plink_x", "https://buy.stripe.com/outroprodutoqualquer")
    assert servico._programa_do_checkout(s, {}) is None


# ------------------------------------------------- ordem das provas

def test_metadata_ganha_do_link(servico):
    """Intenção declarada no painel vale mais que inferência."""
    s = _com_link(servico, "plink_of", settings.STRIPE_LINK_MARINA_OFICIAL_BRL)
    assert servico._programa_do_checkout(s, {"programa": "marina_fundadora"}) == "marina_fundadora"


def test_sem_link_e_sem_metadata_nao_decide(servico):
    """Cai no último recurso, que é do handler — aqui a resposta é 'não sei'."""
    assert servico._programa_do_checkout(SessaoFalsa(), {}) is None
    assert servico._programa_do_checkout(SessaoFalsa(), None) is None


# ------------------------------------------------- as armadilhas

def test_link_nao_configurado_nao_vira_chave(monkeypatch):
    """
    String vazia como chave casaria com qualquer coisa e daria vaga de
    fundadora para quem não comprou.
    """
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_OFICIAL_BRL", "")
    monkeypatch.setattr(settings, "STRIPE_LINK_MARINA_FUNDADORA_BRL", "   ")
    mapa = StripeService._programas_por_link()
    assert "" not in mapa
    assert "   " not in mapa


def test_consulta_que_falha_nao_derruba_o_webhook(servico, monkeypatch):
    """Sem conseguir ler o link, segue sem programa — nunca levanta."""
    import app.services.stripe_service as mod

    class LinkQuebrado:
        @staticmethod
        def retrieve(_):
            raise RuntimeError("stripe fora do ar")

    monkeypatch.setattr(mod.stripe, "PaymentLink", LinkQuebrado)
    assert servico._url_do_payment_link(SessaoFalsa(payment_link="plink_novo")) is None
    assert servico._programa_do_checkout(SessaoFalsa(payment_link="plink_novo"), {}) is None


def test_link_e_consultado_uma_vez_so(servico, monkeypatch):
    """URL de Payment Link não muda; consultar a cada webhook seria desperdício."""
    import app.services.stripe_service as mod
    chamadas = []

    class LinkContado:
        @staticmethod
        def retrieve(plink_id):
            chamadas.append(plink_id)
            return type("L", (), {"url": settings.STRIPE_LINK_MARINA_FUNDADORA_BRL})()

    monkeypatch.setattr(mod.stripe, "PaymentLink", LinkContado)
    s = SessaoFalsa(payment_link="plink_conta")
    for _ in range(3):
        assert servico._programa_do_checkout(s, {}) == "marina_fundadora"
    assert chamadas == ["plink_conta"]
