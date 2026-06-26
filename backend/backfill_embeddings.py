#!/usr/bin/env python3
"""
backfill_embeddings.py — Pipeline de Geração de Embeddings com Polars
=====================================================================
Yachts Atlas · Capitã Solara RAG

Puxa todos os trechos de `normas_conteudo` que ainda NÃO possuem
embedding, gera vetores via OpenAI (text-embedding-ada-002, 1536-dim)
em lotes otimizados e salva de volta no Supabase.

Dependências (já em requirements.txt):
    polars >= 0.20.0
    openai >= 1.40.0
    supabase >= 2.3.0
    python-dotenv >= 1.0.0

Uso:
    cd backend
    python backfill_embeddings.py

Variáveis de ambiente necessárias (.env):
    SUPABASE_URL
    SUPABASE_SERVICE_KEY
    OPENAI_API_KEY
"""

from __future__ import annotations

import os
import sys
import time
import logging
from pathlib import Path

import polars as pl
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

# ── Configuração ────────────────────────────────────────────────
load_dotenv(Path(__file__).resolve().parent / ".env")

SUPABASE_URL: str = os.environ["SUPABASE_URL"]
SUPABASE_KEY: str = os.environ["SUPABASE_SERVICE_KEY"]  # service role
OPENAI_API_KEY: str = os.environ["OPENAI_API_KEY"]

# IMPORTANTE: precisa ser EXATAMENTE o mesmo modelo usado pelo chatbot para
# gerar o embedding da PERGUNTA (config.OPENAI_EMBEDDING_MODEL). Corpus e query
# precisam viver no mesmo espaço vetorial, senão a similaridade vira ruído.
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIM = 1536
BATCH_SIZE = 50          # registros por chamada à OpenAI
UPDATE_CHUNK = 100       # registros por upsert no Supabase
RETRY_LIMIT = 3          # tentativas em caso de erro transitório
RETRY_BACKOFF = 2.0      # fator de backoff exponencial (segundos)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-7s │ %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("backfill")


# ── Clientes ────────────────────────────────────────────────────
def _init_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def _init_openai() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)


# ── Etapa 1: Extrair dados sem embedding ────────────────────────
def fetch_pending(sb: Client) -> pl.DataFrame:
    """Busca todos os registros de `normas_conteudo` cujo embedding é NULL."""
    log.info("Buscando registros sem embedding em normas_conteudo …")

    rows: list[dict] = []
    page_size = 1000
    offset = 0

    while True:
        res = (
            sb.table("normas_conteudo")
            .select("id, norma_codigo, secao, conteudo")
            .is_("embedding", "null")
            .range(offset, offset + page_size - 1)
            .execute()
        )
        batch = res.data or []
        rows.extend(batch)
        if len(batch) < page_size:
            break
        offset += page_size

    if not rows:
        log.info("✅ Nenhum registro pendente — tudo já tem embedding!")
        return pl.DataFrame()

    df = pl.DataFrame(rows)
    log.info(f"📦 {df.height} registros pendentes encontrados.")
    return df


# ── Etapa 2: Gerar embeddings via OpenAI em batches ─────────────
def generate_embeddings(client: OpenAI, df: pl.DataFrame) -> pl.DataFrame:
    """Adiciona coluna `embedding` ao DataFrame usando a API da OpenAI."""
    log.info(f"Gerando embeddings em lotes de {BATCH_SIZE} …")

    all_embeddings: list[list[float]] = []
    total = df.height
    processed = 0

    for batch_start in range(0, total, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total)
        batch_df = df.slice(batch_start, batch_end - batch_start)

        # Monta o texto de entrada: "seção | conteúdo"
        texts = [
            f"{row['secao']} | {row['conteudo']}"
            for row in batch_df.iter_rows(named=True)
        ]

        # Chamada com retry
        embedding_data = _call_openai_with_retry(client, texts)
        all_embeddings.extend(embedding_data)

        processed += len(texts)
        pct = (processed / total) * 100
        log.info(f"  ⚡ {processed}/{total} ({pct:.1f}%)")

    # Adicionar coluna ao DataFrame Polars
    df = df.with_columns(
        pl.Series("embedding", all_embeddings, dtype=pl.List(pl.Float64))
    )
    return df


def _call_openai_with_retry(
    client: OpenAI, texts: list[str]
) -> list[list[float]]:
    """Chama a API de embeddings com retry exponencial."""
    for attempt in range(1, RETRY_LIMIT + 1):
        try:
            response = client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except Exception as exc:
            if attempt == RETRY_LIMIT:
                log.error(f"❌ Falha após {RETRY_LIMIT} tentativas: {exc}")
                raise
            wait = RETRY_BACKOFF ** attempt
            log.warning(
                f"⚠ Tentativa {attempt}/{RETRY_LIMIT} falhou: {exc}. "
                f"Aguardando {wait:.1f}s …"
            )
            time.sleep(wait)
    return []  # unreachable, mas satisfaz o type-checker


# ── Etapa 3: Salvar embeddings de volta no Supabase ─────────────
def save_embeddings(sb: Client, df: pl.DataFrame) -> None:
    """Atualiza o Supabase em chunks usando upsert."""
    total = df.height
    log.info(f"Salvando {total} embeddings no Supabase …")
    saved = 0

    for chunk_start in range(0, total, UPDATE_CHUNK):
        chunk_end = min(chunk_start + UPDATE_CHUNK, total)
        chunk_df = df.slice(chunk_start, chunk_end - chunk_start)

        records = [
            {
                "id": row["id"],
                "norma_codigo": row["norma_codigo"],
                "secao": row["secao"],
                "conteudo": row["conteudo"],
                # pgvector aceita o literal "[v1,v2,...]". Stringificar evita
                # ambiguidade na serialização JSON do PostgREST para o tipo vector.
                "embedding": "[" + ",".join(map(str, row["embedding"])) + "]",
            }
            for row in chunk_df.iter_rows(named=True)
        ]

        # Upsert: insere ou atualiza com base no id
        sb.table("normas_conteudo").upsert(records).execute()

        saved += len(records)
        pct = (saved / total) * 100
        log.info(f"  💾 {saved}/{total} ({pct:.1f}%) salvos")

    log.info("✅ Todos os embeddings salvos com sucesso!")


# ── Pipeline principal ──────────────────────────────────────────
def main() -> None:
    log.info("=" * 60)
    log.info("Yachts Atlas — Backfill de Embeddings (Polars Pipeline)")
    log.info("=" * 60)

    t0 = time.perf_counter()

    sb = _init_supabase()
    oai = _init_openai()

    # 1. Extrair
    df = fetch_pending(sb)
    if df.is_empty():
        return

    # 2. Transformar (gerar embeddings)
    df = generate_embeddings(oai, df)

    # 3. Carregar (salvar no banco)
    save_embeddings(sb, df)

    elapsed = time.perf_counter() - t0
    log.info(f"🏁 Pipeline concluído em {elapsed:.2f}s")
    log.info(
        f"   Resumo: {df.height} embeddings gerados "
        f"({EMBEDDING_MODEL}, {EMBEDDING_DIM}d)"
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("\n🛑 Interrompido pelo usuário.")
        sys.exit(130)
    except Exception as exc:
        log.error(f"💥 Erro fatal: {exc}", exc_info=True)
        sys.exit(1)
