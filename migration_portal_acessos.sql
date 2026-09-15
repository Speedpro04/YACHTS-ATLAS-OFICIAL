-- Visitas do proprietário ao Portal, medidas por nós. Aplicada em 15/09/2026.
--
-- Antes a resposta "o dono já entrou?" vinha do auth.users.last_sign_in_at, e
-- isso tinha dois problemas: (1) o campo guarda a última VALIDAÇÃO DE CÓDIGO,
-- não a última visita — a sessão do navegador se renova sozinha e a data
-- congelava; (2) para lê-lo era preciso varrer o Auth por e-mail, o que
-- permitia a uma Marina gravar o e-mail de qualquer pessoa no próprio barco
-- e descobrir se ela tem conta na plataforma.
--
-- Uma linha por (embarcação, dono): primeira visita, última e quantas.
create table if not exists portal_acessos (
  ativo_id text not null references ativos(id) on delete cascade,
  email text not null,
  primeiro_acesso timestamptz not null default now(),
  ultimo_acesso timestamptz not null default now(),
  visitas integer not null default 1,
  primary key (ativo_id, email)
);

create index if not exists idx_portal_acessos_email on portal_acessos (email);

-- Só o backend (service key) escreve e lê. Sem política, ninguém mais entra.
alter table portal_acessos enable row level security;

comment on table portal_acessos is
  'Visitas do armador ao Portal do Proprietário. Fonte da frase "último acesso" no card Dados da Embarcação.';
