-- ============================================================
-- Yachts Atlas — Programa das 3 Vagas Fundadoras (reserva por e-mail)
-- Complemento de migration_founder_program_spots.sql (tabela)
--                e migration_founder_program_spots_funcs.sql (cobrança).
--
-- Modelo "e-mail pré-autorizado" (passe BRINDE):
--   1. O fundador liga para a marina, oferece a vaga e pré-autoriza o e-mail
--      dela com reservar_vaga_piloto() -> slot fica 'reserved' (relógio parado).
--   2. A marina entra no site oficial e faz o cadastro com a PRÓPRIA senha.
--      O backend chama ativar_vaga_piloto() -> slot vira 'occupied' e os
--      6 meses começam a contar. E-mail não reservado -> segue fluxo pago.
--
-- Idempotente.
-- ============================================================

-- Telefone da marina (preenchido na reserva ou no cadastro)
alter table public.founder_program_spots
  add column if not exists telefone text;

create or replace function public.reservar_vaga_piloto(
  p_email       text,
  p_marina_nome text default null
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_slot public.founder_program_spots;
begin
  if p_email is null or length(trim(p_email)) = 0 then
    raise exception 'E-mail da marina e obrigatorio';
  end if;

  perform pg_advisory_xact_lock(hashtext('founder_program_spots_cadastro'));

  select * into v_slot from public.founder_program_spots
   where lower(email) = lower(p_email) limit 1;
  if found then
    return jsonb_build_object(
      'status', case when v_slot.status = 'occupied' then 'ja_ocupada' else 'ja_reservada' end,
      'slot_number', v_slot.slot_number,
      'vagas_restantes', (select count(*) from public.founder_program_spots where status='available'));
  end if;

  select * into v_slot from public.founder_program_spots
   where status = 'available' order by slot_number limit 1 for update;
  if not found then
    return jsonb_build_object('status','sem_vagas','vagas_restantes',0);
  end if;

  update public.founder_program_spots
     set status='reserved', email=p_email, marina_name=p_marina_nome, updated_at=now()
   where id = v_slot.id
   returning * into v_slot;

  return jsonb_build_object(
    'status','reservada',
    'slot_number', v_slot.slot_number,
    'marina_name', v_slot.marina_name,
    'vagas_restantes', (select count(*) from public.founder_program_spots where status='available'));
end $$;

create or replace function public.ativar_vaga_piloto(
  p_email        text,
  p_marina_nome  text default null,
  p_meses_gratis int default 6
) returns jsonb
language plpgsql
set search_path = ''
as $$
declare
  v_slot public.founder_program_spots;
  v_now  timestamptz := now();
begin
  if p_email is null or length(trim(p_email)) = 0 then
    return jsonb_build_object('status','nao_autorizado');
  end if;

  perform pg_advisory_xact_lock(hashtext('founder_program_spots_cadastro'));

  select * into v_slot from public.founder_program_spots
   where lower(email) = lower(p_email) limit 1
   for update;

  if not found then
    return jsonb_build_object('status','nao_autorizado');
  end if;

  if v_slot.status = 'occupied' then
    return jsonb_build_object(
      'status','ja_ativa',
      'slot_number', v_slot.slot_number,
      'signed_up_at', v_slot.signed_up_at,
      'billing_starts_at', v_slot.billing_starts_at);
  end if;

  update public.founder_program_spots
     set status            = 'occupied',
         marina_name       = coalesce(p_marina_nome, marina_name),
         signed_up_at      = v_now,
         billing_starts_at = v_now + make_interval(months => p_meses_gratis),
         pilot_end_at      = v_now + make_interval(months => p_meses_gratis),
         billing_status    = 'pending',
         access_status     = 'active',
         updated_at        = v_now
   where id = v_slot.id
   returning * into v_slot;

  return jsonb_build_object(
    'status','ativada',
    'slot_number', v_slot.slot_number,
    'signed_up_at', v_slot.signed_up_at,
    'billing_starts_at', v_slot.billing_starts_at,
    'pilot_end_at', v_slot.pilot_end_at);
end $$;

-- Seed das 3 marinas BRINDE (reservas iniciais). Idempotente.
select public.reservar_vaga_piloto('contato@juqueriquere.com.br',          'Marina Juqueriquerê');
select public.reservar_vaga_piloto('atendimento@marinadabarra.com.br',     'Marina da Barra');
select public.reservar_vaga_piloto('secretaria@marinaportoilhabela.com.br','Marina Porto Ilhabela');
update public.founder_program_spots set telefone='(12) 3887-3033' where lower(email)='contato@juqueriquere.com.br';
update public.founder_program_spots set telefone='(12) 99777-9938' where lower(email)='atendimento@marinadabarra.com.br';
update public.founder_program_spots set telefone='(12) 3896-1243' where lower(email)='secretaria@marinaportoilhabela.com.br';
