"""
Fila vazia não custa 1.400 consultas por dia.

O log de produção de 30–31/08/2026 mostrou a agenda consultando o Supabase a
cada 60 segundos, por horas seguidas, e voltando `{'enviados': 0, ...}` todas
as vezes. Duas coisas erradas ao mesmo tempo:

1. **O custo.** Intervalo fixo com fila vazia = ~1.400 consultas/dia para não
   achar nada. Numa plataforma que ainda está no plano gratuito do Supabase,
   isso é cota queimada sem nenhum lead abordado.

2. **O ruído.** O `agenda.py` já dizia no próprio comentário que só queria
   registrar "quando algo aconteceu, para o log não virar ruído que ninguém
   lê" — mas `prospeccao_service` logava o resumo em INFO **incondicional**,
   anulando a intenção. O log ficou ilegível justamente para quem precisa
   achar o envio de verdade no meio dele.

O RECUO NÃO ATRASA NINGUÉM DE FORMA RELEVANTE
---------------------------------------------
O lead só fica elegível DEPOIS da carência (a janela em que uma indicação
errada ainda pode ser cancelada). O recuo só acrescenta espera a partir daí,
e o pior caso é `carência + teto`. Assim que um lead aparece, a volta
seguinte já retoma o ritmo rápido — não fica preso no ritmo lento.
"""
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
AGENDA = APP / "services" / "agenda.py"
SERVICO = APP / "services" / "prospeccao_service.py"


def _codigo(caminho: Path) -> str:
    return "\n".join(l for l in caminho.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith("#"))


def _espera(base: int, teto: int, voltas_vazias: int, achou_no_fim=False) -> int:
    """A regra do laço, isolada do asyncio."""
    espera = base
    for _ in range(voltas_vazias):
        espera = min(espera * 2, teto)
    if achou_no_fim:
        espera = base
    return espera


# ─────────────────────────────────────────────────────────────────────────────
# O recuo
# ─────────────────────────────────────────────────────────────────────────────

def test_a_espera_dobra_enquanto_a_fila_esta_vazia():
    assert _espera(60, 600, 1) == 120
    assert _espera(60, 600, 2) == 240
    assert _espera(60, 600, 3) == 480


def test_o_recuo_tem_teto():
    """Sem teto, uma fila vazia por um fim de semana levaria a espera a horas
    — e o primeiro lead de segunda ficaria parado."""
    assert _espera(60, 600, 10) == 600
    assert _espera(60, 600, 100) == 600


def test_achar_trabalho_retoma_o_ritmo_rapido():
    """O ponto do recuo é economizar quando não há nada, não punir quando
    há. Um lead encontrado depois de horas de silêncio devolve a agenda ao
    intervalo normal na mesma volta."""
    assert _espera(60, 600, 8, achou_no_fim=True) == 60


def test_bloqueado_e_sem_numero_tambem_contam_como_trabalho():
    """`bloqueados` e `sem_numero` significam que HAVIA fila — o lote fez
    trabalho, só não resultou em envio. Tratar isso como silêncio faria a
    agenda recuar justamente quando a fila está se movendo."""
    codigo = _codigo(AGENDA)
    i = codigo.find("houve_trabalho = bool(")
    assert i > 0, "a agenda parou de distinguir volta cheia de volta vazia"
    bloco = codigo[i:i + 260]
    for campo in ("enviados", "falharam", "bloqueados", "sem_numero"):
        assert campo in bloco, f"{campo} sumiu da conta do que é trabalho"


def test_o_laco_usa_a_espera_calculada():
    """Se voltar a dormir o intervalo fixo, o recuo vira decoração."""
    codigo = _codigo(AGENDA)
    assert "await asyncio.sleep(espera)" in codigo
    i = codigo.find("while True:")
    corpo = codigo[i:]
    assert "await asyncio.sleep(settings.PROSPECCAO_INTERVALO_SEGUNDOS)" not in corpo, (
        "o laço voltou ao intervalo fixo"
    )


def test_o_teto_e_configuravel():
    from app.core.config import settings
    assert hasattr(settings, "PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS")
    assert settings.PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS > 0


def test_o_teto_e_maior_que_o_intervalo_normal():
    """Teto menor que o intervalo base tornaria o "recuo" um avanço."""
    from app.core.config import settings
    assert (settings.PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS
            >= settings.PROSPECCAO_INTERVALO_SEGUNDOS)


# ─────────────────────────────────────────────────────────────────────────────
# O silêncio
# ─────────────────────────────────────────────────────────────────────────────

def test_volta_vazia_nao_escreve_em_info():
    """Era esta linha que enchia o log: um INFO por volta, a cada 60s, dias
    a fio."""
    codigo = _codigo(SERVICO)
    i = codigo.find('logger.info(f"Prospecção — lote concluído')
    assert i > 0, "o log do lote sumiu — ele ainda precisa existir quando há envio"

    # Tem que estar sob condição, não solto no fluxo.
    trecho = codigo[max(0, i - 300):i]
    assert 'if resumo.get("enviados")' in trecho, (
        "o resumo voltou a ser registrado em INFO incondicionalmente"
    )


def test_a_volta_vazia_ainda_e_observavel():
    """Silenciar não é apagar: em DEBUG a volta vazia continua visível para
    quem estiver investigando por que um lead não saiu."""
    codigo = _codigo(SERVICO)
    assert "logger.debug(" in codigo, (
        "a volta vazia sumiu por completo — investigar 'por que não enviou' "
        "ficaria sem rastro nenhum"
    )
