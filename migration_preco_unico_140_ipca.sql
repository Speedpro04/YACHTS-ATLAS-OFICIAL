-- ============================================================
-- Yachts Atlas — PREÇO ÚNICO: US$ 140/mês (R$ 697,00), travado
-- 12 meses, depois corrigido por IPCA + 15%
-- ------------------------------------------------------------
-- O QUE MUDA
-- Até aqui havia dois preços: US$ 200/mês para as 20 marinas fundadoras e
-- US$ 250/mês para as demais, com a fundadora subindo para US$ 250 no 13º mês
-- (e o legado de marinas_lancamento falando de US$ 300). Agora é UM preço para
-- todas — US$ 140/mês, R$ 697,00/mês em real —, travado por 12 meses a contar
-- da assinatura de cada marina.
--
-- O programa fundador CONTINUA: 4 vagas por estado (SC/SP/RJ/ES/BA), 18 meses
-- de dossiê 100% da marina. O que ele deixou de ser é desconto. É por isso que
-- as funções passam a devolver o MESMO `preco_mensal` nos dois modos:
-- 'tradicional' quer dizer "sem vaga", e não "mais caro".
--
-- A CORREÇÃO DO 13º MÊS NÃO É UM NÚMERO
-- É IPCA + 15%, e o IPCA do período só é conhecido na época. Não existe, por
-- isso, degrau de preço agendado em lugar nenhum — nem na Stripe (ver
-- stripe_service._registrar_reajuste_do_13o_mes). O que o banco guarda é a
-- REGRA e a DATA: `preco_travado_ate`, `reajuste_indice`, `reajuste_percentual`.
-- Aplicar é ato comercial, com aviso prévio à marina.
--
-- O QUE NÃO MUDA: as linhas que já existem. Elas registram o que foi
-- contratado, e contrato antigo não se reescreve por migration — as 3 marinas
-- em marinas_fundadoras (todas canceladas) seguem com os US$ 200 que pagaram.
-- Preço novo vale para linha nova, pelo default.
--
-- ESPELHOS deste número, que precisam mudar junto:
--   • backend/app/core/config.py          (PRECO_MENSAL_USD / _BRL / REAJUSTE_*)
--   • frontend/src/config/precoServico.ts (a home e o checkout)
--   • os Payment Links da Stripe          (US$ 140/mês e R$ 697,00/mês)
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

-- ------------------------------------------------------------
-- 1) O número, em um lugar só
--    O banco também precisava do preço — estava escrito à mão em duas
--    funções e em três defaults de coluna, cinco cópias do mesmo fato.
-- ------------------------------------------------------------
create or replace function public.preco_mensal_usd()
returns numeric
language sql
stable
set search_path to ''
as $$ select 140::numeric $$;

comment on function public.preco_mensal_usd() is
  'Mensalidade da marina em dolar (US$ 140). Um preco para todas — fundadora '
  'ou nao. Espelha PRECO_MENSAL_USD em backend/app/core/config.py.';

-- ------------------------------------------------------------
-- 2) marinas_fundadoras: preço novo e a regra do reajuste
-- ------------------------------------------------------------
alter table public.marinas_fundadoras
  alter column preco_mensal set default public.preco_mensal_usd();

alter table public.marinas_fundadoras
  add column if not exists preco_travado_ate   timestamptz,
  add column if not exists reajuste_indice     text    not null default 'ipca',
  add column if not exists reajuste_percentual numeric not null default 15;

comment on column public.marinas_fundadoras.preco_mensal is
  'O que ESTA marina paga por mes, em dolar. Guardado na linha (e nao lido do '
  'default) porque e o preco contratado por ela: mudanca de tabela nao reescreve '
  'contrato de quem ja assinou.';

comment on column public.marinas_fundadoras.preco_travado_ate is
  'Fim dos 12 meses de preco travado DESTA marina, contados da assinatura dela. '
  'Gravado pelo webhook do Stripe no pagamento (stripe_service.'
  '_registrar_reajuste_do_13o_mes). Passada a data, entra a correcao por '
  'reajuste_indice + reajuste_percentual — com aviso previo, na mao.';

comment on column public.marinas_fundadoras.reajuste_indice is
  'Indice que corrige o preco apos o periodo travado. "ipca" hoje.';

comment on column public.marinas_fundadoras.reajuste_percentual is
  'Pontos percentuais somados ao indice (15 = IPCA + 15%).';

-- A consulta que o comercial faz: quem vence o preco travado nos proximos dias.
create index if not exists idx_marinas_fundadoras_preco_travado_ate
  on public.marinas_fundadoras (preco_travado_ate)
  where status = 'ativo';

-- ------------------------------------------------------------
-- 3) marinas_lancamento: LEGADO, alinhado para não contradizer
--    Não é mais a tabela da oferta (ver migration_marinas_fundadoras.sql),
--    mas continua de pé com 20 linhas 'disponivel' que ninguém contratou —
--    e com preços antigos, que mentiriam para quem fosse ler.
-- ------------------------------------------------------------
alter table public.marinas_lancamento
  alter column preco_mensal   set default public.preco_mensal_usd(),
  alter column preco_indicada set default public.preco_mensal_usd(),
  -- preco_apos IGUAL ao preco_mensal: nao existe mais degrau fixo no 13º mes.
  -- A coluna e NOT NULL e nao aceita "nenhum valor"; igualdade e a forma de
  -- dizer "nao sobe por tabela" sem inventar um numero novo.
  alter column preco_apos     set default public.preco_mensal_usd();

comment on column public.marinas_lancamento.preco_apos is
  'LEGADO. Era o preco do 13º mes em diante (US$ 300). Hoje nao existe degrau '
  'fixo: a correcao e por indice (IPCA + 15%) e vive em marinas_fundadoras.';

-- Só as vagas que nunca foram contratadas. Linha com marina dentro fica como está.
update public.marinas_lancamento
   set preco_mensal   = public.preco_mensal_usd(),
       preco_indicada = public.preco_mensal_usd(),
       preco_apos     = public.preco_mensal_usd(),
       updated_at     = now()
 where status = 'disponivel'
   and email is null
   and (preco_mensal   <> public.preco_mensal_usd()
     or preco_indicada <> public.preco_mensal_usd()
     or preco_apos     <> public.preco_mensal_usd());

-- ------------------------------------------------------------
-- 4) As duas funções do fluxo de venda
--    Mesmas regras de antes (4 vagas por estado, reserva com prazo, cap sob
--    concorrência). A única mudança: onde devolviam 250 no modo tradicional,
--    devolvem o preço único — pela função, para não voltar a ter o número
--    escrito à mão aqui dentro.
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

  -- Estado fora do programa segue para a oferta oficial: mesmo preco,
  -- sem vaga e sem os 18 meses de dossie 100%.
  if v_uf not in ('SC', 'SP', 'RJ', 'ES', 'BA') then
    return jsonb_build_object(
      'modo', 'tradicional',
      'preco_mensal', public.preco_mensal_usd(),
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
      'preco_mensal', public.preco_mensal_usd(),
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
--    Confirmar a vaga no PAGAMENTO (promove a reserva). Chamada pelo webhook
--    do Stripe. Quem pagou tem a vaga honrada mesmo com a reserva vencida:
--    recusar depois de cobrar geraria estorno.
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
      'modo', 'tradicional', 'preco_mensal', public.preco_mensal_usd(),
      'motivo', 'sem_reserva_e_uf_desconhecida');
  end if;

  v_ocupadas := public.fn_vagas_fundadoras_ocupadas(v_uf);

  if v_ocupadas >= 4 then
    return jsonb_build_object(
      'modo', 'tradicional', 'preco_mensal', public.preco_mensal_usd(),
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
-- ------------------------------------------------------------
-- 5) Quem está vencendo o preço travado
--    A regra guardada que ninguém consegue achar é regra que não existe.
--    `security_invoker` para a view respeitar a RLS de marinas_fundadoras
--    (sem política pública: só o service role lê) — mesmo padrão de
--    vw_registros_situacao.
-- ------------------------------------------------------------
create or replace view public.vw_marinas_a_reajustar
with (security_invoker = true) as
  select id,
         marina_nome,
         email,
         uf,
         preco_mensal,
         preco_travado_ate,
         reajuste_indice,
         reajuste_percentual,
         (preco_travado_ate <= now()) as venceu
    from public.marinas_fundadoras
   where status = 'ativo'
     and preco_travado_ate is not null
   order by preco_travado_ate;

comment on view public.vw_marinas_a_reajustar is
  'Marinas ativas com a data de fim do preco travado. Serve para montar a carta '
  'de reajuste (IPCA + 15%) ANTES de a fatura subir. `venceu` = ja passou da '
  'data e o reajuste esta pendente.';
