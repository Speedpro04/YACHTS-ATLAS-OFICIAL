-- ============================================================
-- Yachts Atlas — Normas Náuticas (catálogo de referência)
-- ------------------------------------------------------------
-- Base da aba "Normas" (consulta), do dossiê amarrado às normas e
-- do futuro chatbot (RAG). Dado de REFERÊNCIA: leitura pública,
-- escrita só pelo backend (service role).
--
-- v1 = principais normas BRASILEIRAS, todas verificadas em fonte
-- oficial (Marinha/DPC e ABNT) em jun/2026. Cada registro guarda o
-- status de verificação — nada "a_verificar" deve aparecer pro cliente
-- como se fosse confirmado.
--
-- Estrutura desenhada para crescer: orgao/jurisdicao já suportam
-- ISO/ABYC/CE/INTL para as próximas fases (LATAM, EUA/Europa).
-- A coluna de embedding (pgvector) será adicionada na fase do chatbot.
-- ============================================================
create table if not exists public.normas (
  id                  uuid primary key default gen_random_uuid(),
  codigo              text not null unique,          -- "NORMAM-211", "NBR 14574"
  titulo              text not null,
  descricao           text,
  orgao               text not null
                      check (orgao in ('NORMAM','ABNT','ISO','ABYC','CE','INTL')),
  serie               text,                          -- p/ NORMAM: "200 - Embarcações"
  jurisdicao          text not null default 'BR'
                      check (jurisdicao in ('BR','INTL','EU','USA','LATAM')),
  escopo              text[] not null default '{}',  -- {recreio, mar_aberto, interior, ...}
  vigencia_inicio     date,
  vigencia_fim        date,                          -- null = vigente
  versao              text,                          -- "Mod.2/2024", "2012"
  fonte_url           text,                          -- link oficial p/ auditoria/citação
  obrigatoria         boolean not null default false,
  status_verificacao  text not null default 'a_verificar'
                      check (status_verificacao in ('verificada','a_verificar')),
  ativo               boolean not null default true,
  ordem               int not null default 100,      -- ordem de exibição
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create index if not exists normas_orgao_idx       on public.normas(orgao);
create index if not exists normas_jurisdicao_idx  on public.normas(jurisdicao);
create index if not exists normas_ativo_idx       on public.normas(ativo);

-- updated_at automático.
create or replace function public.fn_normas_touch()
returns trigger language plpgsql as $$
begin
  new.updated_at := now();
  return new;
end;
$$;

drop trigger if exists trg_normas_touch on public.normas;
create trigger trg_normas_touch
  before update on public.normas
  for each row execute function public.fn_normas_touch();

-- ------------------------------------------------------------
-- SEED — normas brasileiras verificadas (jun/2026)
-- ------------------------------------------------------------
insert into public.normas
  (codigo, titulo, descricao, orgao, serie, jurisdicao, escopo,
   vigencia_inicio, versao, fonte_url, obrigatoria, status_verificacao, ordem)
values
  ('NORMAM-211',
   'Embarcações de esporte e recreio',
   'Normas da Autoridade Marítima para embarcações de esporte e recreio '
   || '(ex-NORMAM-03, renumerada na reorganização da DPC em out/2023). '
   || 'Regularização, inscrição, vistoria, material de salvatagem e segurança.',
   'NORMAM', '200 - Embarcações', 'BR', '{recreio,esporte}',
   '2023-10-02', 'Reorg. out/2023',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 10),

  ('NORMAM-201',
   'Embarcações empregadas na navegação em mar aberto',
   'Normas da Autoridade Marítima para embarcações em navegação de mar aberto. '
   || 'Inscrição, segurança da navegação, material de salvatagem e comunicações.',
   'NORMAM', '200 - Embarcações', 'BR', '{mar_aberto}',
   '2024-07-01', 'Mod.2/2024',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 20),

  ('NORMAM-202',
   'Embarcações empregadas na navegação interior',
   'Normas da Autoridade Marítima para embarcações em navegação interior '
   || '(rios, lagos, baías). Inscrição, segurança e material de salvatagem.',
   'NORMAM', '200 - Embarcações', 'BR', '{interior}',
   '2024-07-01', 'Mod.1/2024',
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   true, 'verificada', 30),

  ('NBR 14574',
   'Embarcações de recreio em PRFV — requisitos para construção',
   'ABNT NBR 14574:2012 — requisitos de construção para embarcações de recreio '
   || 'em plástico reforçado com fibra de vidro (PRFV) de comprimento <= 24 m. '
   || 'Base do programa de certificação ABNT-ACOBAR.',
   'ABNT', null, 'BR', '{recreio,construcao}',
   '2012-01-01', '2012',
   'https://www.abnt.org.br/',
   false, 'verificada', 40),

  -- Escopo exato a confirmar (série 400 - Meio Ambiente); entra inativa e
  -- marcada como não verificada para NÃO aparecer ao cliente como confirmada.
  ('NORMAM-401',
   'Meio ambiente — prevenção da poluição',
   'Normas da Autoridade Marítima da série 400 (Meio Ambiente). '
   || 'Escopo exato a confirmar em fonte oficial antes de publicar.',
   'NORMAM', '400 - Meio Ambiente', 'BR', '{meio_ambiente}',
   null, null,
   'https://www.marinha.mil.br/dpc/normas-da-autoridade-maritima',
   false, 'a_verificar', 50)
on conflict (codigo) do nothing;

-- ------------------------------------------------------------
-- RLS — leitura pública (referência); escrita só via service role.
-- ------------------------------------------------------------
alter table public.normas enable row level security;

drop policy if exists "normas_leitura_publica" on public.normas;
create policy "normas_leitura_publica"
  on public.normas
  for select
  using (ativo = true and status_verificacao = 'verificada');

-- Sem políticas de insert/update/delete: só o backend (service role,
-- que ignora RLS) administra o catálogo.
