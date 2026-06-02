-- ============================================================
-- Yachts Atlas — Tabela `registros` (alinhada às categorias do dossiê)
-- ------------------------------------------------------------
-- Substitui as tabelas técnicas que NÃO existem no banco
-- (engines, maintenance_logs, vessel_inspections) por UMA tabela
-- unificada: cada entrada pertence a uma `categoria` (= id em
-- frontend/src/config/dossieCategorias.ts) e guarda os campos
-- estruturados daquela categoria em JSONB.
--
-- Princípios:
--  - Backbone unificado por baixo (este SQL); telas bespoke por cima.
--  - Custódia: registros são IMUTÁVEIS (só SELECT + INSERT para o dono).
--  - Isolamento por dono via `usuario_id` (mesmo padrão de `ativos`).
--  - Uploads de arquivos continuam em `documentos` (já tem hash_sha256).
--
-- Validado contra o schema real: ativos.id é TEXT; o dono é ativos.usuario_id.
-- NÃO aplicado ainda — revisar e rodar advisors antes.
-- ============================================================

create table if not exists public.registros (
  id          uuid primary key default gen_random_uuid(),
  ativo_id    text not null references public.ativos(id) on delete cascade,
  usuario_id  uuid not null references auth.users(id),         -- dono (= ativos.usuario_id)
  categoria   text not null,                                   -- id da categoria (dossieCategorias.ts)
  titulo      text,
  dados       jsonb not null default '{}'::jsonb,              -- campos estruturados da categoria
  checklist   jsonb not null default '[]'::jsonb,              -- itens marcados
  observacao  text,
  status      text not null default 'registrado'
              check (status in ('registrado','pendente','atencao','concluido')),
  -- custódia
  hash_sha256 text,
  created_by  uuid references auth.users(id),
  created_at  timestamptz not null default timezone('utc', now())
);

create index if not exists registros_ativo_idx     on public.registros(ativo_id);
create index if not exists registros_categoria_idx on public.registros(categoria);
create index if not exists registros_usuario_idx   on public.registros(usuario_id);

-- ------------------------------------------------------------
-- RLS — dono vê/insere só os próprios registros. IMUTÁVEL:
-- sem UPDATE/DELETE para usuários (o cofre não se altera).
-- (A service role do backend ignora RLS para operações administrativas.)
-- ------------------------------------------------------------
alter table public.registros enable row level security;

drop policy if exists registros_select_own on public.registros;
create policy registros_select_own
  on public.registros for select
  to authenticated
  using (usuario_id = (select auth.uid()));

drop policy if exists registros_insert_own on public.registros;
create policy registros_insert_own
  on public.registros for insert
  to authenticated
  with check (usuario_id = (select auth.uid()));

grant usage on schema public to authenticated;
grant select, insert on public.registros to authenticated;

-- ============================================================
-- AJUSTE DE CÓDIGO NECESSÁRIO (depois de aplicar):
--  - backend/app/api/v1/registros.py: gravar `usuario_id` = dono do ativo
--    e `categoria` = id da categoria; (hoje grava sem usuario_id).
--  - frontend TechnicalFormOverlay.tsx: passar a gravar em `registros`
--    (categoria + dados JSONB) em vez de engines/maintenance_logs/
--    vessel_inspections (que não existem).
--  - uploads continuam indo para `documentos` (categoria + hash_sha256).
-- ============================================================
