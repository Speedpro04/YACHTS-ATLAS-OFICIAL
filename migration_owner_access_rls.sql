-- ============================================================
-- Yachts Atlas — Acesso do Proprietário (Armador) + RLS
-- ------------------------------------------------------------
-- Objetivo: o proprietário enxerga SOMENTE o(s) próprio(s)
-- ativo(s) e seus registros/documentos. Anti-IDOR (ninguém
-- bisbilhota embarcação de terceiro), proteção no BANCO.
--
-- Autenticação (camadas) — feita pelo Supabase Auth, NÃO por SQL:
--   1) e-mail + senha            -> auth.signInWithPassword
--   2) código de uso único (OTP) -> auth.signInWithOtp (expira em minutos, 1 uso)
--   3) palavra secreta           -> verificada no app contra o hash em owner_access
-- O RLS abaixo é a "parede do cofre"; o login é a "fechadura".
--
-- Modelo de acesso:
--   - Backend/Marina/Admin usam a SERVICE ROLE -> ignoram RLS (acesso total controlado pela app).
--   - Portal do proprietário usa o usuário AUTHENTICATED -> RLS restringe ao próprio ativo.
--
-- NÃO usar CPF nem nome da embarcação como credencial (não são segredos; CPF = risco LGPD).
--
-- ATENÇÃO: preparar/revisar — rodar `supabase db advisors` (ou MCP get_advisors)
-- e validar contra o schema atual ANTES de aplicar em produção.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Schema privado para funções SECURITY DEFINER
--    (a skill: nunca colocar security definer em schema exposto)
-- ------------------------------------------------------------
create schema if not exists private;

-- ------------------------------------------------------------
-- 2. Palavra secreta do proprietário (armazenada com HASH)
--    Nunca guardar a palavra em texto puro. O app gera o hash
--    (ex: bcrypt) e grava aqui; a verificação compara hashes.
-- ------------------------------------------------------------
create table if not exists public.owner_access (
  user_id          uuid primary key references auth.users(id) on delete cascade,
  secret_word_hash text not null,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

-- ------------------------------------------------------------
-- 3. Vínculo dono <-> embarcação
--    Tabela de ligação: suporta múltiplos ativos por dono e
--    co-proprietários no futuro, sem alterar o núcleo.
-- ------------------------------------------------------------
create table if not exists public.asset_owners (
  ativo_id   uuid not null references public.ativos(id) on delete cascade,
  user_id    uuid not null references auth.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (ativo_id, user_id)
);
create index if not exists asset_owners_user_idx  on public.asset_owners(user_id);
create index if not exists asset_owners_ativo_idx on public.asset_owners(ativo_id);

-- ------------------------------------------------------------
-- 4. Helper de autorização (SECURITY DEFINER, schema privado)
--    Verifica se o usuário logado é dono do ativo SEM causar
--    recursão de RLS. search_path vazio = boa prática de segurança.
-- ------------------------------------------------------------
create or replace function private.user_owns_ativo(p_ativo_id uuid)
returns boolean
language sql
security definer
set search_path = ''
stable
as $$
  select exists (
    select 1
    from public.asset_owners ao
    where ao.ativo_id = p_ativo_id
      and ao.user_id  = (select auth.uid())
  );
$$;

-- ============================================================
-- 5. RLS — habilitar e criar políticas
--    (auth.uid() embrulhado em subselect = melhor performance)
-- ============================================================

-- 5.1 owner_access: cada um só lê/atualiza a própria linha.
--     INSERT fica a cargo da service role (no cadastro feito pela marina).
alter table public.owner_access enable row level security;

drop policy if exists owner_access_select_self on public.owner_access;
create policy owner_access_select_self
  on public.owner_access for select
  to authenticated
  using (user_id = (select auth.uid()));

-- UPDATE exige SELECT (regra do Postgres) — ambas presentes.
drop policy if exists owner_access_update_self on public.owner_access;
create policy owner_access_update_self
  on public.owner_access for update
  to authenticated
  using (user_id = (select auth.uid()))
  with check (user_id = (select auth.uid()));

-- 5.2 asset_owners: o dono só enxerga os próprios vínculos.
alter table public.asset_owners enable row level security;

drop policy if exists asset_owners_select_self on public.asset_owners;
create policy asset_owners_select_self
  on public.asset_owners for select
  to authenticated
  using (user_id = (select auth.uid()));

-- 5.3 ativos: o dono só vê o(s) ativo(s) vinculado(s) a ele.
alter table public.ativos enable row level security;

drop policy if exists owner_selects_own_ativos on public.ativos;
create policy owner_selects_own_ativos
  on public.ativos for select
  to authenticated
  using (private.user_owns_ativo(id));

-- 5.4 registros: o dono só vê registros dos ativos dele.
alter table public.registros enable row level security;

drop policy if exists owner_selects_own_registros on public.registros;
create policy owner_selects_own_registros
  on public.registros for select
  to authenticated
  using (private.user_owns_ativo(ativo_id));

-- 5.5 documentos: o dono só vê documentos dos ativos dele.
alter table public.documentos enable row level security;

drop policy if exists owner_selects_own_documentos on public.documentos;
create policy owner_selects_own_documentos
  on public.documentos for select
  to authenticated
  using (private.user_owns_ativo(ativo_id));

-- ------------------------------------------------------------
-- 6. Grants para o portal do proprietário (role authenticated)
--    Com RLS ligado, o grant + a política juntos = acesso seguro
--    e restrito. (A service role do backend ignora RLS.)
-- ------------------------------------------------------------
grant usage on schema public to authenticated;
grant select on public.ativos      to authenticated;
grant select on public.registros   to authenticated;
grant select on public.documentos  to authenticated;
grant select on public.asset_owners to authenticated;
grant select, update on public.owner_access to authenticated;

-- ============================================================
-- FIM. Próximos passos ao APLICAR:
--   1) Revisar nomes/colunas contra o schema real (ativos/registros/documentos).
--   2) supabase db advisors  (corrigir alertas de segurança/performance).
--   3) Plugar no app: signInWithPassword -> signInWithOtp -> verificar palavra secreta.
--   4) Cadastro: marina cria o vínculo em asset_owners e grava owner_access (service role).
-- ============================================================
