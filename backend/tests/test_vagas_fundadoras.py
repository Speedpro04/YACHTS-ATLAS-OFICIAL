"""
Regressão da oferta da marina paga: 4 vagas fundadoras POR ESTADO.

O estado era coletado no formulário e descartado na hora de decidir o preço —
20 marinas de um mesmo estado podiam tomar todas as vagas. E, quando a consulta
ao banco falhava, o código assumia vaga livre e mandava todo mundo para o link
de US$ 200.

O Supabase é substituído por um dublê — nenhum teste toca no banco real.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1.leads import _oferta_marina, LINK_MARINA_FUNDADORA, LINK_MARINA_OFICIAL
from app.core.config import settings


class _SupabaseFalso:
    """Responde à RPC reservar_vaga_fundadora com um retorno combinado."""

    def __init__(self, retorno=None, erro=None):
        self._retorno = retorno
        self._erro = erro
        self.chamadas = []

    def rpc(self, nome, params):
        self.chamadas.append((nome, params))
        supa = self

        class _Exec:
            def execute(self_inner):
                if supa._erro:
                    raise Exception(supa._erro)
                return types.SimpleNamespace(data=supa._retorno)

        return _Exec()


def _cadastro(state):
    return types.SimpleNamespace(
        email="marina@exemplo.com",
        name="Marina Teste",
        phone="47999999999",
        state=state,
    )


def test_estado_fora_do_programa_vai_para_o_oficial():
    """Paraná não está no programa — tem de cair na oferta de US$ 250."""
    supabase = _SupabaseFalso(
        retorno={"modo": "tradicional", "motivo": "uf_fora_do_programa",
                 "preco_mensal": 250}
    )

    oferta = _oferta_marina(supabase, _cadastro("PR"))

    assert oferta["oferta"] == "oficial"
    assert oferta["preco_mensal"] == settings.TRADITIONAL_PRICE_MONTHLY
    assert oferta["checkout_url"] == LINK_MARINA_OFICIAL


def test_estado_com_vaga_recebe_oferta_fundadora():
    supabase = _SupabaseFalso(
        retorno={"modo": "fundadora", "status": "reservada", "uf": "SC",
                 "preco_mensal": 200, "vagas_restantes": 3}
    )

    oferta = _oferta_marina(supabase, _cadastro("SC"))

    assert oferta["oferta"] == "fundadora"
    assert oferta["preco_mensal"] == settings.LAUNCH_PRICE_MONTHLY
    assert oferta["checkout_url"] == LINK_MARINA_FUNDADORA
    assert oferta["uf"] == "SC"
    assert oferta["vagas_restantes"] == 3


def test_estado_lotado_vai_para_o_oficial():
    supabase = _SupabaseFalso(
        retorno={"modo": "tradicional", "motivo": "vagas_do_estado_esgotadas",
                 "uf": "SC", "vagas_restantes": 0}
    )

    oferta = _oferta_marina(supabase, _cadastro("SC"))

    assert oferta["oferta"] == "oficial"
    assert oferta["preco_mensal"] == settings.TRADITIONAL_PRICE_MONTHLY
    assert oferta["motivo"] == "vagas_do_estado_esgotadas"


def test_falha_na_reserva_cai_no_oficial_nao_no_desconto():
    """O fallback inverteu: sem reserva confirmada, cobra o preço oficial.

    Devolver a diferença para quem merecia US$ 200 é resolvível; prometer uma
    5ª vaga fundadora num estado que só tem 4 não é.
    """
    supabase = _SupabaseFalso(erro="conexao caiu")

    oferta = _oferta_marina(supabase, _cadastro("SC"))

    assert oferta["oferta"] == "oficial"
    assert oferta["preco_mensal"] == settings.TRADITIONAL_PRICE_MONTHLY
    assert oferta["checkout_url"] == LINK_MARINA_OFICIAL


def test_estado_e_repassado_para_a_reserva():
    """Sem o estado chegando na RPC não existe cota por UF."""
    supabase = _SupabaseFalso(
        retorno={"modo": "fundadora", "uf": "BA", "vagas_restantes": 3}
    )

    _oferta_marina(supabase, _cadastro("BA"))

    nome, params = supabase.chamadas[0]
    assert nome == "reservar_vaga_fundadora"
    assert params["p_uf"] == "BA"
    assert params["p_email"] == "marina@exemplo.com"


@pytest.mark.parametrize("uf", ["SC", "SP", "RJ", "ES", "BA"])
def test_os_cinco_estados_do_programa(uf):
    supabase = _SupabaseFalso(
        retorno={"modo": "fundadora", "uf": uf, "vagas_restantes": 3}
    )

    assert _oferta_marina(supabase, _cadastro(uf))["oferta"] == "fundadora"


def test_total_de_vagas_bate_com_quatro_por_estado():
    from app.core.config import LAUNCH_STATES

    assert settings.LAUNCH_SLOTS == settings.LAUNCH_SLOTS_PER_STATE * len(LAUNCH_STATES)
