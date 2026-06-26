"""
Yachts Atlas — Chatbot de Normas (RAG + guard rails)

Fluxo de uma pergunta:

    guard rail de ENTRADA  (chatbot_guardrails.check_input)
        -> rate limit (Redis)
        -> RECUPERA normas relevantes (busca semântica)
        -> guard rail de ESCOPO (is_answerable: tem norma relevante?)
        -> GPT-5-mini responde SÓ com o contexto das normas
        -> guard rail de SAÍDA (scrub_output)

Decisões:
  • Fonte de contexto = SOMENTE a tabela `normas` (verificada/ativa). O bot não
    tem acesso a dados de marina, dono ou pessoas, e não tem nenhuma capacidade
    de escrita. As restrições de segurança são, antes de tudo, arquiteturais.
  • Busca semântica feita em Python com embeddings cacheados no Redis. Para o
    tamanho atual do catálogo é o suficiente; quando crescer, migrar para
    pgvector é uma troca localizada em `retrieve()`.
  • Se a OpenAI/credencial não estiver configurada, o serviço degrada com uma
    mensagem clara em vez de quebrar.
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Optional

from app.core.cache import cache_get_json, cache_set_json, get_client as get_redis
from app.core.config import settings
from app.core.supabase import get_supabase_admin
from app.services import chatbot_guardrails as guard

logger = logging.getLogger(__name__)

_openai_client: Optional[Any] = None
_openai_init_attempted = False

_NORMS_EMB_CACHE_KEY = "chatbot:norms_embeddings:v1"
_NORMS_EMB_TTL = 24 * 3600          # embeddings de normas mudam pouco
_SESSION_TTL = 1800                 # memória de conversa: 30 min
_SESSION_MAX_TURNS = 6              # últimas trocas mantidas no contexto


# ------------------------------------------------------------------
# Cliente OpenAI (lazy, tolerante a ausência de credencial)
# ------------------------------------------------------------------
def _get_openai() -> Optional[Any]:
    global _openai_client, _openai_init_attempted
    if _openai_init_attempted:
        return _openai_client
    _openai_init_attempted = True
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY ausente — chatbot indisponível.")
        return None
    try:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha ao iniciar OpenAI: %s", exc)
        _openai_client = None
    return _openai_client


def _embed(text: str) -> Optional[list[float]]:
    client = _get_openai()
    if client is None:
        return None
    try:
        resp = client.embeddings.create(
            model=settings.OPENAI_EMBEDDING_MODEL,
            input=text[:8000],
        )
        return resp.data[0].embedding
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha ao gerar embedding: %s", exc)
        return None


# ------------------------------------------------------------------
# Recuperação (RAG) — busca as normas mais relevantes
# ------------------------------------------------------------------
def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _load_norms_with_embeddings() -> list[dict]:
    """Carrega normas verificadas/ativas + seus embeddings (cacheados no Redis)."""
    cached = cache_get_json(_NORMS_EMB_CACHE_KEY)
    if cached:
        return cached

    supabase = get_supabase_admin()
    rows = (
        supabase.table("normas")
        .select("codigo,titulo,descricao,orgao,serie,versao,fonte_url")
        .eq("ativo", True)
        .eq("status_verificacao", "verificada")
        .execute()
        .data
        or []
    )

    enriched: list[dict] = []
    for n in rows:
        texto = f"{n['codigo']} — {n.get('titulo','')}. {n.get('descricao','')}"
        emb = _embed(texto)
        if emb is None:
            continue
        enriched.append({**n, "_embedding": emb})

    if enriched:
        cache_set_json(_NORMS_EMB_CACHE_KEY, enriched, ttl=_NORMS_EMB_TTL)
    return enriched


def retrieve(query: str, k: int = 3) -> list[dict]:
    """Retorna as `k` normas mais relevantes, cada uma com `_score` (0..1)."""
    q_emb = _embed(query)
    if q_emb is None:
        return []
    ranked = []
    for n in _load_norms_with_embeddings():
        score = _cosine(q_emb, n["_embedding"])
        ranked.append({**{k: v for k, v in n.items() if k != "_embedding"}, "_score": score})
    ranked.sort(key=lambda x: x["_score"], reverse=True)
    return ranked[:k]


# ------------------------------------------------------------------
# Rate limit (anti-abuso/sondagem) via Redis
# ------------------------------------------------------------------
def rate_limit_ok(user_key: str) -> bool:
    redis = get_redis()
    if redis is None:
        return True  # sem Redis, não bloqueia (cache é opcional)
    try:
        bucket = f"chatbot:rl:{user_key}"
        count = redis.incr(bucket)
        if count == 1:
            redis.expire(bucket, 60)
        return count <= settings.CHATBOT_RATE_LIMIT_PER_MIN
    except Exception:  # noqa: BLE001
        return True


# ------------------------------------------------------------------
# Memória de conversa (curta) via Redis
# ------------------------------------------------------------------
def _session_history(session_id: str) -> list[dict]:
    if not session_id:
        return []
    data = cache_get_json(f"chatbot:sess:{session_id}")
    return data or []


def _save_session(session_id: str, history: list[dict]) -> None:
    if not session_id:
        return
    cache_set_json(f"chatbot:sess:{session_id}", history[-_SESSION_MAX_TURNS:], ttl=_SESSION_TTL)


# ------------------------------------------------------------------
# Orquestração
# ------------------------------------------------------------------
def _build_context(norms: list[dict]) -> str:
    blocos = []
    for n in norms:
        blocos.append(
            f"[{n['codigo']}] {n.get('titulo','')}\n"
            f"Órgão: {n.get('orgao','')} {('· ' + n['serie']) if n.get('serie') else ''}\n"
            f"Versão: {n.get('versao','—')}\n"
            f"{n.get('descricao','')}\n"
            f"Fonte: {n.get('fonte_url','')}"
        )
    return "\n\n---\n\n".join(blocos)


def ask(message: str, session_id: str = "", user_key: str = "anon") -> dict:
    """Processa uma pergunta com todas as camadas de guard rail."""
    # 1) Guard rail de ENTRADA
    verdict = guard.check_input(message)
    if not verdict.allowed:
        return {"answer": verdict.refusal, "blocked": True, "reason": verdict.reason, "sources": []}
    clean_msg = verdict.sanitized or message.strip()

    # 2) Rate limit
    if not rate_limit_ok(user_key):
        return {
            "answer": "Você fez muitas perguntas em pouco tempo. Aguarde um instante e tente de novo.",
            "blocked": True, "reason": "rate_limited", "sources": [],
        }

    # 2b) Saudação / abertura: recebe com calor e pergunta como pode ajudar
    #     (sem exigir norma — cumprimento não é pergunta técnica).
    if guard.is_greeting(clean_msg):
        return {"answer": guard.WELCOME, "blocked": False, "reason": "greeting", "sources": []}

    # 3) Recuperação + guard rail de ESCOPO
    norms = retrieve(clean_msg)
    top = norms[0]["_score"] if norms else None
    if not guard.is_answerable(top, settings.CHATBOT_MIN_RELEVANCE):
        return {"answer": guard.REFUSAL_NO_NORM, "blocked": True, "reason": "no_relevant_norm", "sources": []}

    client = _get_openai()
    if client is None:
        return {
            "answer": "O assistente de normas está temporariamente indisponível.",
            "blocked": True, "reason": "openai_unavailable", "sources": [],
        }

    # 4) Monta mensagens: system + histórico curto + contexto + pergunta
    history = _session_history(session_id)
    messages = [{"role": "system", "content": guard.SYSTEM_PROMPT}]
    messages += history
    contexto = _build_context(norms)
    messages.append({
        "role": "user",
        "content": f"CONTEXTO DE NORMAS (use apenas isto):\n\n{contexto}\n\nPERGUNTA: {clean_msg}",
    })

    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=messages,
            # gpt-5-mini é modelo de raciocínio: o budget inclui os tokens de
            # "pensamento". 600 era baixo demais (o raciocínio consumia tudo e a
            # resposta vinha vazia). Folga generosa garante texto de saída.
            max_completion_tokens=3000,
        )
        raw = resp.choices[0].message.content or ""
        if not raw.strip():
            logger.warning(
                "Resposta vazia do modelo (finish_reason=%s).",
                getattr(resp.choices[0], "finish_reason", "?"),
            )
            raw = (
                "Consegui localizar a(s) norma(s) relacionada(s) abaixo, mas não "
                "gerei o texto da resposta agora. Tente perguntar de novo, por favor."
            )
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha na chamada ao modelo: %s", exc)
        return {
            "answer": "Não consegui responder agora. Tente novamente em instantes.",
            "blocked": True, "reason": "model_error", "sources": [],
        }

    # 5) Guard rail de SAÍDA
    answer = guard.scrub_output(raw)

    # Atualiza memória da conversa
    new_history = history + [
        {"role": "user", "content": clean_msg},
        {"role": "assistant", "content": answer},
    ]
    _save_session(session_id, new_history)

    sources = [{"codigo": n["codigo"], "titulo": n.get("titulo"), "fonte_url": n.get("fonte_url")} for n in norms]
    return {"answer": answer, "blocked": False, "reason": "ok", "sources": sources}
