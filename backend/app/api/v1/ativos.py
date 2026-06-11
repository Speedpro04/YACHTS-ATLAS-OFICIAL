"""
Yachts Atlas — Ativos Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.models import AtivoCreate, AtivoResponse
from app.core.supabase import get_supabase_client
from app.core.security import get_current_user_id
import uuid

router = APIRouter()


@router.get("")
async def list_ativos(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    # Get user profile first to identify their role and marina
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    marina_id = profile.get("marina_id")
    
    if user_role == "marina_manager":
        if not marina_id:
            return []
        response = supabase.table("ativos").select("*").eq("marina_id", marina_id).execute()
    elif user_role == "owner":
        response = supabase.table("ativos").select("*").eq("owner_id", user_id).execute()
    elif user_role == "admin":
        response = supabase.table("ativos").select("*").execute()
    else:
        response = supabase.table("ativos").select("*").eq("owner_id", user_id).execute()
        
    return response.data


@router.post("")
async def create_ativo(
    ativo: AtivoCreate,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    
    # Get user profile to check roles
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    user_marina_id = profile.get("marina_id")
    
    # Determine the marina_id to assign
    marina_id = ativo.marina_id or user_marina_id
    if not marina_id:
        raise HTTPException(status_code=400, detail="marina_id is required")
        
    # Verify manager belongs to the assigned marina
    if user_role == "marina_manager" and user_marina_id and str(user_marina_id) != str(marina_id):
        raise HTTPException(status_code=403, detail="You can only add assets to your own marina")
        
    ativo_id = f"YA-{ativo.tipo.upper()}-{ativo.ano_fabricacao}-{str(uuid.uuid4())[:4].upper()}"
    
    data = {
        "id": ativo_id,
        "marina_id": str(marina_id),
        "owner_id": str(ativo.owner_id) if ativo.owner_id else None,
        "tipo": ativo.tipo.value if hasattr(ativo.tipo, 'value') else ativo.tipo,
        "marca": ativo.marca,
        "modelo": ativo.modelo,
        "ano_fabricacao": ativo.ano_fabricacao,
        "comprimento_pes": ativo.comprimento_pes,
        "classificacao": "bronze",  # Valid check constraint ('bronze', 'silver', 'gold')
        "progresso": 0,
        "status": "ativo"
    }
    
    if ativo.comprimento_metres:
        data["comprimento_metres"] = ativo.comprimento_metres
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
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    marina_id = profile.get("marina_id")
    
    query = supabase.table("ativos").select("*").eq("id", ativo_id)
    if user_role == "marina_manager" and marina_id:
        query = query.eq("marina_id", marina_id)
    elif user_role == "owner":
        query = query.eq("owner_id", user_id)
    elif user_role == "admin":
        pass
    else:
        query = query.eq("owner_id", user_id)
        
    response = query.execute()
    if response.data:
        return response.data[0]
    
    raise HTTPException(status_code=404, detail="Ativo not found")


@router.delete("/{ativo_id}")
async def delete_ativo(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    marina_id = profile.get("marina_id")
    
    query = supabase.table("ativos").select("id, marina_id, owner_id").eq("id", ativo_id)
    response = query.execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    
    authorized = False
    if user_role == "admin":
        authorized = True
    elif user_role == "marina_manager" and marina_id and str(ativo.get("marina_id")) == str(marina_id):
        authorized = True
    elif user_role == "owner" and str(ativo.get("owner_id")) == str(user_id):
        authorized = True
        
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to delete this asset")
        
    supabase.table("ativos").delete().eq("id", ativo_id).execute()
    return {"message": "Ativo deleted"}


@router.get("/{ativo_id}/progresso")
async def get_progresso(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    marina_id = profile.get("marina_id")
    
    query = supabase.table("ativos").select("progresso, classificacao, marina_id, owner_id").eq("id", ativo_id)
    response = query.execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
        
    ativo = response.data[0]
    authorized = False
    if user_role == "admin":
        authorized = True
    elif user_role == "marina_manager" and marina_id and str(ativo.get("marina_id")) == str(marina_id):
        authorized = True
    elif user_role == "owner" and str(ativo.get("owner_id")) == str(user_id):
        authorized = True
        
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to access this asset progress")
        
    return {"progresso": ativo["progresso"], "classificacao": ativo["classificacao"]}