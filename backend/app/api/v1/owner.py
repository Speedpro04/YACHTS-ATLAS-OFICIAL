"""
Yachts Atlas — Owner Access (cadastro da palavra secreta do proprietário)
A Edge Function `verify-owner-secret` VERIFICA; este endpoint DEFINE.
Hash bcrypt (passlib) — compatível com o bcrypt.compare da Edge Function.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from app.core.supabase import get_supabase_admin
from app.core.security import hash_password, verify_token

router = APIRouter()


class OwnerSecretSet(BaseModel):
    user_id: str
    secret_word: str = Field(min_length=3)


def require_admin(token: dict = Depends(verify_token)) -> dict:
    # Restrito a admin/owner da plataforma. (Quando o fluxo de marina existir,
    # a marina autenticada poderá cadastrar a palavra do dono que ela gerencia.)
    if not token or token.get("role") not in ("owner", "admin"):
        raise HTTPException(status_code=403, detail="Acesso restrito")
    return token


@router.post("/secret")
async def definir_palavra_secreta(data: OwnerSecretSet, _admin: dict = Depends(require_admin)):
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
