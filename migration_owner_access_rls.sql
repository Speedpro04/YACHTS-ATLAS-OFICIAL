-- ============================================================
-- Yachts Atlas — Acesso do Proprietário: Palavra Secreta
-- ------------------------------------------------------------
-- IMPORTANTE (validado no banco real via Supabase MCP em 2026):
-- O isolamento anti-bisbilhotice JÁ EXISTE. As tabelas `ativos` e
-- `documentos` já têm políticas RLS com `auth.uid() = usuario_id`
-- (SELECT/INSERT/UPDATE/DELETE). O proprietário já só enxerga o
-- próprio ativo. NÃO recriar essas políticas nem tabela de vínculo
-- (o vínculo dono↔ativo é a coluna `ativos.usuario_id`).
--
-- Portanto, a ÚNICA coisa que falta no banco para o fluxo de acesso
-- do proprietário é guardar a PALAVRA SECRETA (com hash).
--
-- Autenticação (camadas) — feita pelo Supabase Auth, NÃO por SQL:
--   1) e-mail + senha            -> auth.signInWithPassword
--   2) código de uso único (OTP) -> auth.signInWithOtp (expira, 1 uso)
--   3) palavra secreta           -> verificada no app contra o hash abaixo
--
-- NÃO usar CPF nem nome da embarcação como credencial.
-- Antes de aplicar: rodar advisors. NÃO aplicado ainda.
-- ============================================================

-- ------------------------------------------------------------
-- Palavra secreta do proprietário (armazenada com HASH)
-- Nunca em texto puro. O app gera o hash (bcrypt) e grava aqui;
-- a verificação compara hashes no app.
-- ------------------------------------------------------------
create table if not exists public.owner_access (
  user_id          uuid primary key references auth.users(id) on delete cascade,
  secret_word_hash text not null,
  created_at       timestamptz not null default timezone('utc', now()),
  updated_at       timestamptz not null default timezone('utc', now())
);

-- RLS: cada usuário só lê/atualiza a própria linha.
alter table public.owner_access enable row level security;

-- SELECT do próprio registro
drop policy if exists owner_access_select_self on public.owner_access;
create policy owner_access_select_self
  on public.owner_access for select
  to authenticated
  using (user_id = (select auth.uid()));

-- UPDATE do próprio registro (UPDATE no Postgres exige SELECT também — ambas presentes)
drop policy if exists owner_access_update_self on public.owner_access;
create policy owner_access_update_self
  on public.owner_access for update
  to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

-- INSERT: feito pela service role no cadastro (marina configura o dono).
-- Sem política de INSERT para `authenticated` de propósito.

-- Grants para o portal do proprietário (role authenticated).
grant usage on schema public to authenticated;
grant select, update on public.owner_access to authenticated;

-- ============================================================
-- NOTAS / itens separados (NÃO neste arquivo):
--  - `registros` NÃO existe no banco — criar tabela antes de usar
--    o backend de registros (decisão pendente).
--  - `marinas` NÃO existe — o checkout de dossiê com split a referencia.
--  - Formulários técnicos usam `engines`/`maintenance_logs`/
--    `vessel_inspections` que NÃO existem — alinhar código x banco.
--  - Advisors apontaram: bucket `media` público lista arquivos;
--    funções com search_path mutável. Tratar em migrations próprias.
-- ============================================================
