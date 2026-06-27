"""
Yachts Atlas — Leads (marinas e parceiros)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.models import LeadMarinaCreate
from app.core.supabase import get_supabase_admin
from app.core.security import require_platform_admin

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
async def list_marina_leads(_admin: dict = Depends(require_platform_admin)):
    """List all marina leads (admin use)"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("marina_leads").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marina/spots")
async def get_marina_founder_spots():
    """Return founder spot availability for the public marina partnership page."""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("founder_program_spots").select(
            "slot_number,status,marina_name,contact_name,email,billing_status,access_status,updated_at"
        ).order("slot_number").execute()

        spots = result.data or []
        total_spots = 3
        occupied_statuses = {"reserved", "occupied"}
        taken_spots = sum(1 for spot in spots if spot.get("status") in occupied_statuses)
        available_spots = max(total_spots - taken_spots, 0)

        return {
            "total_spots": total_spots,
            "taken_spots": taken_spots,
            "available_spots": available_spots,
            "spots": spots,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
