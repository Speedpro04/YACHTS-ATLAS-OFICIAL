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
        "allowed_origins": settings.cors_origins,
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET),
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY),
    }


@router.get("/diagnostico-avisos")
async def diagnostico_avisos(_admin: dict = Depends(require_platform_admin)):
    """
    Por que os avisos do fundador não estão saindo — sem precisar adivinhar.

    A lógica mora em `app/services/diagnostico_avisos.py` porque o boot da
    aplicação faz a mesma conferência a cada deploy. Duas cópias da mesma
    checagem divergem, e a que fica errada é sempre a que ninguém está olhando.

    NÃO ENVIA NADA. Só lê a configuração, testa a conexão da instância e diz o
    que está faltando. Segredos saem mascarados.
    """
    from app.services.diagnostico_avisos import estado_dos_avisos
    return estado_dos_avisos()
