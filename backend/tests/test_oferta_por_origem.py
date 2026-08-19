"""
Regressão do preço por origem — a regra mais simples e mais cara de errar.

  • site oficial  → US$ 250, sempre;
  • LP de lançamento → US$ 200, enquanto houver vaga fundadora.

O preço de fundadora pertence à CAMPANHA, não ao estado da marina. Sem esta
separação, qualquer um que se cadastrasse pelo site oficial levava US$ 200 e
consumia uma das 20 vagas sem nunca ter visto a campanha — e a exclusividade
da LP não valia nada.
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
def test_fora_da_campanha_paga_a_tabela_oficial(origem):
    """Mesmo em estado com vaga livre: sem origem de campanha, é US$ 250."""
    sb = _Supabase()

    oferta = _oferta_marina(sb, _marina(origem=origem))

    assert oferta["preco_mensal"] == settings.TRADITIONAL_PRICE_MONTHLY
    assert oferta["oferta"] == "oficial"
    # E, principalmente: não encostou na reserva. Uma das 20 vagas não pode ser
    # consumida — nem temporariamente — por quem não veio da campanha.
    assert sb.rpcs == []


@pytest.mark.parametrize("origem", ["lancamento", "LANCAMENTO", "lp-fundadoras", " lancamento "])
def test_campanha_de_lancamento_paga_o_preco_fundador(origem):
    sb = _Supabase()

    oferta = _oferta_marina(sb, _marina(origem=origem))

    assert oferta["preco_mensal"] == settings.LAUNCH_PRICE_MONTHLY
    assert oferta["oferta"] == "fundadora"
    assert sb.rpcs == ["reservar_vaga_fundadora"]


def test_so_a_campanha_recebe_prazo_de_reserva():
    """Sem reserva não há relógio correndo — a oficial não promete prazo nenhum."""
    assert _oferta_marina(_Supabase(), _marina())["reserva_expira_em"] is None
    assert _oferta_marina(_Supabase(), _marina(origem="lancamento"))["reserva_expira_em"]
