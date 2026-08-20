-- ============================================================
-- Yachts Atlas — e-mail do proprietário no ativo
-- ------------------------------------------------------------
-- É a peça que faltava para o Portal do Proprietário existir.
--
-- O PROBLEMA que isto resolve:
--   `ativos` tinha uma única coluna de dono, `usuario_id`, e é a marina.
--   A listagem filtra por ela. Logo, não havia como o armador ver o próprio
--   barco — a única forma de dar acesso a ele seria emprestar a conta da
--   marina, e aí ele enxergaria a frota inteira, de todos os clientes dela.
--
-- A SOLUÇÃO:
--   O barco guarda o e-mail do dono. O armador entra no portal digitando o
--   e-mail dele, recebe um código de uso único e vê só os barcos marcados com
--   aquele e-mail. Nunca a conta da marina, nunca a frota dela.
--
--   O segredo é a caixa de e-mail do armador — diferente de CPF ou nome da
--   embarcação, que estão no próprio dossiê e circulam com ele.
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

alter table public.ativos
  add column if not exists proprietario_email text;

comment on column public.ativos.proprietario_email is
  'E-mail do dono da embarcação. Chave de acesso ao Portal do Proprietário: '
  'o armador digita este e-mail, recebe um código e vê somente os ativos '
  'marcados com ele. Preenchido pela marina no cadastro do barco.';

-- Busca por e-mail é o caminho quente do portal: acontece a cada login do
-- armador. Índice em lower() porque ninguém digita e-mail com a mesma caixa
-- duas vezes — "Roberto@Email.com" e "roberto@email.com" são a mesma pessoa.
create index if not exists idx_ativos_proprietario_email
  on public.ativos (lower(proprietario_email))
  where proprietario_email is not null;
