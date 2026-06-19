"""
Yachts Atlas — Normas Náuticas (catálogo de consulta)

Lista somente normas verificadas e ativas. Read-only e cacheado no Redis
(o catálogo muda pouco). Base da aba "Normas Técnicas Náuticas" no sistema.
"""
from fastapi import APIRouter, HTTPException

from app.core.cache import cache_get_json, cache_set_json
from app.core.supabase import get_supabase_admin

router = APIRouter()

_CACHE_KEY = "normas:lista:v1"
_CACHE_TTL = 3600


@router.get("/")
async def listar_normas():
    """Catálogo de normas verificadas, ordenado para exibição."""
    cached = cache_get_json(_CACHE_KEY)
    if cached:
        return cached

    try:
        supabase = get_supabase_admin()
        rows = (
            supabase.table("normas")
            .select("codigo,titulo,descricao,orgao,serie,jurisdicao,versao,fonte_url,obrigatoria,ordem")
            .eq("ativo", True)
            .eq("status_verificacao", "verificada")
            .order("ordem")
            .execute()
            .data
            or []
        )
        result = {"normas": rows, "total": len(rows)}
        cache_set_json(_CACHE_KEY, result, ttl=_CACHE_TTL)
        return result
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(exc))
