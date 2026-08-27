"""
A vaga de fundadora reconhecida pela reserva que o próprio cadastro criou.

Existe por causa de 27/08/2026. A Antioquia Marina preencheu o cadastro da
Lançamento, o sistema reservou uma das 4 vagas de SP no nome dela, ela pagou —
e a vaga continuou "reservado", vencendo em três horas.

O pagamento entrou, o acesso abriu, o e-mail de boas-vindas saiu com o nome
certo. Só a vaga ficou para trás, sem erro nenhum em lugar algum: do ponto de
vista do sistema, tinha sido um sucesso.

A causa era estreiteza de vista. O código só sabia perguntar duas coisas —
"veio do link certo?" e "o valor bate?" — e nenhuma das duas responde nada num
link de teste. A linha da reserva estava no banco, no nome daquele e-mail,
criada minutos antes por ele mesmo.
"""
from datetime import datetime, timedelta, timezone

import pytest

import app.core.supabase as supa
from app.services.stripe_service import StripeService


class _Consulta:
    """Imita o encadeamento do cliente Supabase: table().select()...execute()."""

    def __init__(self, linhas, ocupadas=0):
        self._linhas = linhas
        self._ocupadas = ocupadas
        self._contando = False

    def __call__(self, *_a, **_k): return self
    def table(self, _nome): return self
    def rpc(self, _nome, _args=None):
        self._contando = True
        return self
    def select(self, *_a, **_k): return self
    def ilike(self, *_a, **_k): return self
    def neq(self, *_a, **_k): return self
    def limit(self, *_a, **_k): return self
    def execute(self):
        dados = self._ocupadas if self._contando else self._linhas
        self._contando = False
        return type("R", (), {"data": dados})()


@pytest.fixture
def servico():
    s = StripeService()
    StripeService._URL_DO_LINK.clear()
    yield s
    StripeService._URL_DO_LINK.clear()


def _com_reserva(monkeypatch, linhas, ocupadas=0):
    consulta = _Consulta(linhas, ocupadas)
    monkeypatch.setattr(supa, "get_supabase_admin", lambda: consulta)


def _daqui(horas):
    return (datetime.now(timezone.utc) + timedelta(hours=horas)).isoformat()


RESERVA = [{"id": "1", "status": "reservado", "uf": "SP", "reservado_ate": None}]


# ------------------------------------------------------- o caso do defeito

def test_quem_tem_vaga_reservada_e_fundadora(servico, monkeypatch):
    _com_reserva(monkeypatch, [{**RESERVA[0], "reservado_ate": _daqui(3)}])
    assert servico._programa_do_checkout(
        type("S", (), {"payment_link": None})(), {}, "activescertus@gmail.com"
    ) == "marina_fundadora"


def test_sem_reserva_nao_inventa_fundadora(servico, monkeypatch):
    """Quem comprou outro produto da casa não pode virar marina fundadora."""
    _com_reserva(monkeypatch, [])
    assert servico._programa_do_checkout(
        type("S", (), {"payment_link": None})(), {}, "alguem@exemplo.com"
    ) is None


def test_sem_email_nao_consulta(servico, monkeypatch):
    def explode(): raise AssertionError("nao devia consultar o banco")
    monkeypatch.setattr(supa, "get_supabase_admin", explode)
    assert servico._tem_reserva_de_fundadora(None) is False
    assert servico._tem_reserva_de_fundadora("   ") is False


# ------------------------------------------------------- ordem das provas

def test_metadata_ganha_da_reserva(servico, monkeypatch):
    _com_reserva(monkeypatch, RESERVA)
    assert servico._programa_do_checkout(
        type("S", (), {"payment_link": None})(), {"programa": "marina_oficial"}, "x@y.com"
    ) == "marina_oficial"


def test_link_conhecido_ganha_da_reserva(servico, monkeypatch):
    """
    Comprou pelo link do Oficial: é oficial, mesmo que exista uma reserva velha
    no nome dela. O que ela pagou agora vale mais que o que reservou antes.
    """
    from app.core.config import settings
    _com_reserva(monkeypatch, RESERVA)
    StripeService._URL_DO_LINK["plink_of"] = settings.STRIPE_LINK_MARINA_OFICIAL_BRL
    assert servico._programa_do_checkout(
        type("S", (), {"payment_link": "plink_of"})(), {}, "x@y.com"
    ) == "marina_oficial"


def test_marina_ja_ativa_nao_precisa_de_reserva(servico, monkeypatch):
    """A consulta ignora status 'ativo' — quem já é fundadora não reativa."""
    _com_reserva(monkeypatch, [])   # o filtro neq('status','ativo') já excluiu
    assert servico._tem_reserva_de_fundadora("ativa@exemplo.com") is False


# ------------------------------------------------------- as armadilhas

def test_prazo_vencido_com_vaga_sobrando_ativa(servico, monkeypatch, caplog):
    """Venceu o prazo, mas o estado ainda tem espaço: honra e registra."""
    _com_reserva(monkeypatch, [{**RESERVA[0], "reservado_ate": _daqui(-2)}], ocupadas=2)
    with caplog.at_level("WARNING"):
        assert servico._tem_reserva_de_fundadora("tarde@exemplo.com") is True
    assert "FORA DO PRAZO" in caplog.text


def test_prazo_vencido_com_estado_lotado_nao_ativa(servico, monkeypatch, caplog):
    """
    São 20 vagas e ponto — 4 por estado, anunciadas na página. Não existe 5ª.
    Quem pagou preço de fundadora sem vaga recebe a diferença de volta, e isso
    é decisão de gente: o sistema só grita.
    """
    _com_reserva(monkeypatch, [{**RESERVA[0], "reservado_ate": _daqui(-2)}], ocupadas=4)
    with caplog.at_level("ERROR"):
        assert servico._tem_reserva_de_fundadora("tarde@exemplo.com") is False
    assert "VAGA FUNDADORA PERDIDA" in caplog.text


def test_sem_conseguir_contar_nao_arrisca_a_quinta(servico, monkeypatch, caplog):
    """Na dúvida sobre quantas estão ocupadas, não ativa."""
    class Instavel(_Consulta):
        def execute(self):
            if self._contando:
                raise RuntimeError("rpc fora do ar")
            return super().execute()
    monkeypatch.setattr(supa, "get_supabase_admin",
                        lambda: Instavel([{**RESERVA[0], "reservado_ate": _daqui(-2)}]))
    with caplog.at_level("ERROR"):
        assert servico._tem_reserva_de_fundadora("x@y.com") is False
    assert "nao consegui contar" in caplog.text


def test_banco_fora_do_ar_nao_derruba_o_pagamento(servico, monkeypatch):
    """Perder a ativação é ruim; derrubar o webhook é pior — aí nem o acesso sai."""
    def explode(): raise RuntimeError("conexao caiu")
    monkeypatch.setattr(supa, "get_supabase_admin", explode)
    assert servico._tem_reserva_de_fundadora("x@y.com") is False


def test_data_ilegivel_nao_tira_a_vaga_de_quem_pagou(servico, monkeypatch):
    """Formato estranho de data não pode custar a vaga de quem pagou no prazo."""
    _com_reserva(monkeypatch, [{**RESERVA[0], "reservado_ate": "ontem de manhã"}])
    assert servico._tem_reserva_de_fundadora("x@y.com") is True
