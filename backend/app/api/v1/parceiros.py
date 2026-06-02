"""
Yachts Atlas — Parceiros: rastreio de cliques de contato (cobrança futura).
O Atlas é a ponte: cada clique em WhatsApp/e-mail/site de um parceiro é
registrado em partner_clicks -> base para cobrança por lead/clique.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from app.core.supabase import get_supabase_admin

router = APIRouter()

TIPOS = ("whatsapp", "email", "site")


class CliqueParceiro(BaseModel):
    partner_id: str
    categoria: str
    tipo_contato: str
    ativo_id: Optional[str] = None


@router.post("/clique")
async def registrar_clique(data: CliqueParceiro, request: Request = None):
    """Registra um clique de contato em um parceiro (fire-and-forget)."""
    if data.tipo_contato not in TIPOS:
        raise HTTPException(status_code=400, detail="tipo_contato inválido")
    try:
        supabase = get_supabase_admin()
        ua = request.headers.get("user-agent") if request else None
        supabase.table("partner_clicks").insert({
            "partner_id": data.partner_id,
            "categoria": data.categoria,
            "tipo_contato": data.tipo_contato,
            "ativo_id": data.ativo_id,
            "user_agent": ua[:300] if ua else None,
        }).execute()
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
