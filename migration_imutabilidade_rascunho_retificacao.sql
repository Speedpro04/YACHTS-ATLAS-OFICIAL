-- ============================================================
-- Yachts Atlas — Imutabilidade real: rascunho -> selo -> retificacao
--
-- STATUS: JA APLICADO em producao (owzelkiyorumnlaycral) em 19/07/2026
--         via migracao `imutabilidade_rascunho_retificacao`.
--         Este arquivo existe para deixar a mudanca reproduzivel e revisavel
--         — nao rode de novo sem necessidade (e idempotente, mas confira).
--
-- MODELO DE CUSTODIA decidido pelo fundador:
--   "enquanto preenche pode apagar; salvou, ja era —
--    o erro e a correcao ficam os dois a vista."
--
--   1. RASCUNHO (registros_rascunho) — livre: edita, salva, descarta.
--   2. SELADO   (registros)          — append-only: sem UPDATE, sem DELETE,
--                                      nem com service_role. Selar = INSERT.
--
-- Por que DUAS tabelas e nao um flag `status='rascunho'`:
--   com uma tabela so, a trigger viraria condicional ("bloqueia se selado"),
--   e imutabilidade condicional cai com um bug ou um WHERE mal escrito.
--   Separando, o bloqueio continua absoluto — sem excecao a avaliar.
--
-- O QUE ISSO CORRIGIU (falha real encontrada em 19/07/2026):
--   `DELETE /ativos/{id}` chamava .delete() em ativos e o ON DELETE CASCADE
--   varria TODOS os registros e documentos do ativo. O proprio dono podia
--   apagar o ativo e recadastrar limpo — o que destruia a proposta de valor
--   do produto. Hoje: FK RESTRICT + trigger de DELETE + arquivamento.
-- ============================================================

-- ── 1. DELETE bloqueado nas tabelas seladas ─────────────────
create or replace function public.fn_registros_sem_delete()
returns trigger language plpgsql set search_path to '' as $$
begin
  raise exception
    'Registro selado nao pode ser excluido (cadeia de custodia Yachts Atlas). Para corrigir, insira um registro de retificacao apontando para %.', old.id;
end $$;

drop trigger if exists trg_registros_no_delete on public.registros;
create trigger trg_registros_no_delete
  before delete on public.registros
  for each row execute function public.fn_registros_sem_delete();

create or replace function public.fn_documentos_sem_delete()
returns trigger language plpgsql set search_path to '' as $$
begin
  raise exception
    'Documento selado nao pode ser excluido (cadeia de custodia Yachts Atlas).';
end $$;

drop trigger if exists trg_documentos_no_delete on public.documentos;
create trigger trg_documentos_no_delete
  before delete on public.documentos
  for each row execute function public.fn_documentos_sem_delete();

-- ── 2. CASCADE -> RESTRICT ──────────────────────────────────
alter table public.registros  drop constraint if exists registros_ativo_id_fkey;
alter table public.registros  add  constraint registros_ativo_id_fkey
  foreign key (ativo_id) references public.ativos(id) on delete restrict;

alter table public.documentos drop constraint if exists documentos_ativo_id_fkey;
alter table public.documentos add  constraint documentos_ativo_id_fkey
  foreign key (ativo_id) references public.ativos(id) on delete restrict;

-- ── 3. Arquivamento de ativo (substitui a exclusao) ─────────
alter table public.ativos add column if not exists arquivado_em     timestamptz;
alter table public.ativos add column if not exists arquivado_por    uuid;
alter table public.ativos add column if not exists arquivado_motivo text;

create index if not exists idx_ativos_arquivado on public.ativos(arquivado_em);

-- dono nao apaga mais o ativo; arquiva (UPDATE ja permitido pela policy existente)
drop policy if exists "Usuários deletam seus próprios ativos" on public.ativos;

-- ── 4. Rascunho: mutavel, fora da tabela selada ─────────────
create table if not exists public.registros_rascunho (
  id          uuid primary key default gen_random_uuid(),
  ativo_id    text not null references public.ativos(id) on delete cascade,
  usuario_id  uuid not null,
  categoria   text not null,
  titulo      text,
  dados       jsonb not null default '{}'::jsonb,
  checklist   jsonb not null default '[]'::jsonb,
  observacao  text,
  status      text not null default 'rascunho',
  created_by  uuid,
  created_at  timestamptz not null default timezone('utc', now()),
  updated_at  timestamptz not null default timezone('utc', now())
);

create index if not exists idx_rascunho_ativo   on public.registros_rascunho(ativo_id);
create index if not exists idx_rascunho_usuario on public.registros_rascunho(usuario_id);

create or replace function public.fn_rascunho_touch()
returns trigger language plpgsql set search_path to '' as $$
begin
  new.updated_at := timezone('utc', now());
  return new;
end $$;

drop trigger if exists trg_rascunho_touch on public.registros_rascunho;
create trigger trg_rascunho_touch
  before update on public.registros_rascunho
  for each row execute function public.fn_rascunho_touch();

alter table public.registros_rascunho enable row level security;

drop policy if exists rascunho_select_own on public.registros_rascunho;
create policy rascunho_select_own on public.registros_rascunho
  for select using (usuario_id = (select auth.uid()));

drop policy if exists rascunho_insert_own on public.registros_rascunho;
create policy rascunho_insert_own on public.registros_rascunho
  for insert with check (usuario_id = (select auth.uid()));

drop policy if exists rascunho_update_own on public.registros_rascunho;
create policy rascunho_update_own on public.registros_rascunho
  for update using (usuario_id = (select auth.uid()));

drop policy if exists rascunho_delete_own on public.registros_rascunho;
create policy rascunho_delete_own on public.registros_rascunho
  for delete using (usuario_id = (select auth.uid()));

comment on table public.registros_rascunho is
  'Rascunhos editaveis. Selar = INSERT em public.registros + DELETE aqui. Nunca e fonte do dossie.';

-- ── 5. Retificacao por par ──────────────────────────────────
-- O original NUNCA e alterado (UPDATE segue bloqueado). A situacao
-- "retificado" e DERIVADA da existencia de um registro que aponte pra ele.
alter table public.registros add column if not exists retifica_id uuid
  references public.registros(id) on delete restrict;
alter table public.registros add column if not exists motivo_retificacao text;
alter table public.registros add column if not exists hash_versao smallint not null default 1;

-- registros antigos ficam com hash_versao=1 (formula sem os campos de
-- retificacao); novos nascem v2. Verificacao deve escolher a formula pela versao.
alter table public.registros alter column hash_versao set default 2;

create index if not exists idx_registros_retifica on public.registros(retifica_id);

-- um registro so pode ser retificado uma vez (evita ambiguidade na cadeia)
create unique index if not exists uq_registros_retifica_alvo
  on public.registros(retifica_id) where retifica_id is not null;

-- retificacao exige motivo: sem justificativa, correcao e indistinguivel de maquiagem
alter table public.registros drop constraint if exists chk_retificacao_motivo;
alter table public.registros add constraint chk_retificacao_motivo check (
  retifica_id is null
  or (motivo_retificacao is not null and length(btrim(motivo_retificacao)) >= 10)
);

-- hash v2: passa a selar tambem o vinculo e o motivo da retificacao
create or replace function public.fn_registro_hash()
returns trigger language plpgsql set search_path to '' as $$
begin
  new.hash_versao := 2;
  new.hash_sha256 := encode(sha256(convert_to(
    coalesce(new.ativo_id,'')            || '|' ||
    coalesce(new.categoria,'')           || '|' ||
    coalesce(new.titulo,'')              || '|' ||
    coalesce(new.dados::text,'')         || '|' ||
    coalesce(new.checklist::text,'')     || '|' ||
    coalesce(new.observacao,'')          || '|' ||
    coalesce(new.status,'')              || '|' ||
    coalesce(new.created_at::text,'')    || '|' ||
    coalesce(new.retifica_id::text,'')   || '|' ||
    coalesce(new.motivo_retificacao,'')
  , 'UTF8')), 'hex');
  return new;
end $$;

-- visao com a situacao derivada — e o que o dossie e o painel devem ler
create or replace view public.vw_registros_situacao as
select r.*,
       (rr.id is not null)                as foi_retificado,
       rr.id                              as retificado_por_id,
       rr.motivo_retificacao              as retificado_motivo,
       rr.created_at                      as retificado_em,
       case
         when rr.id is not null         then 'retificado'
         when r.retifica_id is not null then 'retificador'
         else 'vigente'
       end                                as situacao
from public.registros r
left join public.registros rr on rr.retifica_id = r.id;

comment on view public.vw_registros_situacao is
  'Registros com situacao derivada (vigente / retificado / retificador). Fonte do dossie e do painel.';

-- ============================================================
-- AINDA PENDENTE (nao coberto por esta migracao):
--   * Encadeamento de hash (prev_hash): append-only impede editar e apagar
--     pelo app, mas nao prova que nada foi suprimido por fora.
--   * Carimbo de tempo (RFC 3161): hoje a data e campo comum, nao prova.
--   * LGPD Art. 18: diario de bordo guarda nome de condutor e CHA numa tabela
--     agora imutavel. Separar dado pessoal do registro tecnico antes que o
--     direito de eliminacao colida com a imutabilidade.
-- ============================================================
