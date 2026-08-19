-- ============================================================
-- Yachts Atlas — fecha dois furos de exposição no PostgREST
-- ------------------------------------------------------------
-- Aplicado em 18/08/2026. Ambos confirmados no advisor do
-- Supabase e reproduzidos com `set role anon` antes da correção.
--
-- Idempotente: pode rodar mais de uma vez.
-- ============================================================

-- ------------------------------------------------------------
-- 1) vw_registros_situacao rodava como o dono (postgres)
--
-- Com SECURITY DEFINER a view ignorava o RLS de `registros`. Como
-- anon/authenticated têm SELECT nela, qualquer pessoa com a chave
-- pública lia os registros de TODOS os proprietários — a tabela
-- devolvia 0 linhas para anon e a view devolvia 112.
--
-- O backend consulta a view com service_role (registros.py e
-- dossie_data.py), que ignora RLS de qualquer forma, então o
-- produto não muda em nada.
-- ------------------------------------------------------------
alter view public.vw_registros_situacao set (security_invoker = true);


-- ------------------------------------------------------------
-- 2) fn_lgpd_redigir estava exposta em /rest/v1/rpc
--
-- É a única função autorizada a alterar um registro selado (apaga
-- dado pessoal e recalcula o hash). O backend protege com
-- _exige_admin, mas a chamada direta pelo PostgREST contornava
-- essa checagem.
--
-- Não era explorável na prática: a função exige uma solicitação
-- LGPD válida e um registro existente, e anon não consegue ler
-- `lgpd_solicitacoes` nem `registros` para descobrir os UUIDs.
-- Mesmo assim não há motivo para ela estar publicada — o backend
-- chama com service_role.
-- ------------------------------------------------------------
revoke execute on function public.fn_lgpd_redigir(uuid, uuid, text[]) from anon;
revoke execute on function public.fn_lgpd_redigir(uuid, uuid, text[]) from authenticated;
revoke execute on function public.fn_lgpd_redigir(uuid, uuid, text[]) from public;
