"""
Yachts Atlas — FastAPI Backend
Main application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import router as api_v1
from app.core.config import settings
from app.middleware.tracking import RequestTrackingMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Registro digital imutável para ativos náuticos",
)

# Add request tracking middleware
app.add_middleware(RequestTrackingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1.router, prefix="/api/v1")


@app.on_event("startup")
async def _ligar_agenda() -> None:
    """
    A régua de cobrança roda dentro da aplicação, não num cron externo.

    Cron externo some numa migração de servidor, quebra quando o caminho do
    Python muda, para quando alguém recria o container — e ninguém percebe,
    porque não avisar é indistinguível de "não havia ninguém devendo". O erro
    aparece na conversa mais cara possível: a marina cortada dizendo que nunca
    foi avisada. Ver app/services/agenda.py.
    """
    from app.services.agenda import iniciar
    iniciar()


@app.on_event("shutdown")
async def _desligar_agenda() -> None:
    from app.services.agenda import parar
    parar()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "tracking": "enabled",
        "audit": "enabled"
    }