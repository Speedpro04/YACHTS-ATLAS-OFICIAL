"""
Yachts Atlas — Supabase Client
"""
from functools import lru_cache
from supabase import create_client, Client
from app.core.config import settings


@lru_cache()
def _build_supabase_client(url: str, key: str) -> Client:
    return create_client(url, key)


def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be configured")
    return _build_supabase_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)


def get_supabase_admin() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be configured")
    return _build_supabase_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
