"""
Yachts Atlas — Ativos Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.models import AtivoCreate, AtivoResponse
from app.core.supabase import get_supabase_client
from app.core.security import verify_token
import uuid

router = APIRouter()


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.get("")
async def list_ativos(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("ativos").select("*").eq("usuario_id", user_id).execute()
    return response.data


@router.post("")
async def create_ativo(
    ativo: AtivoCreate,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    
    ativo_id = f"YA-{ativo.tipo.upper()}-{ativo.ano_fabricacao}-{str(uuid.uuid4())[:4].upper()}"
    
    data = {
        "id": ativo_id,
        "usuario_id": user_id,
        "tipo": ativo.tipo.value if hasattr(ativo.tipo, 'value') else ativo.tipo,
        "marca": ativo.marca,
        "modelo": ativo.modelo,
        "ano_fabricacao": ativo.ano_fabricacao,
        "classificacao": "compact",
        "progresso": 0,
        "status": "ativo"
    }
    
    if ativo.comprimento:
        data["comprimento"] = ativo.comprimento
    if ativo.largura:
        data["largura"] = ativo.largura
    if ativo.calado:
        data["calado"] = ativo.calado
    if ativo.material_casco:
        data["material_casco"] = ativo.material_casco.value if hasattr(ativo.material_casco, 'value') else ativo.material_casco
    if ativo.capacidade_passageiros:
        data["capacidade_passageiros"] = ativo.capacidade_passageiros
    
    response = supabase.table("ativos").insert(data).execute()
    
    if response.data:
        return response.data[0]
    
    raise HTTPException(status_code=400, detail="Failed to create ativo")


@router.get("/{ativo_id}")
async def get_ativo(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("ativos").select("*").eq("id", ativo_id).eq("usuario_id", user_id).execute()
    
    if response.data:
        return response.data[0]
    
    raise HTTPException(status_code=404, detail="Ativo not found")


@router.delete("/{ativo_id}")
async def delete_ativo(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("ativos").delete().eq("id", ativo_id).eq("usuario_id", user_id).execute()
    
    return {"message": "Ativo deleted"}


@router.get("/{ativo_id}/progresso")
async def get_progresso(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    
    ativo = supabase.table("ativos").select("progresso, classificacao").eq("id", ativo_id).eq("usuario_id", user_id).execute()
    
    if not ativo.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    
    return ativo.data[0]