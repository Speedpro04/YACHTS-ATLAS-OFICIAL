-- ============================================================
-- Yachts Atlas — Tabela DEDICADA da oferta especial
-- ------------------------------------------------------------
-- 20 marinas fundadoras a US$ 200/mês (preço travado 12 meses),
-- dossiê 100% por 18 meses, permanência mínima 6 meses.
-- Começa VAZIA (0 linhas = 20 vagas livres). Cap rígido de 20.
-- Cadastro keyado por E-MAIL. Esgotou as 20 -> modo tradicional (US$ 250).
-- Substitui o uso de marinas_lancamento para esta oferta.
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

create table if not exists public.marinas_fundadoras (
  id                       uuid primary key default gen_random_uuid(),
  marina_nome              text,
  responsavel              text,
  email                    text not null,
  telefone                 text,
  uf                       text check (uf in ('SC','SP','RJ','ES','BA')),
  preco_mensal             numeric not null default 200,   -- US$ 200/mês fundadora
  meses_promocao           int     not null default 12,    -- preço travado 12 meses
  dossie_meses             int     not null default 18,    -- dossiê 100% por 18 meses
  permanencia_minima_meses int     not null default 6,     -- regra dos 6 meses
  stripe_checkout          text,
  status                   text    not null default 'ativo'
                           check (status in ('ativo','cancelado')),
  created_at               timestamptz not null default now(),
  updated_at               timestamptz not null default now()
);

-- E-mail é a chave (case-insensitive, sem duplicar marina)
create unique index if not exists marinas_fundadoras_email_uniq
  on public.marinas_fundadoras (lower(email));

-- Guardrail: cap rígido de 20 marinas ativas
create or replace function public.fn_marinas_fundadoras_limite()
returns trigger language plpgsql as $$
begin
  if (select count(*) from public.marinas_fundadoras where status = 'ativo') >= 20 then
    raise exception 'Limite de 20 marinas fundadoras atingido';
  end if;
  return new;
end $$;

drop trigger if exists trg_marinas_fundadoras_limite on public.marinas_fundadoras;
create trigger trg_marinas_fundadoras_limite
  before insert on public.marinas_fundadoras
  for each row execute function public.fn_marinas_fundadoras_limite();

-- RLS: só backend (service role). Sem políticas públicas.
alter table public.marinas_fundadoras enable row level security;

-- ------------------------------------------------------------
-- Cadastro por e-mail. Retorna jsonb:
--   • {modo:'fundadora', status, preco_mensal:200, vagas_restantes}
--   • {modo:'tradicional', preco_mensal:250, motivo} quando as 20 esgotam
-- NÃO lança erro no limite — apenas sinaliza modo tradicional.
-- Chamada pelo webhook do Stripe quando metadata.programa == 'marina_fundadora'.
-- ------------------------------------------------------------
create or replace function public.cadastrar_marina_fundadora(
  p_email           text,
  p_marina_nome     text default null,
  p_responsavel     text default null,
  p_telefone        text default null,
  p_uf              text default null,
  p_stripe_checkout text default null
) returns jsonb
language plpgsql
as $$
declare
  v_count int;
  v_row   public.marinas_fundadoras;
begin
  if p_email is null or length(trim(p_email)) = 0 then
    raise exception 'E-mail da marina e obrigatorio';
  end if;

  -- Serializa o cadastro para o cap de 20 ser seguro sob concorrencia
  perform pg_advisory_xact_lock(hashtext('marinas_fundadoras_cadastro'));

  -- Ja cadastrada por e-mail? idempotente
  select * into v_row from public.marinas_fundadoras
   where lower(email) = lower(p_email) limit 1;
  if found then
    return jsonb_build_object(
      'modo','fundadora','status','ja_cadastrada',
      'preco_mensal', v_row.preco_mensal,
      'vagas_restantes', greatest(0, 20 - (select count(*) from public.marinas_fundadoras where status='ativo')));
  end if;

  -- Limite de 20 -> MODO TRADICIONAL (sem erro, preco padrao 250)
  select count(*) into v_count from public.marinas_fundadoras where status = 'ativo';
  if v_count >= 20 then
    return jsonb_build_object(
      'modo','tradicional','preco_mensal',250,'motivo','vagas_fundadoras_esgotadas');
  end if;

  -- Cadastra a marina fundadora (US$ 200)
  insert into public.marinas_fundadoras
    (marina_nome, responsavel, email, telefone, uf, stripe_checkout)
  values
    (p_marina_nome, p_responsavel, p_email, p_telefone, p_uf, p_stripe_checkout)
  returning * into v_row;

  return jsonb_build_object(
    'modo','fundadora','status','cadastrada',
    'preco_mensal', v_row.preco_mensal,
    'vagas_restantes', 20 - (select count(*) from public.marinas_fundadoras where status='ativo'));
end $$;
