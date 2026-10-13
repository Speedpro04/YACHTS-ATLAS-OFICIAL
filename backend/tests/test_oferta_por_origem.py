"""
Regressão da oferta por origem — a regra mais simples e mais cara de errar.

  • site oficial     → oferta oficial, sem vaga;
  • LP de lançamento → vaga fundadora, enquanto houver no estado.

O PREÇO É O MESMO NAS DUAS desde 13/10/2026 (US$ 140 / R$ 647,00): o que a
campanha dá é a VAGA, e com ela os 18 meses de dossiê 100% da marina. Antes a
diferença era de preço — US$ 200 contra US$ 250 — e é daí que vem o nome
antigo destes testes.

A vaga pertence à CAMPANHA, não ao estado da marina. Sem esta separação,
qualquer um que se cadastrasse pelo site oficial consumia uma das 20 vagas sem
nunca ter visto a campanha — e a exclusividade da LP não valia nada.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1.leads import _oferta_marina
from app.core.config import settings


class _Supabase:
    """Devolve sempre vaga fundadora disponível — o pior caso para o teste."""

    def __init__(self):
        self.rpcs = []

    def rpc(self, nome, params):
        self.rpcs.append(nome)
        return types.SimpleNamespace(
            execute=lambda: types.SimpleNamespace(
                data={"modo": "fundadora", "uf": "SC", "vagas_restantes": 3}
            )
        )


def _marina(origem=None, state="SC"):
    return types.SimpleNamespace(
        name="Marina Teste", email="marina@exemplo.com", phone="48999999999",
        state=state, origem=origem,
    )


@pytest.mark.parametrize("origem", [None, "", "   ", "google", "instagram", "oficial"])
def test_fora_da_campanha_nao_ganha_vaga_fundadora(origem):
    """Mesmo em estado com vaga livre: sem origem de campanha, é a oficial."""
    sb = _Supabase()

    oferta = _oferta_marina(sb, _marina(origem=origem))

    assert oferta["preco_mensal"] == settings.PRECO_MENSAL_USD
    assert oferta["oferta"] == "oficial"
    # E, principalmente: não encostou na reserva. Uma das 20 vagas não pode ser
    # consumida — nem temporariamente — por quem não veio da campanha.
    assert sb.rpcs == []


@pytest.mark.parametrize("origem", ["lancamento", "LANCAMENTO", "lp-fundadoras", " lancamento "])
def test_campanha_de_lancamento_recebe_a_vaga_fundadora(origem):
    sb = _Supabase()

    oferta = _oferta_marina(sb, _marina(origem=origem))

    assert oferta["preco_mensal"] == settings.PRECO_MENSAL_USD
    assert oferta["oferta"] == "fundadora"
    assert sb.rpcs == ["reservar_vaga_fundadora"]


def test_as_duas_ofertas_custam_o_mesmo():
    """O preço é um só, e quem reintroduzir dois valores quebra aqui.

    Era a diferença entre US$ 200 e US$ 250. Hoje a campanha vende vaga e
    bônus, não desconto — e a página anuncia um número só.
    """
    fundadora = _oferta_marina(_Supabase(), _marina(origem="lancamento"))
    oficial = _oferta_marina(_Supabase(), _marina(origem="google"))

    assert fundadora["oferta"] == "fundadora"
    assert oficial["oferta"] == "oficial"
    assert fundadora["preco_mensal"] == oficial["preco_mensal"] == 140


def test_so_a_campanha_recebe_prazo_de_reserva():
    """Sem reserva não há relógio correndo — a oficial não promete prazo nenhum."""
    assert _oferta_marina(_Supabase(), _marina())["reserva_expira_em"] is None
    assert _oferta_marina(_Supabase(), _marina(origem="lancamento"))["reserva_expira_em"]
