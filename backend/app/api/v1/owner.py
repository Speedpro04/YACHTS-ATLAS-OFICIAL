"""
Yachts Atlas — Owner Access (cadastro da palavra secreta do proprietário)
A Edge Function `verify-owner-secret` VERIFICA; este endpoint DEFINE.
Hash bcrypt (passlib) — compatível com o bcrypt.compare da Edge Function.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.core.supabase import get_supabase_admin
from app.core.security import hash_password, require_platform_admin

router = APIRouter()


class OwnerSecretSet(BaseModel):
    user_id: str
    secret_word: str = Field(min_length=3)


@router.post("/secret")
async def definir_palavra_secreta(data: OwnerSecretSet, _admin: dict = Depends(require_platform_admin)):
    """Define/atualiza a palavra secreta (hash) de um proprietário."""
    try:
        supabase = get_supabase_admin()
        supabase.table("owner_access").upsert({
            "user_id": data.user_id,
            "secret_word_hash": hash_password(data.secret_word),
            "updated_at": "now()",
        }).execute()
        return {"message": "Palavra secreta definida"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
