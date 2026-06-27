-- ============================================================
-- Yachts Atlas — Programa das 3 Vagas Fundadoras
-- Controle comercial das vagas piloto via Supabase.
-- Seed inicial com 3 slots disponíveis.
-- ============================================================

create table if not exists public.founder_program_spots (
  id              uuid primary key default gen_random_uuid(),
  slot_number     smallint not null unique check (slot_number between 1 and 3),
  status          text not null default 'available'
                  check (status in ('available','reserved','occupied')),
  marina_name     text,
  contact_name    text,
  email           text,
  fleet_size      text,
  source          text,
  signed_up_at    timestamptz,
  billing_starts_at timestamptz,
  billing_status  text not null default 'pending'
                  check (billing_status in ('pending','active','past_due','blocked')),
  access_status   text not null default 'active'
                  check (access_status in ('active','blocked')),
  pilot_program   boolean not null default true,
  pilot_end_at    timestamptz,
  pilot_case_notes text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists founder_program_spots_status_idx
  on public.founder_program_spots(status);

create index if not exists founder_program_spots_billing_idx
  on public.founder_program_spots(billing_status);

alter table public.founder_program_spots enable row level security;

drop policy if exists founder_program_spots_service_only on public.founder_program_spots;
create policy founder_program_spots_service_only
  on public.founder_program_spots
  for all
  to authenticated
  using (false)
  with check (false);

drop policy if exists founder_program_spots_no_public_access on public.founder_program_spots;
create policy founder_program_spots_no_public_access
  on public.founder_program_spots
  for all
  to anon
  using (false)
  with check (false);

insert into public.founder_program_spots (slot_number, status)
values
  (1, 'available'),
  (2, 'available'),
  (3, 'available')
on conflict (slot_number) do nothing;

