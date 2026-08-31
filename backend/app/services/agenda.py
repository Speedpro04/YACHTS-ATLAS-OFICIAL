"""
Agenda interna — a régua de cobrança roda sozinha, dentro da aplicação.

Por que aqui, e não num cron externo
------------------------------------
O jeito clássico seria agendar `python -m app.services.cron_cobranca` no
servidor. Funciona — até o dia em que para de funcionar.

Cron externo é a coisa mais silenciosa que existe numa operação de uma pessoa
só: some numa migração de servidor, quebra quando o caminho do Python muda,
para quando alguém recria o container. E ninguém percebe, porque a ausência de
aviso é indistinguível de "não havia ninguém devendo". O erro só aparece na
conversa mais cara possível: a marina cortada dizendo que nunca foi avisada.

Estando dentro da aplicação, ela vive enquanto a aplicação viver. Se o Atlas
está no ar, a régua está rodando — e se o Atlas caiu, você já tem um problema
maior e mais visível.

Por que isto é seguro
---------------------
A régua é idempotente por construção (`marco_devido` consulta os avisos já
enviados). Rodar duas vezes no mesmo dia não manda aviso duplicado, e ficar
dias sem rodar não perde o aviso — ela envia o marco vencido mais recente.

Isso é o que permite rodar aqui sem medo: o pior caso de uma reexecução é uma
consulta a mais ao banco.

Ainda assim, uma marca no cache evita reprocessar a cada reinício do
container — em dia de deploy, seriam várias execuções seguidas sem propósito.

E o corte NÃO depende disto
---------------------------
O acesso é cortado na leitura, pelo porteiro em `core/acesso.py`. Esta rotina
só AVISA. Ela pode falhar, atrasar ou ficar dias parada sem que ninguém seja
cortado por engano nem deixe de ser cortado.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Intervalo entre verificações. Curto o bastante para que um container que
# subiu à noite não deixe o aviso do dia para depois; a marca no cache impede
# que isso vire trabalho repetido.
_INTERVALO_SEGUNDOS = 6 * 3600

# Espera antes da primeira execução: deixa a aplicação terminar de subir e
# responder aos healthchecks antes de disputar CPU com uma varredura no banco.
_ESPERA_INICIAL = 90

_CHAVE_MARCA = "cobranca:ultimo_dia_processado"
_TTL_MARCA = 3 * 24 * 3600


def _hoje() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _ja_rodou_hoje() -> bool:
    """
    Sem cache configurado, devolve False — e a régua roda.

    Preferir rodar de novo a não rodar: repetir custa uma consulta; não rodar
    custa uma marina cortada sem aviso.
    """
    try:
        from app.core.cache import cache_get_json
        return cache_get_json(_CHAVE_MARCA) == _hoje()
    except Exception:
        return False


def _marcar_rodado() -> None:
    try:
        from app.core.cache import cache_set_json
        cache_set_json(_CHAVE_MARCA, _hoje(), ttl=_TTL_MARCA)
    except Exception:
        pass


def _processar() -> None:
    """Uma passada da régua. Síncrona — roda fora do event loop."""
    from app.services.cobranca_service import processar_inadimplentes
    from app.services.notify_service import notificar_fundador

    resumo = processar_inadimplentes()
    logger.info(
        "Régua de cobrança: em atraso=%s avisos=%s cortadas=%s erros=%s",
        resumo.get("em_atraso"), resumo.get("avisos_enviados"),
        resumo.get("cortadas"), resumo.get("erros"),
    )

    # Silêncio é o estado normal — a maioria dos dias não tem ninguém devendo.
    # Só interrompe o fundador quando há o que decidir.
    if resumo.get("em_atraso"):
        notificar_fundador(
            "Cobrança — marinas em atraso",
            f"Em atraso: {resumo['em_atraso']}\n"
            f"Com acesso suspenso: {resumo['cortadas']}\n"
            f"Avisos enviados hoje: {resumo['avisos_enviados']}",
        )


async def _laco() -> None:
    await asyncio.sleep(_ESPERA_INICIAL)
    while True:
        try:
            if not _ja_rodou_hoje():
                # to_thread porque a régua faz I/O bloqueante (Supabase, SMTP,
                # WhatsApp). No event loop, ela travaria as requisições da
                # marina enquanto varre a base.
                await asyncio.to_thread(_processar)
                _marcar_rodado()
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            # Nunca derruba a aplicação por causa de um aviso: quem paga
            # continua usando o sistema mesmo se a cobrança falhar.
            logger.error("Falha na régua de cobrança: %s", e)
        await asyncio.sleep(_INTERVALO_SEGUNDOS)


async def _laco_prospeccao() -> None:
    """Manda as mensagens de prospecção cuja carência já venceu.

    Laço PRÓPRIO, separado da régua de cobrança, por dois motivos:

      * cadência diferente — cobrança olha uma vez por dia, prospecção precisa
        olhar de minutos em minutos para respeitar a carência;
      * isolamento — falha numa não pode calar a outra. Cobrança que para é
        dinheiro que não entra; prospecção que para é venda que não acontece.
        São perdas diferentes e não devem compartilhar destino.

    Só roda se `PROSPECCAO_AUTOMATICA` estiver ligada. Desligada é o padrão:
    esta é a única rotina que fala com quem nunca pediu contato, e um deploy
    não pode começar a abordar gente por conta própria.
    """
    from app.core.config import settings

    if not settings.PROSPECCAO_AUTOMATICA:
        logger.info(
            "Prospecção automática DESLIGADA (PROSPECCAO_AUTOMATICA). "
            "Os leads ficam na fila; ninguém é abordado."
        )
        return

    await asyncio.sleep(_ESPERA_INICIAL)
    logger.info(
        "Prospecção automática LIGADA — carência de %s min, conferindo a cada %ss.",
        settings.PROSPECCAO_CARENCIA_MINUTOS,
        settings.PROSPECCAO_INTERVALO_SEGUNDOS,
    )

    # RECUO QUANDO NÃO HÁ TRABALHO
    # ------------------------------
    # A espera dobra a cada volta vazia, até o teto, e volta ao intervalo
    # normal assim que aparece um lead. Antes disto a agenda consultava o
    # Supabase no intervalo fixo mesmo com a fila vazia — em produção, uma
    # consulta a cada 60s por dias seguidos, cerca de 1.400 por dia, todas
    # voltando zero.
    #
    # O lead não sofre com isso: ele só fica elegível DEPOIS da carência, e
    # o pior caso passa a ser carência + teto. Quando um aparece, a próxima
    # volta já retoma o ritmo rápido.
    espera = settings.PROSPECCAO_INTERVALO_SEGUNDOS

    while True:
        houve_trabalho = False
        try:
            from app.services.prospeccao_service import disparar_lote

            # to_thread: o lote faz I/O bloqueante (Supabase e WhatsApp, com
            # pausa entre envios). No event loop, travaria as requisições da
            # marina enquanto conversa com o provedor.
            resumo = await asyncio.to_thread(disparar_lote)

            # Silêncio é o estado normal: na maioria das voltas não há nada
            # com a carência vencida. Só registra quando algo aconteceu, para
            # o log não virar ruído que ninguém lê.
            houve_trabalho = bool(
                resumo.get("enviados") or resumo.get("falharam")
                or resumo.get("bloqueados") or resumo.get("sem_numero")
            )

            if resumo.get("enviados") or resumo.get("falharam"):
                logger.info(
                    "Prospecção: enviadas=%s falharam=%s bloqueadas=%s sem_numero=%s",
                    resumo.get("enviados"), resumo.get("falharam"),
                    resumo.get("bloqueados"), resumo.get("sem_numero"),
                )
            if resumo.get("erro"):
                logger.warning("Prospecção não rodou: %s", resumo["erro"])
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error("Falha no lote de prospecção: %s", e)
        if houve_trabalho:
            espera = settings.PROSPECCAO_INTERVALO_SEGUNDOS
        else:
            espera = min(espera * 2, settings.PROSPECCAO_INTERVALO_OCIOSO_SEGUNDOS)
        await asyncio.sleep(espera)


_tarefa: asyncio.Task | None = None
_tarefa_prospeccao: asyncio.Task | None = None


def iniciar() -> None:
    """Liga a agenda. Chamada no startup da aplicação."""
    global _tarefa
    if _tarefa and not _tarefa.done():
        return
    try:
        # Conferir o loop ANTES de chamar `_laco()`: criar a coroutine para
        # depois descobrir que não há onde rodá-la deixa um objeto pendente e
        # um RuntimeWarning a cada import em script ou teste.
        asyncio.get_running_loop()
    except RuntimeError:
        logger.debug("Agenda não iniciada: sem event loop (script ou teste).")
        return
    global _tarefa_prospeccao
    _tarefa = asyncio.create_task(_laco())
    _tarefa_prospeccao = asyncio.create_task(_laco_prospeccao())
    logger.info("Agenda interna ligada — régua de cobrança a cada %sh.",
                _INTERVALO_SEGUNDOS // 3600)


def parar() -> None:
    """Desliga a agenda no shutdown, para o container encerrar limpo."""
    global _tarefa, _tarefa_prospeccao
    for tarefa in (_tarefa, _tarefa_prospeccao):
        if tarefa and not tarefa.done():
            tarefa.cancel()
    _tarefa = None
    _tarefa_prospeccao = None
