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

MENSAGEM_1 = (
    "Olá, {responsavel}. Aqui é do *Yachts Atlas*.\n\n"
    "A *{indicadora}* indicou a {indicada} para integrar nossa rede.\n\n"
    "Somos a custódia digital de ativos náuticos: organizamos documentos, "
    "laudos e histórico de embarcações num dossiê certificado. Para a marina, "
    "cada dossiê emitido vira receita.\n\n"
    "Conheça nosso Programa Atlas: {link}\n\n"
    "Faz sentido conversarmos?"
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

    Ainda não há webhook da Evolution ligado: enquanto não houver, o opt-out
    depende de alguém rodar isto à mão ao ver um "SAIR" na caixa. A mensagem
    promete a saída, então essa ponta precisa existir antes do primeiro lote.
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


def disparar_lote(limite: int = LOTE_MAXIMO, dry_run: bool = False) -> dict:
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

    logger.info(f"Prospecção — lote concluído: {resumo}")
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
