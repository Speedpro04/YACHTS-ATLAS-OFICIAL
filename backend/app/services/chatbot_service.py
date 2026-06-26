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
import re
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
# Recuperação (RAG) — busca HÍBRIDA (código + semântica)
# ------------------------------------------------------------------
_known_codes: Optional[list[str]] = None


def _load_known_codes() -> list[str]:
    """Códigos de normas ativas/verificadas, em cache de processo."""
    global _known_codes
    if _known_codes is not None:
        return _known_codes
    try:
        rows = (
            get_supabase_admin()
            .table("normas")
            .select("codigo")
            .eq("ativo", True)
            .eq("status_verificacao", "verificada")
            .execute()
            .data
            or []
        )
        _known_codes = [r["codigo"] for r in rows]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Falha ao carregar códigos de normas (busca híbrida): %s", exc)
        _known_codes = []
    return _known_codes


def _codes_in_query(query: str) -> list[str]:
    """Detecta códigos de norma citados na pergunta (ex.: 'NORMAM-211', 'SOLAS').

    Códigos alfabéticos (LESTA, SOLAS, MARPOL...) exigem fronteira de palavra
    para não casarem dentro de outra palavra (ex.: 'molesta'). Códigos com
    dígito/separador (NORMAM-211, NBR-ISO-8666) casam por forma normalizada,
    tolerando variações de espaço/hífen.
    """
    up = query.upper()
    qn = re.sub(r"[\s\-]", "", up)
    hits: list[str] = []
    for code in _load_known_codes():
        cu = code.upper()
        if cu.isalpha():
            if re.search(rf"\b{re.escape(cu)}\b", up):
                hits.append(code)
        else:
            cn = re.sub(r"[\s\-]", "", cu)
            if len(cn) >= 4 and cn in qn:
                hits.append(code)
    return hits


def _sections_by_codes(codes: list[str], k: int) -> list[dict]:
    """Match lexical: seções das normas citadas pelo código, direto do banco."""
    if not codes:
        return []
    sb = get_supabase_admin()
    try:
        metas = (
            sb.table("normas").select("codigo,titulo,fonte_url")
            .in_("codigo", codes).eq("ativo", True).eq("status_verificacao", "verificada")
            .execute().data or []
        )
        meta = {m["codigo"]: m for m in metas}
        if not meta:
            return []
        secs = (
            sb.table("normas_conteudo").select("norma_codigo,secao,conteudo")
            .in_("norma_codigo", list(meta)).order("ordem").execute().data or []
        )
        return [
            {
                "codigo": s["norma_codigo"],
                "titulo": f"{meta[s['norma_codigo']]['titulo']} ({s['secao']})",
                "descricao": s["conteudo"],
                "fonte_url": meta[s["norma_codigo"]]["fonte_url"],
                "_score": 1.0,  # citação explícita do código = match forte
            }
            for s in secs[: k + 2]
        ]
    except Exception as exc:  # noqa: BLE001
        logger.warning("Busca por código falhou: %s", exc)
        return []


def _semantic_search(query: str, k: int) -> list[dict]:
    """Busca semântica via pgvector (Supabase RPC)."""
    q_emb = _embed(query)
    if q_emb is None:
        return []
    try:
        res = get_supabase_admin().rpc("match_normas_conteudo", {
            "query_embedding": q_emb,
            "match_threshold": settings.CHATBOT_MIN_RELEVANCE,
            "match_count": k,
        }).execute()
        return [
            {
                "codigo": r["norma_codigo"],
                "titulo": f"{r['titulo']} ({r['secao']})",
                "descricao": r["conteudo"],
                "fonte_url": r["fonte_url"],
                "_score": r["similarity"],
            }
            for r in (res.data or [])
        ]
    except Exception as exc:  # noqa: BLE001
        logger.error("Busca vetorial RPC falhou (pgvector ativo?): %s", exc)
        return []


def retrieve(query: str, k: int = 3) -> list[dict]:
    """Recuperação HÍBRIDA das normas mais relevantes.

    Combina (a) match lexical por código citado na pergunta — "o que diz a
    NORMAM-211?" — com (b) busca semântica via pgvector. O match por código vem
    primeiro: quando a pessoa cita a norma pelo nome, é isso que ela quer ver.
    """
    direct = _sections_by_codes(_codes_in_query(query), k)
    semantic = _semantic_search(query, k)

    out: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for item in direct + semantic:
        key = (item["codigo"], item["titulo"])
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out[: max(k, len(direct))]


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


def _fallback_from_norms(norms: list[dict], limit: int = 2) -> str:
    """Resposta de contingência quando o LLM está indisponível.

    Em vez de deixar a Capitã muda, servimos o conteúdo da(s) norma(s)
    recuperada(s) direto da fonte. A promessa central — citar a norma — continua
    de pé mesmo sem o modelo de linguagem (resiliência a queda/quota da OpenAI).
    """
    blocos = []
    for n in norms[:limit]:
        corpo = (n.get("descricao") or "").strip()
        if not corpo:
            continue
        bloco = f"**{n.get('codigo', '')} — {n.get('titulo', '')}**\n\n{corpo}"
        if n.get("fonte_url"):
            bloco += f"\n\nFonte: {n['fonte_url']}"
        blocos.append(bloco)

    if not blocos:
        return (
            "Estou com uma instabilidade momentânea para gerar a resposta. "
            "Tente novamente em instantes, por favor."
        )

    return (
        "Estou com uma instabilidade momentânea no meu gerador de respostas, "
        "mas localizei a norma que trata disso e te trago o trecho direto da fonte:\n\n"
        + "\n\n———\n\n".join(blocos)
    )


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

    reason = "ok"
    raw = ""
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
    except Exception as exc:  # noqa: BLE001
        # Loga o TIPO do erro (quota/modelo inválido/timeout/…) para diagnóstico.
        logger.error("Falha na chamada ao modelo (%s): %s", type(exc).__name__, exc)

    # 5) Guard rail de SAÍDA
    answer = guard.scrub_output(raw)

    # CONTINGÊNCIA: se o modelo falhou ou veio vazio, a Capitã NÃO fica muda.
    # Servimos o conteúdo da norma recuperada direto da fonte. Ela só fica
    # indisponível de verdade se nem isso houver (não deveria, pois já passou
    # pelo guard rail de escopo com norma relevante).
    if not answer.strip():
        reason = "model_degraded"
        answer = guard.scrub_output(_fallback_from_norms(norms))

    # Atualiza memória da conversa
    new_history = history + [
        {"role": "user", "content": clean_msg},
        {"role": "assistant", "content": answer},
    ]
    _save_session(session_id, new_history)

    # Fontes para a UI: uma por norma (dedupe por código; várias seções da
    # mesma norma não devem virar vários chips repetidos).
    sources = []
    seen_src: set[str] = set()
    for n in norms:
        if n["codigo"] in seen_src:
            continue
        seen_src.add(n["codigo"])
        sources.append({"codigo": n["codigo"], "titulo": n.get("titulo"), "fonte_url": n.get("fonte_url")})
    return {"answer": answer, "blocked": False, "reason": reason, "sources": sources}
