"""
Yachts Atlas — Admin Maintenance Endpoints
"""
from fastapi import APIRouter, Depends
from app.core.security import require_platform_admin
from app.core.config import settings

router = APIRouter()


@router.get("/maintenance/status")
async def maintenance_status(_admin: dict = Depends(require_platform_admin)):
    return {
        "status": "ok",
        "maintenance_bypass_enabled": settings.MAINTENANCE_BYPASS_ENABLED,
        "allowed_origins": settings.ALLOWED_ORIGINS,
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET),
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY),
    }
