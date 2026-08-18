-- ============================================================
-- Yachts Atlas — payments: rastreio da RENOVAÇÃO mensal
-- ------------------------------------------------------------
-- A recorrência é o produto, mas payments só guardava o primeiro
-- mês (o checkout). As renovações chegam pelo evento invoice.paid,
-- que não tem checkout session nem payment intent próprios —
-- precisam de chave própria para não duplicar em cada reentrega
-- do webhook.
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

alter table public.payments
  add column if not exists stripe_invoice_id text;

-- Chave de idempotência da renovação: o Stripe reentrega invoice.paid
-- em caso de falha de resposta, e sem isto cada retry viraria uma
-- linha nova de dinheiro que não existe.
create unique index if not exists payments_stripe_invoice_id_key
  on public.payments (stripe_invoice_id)
  where stripe_invoice_id is not null;

-- A renovação é buscada pela assinatura de origem (para herdar o
-- usuário do checkout inicial). Sem índice isso vira seq scan a cada
-- fatura paga.
create index if not exists idx_payments_stripe_subscription_created
  on public.payments (stripe_subscription_id, created_at);

comment on column public.payments.stripe_invoice_id is
  'Invoice do Stripe. Preenchido nas renovações mensais (invoice.paid); '
  'nulo no checkout inicial, que é identificado pelo checkout session id.';
