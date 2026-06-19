"""
Yachts Atlas — Core Configuration
"""
import json
import os
from functools import lru_cache

from pydantic_settings import BaseSettings


def _parse_allowed_origins(raw: str | None) -> list[str]:
    if not raw:
        return [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://yachts.axoshub.com",
            "https://yachtsatlas.com",
            "https://www.yachtsatlas.com",
            "https://yachtsatlas.online",
            "https://www.yachtsatlas.online",
        ]

    raw = raw.strip()
    if raw.startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [str(origin).strip() for origin in parsed if str(origin).strip()]
        except json.JSONDecodeError:
            pass

    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Yachts Atlas"
    VERSION: str = "0.1.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = _parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))

    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    SUPABASE_JWT_SECRET: str = os.getenv("SUPABASE_JWT_SECRET", "")

    # Redis — cache de velocidade. Secret só em variável de ambiente (repo público).
    # Se vazio ou indisponível, o app funciona normalmente (cache é opcional).
    REDIS_URL: str = os.getenv("REDIS_URL", "")
    REDIS_DEFAULT_TTL: int = int(os.getenv("REDIS_DEFAULT_TTL", "3600"))

    # OpenAI — chatbot de normas (RAG). Secrets só em variável de ambiente.
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_CHAT_MODEL: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-5-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    # Anti-abuso/sondagem: máximo de perguntas por usuário por minuto.
    CHATBOT_RATE_LIMIT_PER_MIN: int = int(os.getenv("CHATBOT_RATE_LIMIT_PER_MIN", "15"))
    # Score mínimo de similaridade para considerar que existe norma relevante.
    # Abaixo disso, o bot recusa em vez de "inventar" (anti-alucinação).
    CHATBOT_MIN_RELEVANCE: float = float(os.getenv("CHATBOT_MIN_RELEVANCE", "0.35"))

    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "yachts-docs")

    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    STRIPE_PRICE_ID: str = os.getenv("STRIPE_PRICE_ID", "")
    MAINTENANCE_USERNAME: str = os.getenv("MAINTENANCE_USERNAME", "")
    MAINTENANCE_PASSWORD: str = os.getenv("MAINTENANCE_PASSWORD", "")
    MAINTENANCE_BYPASS_ENABLED: bool = os.getenv("MAINTENANCE_BYPASS_ENABLED", "false").lower() == "true"
    MAINTENANCE_MASTER_TOKEN: str = os.getenv("MAINTENANCE_MASTER_TOKEN", "")

    # Dossiê: quando true, o PDF só sai para ativo com pagamento concluído.
    # Mantido false — o dossiê não é mais vendido pela plataforma (vai direto
    # marina <-> dono). O dono/marina sempre acessa o próprio dossiê.
    DOSSIER_REQUIRE_PAYMENT: bool = os.getenv("DOSSIER_REQUIRE_PAYMENT", "false").lower() == "true"

    # Senha-mestra para liberação de dossiê a terceiros (broker/comprador/
    # seguradora) via link público no celular. Defina em variável de ambiente.
    DOSSIER_MASTER_PASSWORD: str = os.getenv("DOSSIER_MASTER_PASSWORD", "")

    # URL pública do site (usada em e-mails de liberação de dossiê)
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "https://yachtsatlas.online")

    # Email Configuration for Alerts
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "yachtsatlas@gmail.com")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")
    EMAIL_SMTP_HOST: str = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
    EMAIL_SMTP_PORT: int = int(os.getenv("EMAIL_SMTP_PORT", "465"))

    # Telegram — aviso de novo pedido de dossiê no celular do fundador
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Referral Program — real limit is 30 (frontend displays 14 for scarcity)
    # Modelo definitivo: marina que indica fica com 100% dos dossiês por 18 meses.
    # Após o 1º ano de operação: assinatura sobe p/ $300 e 100% do dossiê é da
    # marina permanentemente (negócio = recorrência mensal).
    REFERRAL_MAX_SLOTS: int = 30
    REFERRAL_DOSSIER_SHARE_PERCENT: int = 100  # 100% for referring marina
    REFERRAL_REWARD_MONTHS: int = 18
    REFERRAL_MIN_RETENTION_MONTHS: int = 3  # referred marina must stay 3 months

    # Programa de Lançamento — 7 Marinas Fundadoras
    # $180/mês por 12 meses → depois $300/mês. Bônus: 100% dos dossiês por 18
    # meses, destravado ao trazer 7 marinas. Marinas indicadas pagam $250/mês.
    LAUNCH_SLOTS: int = 7
    LAUNCH_PRICE_MONTHLY: int = 180
    LAUNCH_PROMO_MONTHS: int = 12
    LAUNCH_PRICE_AFTER: int = 300
    LAUNCH_REFERRED_PRICE: int = 250
    LAUNCH_REFERRALS_REQUIRED: int = 7
    LAUNCH_DOSSIER_BONUS_MONTHS: int = 18

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
