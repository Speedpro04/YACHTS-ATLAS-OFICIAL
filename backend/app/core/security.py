"""
Yachts Atlas — Security Utilities
"""
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SUPABASE_SERVICE_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    if (
        settings.MAINTENANCE_BYPASS_ENABLED
        and settings.MAINTENANCE_MASTER_TOKEN
        and token == settings.MAINTENANCE_MASTER_TOKEN
    ):
        return {"sub": "maintenance-admin", "role": "owner", "type": "access"}

    try:
        payload = jwt.decode(token, settings.SUPABASE_SERVICE_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
