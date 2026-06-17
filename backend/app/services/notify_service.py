"""
Yachts Atlas — Notificações no celular (Telegram)

Aviso instantâneo para o fundador via bot do Telegram. Usa apenas a stdlib
(urllib) — sem dependência nova. É best-effort: nunca quebra o fluxo principal.

Configuração (variáveis de ambiente):
  TELEGRAM_BOT_TOKEN  -> token do bot criado no @BotFather
  TELEGRAM_CHAT_ID    -> id do chat (descoberto via /telegram/chat-id após
                          você mandar uma mensagem para o bot)
"""
import json
import logging
import urllib.parse
import urllib.request

from app.core.config import settings

logger = logging.getLogger(__name__)

_API = "https://api.telegram.org/bot{token}/{method}"


def _call(method: str, params: dict) -> dict | None:
    """Chamada simples à Bot API do Telegram. Retorna o JSON ou None."""
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return None
    try:
        url = _API.format(token=token, method=method)
        data = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.error(f"Telegram {method} falhou: {e}")
        return None


def send_telegram(text: str) -> bool:
    """Envia uma mensagem ao chat configurado. Retorna True se enviada."""
    chat_id = settings.TELEGRAM_CHAT_ID
    if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
        logger.info("Telegram não configurado (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID).")
        return False
    result = _call("sendMessage", {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    })
    return bool(result and result.get("ok"))


def descobrir_chats() -> list[dict]:
    """
    Lista os chats que já falaram com o bot (via getUpdates). Use para achar
    seu chat_id: mande qualquer mensagem ao bot e chame esta função.
    """
    result = _call("getUpdates", {})
    if not result or not result.get("ok"):
        return []
    chats: dict[str, dict] = {}
    for upd in result.get("result", []):
        msg = upd.get("message") or upd.get("edited_message") or {}
        chat = msg.get("chat")
        if chat and "id" in chat:
            chats[str(chat["id"])] = {
                "chat_id": chat["id"],
                "nome": (f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                         or chat.get("title") or chat.get("username")),
                "tipo": chat.get("type"),
            }
    return list(chats.values())
