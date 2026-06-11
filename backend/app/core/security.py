"""
Yachts Atlas — Security Utilities
"""
from datetime import datetime, timedelta
from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def _internal_jwt_secret() -> str:
    # Segredo dedicado aos tokens internos (login de manutenção).
    # Nunca usar a service key como segredo de assinatura.
    return settings.SUPABASE_JWT_SECRET or settings.SUPABASE_SERVICE_KEY


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, _internal_jwt_secret(), algorithm=ALGORITHM)


def _decode_internal_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, _internal_jwt_secret(), algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Dependência unificada: lê o JWT da sessão Supabase no header Authorization
    e valida via Supabase Auth. Aceita também o token interno de manutenção.
    Retorna {sub, email, role}.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.split(" ", 1)[1].strip()

    # Bypass de manutenção (admin da plataforma)
    if (
        settings.MAINTENANCE_BYPASS_ENABLED
        and settings.MAINTENANCE_MASTER_TOKEN
        and token == settings.MAINTENANCE_MASTER_TOKEN
    ):
        return {"sub": "maintenance-admin", "email": None, "role": "platform_admin"}

    # Token interno do login de manutenção
    internal = _decode_internal_token(token)
    if internal and internal.get("sub") == "maintenance-admin":
        return {"sub": "maintenance-admin", "email": None, "role": "platform_admin"}

    try:
        from app.core.supabase import get_supabase_admin
        res = get_supabase_admin().auth.get_user(token)
        user = getattr(res, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Sessão inválida")
        return {"sub": user.id, "email": getattr(user, "email", None), "role": None}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Sessão inválida")


def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    return user["sub"]


def require_platform_admin(user: dict = Depends(get_current_user)) -> dict:
    """Restringe ao admin da plataforma (manutenção) ou perfil com user_role='admin'."""
    if user.get("sub") == "maintenance-admin":
        return user
    try:
        from app.core.supabase import get_supabase_admin
        prof = (
            get_supabase_admin()
            .table("profiles")
            .select("user_role")
            .eq("id", user["sub"])
            .execute()
        )
        role = prof.data[0].get("user_role") if prof.data else None
    except Exception:
        role = None
    if role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user
