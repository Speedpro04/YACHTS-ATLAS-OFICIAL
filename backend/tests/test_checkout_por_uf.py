"""
Em que moeda a marina é cobrada — decidido pelo estado dela.

Em 19/08/2026 um Visa recusou uma cobrança de US$ 250 com "moeda não aceita".
Cartão brasileiro costuma vir com compra internacional bloqueada, e Elo e
Hipercard — comuns em conta empresarial — são nacionais: em dólar não passam
de jeito nenhum.

O preço anunciado continua em dólar. O real é forma de pagamento, não oferta
diferente.
"""
import pytest

from app.api.v1.leads import UFS_DO_BRASIL, _checkout, _oferta_oficial
from app.core.config import settings


class DadosFalsos:
    def __init__(self, state=None, origem=None, email="marina@exemplo.com", name="Marina X"):
        self.state, self.origem, self.email, self.name = state, origem, email, name


# ------------------------------------------------------------ o caso comum

@pytest.mark.parametrize("uf", ["SC", "SP", "RJ", "ES", "BA", "PR", "AM"])
def test_marina_brasileira_paga_em_real(uf):
    url, moeda = _checkout(fundadora=True, uf=uf)
    assert moeda == "brl"
    assert url == settings.STRIPE_LINK_MARINA_FUNDADORA_BRL


def test_uf_minuscula_e_com_espaco_tambem_conta():
    """O estado vem do CEP e do formulário — não dá para confiar no formato."""
    assert _checkout(fundadora=False, uf=" sc ")[1] == "brl"
    assert _checkout(fundadora=False, uf="Sp")[1] == "brl"


def test_fundadora_e_oficial_vao_para_links_diferentes():
    assert _checkout(True, "SC")[0] != _checkout(False, "SC")[0]


# ------------------------------------------------------------ o resto do mundo

@pytest.mark.parametrize("uf", ["FL", "CA", "XX", "", None, "  "])
def test_fora_do_brasil_continua_em_dolar(uf):
    assert _checkout(fundadora=False, uf=uf)[1] == "usd"
    assert _checkout(fundadora=True, uf=uf)[1] == "usd"


def test_as_27_ufs_estao_na_lista():
    """Faltar uma UF significa marina daquele estado cobrada em dólar sem motivo."""
    assert len(UFS_DO_BRASIL) == 27


# ------------------------------------------------------------ as armadilhas

def test_sem_link_em_real_cai_no_dolar(monkeypatch):
    """
    Melhor cobrar na moeda de sempre do que mandar a marina para uma URL que
    não existe. Vale para a janela entre criar o preço e publicar o link.
    """
    import app.api.v1.leads as mod
    monkeypatch.setattr(mod, "LINK_MARINA_OFICIAL_BRL", "")
    monkeypatch.setattr(mod, "LINK_MARINA_FUNDADORA_BRL", "   ")
    assert _checkout(fundadora=False, uf="SC")[1] == "usd"
    assert _checkout(fundadora=True, uf="SC")[1] == "usd"


def test_oferta_oficial_leva_a_uf_ate_o_checkout():
    """
    Sem isto a rota morre no meio: a oferta oficial não recebia estado nenhum,
    e toda marina brasileira que chegasse por fora da campanha ia para o dólar.
    """
    assert _oferta_oficial("RJ")["moeda_cobranca"] == "brl"
    assert _oferta_oficial(None)["moeda_cobranca"] == "usd"


def test_preco_anunciado_continua_em_dolar():
    """O real não é oferta diferente — a página segue dizendo US$ 250."""
    oferta = _oferta_oficial("SP")
    assert oferta["preco_mensal"] == settings.TRADITIONAL_PRICE_MONTHLY == 250
