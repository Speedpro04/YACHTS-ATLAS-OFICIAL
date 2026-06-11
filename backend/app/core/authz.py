"""
Yachts Atlas — Autorização de acesso a ativos.
Tolerante aos dois schemas: legado (ativos.usuario_id) e novo
(ativos.owner_id / marina_id + profiles.marina_id / user_role).
"""
from fastapi import HTTPException
from app.core.supabase import get_supabase_admin


def get_ativo_autorizado(ativo_id: str, user_id: str) -> dict:
    """Retorna o ativo se o usuário tiver acesso; senão levanta 403/404."""
    if user_id == "maintenance-admin":
        supabase = get_supabase_admin()
        res = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Ativo not found")
        return res.data[0]

    supabase = get_supabase_admin()
    res = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = res.data[0]

    if str(ativo.get("usuario_id") or "") == str(user_id):
        return ativo
    if str(ativo.get("owner_id") or "") == str(user_id):
        return ativo

    prof = supabase.table("profiles").select("*").eq("id", user_id).execute()
    profile = prof.data[0] if prof.data else {}
    if profile.get("user_role") == "admin":
        return ativo
    ativo_marina = ativo.get("marina_id")
    if ativo_marina and str(profile.get("marina_id") or "") == str(ativo_marina):
        return ativo

    raise HTTPException(status_code=403, detail="Not authorized for this asset")
