-- ============================================================
-- Yachts Atlas — Migração RAG para pgvector
-- ------------------------------------------------------------
-- Esta migração ativa a extensão pgvector e cria as
-- estruturas nativas para a busca vetorial (RAG) da Capitã Solara.
-- ============================================================

-- 1. Ativar a extensão vector
create extension if not exists vector with schema public;

-- 2. Adicionar a coluna de embeddings na tabela normas_conteudo
alter table public.normas_conteudo add column if not exists embedding vector(1536);

-- 3. Criar índice HNSW para busca vetorial extremamente rápida
create index if not exists normas_conteudo_embedding_idx 
on public.normas_conteudo 
using hnsw (embedding vector_cosine_ops)
with (m = 16, ef_construction = 64);

-- 3b. Índice único: impede seções duplicadas (segurança em re-execução de seeds)
create unique index if not exists normas_conteudo_norma_secao_uk
on public.normas_conteudo (norma_codigo, secao);

-- 4. Função RPC para a busca RAG (Chamada pelo backend Python)
create or replace function match_normas_conteudo (
  query_embedding vector(1536),
  match_threshold float,
  match_count int
)
returns table (
  id uuid,
  norma_codigo text,
  secao text,
  conteudo text,
  titulo text,
  fonte_url text,
  similarity float
)
language sql stable
set search_path = public
as $$
  select
    nc.id,
    nc.norma_codigo,
    nc.secao,
    nc.conteudo,
    n.titulo,
    n.fonte_url,
    1 - (nc.embedding <=> query_embedding) as similarity
  from public.normas_conteudo nc
  join public.normas n on n.codigo = nc.norma_codigo
  where nc.embedding is not null
    and 1 - (nc.embedding <=> query_embedding) > match_threshold
    and n.ativo = true
    and n.status_verificacao = 'verificada'
  order by nc.embedding <=> query_embedding
  limit match_count;
$$;
