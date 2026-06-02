-- ============================================================
-- Yachts Atlas — partner_clicks (rastreio de cliques p/ cobrança futura)
-- O Atlas é a ponte: registra cada clique de contato em um parceiro
-- (WhatsApp/e-mail/site) -> base para cobrança por lead/clique.
-- NÃO aplicado ainda.
-- ============================================================
create table if not exists public.partner_clicks (
  id           uuid primary key default gen_random_uuid(),
  partner_id   text not null,                 -- id do parceiro no diretório (futuro FK)
  categoria    text not null,
  tipo_contato text not null
               check (tipo_contato in ('whatsapp','email','site')),
  user_id      uuid,                          -- quem clicou (se autenticado)
  ativo_id     text,                          -- contexto (opcional)
  user_agent   text,
  created_at   timestamptz not null default now()
);

create index if not exists partner_clicks_partner_idx   on public.partner_clicks(partner_id);
create index if not exists partner_clicks_categoria_idx on public.partner_clicks(categoria);
create index if not exists partner_clicks_created_idx   on public.partner_clicks(created_at);

alter table public.partner_clicks enable row level security;

-- Inserção liberada (o clique vem do diretório, com ou sem login).
-- Leitura/relatórios de cobrança apenas via service role (sem policy de SELECT).
drop policy if exists partner_clicks_insert on public.partner_clicks;
create policy partner_clicks_insert
  on public.partner_clicks for insert
  to anon, authenticated
  with check (true);
