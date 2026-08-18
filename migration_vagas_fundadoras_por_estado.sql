-- ============================================================
-- Yachts Atlas — vagas fundadoras: 4 POR ESTADO + reserva
-- ------------------------------------------------------------
-- O programa é 4 marinas fundadoras em cada um dos 5 estados
-- (SC/SP/RJ/ES/BA) = 20 no total. O teto de 20 passa a ser
-- CONSEQUÊNCIA das 4 por estado, não uma regra própria — antes
-- era o contrário, e 20 marinas de um mesmo estado zeravam as
-- vagas dos outros quatro.
--
-- A vaga também passa a ser RESERVADA no cadastro, não só no
-- pagamento. Entre preencher o formulário e pagar existia uma
-- janela em que todo mundo via "tem vaga" e recebia o link de
-- US$ 200 — mais gente podia pagar preço de fundadora do que
-- existe vaga para honrar.
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

-- ------------------------------------------------------------
-- 1) Estrutura: status 'reservado' e validade da reserva
-- ------------------------------------------------------------
alter table public.marinas_fundadoras
  add column if not exists reservado_ate timestamptz;

alter table public.marinas_fundadoras
  drop constraint if exists marinas_fundadoras_status_check;

alter table public.marinas_fundadoras
  add constraint marinas_fundadoras_status_check
  check (status in ('reservado', 'ativo', 'cancelado'));

comment on column public.marinas_fundadoras.reservado_ate is
  'Até quando a reserva segura a vaga. Vencida e não paga, a vaga volta '
  'para o estado automaticamente (nada é apagado).';

-- Contagem por estado é a consulta mais quente do fluxo de venda.
create index if not exists idx_marinas_fundadoras_uf_status
  on public.marinas_fundadoras (uf, status);

-- ------------------------------------------------------------
-- 2) Quantas vagas de um estado estão ocupadas
--    Ocupada = paga (ativo) OU reservada e ainda dentro do prazo.
-- ------------------------------------------------------------
create or replace function public.fn_vagas_fundadoras_ocupadas(p_uf text)
returns int
language sql
stable
set search_path to ''
as $$
  select count(*)::int
    from public.marinas_fundadoras
   where upper(uf) = upper(p_uf)
     and (status = 'ativo'
          or (status = 'reservado' and reservado_ate > now()));
$$;

-- ------------------------------------------------------------
-- 3) Guardrail: no máximo 4 por estado (vale para reserva e ativo)
-- ------------------------------------------------------------
create or replace function public.fn_marinas_fundadoras_limite()
returns trigger
language plpgsql
set search_path to ''
as $$
declare
  v_ocupadas int;
begin
  if new.uf is null then
    raise exception 'UF e obrigatoria para ocupar vaga fundadora';
  end if;

  v_ocupadas := public.fn_vagas_fundadoras_ocupadas(new.uf);

  if v_ocupadas >= 4 then
    raise exception 'Limite de 4 marinas fundadoras em % atingido', new.uf;
  end if;

  return new;
end $$;

-- ------------------------------------------------------------
-- 4) Reservar a vaga no CADASTRO (antes do pagamento)
--    Retorna jsonb:
--      {modo:'fundadora',  status, preco_mensal:200, uf, vagas_restantes}
--      {modo:'tradicional', preco_mensal:250, motivo}
--    Nunca lança erro por falta de vaga — apenas sinaliza tradicional.
-- ------------------------------------------------------------
create or replace function public.reservar_vaga_fundadora(
  p_email       text,
  p_uf          text,
  p_marina_nome text default null,
  p_responsavel text default null,
  p_telefone    text default null,
  p_minutos     int  default 60
) returns jsonb
language plpgsql
set search_path to ''
as $$
declare
  v_uf       text;
  v_ocupadas int;
  v_row      public.marinas_fundadoras;
begin
  if p_email is null or length(trim(p_email)) = 0 then
    raise exception 'E-mail da marina e obrigatorio';
  end if;

  v_uf := upper(trim(coalesce(p_uf, '')));

  -- Estado fora do programa segue para a oferta oficial de US$ 250.
  if v_uf not in ('SC', 'SP', 'RJ', 'ES', 'BA') then
    return jsonb_build_object(
      'modo', 'tradicional',
      'preco_mensal', 250,
      'motivo', 'uf_fora_do_programa');
  end if;

  -- Serializa por estado: o cap de 4 precisa valer sob concorrencia.
  perform pg_advisory_xact_lock(hashtext('marinas_fundadoras_' || v_uf));

  select * into v_row
    from public.marinas_fundadoras
   where lower(email) = lower(p_email)
   limit 1;

  -- Ja conhecida: renova a reserva em vez de criar outra linha.
  if found then
    if v_row.status = 'ativo' then
      return jsonb_build_object(
        'modo', 'fundadora', 'status', 'ja_ativa',
        'preco_mensal', v_row.preco_mensal, 'uf', v_row.uf,
        'vagas_restantes', greatest(0, 4 - public.fn_vagas_fundadoras_ocupadas(v_row.uf)));
    end if;

    update public.marinas_fundadoras
       set status        = 'reservado',
           reservado_ate = now() + make_interval(mins => p_minutos),
           marina_nome   = coalesce(p_marina_nome, marina_nome),
           responsavel   = coalesce(p_responsavel, responsavel),
           telefone      = coalesce(p_telefone, telefone),
           uf            = v_uf,
           updated_at    = now()
     where id = v_row.id
    returning * into v_row;

    return jsonb_build_object(
      'modo', 'fundadora', 'status', 'reserva_renovada',
      'preco_mensal', v_row.preco_mensal, 'uf', v_row.uf,
      'vagas_restantes', greatest(0, 4 - public.fn_vagas_fundadoras_ocupadas(v_uf)));
  end if;

  v_ocupadas := public.fn_vagas_fundadoras_ocupadas(v_uf);

  if v_ocupadas >= 4 then
    return jsonb_build_object(
      'modo', 'tradicional',
      'preco_mensal', 250,
      'motivo', 'vagas_do_estado_esgotadas',
      'uf', v_uf,
      'vagas_restantes', 0);
  end if;

  insert into public.marinas_fundadoras
    (marina_nome, responsavel, email, telefone, uf, status, reservado_ate)
  values
    (p_marina_nome, p_responsavel, p_email, p_telefone, v_uf,
     'reservado', now() + make_interval(mins => p_minutos))
  returning * into v_row;

  return jsonb_build_object(
    'modo', 'fundadora', 'status', 'reservada',
    'preco_mensal', v_row.preco_mensal, 'uf', v_row.uf,
    'vagas_restantes', greatest(0, 4 - public.fn_vagas_fundadoras_ocupadas(v_uf)));
end $$;

-- ------------------------------------------------------------
-- 5) Confirmar a vaga no PAGAMENTO (promove a reserva)
--    Chamada pelo webhook do Stripe. Mantém a assinatura antiga
--    para não quebrar quem já chama.
--
--    Quem pagou tem a vaga honrada mesmo com a reserva vencida:
--    recusar depois de cobrar geraria estorno. O caso só aparece
--    se ela demorar mais que o prazo entre reservar e pagar.
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
set search_path to ''
as $$
declare
  v_uf       text;
  v_ocupadas int;
  v_row      public.marinas_fundadoras;
begin
  if p_email is null or length(trim(p_email)) = 0 then
    raise exception 'E-mail da marina e obrigatorio';
  end if;

  v_uf := upper(trim(coalesce(p_uf, '')));

  perform pg_advisory_xact_lock(
    hashtext('marinas_fundadoras_' || coalesce(nullif(v_uf, ''), 'sem_uf')));

  select * into v_row
    from public.marinas_fundadoras
   where lower(email) = lower(p_email)
   limit 1;

  if found then
    if v_row.status = 'ativo' then
      return jsonb_build_object(
        'modo', 'fundadora', 'status', 'ja_cadastrada',
        'preco_mensal', v_row.preco_mensal, 'uf', v_row.uf,
        'vagas_restantes', greatest(0, 4 - public.fn_vagas_fundadoras_ocupadas(v_row.uf)));
    end if;

    -- Promove a reserva (mesmo vencida — ela pagou).
    update public.marinas_fundadoras
       set status          = 'ativo',
           reservado_ate   = null,
           stripe_checkout = coalesce(p_stripe_checkout, stripe_checkout),
           marina_nome     = coalesce(marina_nome, p_marina_nome),
           responsavel     = coalesce(responsavel, p_responsavel),
           telefone        = coalesce(telefone, p_telefone),
           updated_at      = now()
     where id = v_row.id
    returning * into v_row;

    return jsonb_build_object(
      'modo', 'fundadora', 'status', 'cadastrada',
      'preco_mensal', v_row.preco_mensal, 'uf', v_row.uf,
      'vagas_restantes', greatest(0, 4 - public.fn_vagas_fundadoras_ocupadas(v_row.uf)));
  end if;

  -- Sem reserva: pagou por um caminho que não passou pelo cadastro.
  if v_uf not in ('SC', 'SP', 'RJ', 'ES', 'BA') then
    return jsonb_build_object(
      'modo', 'tradicional', 'preco_mensal', 250,
      'motivo', 'sem_reserva_e_uf_desconhecida');
  end if;

  v_ocupadas := public.fn_vagas_fundadoras_ocupadas(v_uf);

  if v_ocupadas >= 4 then
    return jsonb_build_object(
      'modo', 'tradicional', 'preco_mensal', 250,
      'motivo', 'vagas_do_estado_esgotadas', 'uf', v_uf);
  end if;

  insert into public.marinas_fundadoras
    (marina_nome, responsavel, email, telefone, uf, status, stripe_checkout)
  values
    (p_marina_nome, p_responsavel, p_email, p_telefone, v_uf, 'ativo', p_stripe_checkout)
  returning * into v_row;

  return jsonb_build_object(
    'modo', 'fundadora', 'status', 'cadastrada',
    'preco_mensal', v_row.preco_mensal, 'uf', v_row.uf,
    'vagas_restantes', greatest(0, 4 - public.fn_vagas_fundadoras_ocupadas(v_uf)));
end $$;
