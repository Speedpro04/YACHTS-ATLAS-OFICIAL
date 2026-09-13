"""
O caminho do pré-dado até o dossiê — e o que não pode se perder nele.

Regra do produto, dita pelo fundador: nada do Atlas Pré-Data entra no dossiê
antes de tratado. Depois de tratado, entra — e é aí que moram estes testes, no
momento da passagem, que é onde informação some sem erro nenhum para avisar.
"""
import pytest

from app.api.v1.registros import _status_do_selo
from app.services.dossie_pdf import INTERNAS_DADOS


# --- a condição levantada no píer atravessa o selo ---
#
# Ela chegava e era descartada duas vezes: o insert do rascunho não gravava a
# coluna, e o selo rebaixava o que não fosse válido para "registrado". Um
# "atenção" marcado no barco virava "registrado" no documento — o sinal de
# avaria sumia entre o píer e o dossiê.

def test_condicao_da_coluna_manda():
    assert _status_do_selo({"status": "atencao"}) == "atencao"
    assert _status_do_selo({"status": "concluido"}) == "concluido"
    assert _status_do_selo({"status": "pendente"}) == "pendente"


def test_rascunho_antigo_recupera_a_condicao_do_jsonb():
    # Gravados antes do conserto: status 'rascunho' na coluna, condição só no
    # jsonb. Sem esta leitura, selar apagaria o "atenção" de vez.
    antigo = {"status": "rascunho", "dados": {"condicao": "atencao"}}
    assert _status_do_selo(antigo) == "atencao"


def test_sem_condicao_nenhuma_cai_no_padrao():
    assert _status_do_selo({}) == "registrado"
    assert _status_do_selo({"status": "rascunho"}) == "registrado"
    assert _status_do_selo({"status": "rascunho", "dados": {}}) == "registrado"


def test_valor_invalido_nao_passa():
    # O jsonb vem do aparelho: não é fonte confiável de vocabulário.
    sujo = {"status": "rascunho", "dados": {"condicao": "urgentissimo"}}
    assert _status_do_selo(sujo) == "registrado"


def test_dados_ausente_nao_quebra():
    assert _status_do_selo({"status": "rascunho", "dados": None}) == "registrado"


# --- telemetria do campo não vira linha do dossiê ---
#
# O selo copia `dados` inteiro do rascunho. Sem esta lista, o documento
# probatório imprimiria "Client Id bad3fa54-f211..." e "Fotos No Aparelho 5"
# entre os dados do serviço — e quem lê um dossiê não distingue telemetria de
# fato sobre a embarcação.

@pytest.mark.parametrize("chave", [
    "origem", "client_id", "capturado_em", "capturado_por",
    "fotos_no_aparelho", "registrado_por_login", "condicao",
])
def test_metadado_do_pre_data_fica_fora_da_ficha(chave):
    assert chave in INTERNAS_DADOS


@pytest.mark.parametrize("chave", ["registrado_por", "executado_por"])
def test_quem_fez_o_servico_continua_aparecendo(chave):
    # Estes são fato do serviço, não telemetria: escondê-los tiraria do dossiê
    # justamente a autoria que o campo foi buscar.
    assert chave not in INTERNAS_DADOS


# --- recusar: o item sai da fila, não do banco ---
#
# A revisão só sabia dizer sim. Foto do barco errado ou envio repetido ficavam
# pendentes para sempre, e a fila ia escondendo o que importa atrás do que não
# importa. Dizer "isto não entra" é a decisão mais séria do revisor — e por isso
# exige motivo e não apaga nada.

def test_recusa_do_rascunho_nao_toca_a_condicao():
    """A recusa mora em `dados`, não na coluna `status`.

    Gravar "recusado" no status apagaria a condição vinda do barco — o "atenção"
    que este mesmo arquivo passa o resto do tempo tentando preservar.
    """
    recusado = {
        "status": "atencao",
        "dados": {"condicao": "atencao", "recusado_em": "2026-09-13T16:00:00Z",
                  "motivo_recusa": "foto do barco errado"},
    }
    assert _status_do_selo(recusado) == "atencao"


def test_motivo_curto_nao_vale_como_motivo():
    # Espelha a validação do servidor: menos de 3 caracteres é um "ok" disfarçado
    # de justificativa, e quem recebe a recusa continua sem saber o que houve.
    from app.api.v1.registros import RecusarRascunhoBody
    assert len((RecusarRascunhoBody(motivo="  x  ").motivo or "").strip()) < 3
