-- ============================================================
-- Yachts Atlas — Programa Marinas Fundadoras (OFERTA ESPECIAL)
-- ------------------------------------------------------------
-- Evolui public.marinas_lancamento do modelo original (7 vagas)
-- para o modelo atual:
--   • 20 vagas  (4 por estado x 5 praças: SC, SP, RJ, ES, BA)
--   • Fundadora: US$ 200/mês por 12 meses; dossiê 100% por 18 meses
--   • Indicada:  US$ 250/mês;             dossiê 100% por 12 meses
--   • Permanência mínima: 6 meses
--   • Cadastro keyado pelo E-MAIL da marina (idempotente)
-- Complementa migration_marinas_lancamento.sql (não o substitui).
-- Idempotente: pode rodar mais de uma vez sem efeitos colaterais.
-- ============================================================

-- 1) Slots: 7 -> 20
alter table public.marinas_lancamento
  drop constraint if exists marinas_lancamento_slot_check;
alter table public.marinas_lancamento
  add constraint marinas_lancamento_slot_check check (slot between 1 and 20);

-- 2) Preço fundador padrão: 180 -> 200
alter table public.marinas_lancamento alter column preco_mensal set default 200;
update public.marinas_lancamento
   set preco_mensal = 200, updated_at = now()
 where preco_mensal = 180;

-- 3) Campos da oferta especial (modelo em camadas)
alter table public.marinas_lancamento
  add column if not exists tipo text not null default 'fundadora'
    check (tipo in ('fundadora','indicada')),
  add column if not exists uf text check (uf in ('SC','SP','RJ','ES','BA')),
  add column if not exists permanencia_minima_meses int not null default 6,
  add column if not exists dossie_meses_indicada int not null default 12,
  add column if not exists indicada_por_slot int,
  add column if not exists stripe_checkout text;

-- 4) E-mail como chave de cadastro (case-insensitive, sem duplicar marina)
create unique index if not exists marinas_lancamento_email_uniq
  on public.marinas_lancamento (lower(email)) where email is not null;

-- 5) Semeia as 20 vagas (mantém as já existentes)
insert into public.marinas_lancamento
  (slot, status, preco_mensal, meses_promocao, preco_apos, preco_indicada,
   indicacoes_necessarias, bonus_dossie_meses)
select g, 'disponivel', 200, 12, 300, 250, 7, 18
from generate_series(1, 20) as g
on conflict (slot) do nothing;

-- 6) Função de cadastro por e-mail: ocupa a próxima vaga fundadora disponível.
--    Idempotente por e-mail; segura para concorrência (FOR UPDATE SKIP LOCKED).
--    Chamada pelo webhook do Stripe (checkout.session.completed) quando
--    metadata.programa == 'marina_fundadora'.
create or replace function public.cadastrar_marina_fundadora(
  p_email           text,
  p_marina_nome     text default null,
  p_responsavel     text default null,
  p_telefone        text default null,
  p_uf              text default null,
  p_stripe_checkout text default null
) returns public.marinas_lancamento
language plpgsql
as $$
declare
  v_slot int;
  v_row  public.marinas_lancamento;
begin
  if p_email is null or length(trim(p_email)) = 0 then
    raise exception 'E-mail da marina e obrigatorio';
  end if;

  -- Ja cadastrada por e-mail? devolve o slot dela (idempotente)
  select * into v_row from public.marinas_lancamento
   where lower(email) = lower(p_email) limit 1;
  if found then
    return v_row;
  end if;

  -- Ocupa o menor slot fundador disponivel
  select slot into v_slot from public.marinas_lancamento
   where status = 'disponivel' and tipo = 'fundadora'
   order by slot limit 1
   for update skip locked;

  if v_slot is null then
    raise exception 'Sem vagas fundadoras disponiveis';
  end if;

  update public.marinas_lancamento
     set email           = p_email,
         marina_nome     = p_marina_nome,
         responsavel     = p_responsavel,
         telefone        = p_telefone,
         uf              = coalesce(p_uf, uf),
         stripe_checkout = p_stripe_checkout,
         status          = 'ativo',
         ativada_em      = now(),
         updated_at      = now()
   where slot = v_slot
  returning * into v_row;

  return v_row;
end;
$$;
