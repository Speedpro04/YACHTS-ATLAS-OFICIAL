-- ============================================================
-- Yachts Atlas — Tabela dossie_saidas (Livro-razão de saídas de dossiê)
-- ------------------------------------------------------------
-- Registra CADA dossiê que efetivamente saiu para um terceiro:
-- pra quem foi, qual marina, qual barco (ativo), com que finalidade e quando.
-- Como o pagamento do dossiê não passa mais pela plataforma, esta tabela é a
-- visibilidade gerencial de quantos dossiês saíram e para quem.
-- Alimentada automaticamente quando o link de acesso é aberto com sucesso.
-- ============================================================
create table if not exists public.dossie_saidas (
  id                  uuid primary key default gen_random_uuid(),
  solicitacao_id      uuid references public.dossie_solicitacoes(id) on delete set null,
  ativo_id            text,                 -- qual barco
  marina_nome         text,                 -- qual marina
  destinatario_nome   text,                 -- pra quem foi
  destinatario_email  text,
  finalidade          text,                 -- venda / seguro / outro
  canal               text not null default 'acesso_link'
                      check (canal in ('acesso_link','download_dono','outro')),
  ip                  text,
  created_at          timestamptz not null default now()
);

create index if not exists dossie_saidas_ativo_idx  on public.dossie_saidas(ativo_id);
create index if not exists dossie_saidas_marina_idx on public.dossie_saidas(marina_nome);
create index if not exists dossie_saidas_solic_idx  on public.dossie_saidas(solicitacao_id);
create index if not exists dossie_saidas_data_idx   on public.dossie_saidas(created_at);

alter table public.dossie_saidas enable row level security;
-- Escrita e leitura só via service role (backend). Sem políticas públicas.
