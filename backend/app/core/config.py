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

    # Dossiê: quando true, o PDF só sai para ativo com pagamento concluído
    DOSSIER_REQUIRE_PAYMENT: bool = os.getenv("DOSSIER_REQUIRE_PAYMENT", "false").lower() == "true"

    # Email Configuration for Alerts
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER", "yachtsatlas@gmail.com")
    EMAIL_PASSWORD: str = os.getenv("EMAIL_PASSWORD", "")

    # Referral Program — real limit is 30 (frontend displays 14 for scarcity)
    REFERRAL_MAX_SLOTS: int = 30
    REFERRAL_DOSSIER_SHARE_PERCENT: int = 100  # 100% for referred marinas
    REFERRAL_REWARD_MONTHS: int = 12
    REFERRAL_MIN_RETENTION_MONTHS: int = 3  # referred marina must stay 3 months

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
