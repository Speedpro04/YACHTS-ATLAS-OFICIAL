-- ============================================================
-- Yachts Atlas — Programa das 3 Vagas Fundadoras (funções)
-- Complemento de migration_founder_program_spots.sql (tabela + seed).
--
--  • cadastrar_marina_piloto: ocupa um slot e INICIA a contagem de 6 meses
--    a partir do cadastro da marina (signed_up_at = now;
--    billing_starts_at = now + 6 meses). Cap rígido de 3. Idempotente por e-mail.
--  • processar_vencimentos_piloto: scheduler diário — ao vencer o período
--    gratuito, inicia a cobrança (past_due) e trava o acesso (blocked).
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

-- Índice único por e-mail (não duplica marina entre slots)
create unique index if not exists founder_program_spots_email_uniq
  on public.founder_program_spots(lower(email)) where email is not null;

create or replace function public.cadastrar_marina_piloto(
  p_email        text,
  p_marina_nome  text default null,
  p_contact_name text default null,
  p_fleet_size   text default null,
  p_source       text default null,
  p_meses_gratis int  default 6
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_slot public.founder_program_spots;
  v_now  timestamptz := now();
begin
  if p_email is null or length(trim(p_email)) = 0 then
    raise exception 'E-mail da marina e obrigatorio';
  end if;

  -- Serializa o cadastro para o cap de 3 ser seguro sob concorrencia
  perform pg_advisory_xact_lock(hashtext('founder_program_spots_cadastro'));

  -- Idempotente: ja cadastrada por e-mail -> devolve o slot existente
  select * into v_slot from public.founder_program_spots
   where lower(email) = lower(p_email) limit 1;
  if found then
    return jsonb_build_object(
      'status','ja_cadastrada',
      'slot_number', v_slot.slot_number,
      'signed_up_at', v_slot.signed_up_at,
      'billing_starts_at', v_slot.billing_starts_at,
      'vagas_restantes', (select count(*) from public.founder_program_spots where status='available'));
  end if;

  -- Pega o menor slot disponivel
  select * into v_slot from public.founder_program_spots
   where status = 'available'
   order by slot_number
   limit 1
   for update;

  if not found then
    return jsonb_build_object('status','sem_vagas','vagas_restantes',0);
  end if;

  update public.founder_program_spots
     set status            = 'occupied',
         marina_name       = p_marina_nome,
         contact_name      = p_contact_name,
         email             = p_email,
         fleet_size        = p_fleet_size,
         source            = p_source,
         signed_up_at      = v_now,
         billing_starts_at = v_now + make_interval(months => p_meses_gratis),
         pilot_end_at      = v_now + make_interval(months => p_meses_gratis),
         billing_status    = 'pending',
         access_status     = 'active',
         updated_at        = v_now
   where id = v_slot.id
   returning * into v_slot;

  return jsonb_build_object(
    'status','cadastrada',
    'slot_number', v_slot.slot_number,
    'signed_up_at', v_slot.signed_up_at,
    'billing_starts_at', v_slot.billing_starts_at,
    'pilot_end_at', v_slot.pilot_end_at,
    'vagas_restantes', (select count(*) from public.founder_program_spots where status='available'));
end $$;

create or replace function public.processar_vencimentos_piloto()
returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_vencidas jsonb;
begin
  with vencidas as (
    update public.founder_program_spots
       set billing_status = 'past_due',
           access_status  = 'blocked',
           updated_at     = now()
     where status = 'occupied'
       and billing_status = 'pending'
       and billing_starts_at is not null
       and now() >= billing_starts_at
    returning slot_number, marina_name, email, billing_starts_at
  )
  select coalesce(jsonb_agg(to_jsonb(v)), '[]'::jsonb) into v_vencidas from vencidas v;

  return jsonb_build_object(
    'processed_at', now(),
    'vencidas', v_vencidas,
    'total_vencidas', jsonb_array_length(v_vencidas));
end $$;
