"""
Regressão da autorização dos registros — o histórico selado não vaza.

Os endpoints de `registros` **não verificavam nada**. Qualquer conta
autenticada lia os registros de qualquer barco sabendo o id — e o id é
previsível (`YA-IATE-2015-3A38`), então bastava trocar os dígitos finais para
varrer os clientes das outras marinas.

Escrever também passava: `_owner_do_ativo` apenas DESCOBRIA de quem era o
ativo para preencher o campo, sem perguntar se quem pedia tinha direito.

O histórico selado é o produto. Vazá-lo destrói o motivo de alguém confiar o
barco à plataforma — e a trava construída em `core/authz.py` ficava sendo
contornada justamente na tabela que mais importa.

A regra que estes testes guardam tem duas metades:

  • **ler** — a marina dona E o armador do barco (ver é direito dele);
  • **escrever** — só a marina. Rascunho, selagem e retificação inclusive.

A segunda é a que se perde sem querer: basta alguém trocar `_so_a_marina` por
`_pode_ler` "para o portal do dono funcionar" e o armador passa a escrever no
próprio dossiê, que deveria ser prova independente dele.
"""
import inspect
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1 import registros


def _fonte(nome: str) -> str:
    return inspect.getsource(getattr(registros, nome))


# --------------------------------------------------------------------------
# Nenhum endpoint fica sem guarda
# --------------------------------------------------------------------------

ESCRITA = [
    "create_registro",
    "retificar_registro",
    "create_rascunho",
    "update_rascunho",
    "descartar_rascunho",
    "selar_rascunho",
    "list_rascunhos",   # rascunho é trabalho em andamento da marina
]

LEITURA = ["list_registros", "get_registro_stats"]


@pytest.mark.parametrize("endpoint", ESCRITA)
def test_escrita_exige_ser_a_marina(endpoint):
    """
    O armador lê, não mexe.

    Selar é irreversível: sem esta trava, bastava um id de rascunho para selar
    trabalho de outra marina — e registro selado não se apaga.
    """
    fonte = _fonte(endpoint)
    assert "_so_a_marina(" in fonte, f"{endpoint} está sem guarda de escrita"


@pytest.mark.parametrize("endpoint", LEITURA)
def test_leitura_inclui_o_armador(endpoint):
    """Ver o próprio barco é direito do dono — é o Portal do Proprietário."""
    fonte = _fonte(endpoint)
    assert "_pode_ler(" in fonte, f"{endpoint} está sem guarda de leitura"


def test_todo_endpoint_tem_alguma_guarda():
    """
    Rede final: endpoint novo nasce protegido ou a suíte quebra.

    Vale mais que os testes acima — eles cobrem o que existe hoje; este cobre
    o que alguém acrescentar amanhã.
    """
    fonte = inspect.getsource(registros)
    blocos = fonte.split("@router.")[1:]
    for bloco in blocos:
        assinatura = bloco.split("\n")[1] if "\n" in bloco else bloco
        rota = bloco.split("\n")[0]
        assert "_so_a_marina(" in bloco or "_pode_ler(" in bloco, (
            f"Endpoint sem autorização: @router.{rota} ({assinatura.strip()})"
        )


# --------------------------------------------------------------------------
# A distinção entre ler e escrever não pode se perder
# --------------------------------------------------------------------------

def test_ler_e_escrever_usam_guardas_diferentes():
    """
    Se as duas virarem a mesma coisa, ou o dono perde o portal ou passa a
    escrever no dossiê. Nenhum dos dois é aceitável.
    """
    ler = _fonte("_pode_ler")
    escrever = _fonte("_so_a_marina")
    assert "incluir_proprietario=True" in ler
    assert "incluir_proprietario" not in escrever


def test_rascunho_resolve_o_ativo_antes_de_autorizar():
    """
    Estes endpoints recebem o id do RASCUNHO, não do ativo.

    Sem o salto a mais, a checagem seria feita contra um id que não é de
    ativo nenhum — e passaria batido.
    """
    for endpoint in ("update_rascunho", "descartar_rascunho", "selar_rascunho"):
        fonte = _fonte(endpoint)
        assert "_ativo_do_rascunho(" in fonte, f"{endpoint} autoriza contra o id errado"
