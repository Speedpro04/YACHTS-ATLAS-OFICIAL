"""
Yachts Atlas — API v1 Router
"""
from fastapi import APIRouter
from app.api.v1 import auth, ativos, documentos, integridade, payments, brokers, insurance

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(ativos.router, prefix="/ativos", tags=["ativos"])
router.include_router(documentos.router, prefix="/documentos", tags=["documentos"])
router.include_router(integridade.router, prefix="/integridade", tags=["integridade"])
router.include_router(payments.router, prefix="/payments", tags=["payments"])
router.include_router(brokers.router, prefix="/brokers", tags=["brokers"])
router.include_router(insurance.router, prefix="/insurance", tags=["insurance"])