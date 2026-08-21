-- ============================================================
-- Yachts Atlas — o que perguntam à Capitã Solara
-- ------------------------------------------------------------
-- NÃO é métrica de atendimento. É pesquisa de produto.
--
-- Com 20 marinas, as perguntas de suporte são o sinal mais honesto de onde a
-- interface está confusa. Pergunta que chega vinte vezes não é caso de
-- suporte: é tela que precisa mudar. Foi assim que a categoria "Fotos da
-- Embarcação" apareceu — alguém olhou a tela e sentiu que faltava.
--
-- Automatizar o atendimento sem guardar isso deixaria o fundador surdo justo
-- quando ele mais precisa ouvir: a Solara responderia com paciência infinita
-- "está em Integridade do Casco mesmo", e a categoria confusa viraria
-- permanente, porque ninguém mais reclama quando o atendimento é bom.
--
-- O sinal mais valioso é `respondida = false`: ou é buraco na documentação,
-- ou é coisa que o produto não faz e a marina esperava que fizesse.
--
-- Guarda a PERGUNTA, nunca a resposta nem quem perguntou — o que interessa é
-- o padrão, não o indivíduo.
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

create table if not exists public.solara_perguntas (
  id           uuid primary key default gen_random_uuid(),
  criado_em    timestamptz not null default now(),
  pergunta     text        not null,
  dominio      text        not null check (dominio in ('norma','produto')),
  respondida   boolean     not null,
  motivo       text,
  session_id   text
);

comment on table public.solara_perguntas is
  'O que perguntam a Capita Solara. Mapa do que esta confuso no produto, '
  'ordenado por frequencia. respondida=false e o sinal mais valioso.';

create index if not exists idx_solara_perguntas_data
  on public.solara_perguntas (criado_em desc);

-- O caminho quente da análise: "o que ela NÃO soube responder".
create index if not exists idx_solara_perguntas_sem_resposta
  on public.solara_perguntas (dominio, criado_em desc)
  where respondida = false;

alter table public.solara_perguntas enable row level security;

-- Sem policy de leitura, de propósito: só a service_role (backend) escreve e
-- lê. Pergunta de uma marina não pode ser lida por outra.
