"""
Yachts Atlas — Registros (Cofre Digital Imutável)
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase import get_supabase_admin
from app.core.security import verify_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class RegistroCreate(BaseModel):
    ativo_id: str
    categoria: str
    titulo: str
    descricao: str


@router.get("/{ativo_id}")
async def list_registros(ativo_id: str, token: dict = Depends(verify_token)):
    """List all immutable service records for an asset"""
    try:
        supabase = get_supabase_admin()
        result = (
            supabase.table("registros")
            .select("*")
            .eq("ativo_id", ativo_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_registro(data: RegistroCreate, token: dict = Depends(verify_token)):
    """Create an immutable service record"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("registros").insert({
            "ativo_id": data.ativo_id,
            "categoria": data.categoria,
            "titulo": data.titulo,
            "descricao": data.descricao,
            "status": "pending",
            "created_by": token.get("sub") if token else None,
        }).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{ativo_id}")
async def get_registro_stats(ativo_id: str, token: dict = Depends(verify_token)):
    """Get record counts by status for an asset"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("registros").select("status").eq("ativo_id", ativo_id).execute()
        records = result.data or []
        return {
            "total": len(records),
            "completed": sum(1 for r in records if r["status"] == "completed"),
            "pending": sum(1 for r in records if r["status"] == "pending"),
            "attention": sum(1 for r in records if r["status"] == "attention"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
