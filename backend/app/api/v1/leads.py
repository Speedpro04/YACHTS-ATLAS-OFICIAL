"""
Yachts Atlas — Leads (marinas e parceiros)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.models import LeadMarinaCreate
from app.core.supabase import get_supabase_admin

router = APIRouter()


class LeadParceiroCreate(BaseModel):
    categoria: str
    empresa: str
    responsavel: str
    email: EmailStr
    telefone: Optional[str] = None
    cidade: Optional[str] = None
    mensagem: Optional[str] = None


@router.post("/marina")
async def create_marina_lead(data: LeadMarinaCreate):
    """Save marina partner lead to database"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("marina_leads").insert({
            "marina_name": data.marina,
            "contact_name": data.name,
            "email": data.email,
            "fleet_size": data.fleet,
            "source": data.source,
            "status": "pending",
        }).execute()
        return {
            "message": "Solicitação recebida com sucesso",
            "id": result.data[0]["id"] if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parceiro")
async def create_partner_lead(data: LeadParceiroCreate):
    """Salva solicitação de parceiro (diretório Parceiros Atlas)."""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("partner_leads").insert({
            "categoria": data.categoria,
            "empresa": data.empresa,
            "responsavel": data.responsavel,
            "email": data.email,
            "telefone": data.telefone,
            "cidade": data.cidade,
            "mensagem": data.mensagem,
            "status": "pending",
        }).execute()
        return {
            "message": "Solicitação recebida com sucesso",
            "id": result.data[0]["id"] if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marina")
async def list_marina_leads():
    """List all marina leads (admin use)"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("marina_leads").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
