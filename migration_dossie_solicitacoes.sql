-- ============================================================
-- Yachts Atlas — Tabela dossie_solicitacoes (Pedidos de Dossiê)
-- Substitui a compra via Stripe: o interessado (broker/comprador/
-- seguradora) solicita o dossiê por um formulário aberto; o dossiê é
-- liberado MANUALMENTE pela Yachts Atlas e acessado por senha-mestra.
-- O pagamento do dossiê acontece direto marina <-> dono (fora da
-- plataforma). Mesmo padrão de partner_leads. NÃO aplicado ainda.
-- ============================================================
create table if not exists public.dossie_solicitacoes (
  id                    uuid primary key default gen_random_uuid(),
  ativo_id              text,
  marina_nome           text,
  solicitante_nome      text not null,
  solicitante_email     text not null,
  solicitante_telefone  text,
  finalidade            text not null default 'outro'
                        check (finalidade in ('venda','seguro','outro')),
  mensagem              text,
  status                text not null default 'pendente'
                        check (status in ('pendente','liberado','recusado')),
  liberado_em           timestamptz,
  liberado_por          text,
  acessos               int not null default 0,
  ultimo_acesso         timestamptz,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index if not exists dossie_solicitacoes_status_idx on public.dossie_solicitacoes(status);
create index if not exists dossie_solicitacoes_ativo_idx  on public.dossie_solicitacoes(ativo_id);
create index if not exists dossie_solicitacoes_email_idx  on public.dossie_solicitacoes(solicitante_email);

alter table public.dossie_solicitacoes enable row level security;

-- Inserção pública (formulário aberto). Leitura/liberação só via service role (backend).
drop policy if exists dossie_solicitacoes_insert_public on public.dossie_solicitacoes;
create policy dossie_solicitacoes_insert_public
  on public.dossie_solicitacoes for insert
  to anon, authenticated
  with check (true);
