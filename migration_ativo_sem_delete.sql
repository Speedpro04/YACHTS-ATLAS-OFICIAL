-- ============================================================================
-- ATIVO NÃO SE APAGA: ARQUIVA
-- ============================================================================
-- 30/08/2026 — fecha a última porta que ainda destruía histórico selado.
--
-- O PROBLEMA
-- ----------
-- `registros` e `documentos` já recusam DELETE por gatilho, e `registros`
-- recusa até UPDATE (só a redação LGPD passa, com seis travas). Mas `ativos`
-- não tinha nenhum: um DELETE ali levava os registros junto, em cascata,
-- contornando por cima toda a imutabilidade construída embaixo.
--
-- Uma cadeia de custódia com uma porta aberta na tabela-pai não é cadeia de
-- custódia — e é a primeira coisa que um auditor de SOC 2 / ISO 27001 procura.
--
-- POR QUE O RISCO DE APLICAR É ZERO
-- ---------------------------------
-- Ninguém apaga ativo hoje: não há `.delete()` sobre `ativos` em nenhum ponto
-- do backend nem do frontend (conferido em 30/08/2026). E o caminho correto
-- JÁ EXISTE desde antes: `ativos.arquivado_em`, com a listagem escondendo
-- arquivados por padrão e `?incluir_arquivados=true` para trazê-los de volta
-- (api/v1/ativos.py). Este gatilho só torna obrigatório o que já era a prática.
--
-- A MENSAGEM DE ERRO ENSINA O CAMINHO
-- -----------------------------------
-- Erro que só proíbe manda o operador procurar contorno. Este diz o que fazer
-- no lugar — é o mesmo padrão de `fn_registros_sem_delete`, que aponta para a
-- retificação.
-- ============================================================================

create or replace function public.fn_ativos_sem_delete()
returns trigger
language plpgsql
set search_path to ''
as $$
begin
  raise exception
    'Ativo sob custodia nao pode ser excluido (cadeia de custodia Yachts Atlas): '
    'apagar % levaria os registros selados junto, em cascata. '
    'Para tirar de operacao, ARQUIVE: update ativos set arquivado_em = now() where id = %. '
    'O historico continua verificavel e volta na listagem com ?incluir_arquivados=true.',
    old.id, old.id;
end $$;

drop trigger if exists trg_ativos_no_delete on public.ativos;
create trigger trg_ativos_no_delete
  before delete on public.ativos
  for each row execute function public.fn_ativos_sem_delete();

comment on function public.fn_ativos_sem_delete() is
  'Recusa DELETE em ativos. O ativo sai de operacao por arquivado_em, nunca '
  'por exclusao: DELETE aqui apagaria registros e documentos em cascata, '
  'contornando os gatilhos de imutabilidade das tabelas filhas.';

comment on column public.ativos.arquivado_em is
  'Soft delete do ativo. Preenchido = fora da operacao, mas com historico '
  'preservado e verificavel. E o unico caminho para "remover" um ativo: '
  'DELETE e recusado por trg_ativos_no_delete.';
