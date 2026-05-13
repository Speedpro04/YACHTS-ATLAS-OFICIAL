"""
Yachts Atlas — Admin Maintenance Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import verify_token
from app.core.config import settings

router = APIRouter()


def require_maintenance_admin(token: str) -> dict:
    payload = verify_token(token)
    if not payload or payload.get("sub") != "maintenance-admin":
        raise HTTPException(status_code=401, detail="Maintenance admin access required")
    return payload


@router.get("/maintenance/status")
async def maintenance_status(token: str):
    require_maintenance_admin(token)
    return {
        "status": "ok",
        "maintenance_bypass_enabled": settings.MAINTENANCE_BYPASS_ENABLED,
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET),
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY),
    }
