-- Consentimento do titular para o dossie sair para terceiro.
-- Aplicada em producao em 31/08/2026 (nome: consentimento_do_titular_append_only).
--
-- Fica em tabela propria, e nao numa coluna de `ativos`, por dois motivos:
--
-- 1. `ativos` aceita UPDATE. Consentimento guardado la poderia ter a data
--    alterada depois, em silencio -- inutil como prova numa auditoria. Numa
--    plataforma que vende custodia, isso seria constrangedor.
-- 2. Consentimento tem historia: e concedido e pode ser retirado. Uma coluna
--    booleana apaga a retirada anterior; uma linha por evento preserva a
--    sequencia, que e justamente o que a LGPD (art. 8o, §5o) pressupoe.
--
-- O titular e o armador. As colunas `titular_*` guardam FOTOGRAFIA do nome e
-- documento no momento do consentimento: barco troca de dono, e o consenti-
-- mento do dono anterior nao vale para o novo.
create table if not exists public.ativo_consentimentos (
  id                 uuid primary key default gen_random_uuid(),
  ativo_id           text not null references public.ativos(id) on delete restrict,
  evento             text not null check (evento in ('concedido','revogado')),
  titular_nome       text,
  titular_documento  text,
  termo_versao       text not null,
  termo_texto        text not null,
  obtido_via         text not null check (obtido_via in
                       ('contrato_marina','assinatura_digital','email','presencial')),
  observacao         text,
  registrado_por     uuid,
  registrado_em      timestamptz not null default now()
);

comment on table public.ativo_consentimentos is
  'Append-only. Base legal para compartilhar o dossie com terceiro. Retirar consentimento e um evento "revogado", nunca um UPDATE.';

create index if not exists idx_ativo_consentimentos_ativo
  on public.ativo_consentimentos (ativo_id, registrado_em desc);

-- RLS ligada sem politica = nada alcanca pela API publica. O backend usa a
-- chave de servico, que ignora RLS. Mesmo padrao de `dossie_saidas`.
alter table public.ativo_consentimentos enable row level security;

-- `search_path = ''` desde 31/08/2026 (migration_endurece_funcoes.sql): sem
-- isso, quem conseguisse criar objetos num schema anterior na busca poderia
-- sombrear a tabela.
create or replace function public.fn_ativo_consentimentos_imutavel()
returns trigger language plpgsql set search_path = '' as $$
begin
  raise exception
    'ativo_consentimentos e append-only: consentimento nao se edita nem se apaga. Para retirar, registre um evento "revogado".';
end;
$$;

drop trigger if exists trg_ativo_consentimentos_imutavel on public.ativo_consentimentos;
create trigger trg_ativo_consentimentos_imutavel
  before update or delete on public.ativo_consentimentos
  for each row execute function public.fn_ativo_consentimentos_imutavel();

-- Estado vigente = ultimo evento. Sem linha nenhuma, sem consentimento.
create or replace function public.fn_consentimento_vigente(p_ativo_id text)
returns table (vigente boolean, evento text, registrado_em timestamptz,
               termo_versao text, titular_nome text)
language sql stable set search_path = '' as $$
  select (c.evento = 'concedido'), c.evento, c.registrado_em,
         c.termo_versao, c.titular_nome
  from public.ativo_consentimentos c
  where c.ativo_id = p_ativo_id
  order by c.registrado_em desc, c.id desc
  limit 1;
$$;
