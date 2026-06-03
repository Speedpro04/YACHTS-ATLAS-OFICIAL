"""
Yachts Atlas — Registros (Cofre Digital Imutável)
Alinhado à tabela public.registros (migration_registros_categorias.sql):
  ativo_id, usuario_id (dono), categoria, titulo, dados (jsonb),
  checklist (jsonb), observacao, status, hash_sha256, created_by, created_at.
Registros são imutáveis: só criação e leitura.
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase import get_supabase_admin
from app.core.security import get_current_user
from pydantic import BaseModel
from typing import Optional, Any

router = APIRouter()

# Status válidos conforme o CHECK da tabela
STATUS_VALIDOS = ["registrado", "pendente", "atencao", "concluido"]


class RegistroCreate(BaseModel):
    ativo_id: str
    categoria: str
    titulo: Optional[str] = None
    observacao: Optional[str] = None
    dados: dict[str, Any] = {}
    checklist: list[Any] = []
    status: str = "registrado"


def _owner_do_ativo(supabase, ativo_id: str) -> Optional[str]:
    """Retorna o usuario_id (dono) do ativo, para vincular o registro."""
    ativo = supabase.table("ativos").select("usuario_id").eq("id", ativo_id).execute()
    return ativo.data[0]["usuario_id"] if ativo.data else None


@router.get("/{ativo_id}")
async def list_registros(ativo_id: str, token: dict = Depends(get_current_user)):
    """Lista os registros imutáveis de um ativo."""
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
async def create_registro(data: RegistroCreate, token: dict = Depends(get_current_user)):
    """Cria um registro imutável."""
    if data.status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"status inválido (use: {', '.join(STATUS_VALIDOS)})")
    try:
        supabase = get_supabase_admin()

        usuario_id = _owner_do_ativo(supabase, data.ativo_id)
        if not usuario_id:
            raise HTTPException(status_code=404, detail="Ativo não encontrado")

        result = supabase.table("registros").insert({
            "ativo_id": data.ativo_id,
            "usuario_id": usuario_id,
            "categoria": data.categoria,
            "titulo": data.titulo,
            "observacao": data.observacao,
            "dados": data.dados,
            "checklist": data.checklist,
            "status": data.status,
            "created_by": token.get("sub") if token else None,
        }).execute()
        return result.data[0] if result.data else {}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{ativo_id}")
async def get_registro_stats(ativo_id: str, token: dict = Depends(get_current_user)):
    """Contagem de registros por status para um ativo."""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("registros").select("status").eq("ativo_id", ativo_id).execute()
        records = result.data or []
        return {
            "total": len(records),
            "registrado": sum(1 for r in records if r["status"] == "registrado"),
            "pendente": sum(1 for r in records if r["status"] == "pendente"),
            "atencao": sum(1 for r in records if r["status"] == "atencao"),
            "concluido": sum(1 for r in records if r["status"] == "concluido"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
