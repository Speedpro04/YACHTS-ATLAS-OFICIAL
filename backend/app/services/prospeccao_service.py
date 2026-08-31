"""
Yachts Atlas — Prospecção de marinas indicadas (WhatsApp).

Fluxo de um disparo:

    lê leads com whatsapp_status='pendente'
        -> normaliza o número
        -> consulta a blocklist  (quem pediu SAIR)
        -> monta a mensagem a partir de TEMPLATE FIXO
        -> envia pela instância de PROSPECÇÃO (nunca a transacional)
        -> grava o resultado no próprio lead
        -> espera PAUSA_ENTRE_ENVIOS antes do próximo

Decisões:

  • SEM IA. A mensagem é template com substituição de variável. Ela carrega
    condição comercial ("12 meses", "100%"), e texto gerado a cada envio seria
    (a) risco de prometer o que não foi combinado e (b) sinal de bot para o
    WhatsApp, que classifica por padrão. Quando houver IA neste processo, ela
    entra na RESPOSTA, não na saída.

  • Os números comerciais são CONSTANTES deste módulo. Não vêm de banco, não
    vêm de modelo, não são digitados na hora. Mudou a oferta, muda aqui, num
    lugar só — e o que foi enviado ontem continua rastreável.

  • Instância separada, sempre: `enviar_whatsapp(..., prospeccao=True)`. A
    instância transacional entrega código de login e régua de cobrança; um ban
    por denúncia de spam lá derruba as duas coisas junto.

  • Ritmo, não rajada. `PAUSA_ENTRE_ENVIOS` e `LOTE_MAXIMO` existem para o
    número não ser banido no primeiro dia. É o ativo mais frágil da operação.

  • Idempotente por status: o lead sai de 'pendente' assim que é tratado. Uma
    falha de rede no meio do lote não faz a marina receber duas vezes.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.supabase import get_supabase_admin
from app.services.whatsapp_service import (
    enviar_whatsapp,
    normalizar_telefone,
    prospeccao_ativa,
)

logger = logging.getLogger(__name__)

# --- Condições comerciais -----------------------------------------------
# Fonte única do que a mensagem promete. Ver a memória do projeto: o Oficial
# trata SOMENTE US$ 250/mês e 12 meses de dossiê 100%.
MESES_DOSSIE_INDICACAO = 12
PERCENTUAL_DOSSIE = 100

# --- Ritmo ---------------------------------------------------------------
# Conservador de propósito. Número novo disparando em volume é o padrão que o
# WhatsApp bane. Subir isto só depois do número estar aquecido.
LOTE_MAXIMO = 20
PAUSA_ENTRE_ENVIOS = 45  # segundos

LINK = "https://yachtsatlas.online"

# O nome de quem indicou aparece DUAS vezes, e a primeira na segunda linha.
# É o único ativo que separa esta mensagem de um disparo frio qualquer: se ele
# aparece só no fim, a marina já leu tudo como propaganda antes de chegar lá.
#
# O que a mensagem NÃO faz, de propósito:
#   • não diz "todos estão aderindo" — a rede está em formação e o contador
#     mostra 0 de 20 vagas. Afirmação que o interlocutor desmente em um clique
#     custa mais do que ganha, ainda mais em mensagem não solicitada;
#   • não diz que a rede está começando ("primeiras vagas", "estamos abrindo").
#     Isso entrega o estágio da operação para quem não precisa saber, e enfraquece
#     a proposta em vez de criar urgência. A condição especial se sustenta no
#     fato de ELA ter sido indicada, que é sobre ela e não sobre nós;
#   • não abre o preço. "Condição especial" convida a responder; número no
#     primeiro toque encerra a conversa antes de existir valor.
MENSAGEM_1 = (
    "Olá, {responsavel}. Aqui é do *Yachts Atlas*.\n\n"
    "A *{indicadora}* indicou a {indicada} para o nosso "
    "*Programa de Custódia*.\n\n"
    # "sua Marina", com M maiúsculo: fala com ELA, não sobre uma categoria.
    # A maiúscula é deliberada — trata a Marina como instituição, do mesmo modo
    # que se escreve o nome de uma empresa. Não "corrigir" para minúscula.
    # "selo de integridade", NÃO "dossiê certificado". O Atlas não inspeciona
    # embarcação nem emite certificado — isso é atribuição de órgão competente,
    # e a própria FAQ do site diz isso. O que ele certifica é a INTEGRIDADE do
    # registro (SHA-256, selo imutável, QR que valida). Prometer certificação
    # do ativo em mensagem comercial é promessa que o produto não cumpre.
    "Organizamos documentos, laudos e todo o histórico de cada embarcação num "
    "*Dossiê Náutico* com selo de integridade — e cada dossiê emitido vira "
    "receita para sua Marina.\n\n"
    "A indicação da *{indicadora}* garante condição especial para vocês.\n\n"
    # Instrução explícita antes do link. Link solto no meio do texto é fácil de
    # passar batido; dizer o que fazer com ele é o que transforma leitura em
    # clique.
    "Acesse a página e conheça o programa:\n"
    "{link}\n\n"
    "Faz sentido conversarmos?\n\n"
    # A saída fica em itálico e por último: cumpre o dever de transparência sem
    # roubar a atenção da pergunta. Só pode existir porque o webhook de opt-out
    # existe (api/v1/whatsapp.py) — prometer saída que não funciona é o que
    # transforma "não quero" em denúncia, e denúncia é o que bane o número.
    "_Se preferir não receber, é só responder SAIR._"
)


def montar_mensagem(responsavel: str, indicadora: str, indicada: str) -> str:
    """Preenche o template. Nada aqui é gerado — só substituído."""
    return MENSAGEM_1.format(
        responsavel=(responsavel or "").split()[0] if responsavel else "tudo bem",
        indicadora=indicadora or "uma marina parceira",
        indicada=indicada or "sua marina",
        link=LINK,
    )


def esta_bloqueado(supabase, telefone: str) -> bool:
    """Se o número pediu para não receber mais.

    Falha fechada: se a consulta der erro, tratamos como bloqueado. Mandar
    para quem pediu SAIR é o que gera denúncia — e denúncia é o que bane o
    número. Na dúvida, não enviar custa menos.
    """
    try:
        r = (
            supabase.table("whatsapp_blocklist")
            .select("telefone")
            .eq("telefone", telefone)
            .limit(1)
            .execute()
        )
        return bool(r.data)
    except Exception as e:
        logger.error(f"Blocklist ilegível para {telefone}: {e} — tratando como bloqueado")
        return True


def bloquear(telefone: Optional[str], motivo: str = "pediu SAIR") -> bool:
    """Põe um número na blocklist. Chamada pelo webhook de resposta.

    Chamada por `api/v1/whatsapp.py` quando a marina responde SAIR. Também
    serve para bloquear à mão um número que pediu por outro caminho.
    """
    numero = normalizar_telefone(telefone)
    if not numero:
        return False
    try:
        get_supabase_admin().table("whatsapp_blocklist").upsert(
            {"telefone": numero, "motivo": motivo},
            on_conflict="telefone",
        ).execute()
        logger.info(f"Número {numero} entrou na blocklist ({motivo})")
        return True
    except Exception as e:
        logger.error(f"Falha ao bloquear {numero}: {e}")
        return False


def _marcar(supabase, lead_id: str, status: str, erro: Optional[str] = None) -> None:
    """Tira o lead de 'pendente'. Falhar aqui repetiria o envio no próximo lote."""
    dados = {"whatsapp_status": status, "whatsapp_erro": erro}
    if status == "enviado":
        dados["whatsapp_enviado_em"] = "now()"
    try:
        supabase.table("marina_leads").update(dados).eq("id", lead_id).execute()
    except Exception as e:
        logger.error(f"Falha ao marcar lead {lead_id} como {status}: {e}")


def _limite_de_carencia(minutos: Optional[int]) -> str:
    """Instante-limite: só entram leads criados ANTES disto.

    A carência não é atraso técnico — é a janela em que um lead errado ainda
    pode ser tirado da fila. Mensagem enviada não volta; lead na fila, sim.
    """
    if minutos is None:
        minutos = settings.PROSPECCAO_CARENCIA_MINUTOS
    corte = datetime.now(timezone.utc) - timedelta(minutes=max(0, minutos))
    return corte.isoformat()


def disparar_lote(
    limite: int = LOTE_MAXIMO,
    dry_run: bool = False,
    carencia_minutos: Optional[int] = None,
) -> dict:
    """Dispara um lote de prospecção. Devolve o resumo do que aconteceu.

    `dry_run=True` monta tudo e não envia nada — serve para conferir a
    mensagem com dados reais antes de falar com marina de verdade.
    """
    if not dry_run and not prospeccao_ativa():
        return {
            "erro": "instância de prospecção não configurada "
                    "(EVOLUTION_INSTANCE_PROSPECCAO)",
            "enviados": 0,
        }

    supabase = get_supabase_admin()
    resumo = {"enviados": 0, "bloqueados": 0, "sem_numero": 0, "falharam": 0,
              "dry_run": dry_run, "amostra": None}

    try:
        leads = (
            supabase.table("marina_leads")
            .select("id, marina_name, contact_name, whatsapp, source")
            .eq("whatsapp_status", "pendente")
            .lte("created_at", _limite_de_carencia(carencia_minutos))
            .order("created_at")
            .limit(limite)
            .execute()
        ).data or []
    except Exception as e:
        logger.error(f"Falha ao ler leads de prospecção: {e}")
        return {"erro": str(e), "enviados": 0}

    for i, lead in enumerate(leads):
        numero = normalizar_telefone(lead.get("whatsapp"))
        if not numero:
            resumo["sem_numero"] += 1
            if not dry_run:
                _marcar(supabase, lead["id"], "sem_numero")
            continue

        if esta_bloqueado(supabase, numero):
            resumo["bloqueados"] += 1
            if not dry_run:
                _marcar(supabase, lead["id"], "bloqueado")
            continue

        texto = montar_mensagem(
            responsavel=lead.get("contact_name", ""),
            indicadora=lead.get("source", ""),
            indicada=lead.get("marina_name", ""),
        )

        if dry_run:
            resumo["enviados"] += 1
            if resumo["amostra"] is None:
                resumo["amostra"] = {"para": numero, "texto": texto}
            continue

        if enviar_whatsapp(numero, texto, prospeccao=True):
            resumo["enviados"] += 1
            _marcar(supabase, lead["id"], "enviado")
        else:
            resumo["falharam"] += 1
            _marcar(supabase, lead["id"], "falhou", "envio recusado pelo provedor")

        # Ritmo: só entre envios de verdade, e não depois do último.
        if i < len(leads) - 1:
            time.sleep(PAUSA_ENTRE_ENVIOS)

    # Volta vazia é o estado NORMAL: na maioria das vezes não há lead com a
    # carência vencida. Em INFO, isso escreveu uma linha a cada 60 segundos
    # durante dias — e o `agenda.py`, que chama esta função, já dizia no
    # próprio comentário que só queria registrar quando algo acontecesse. O
    # log ficou ilegível justamente para quem precisa achar o envio de
    # verdade no meio dele.
    if resumo.get("enviados") or resumo.get("falharam") or resumo.get("bloqueados"):
        logger.info(f"Prospecção — lote concluído: {resumo}")
    else:
        logger.debug(f"Prospecção — nada na fila: {resumo}")
    return resumo


if __name__ == "__main__":
    # Conferir a mensagem antes de falar com marina de verdade:
    #     python -m app.services.prospeccao_service          (dry run)
    #     python -m app.services.prospeccao_service --enviar (dispara)
    import sys

    enviar = "--enviar" in sys.argv
    print(f"instância prospecção: {settings.EVOLUTION_INSTANCE_PROSPECCAO or '(não configurada)'}")
    print(f"modo               : {'ENVIO REAL' if enviar else 'dry run (nada sai)'}")
    resultado = disparar_lote(dry_run=not enviar)
    amostra = resultado.pop("amostra", None)
    print(resultado)
    if amostra:
        print("\n--- amostra ---")
        print(f"para: {amostra['para']}\n")
        print(amostra["texto"])
