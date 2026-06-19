"""
Yachts Atlas — Chatbot de Normas (endpoint)

Assistente de CONSULTA às normas náuticas. Read-only por construção:
não cadastra, não altera, não acessa dados de marinas/pessoas. Toda a
blindagem vive em chatbot_guardrails + chatbot_service.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

from app.services import chatbot_service

router = APIRouter()


class PerguntaChatbot(BaseModel):
    mensagem: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None


@router.post("/ask")
async def perguntar(data: PerguntaChatbot, request: Request = None):
    """Recebe uma pergunta sobre normas e devolve a resposta com fontes."""
    # Chave de rate limit: IP do cliente (anti-abuso/sondagem em massa).
    user_key = "anon"
    if request and request.client:
        user_key = request.client.host or "anon"

    try:
        resultado = chatbot_service.ask(
            message=data.mensagem,
            session_id=data.session_id or "",
            user_key=user_key,
        )
        return resultado
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))
