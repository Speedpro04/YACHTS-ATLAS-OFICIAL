"""
Yachts Atlas — Supabase Client
"""
import logging
from functools import lru_cache
from typing import Any, Optional

from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)


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


_PAGINA = 200
_MAX_PAGINAS = 25  # teto defensivo: 5000 usuarios


def buscar_usuario_por_email(email: str) -> Optional[Any]:
    """
    Acha o usuario do Auth pelo e-mail, ou None.

    O admin do supabase-py so expoe get_user_by_id, entao paginamos list_users
    e filtramos aqui. Usado pelo webhook do Stripe: o Payment Link nao carrega
    user_id no metadata, e payments.usuario_id e NOT NULL — sem essa busca o
    pagamento da marina nao consegue ser gravado.
    """
    if not email:
        return None

    alvo = email.strip().lower()
    try:
        admin = get_supabase_admin().auth.admin
    except Exception as e:
        logger.error(f"Supabase admin indisponivel ao buscar {alvo}: {e}")
        return None

    for pagina in range(1, _MAX_PAGINAS + 1):
        try:
            usuarios = admin.list_users(page=pagina, per_page=_PAGINA)
        except Exception as e:
            logger.error(f"Falha ao listar usuarios (pagina {pagina}) para {alvo}: {e}")
            return None

        if not usuarios:
            return None

        for usuario in usuarios:
            if (getattr(usuario, "email", "") or "").strip().lower() == alvo:
                return usuario

        if len(usuarios) < _PAGINA:
            return None

    logger.warning(f"Busca por {alvo} passou de {_MAX_PAGINAS * _PAGINA} usuarios sem achar")
    return None
