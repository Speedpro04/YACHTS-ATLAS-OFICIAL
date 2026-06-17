-- ============================================================
-- Yachts Atlas — Programa de Lançamento (7 Marinas Fundadoras)
-- ------------------------------------------------------------
-- Oferta das 7 primeiras marinas:
--   • Assinatura: $180/mês por 12 meses → depois $300/mês.
--   • Bônus: 100% dos dossiês por 18 meses, DESTRAVADO quando a marina
--     trouxer 7 novas marinas (indicações).
--   • As marinas indicadas por elas pagam o valor normal: $250/mês.
-- Tabela com no máximo 7 vagas (slot 1..7, único).
-- ============================================================
create table if not exists public.marinas_lancamento (
  id                      uuid primary key default gen_random_uuid(),
  slot                    int  not null unique check (slot between 1 and 7),
  marina_nome             text,
  responsavel             text,
  email                   text,
  telefone                text,
  status                  text not null default 'disponivel'
                          check (status in ('disponivel','reservado','ativo','cancelado')),
  preco_mensal            numeric not null default 180,    -- $180 nos 12 primeiros meses
  meses_promocao          int     not null default 12,     -- duração do preço promocional
  preco_apos              numeric not null default 300,    -- sobe para $300 após a promoção
  preco_indicada          numeric not null default 250,    -- valor das marinas que ela indicar
  indicacoes_necessarias  int     not null default 7,      -- precisa trazer 7 para o bônus
  indicacoes_feitas       int     not null default 0,
  bonus_dossie_meses      int     not null default 18,     -- 100% dos dossiês por 18 meses
  bonus_dossie_liberado   boolean not null default false,  -- destrava ao atingir as indicações
  ativada_em              timestamptz,
  created_at              timestamptz not null default now(),
  updated_at              timestamptz not null default now()
);

create index if not exists marinas_lancamento_status_idx on public.marinas_lancamento(status);

-- Destrava o bônus de dossiê automaticamente quando as indicações chegam a 7.
create or replace function public.fn_marina_lancamento_bonus()
returns trigger language plpgsql as $$
begin
  new.bonus_dossie_liberado := (new.indicacoes_feitas >= new.indicacoes_necessarias);
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_marina_lancamento_bonus on public.marinas_lancamento;
create trigger trg_marina_lancamento_bonus
  before insert or update on public.marinas_lancamento
  for each row execute function public.fn_marina_lancamento_bonus();

-- Semeia exatamente 7 vagas (disponíveis).
insert into public.marinas_lancamento (slot)
select g from generate_series(1, 7) as g
on conflict (slot) do nothing;

alter table public.marinas_lancamento enable row level security;
-- Leitura/escrita só via service role (backend). Sem políticas públicas.
