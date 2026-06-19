"""
Yachts Atlas — Camada de cache (Redis)

Regra de ouro: o cache NUNCA pode derrubar o app. Se o Redis estiver
indisponível (ou REDIS_URL vazio), todas as funções degradam em silêncio —
o sistema continua respondendo, apenas sem o ganho de velocidade.

Uso típico:

    from app.core.cache import cache_get_json, cache_set_json, cached

    data = cache_get_json("normas:lista")
    if data is None:
        data = consulta_cara_no_banco()
        cache_set_json("normas:lista", data, ttl=3600)

ou, como decorator:

    @cached("normas:lista", ttl=3600)
    def listar_normas():
        return consulta_cara_no_banco()
"""
from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: "Optional[Any]" = None
_init_attempted = False


def get_client() -> Optional[Any]:
    """Retorna o client Redis singleton, ou None se indisponível.

    A conexão é tentada uma única vez (lazy). Falha não levanta exceção —
    apenas desativa o cache para o resto do processo.
    """
    global _client, _init_attempted
    if _init_attempted:
        return _client

    _init_attempted = True
    if not settings.REDIS_URL:
        logger.info("REDIS_URL não definido — cache desativado.")
        return None

    try:
        import redis  # import tardio: dependência opcional em runtime

        client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        _client = client
        logger.info("Redis conectado — cache ativo.")
    except Exception as exc:  # noqa: BLE001 — cache nunca derruba o app
        logger.warning("Redis indisponível, seguindo sem cache: %s", exc)
        _client = None

    return _client


def cache_get_json(key: str) -> Optional[Any]:
    """Lê um valor JSON do cache. Retorna None se ausente, expirado ou em erro."""
    client = get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw is not None else None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao ler cache (%s): %s", key, exc)
        return None


def cache_set_json(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Grava um valor JSON no cache com TTL (segundos). Falha em silêncio."""
    client = get_client()
    if client is None:
        return
    try:
        client.set(
            key,
            json.dumps(value, default=str, ensure_ascii=False),
            ex=ttl or settings.REDIS_DEFAULT_TTL,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao gravar cache (%s): %s", key, exc)


def cache_delete(*keys: str) -> None:
    """Invalida chaves do cache. Falha em silêncio."""
    client = get_client()
    if client is None or not keys:
        return
    try:
        client.delete(*keys)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao invalidar cache (%s): %s", keys, exc)


def cached(key: str, ttl: Optional[int] = None) -> Callable:
    """Decorator que cacheia o retorno (serializável em JSON) de uma função.

    Use uma chave fixa para funções sem argumento, ou inclua os argumentos na
    chave manualmente quando o resultado depender deles.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cached_value = cache_get_json(key)
            if cached_value is not None:
                return cached_value
            result = func(*args, **kwargs)
            cache_set_json(key, result, ttl=ttl)
            return result

        return wrapper

    return decorator
