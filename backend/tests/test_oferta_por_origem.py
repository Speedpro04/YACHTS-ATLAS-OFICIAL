"""
A origem do cadastro deixou de decidir qualquer coisa.

A regra tinha duas linhas e era a mais cara de errar:

  • site oficial     → oferta oficial, sem vaga;
  • LP de lançamento → vaga fundadora, enquanto houver no estado.

Hoje é UMA: toda origem recebe a Oficial, a US$ 140/mês. O preço já era o
mesmo desde 13/10/2026; em 14/10 o programa fundador foi suspenso pelo
fundador — *"vamos deixar de lado a página fundadora, iremos trabalhar só com
a oficial nesse novo valor"* — e a vaga, que era a última coisa que a campanha
dava, parou de ser concedida.

O QUE ESTES TESTES PROTEGEM AGORA: que `data.origem` não volte a abrir caminho
para a reserva sem uma decisão comercial atrás. A lista `ORIGENS_DE_LANCAMENTO`
continua escrita em `leads.py`, dormente — e código dormente perto de um `if`
é como o religamento acontece sem ninguém querer.
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
def test_fora_da_campanha_recebe_a_oficial(origem):
    sb = _Supabase()

    oferta = _oferta_marina(sb, _marina(origem=origem))

    assert oferta["preco_mensal"] == settings.PRECO_MENSAL_USD
    assert oferta["oferta"] == "oficial"
    # E, principalmente: não encostou na reserva.
    assert sb.rpcs == []


@pytest.mark.parametrize("origem", ["lancamento", "LANCAMENTO", "lp-fundadoras", " lancamento "])
def test_a_campanha_tambem_recebe_a_oficial(origem):
    """O ponto da suspensão.

    Estas quatro origens eram a porta da vaga — a lista continua em
    `ORIGENS_DE_LANCAMENTO`, e é justamente por isso que elas são as que
    precisam estar sob teste. Entram como qualquer outra.
    """
    sb = _Supabase()

    oferta = _oferta_marina(sb, _marina(origem=origem))

    assert oferta["preco_mensal"] == settings.PRECO_MENSAL_USD
    assert oferta["oferta"] == "oficial"
    assert sb.rpcs == [], "a campanha não reserva mais vaga"


def test_toda_origem_recebe_exatamente_a_mesma_oferta():
    """Uma oferta só: mesmo preço, mesmo rótulo, mesmo checkout.

    Quebra se alguém reintroduzir qualquer bifurcação por origem — de preço,
    de vaga ou de link.
    """
    campanha = _oferta_marina(_Supabase(), _marina(origem="lancamento"))
    site = _oferta_marina(_Supabase(), _marina(origem="google"))

    assert campanha["oferta"] == site["oferta"] == "oficial"
    assert campanha["preco_mensal"] == site["preco_mensal"] == 140
    assert campanha["checkout_url"] == site["checkout_url"]


def test_ninguem_recebe_prazo_de_reserva():
    """Sem vaga não há relógio correndo, para origem nenhuma."""
    assert _oferta_marina(_Supabase(), _marina())["reserva_expira_em"] is None
    assert _oferta_marina(_Supabase(), _marina(origem="lancamento"))["reserva_expira_em"] is None
