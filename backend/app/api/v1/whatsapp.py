"""
Yachts Atlas — Webhook de respostas do WhatsApp (opt-out da prospecção).

Existe por uma razão só: a mensagem de prospecção promete "responda SAIR", e
promessa de saída que não funciona é pior que não prometer. Quem pede para sair
e recebe de novo é exatamente quem denuncia — e denúncia é o que bane o número.
O número é o ativo mais frágil da operação.

Fluxo:

    Evolution recebe resposta da marina
        -> POST /api/v1/whatsapp/webhook?token=...
        -> confere o token (segredo compartilhado)
        -> ignora mensagem que o próprio Atlas enviou (fromMe)
        -> se o texto for um pedido de saída, entra na blocklist
        -> responde 200 SEMPRE

Decisões:

  • **Responde 200 mesmo quando ignora.** Provedor de webhook que recebe erro
    reenvia, e reenvio em loop de uma mensagem que nunca vai ser aceita só
    gasta os dois lados. O que interessa é o log, não o status.

  • **Token obrigatório.** O endpoint é público (a Evolution chama de fora) e
    escreve na blocklist. Sem segredo, qualquer um bloqueia qualquer número.
    Sem `WHATSAPP_WEBHOOK_TOKEN` configurado, o webhook fica DESLIGADO — não
    aberto.

  • **Só reconhece saída, não faz mais nada.** Nenhuma outra ação é disparada
    por mensagem de fora. Um webhook que só sabe uma coisa não pode ser usado
    para outra.
"""
from __future__ import annotations

import hmac
import logging
import re
from typing import Any, Optional

from fastapi import APIRouter, Request

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# O que conta como pedido de saída. Casado por PALAVRA INTEIRA: "sair" dentro
# de "vou sair do escritório agora" não é opt-out, e bloquear quem estava
# conversando é perder a marina justamente quando ela respondeu.
_PALAVRAS_DE_SAIDA = (
    "sair", "sai", "pare", "parar", "para", "cancelar", "cancela",
    "descadastrar", "remover", "stop", "unsubscribe",
)
_PADRAO_SAIDA = re.compile(
    r"^\W*(" + "|".join(_PALAVRAS_DE_SAIDA) + r")\W*$", re.IGNORECASE
)


def _quer_sair(texto: Optional[str]) -> bool:
    """
    True quando a mensagem é SÓ o pedido de saída.

    Exigir a mensagem inteira é deliberado. A alternativa — procurar a palavra
    em qualquer lugar do texto — bloquearia "não quero cancelar, quero saber
    mais", que é o oposto do que a marina disse.
    """
    if not texto:
        return False
    return bool(_PADRAO_SAIDA.match(texto.strip()))


def _extrair(evento: dict[str, Any]) -> tuple[Optional[str], Optional[str], bool]:
    """
    Tira (telefone, texto, fromMe) do corpo da Evolution.

    O formato varia entre versões e entre tipos de mensagem, então cada acesso
    é defensivo: webhook que levanta exceção vira reenvio em loop.
    """
    dados = evento.get("data") or evento
    if isinstance(dados, list):
        dados = dados[0] if dados else {}
    if not isinstance(dados, dict):
        return None, None, False

    chave = dados.get("key") or {}
    jid = chave.get("remoteJid") or ""
    telefone = str(jid).split("@")[0] or None
    from_me = bool(chave.get("fromMe"))

    msg = dados.get("message") or {}
    texto = (
        msg.get("conversation")
        or (msg.get("extendedTextMessage") or {}).get("text")
        or (msg.get("ephemeralMessage") or {}).get("message", {}).get("conversation")
        or dados.get("body")
    )
    return telefone, texto, from_me


@router.post("/webhook")
async def receber_resposta(request: Request):
    """Recebe resposta do WhatsApp. Só age em pedido de saída."""
    esperado = settings.WHATSAPP_WEBHOOK_TOKEN
    if not esperado:
        logger.warning("Webhook do WhatsApp chamado sem WHATSAPP_WEBHOOK_TOKEN configurado — ignorado")
        return {"ok": True, "acao": "desligado"}

    # compare_digest: comparação de segredo não pode vazar tamanho pelo tempo.
    recebido = request.query_params.get("token") or request.headers.get("x-webhook-token") or ""
    if not hmac.compare_digest(recebido, esperado):
        logger.warning("Webhook do WhatsApp com token inválido — ignorado")
        return {"ok": True, "acao": "token_invalido"}

    try:
        evento = await request.json()
    except Exception:
        return {"ok": True, "acao": "corpo_ilegivel"}

    telefone, texto, from_me = _extrair(evento if isinstance(evento, dict) else {})

    # Mensagem que o próprio Atlas mandou volta no webhook. Sem esta guarda, o
    # disparo se auto-bloquearia no dia em que o texto contivesse a palavra.
    if from_me:
        return {"ok": True, "acao": "ignorado_proprio"}

    if not _quer_sair(texto):
        return {"ok": True, "acao": "sem_acao"}

    from app.services.prospeccao_service import bloquear
    ok = bloquear(telefone, motivo="respondeu SAIR")
    logger.info(f"Opt-out de {telefone}: {'registrado' if ok else 'FALHOU'}")
    return {"ok": True, "acao": "opt_out" if ok else "opt_out_falhou"}
