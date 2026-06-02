-- ============================================================
-- Yachts Atlas — Tabela partner_leads (diretório Parceiros Atlas)
-- Solicitações de parceria via /seja-parceiro -> POST /leads/parceiro.
-- Mesmo padrão de marina_leads. NÃO aplicado ainda.
-- ============================================================
create table if not exists public.partner_leads (
  id          uuid primary key default gen_random_uuid(),
  categoria   text not null,
  empresa     text not null,
  responsavel text not null,
  email       text not null,
  telefone    text,
  cidade      text,
  mensagem    text,
  status      text not null default 'pending'
              check (status in ('pending','contacted','approved','rejected')),
  created_at  timestamptz not null default now(),
  updated_at  timestamptz not null default now()
);

create index if not exists partner_leads_status_idx on public.partner_leads(status);
create index if not exists partner_leads_categoria_idx on public.partner_leads(categoria);

alter table public.partner_leads enable row level security;

-- Inserção pública (formulário aberto). Leitura/edição só via service role.
drop policy if exists partner_leads_insert_public on public.partner_leads;
create policy partner_leads_insert_public
  on public.partner_leads for insert
  to anon, authenticated
  with check (true);
