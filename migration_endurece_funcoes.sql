-- Endurecimento de tres achados do linter de seguranca do Supabase.
-- Aplicada em producao em 31/08/2026
-- (nome: endurece_funcoes_consentimento_e_integridade).
--
-- Rodado a pedido do fundador, que perguntou se o sistema estava pronto para
-- uma auditoria. Dos cinco WARN que o linter apontou, tres eram acionaveis --
-- e DOIS eram do mesmo dia, das funcoes de consentimento recem-criadas.

-- ─────────────────────────────────────────────────────────────────────────
-- 1. search_path fixo nas duas funcoes criadas em 31/08/2026
-- ─────────────────────────────────────────────────────────────────────────
-- Toda funcao anterior do projeto ja usava `search_path=""` -- fn_registro_hash,
-- fn_registro_hash_esperado, fn_verificar_integridade_ativo,
-- vagas_fundadoras_resumo. Estas duas nasceram sem, e foram as unicas que o
-- linter apontou: um padrao estabelecido que nao foi seguido.
--
-- Sem search_path fixo, quem conseguisse criar objetos num schema anterior na
-- busca poderia sombrear `ativo_consentimentos` e fazer a funcao ler outra
-- tabela. O consentimento e a base legal do compartilhamento: e o ultimo
-- lugar do sistema onde se quer ambiguidade sobre QUAL tabela foi lida.
--
-- Os corpos ja qualificam tudo com `public.`, entao isto nao altera
-- comportamento -- so fecha o caminho.
alter function public.fn_consentimento_vigente(text) set search_path = '';
alter function public.fn_ativo_consentimentos_imutavel() set search_path = '';

-- ─────────────────────────────────────────────────────────────────────────
-- 2. Vazamento entre marinas em fn_verificar_integridade_ativo
-- ─────────────────────────────────────────────────────────────────────────
-- Ela e SECURITY DEFINER de proposito: precisa ler `registros` apesar do RLS
-- para recalcular os hashes. O problema era o GRANT -- `authenticated` tinha
-- EXECUTE, entao qualquer marina logada podia chamar
--
--     POST /rest/v1/rpc/fn_verificar_integridade_ativo
--
-- com o ID de um ativo de OUTRA marina e receber quantos registros conferem,
-- quantos divergem e se a cadeia esta integra.
--
-- Nao expoe conteudo de registro, mas confirma a existencia do ativo e revela
-- o estado da custodia alheia. E exatamente a pergunta que uma auditoria de
-- seguradora faz: "marina A consegue saber algo sobre a marina B?"
--
-- O backend chama esta funcao com o cliente de servico (get_supabase_admin()
-- em api/v1/verificacao.py), que ignora grant. Revogar de `authenticated` nao
-- afeta a pagina publica de verificacao (destino do QR) nem o painel: fecha
-- so a chamada direta com JWT de usuario.
--
-- Conferido depois de aplicar: a funcao segue devolvendo
-- total=16 conferem=16 divergem=0 integro=true para YA-IATE-2015-3A38.
revoke execute on function public.fn_verificar_integridade_ativo(text) from authenticated;
revoke execute on function public.fn_verificar_integridade_ativo(text) from anon;
revoke execute on function public.fn_verificar_integridade_ativo(text) from public;

-- ─────────────────────────────────────────────────────────────────────────
-- O QUE FICOU DE FORA, E POR QUE
-- ─────────────────────────────────────────────────────────────────────────
-- Os 14 INFO de `rls_enabled_no_policy` NAO sao defeito: sao o padrao
-- deny-all adotado de proposito. RLS ligada sem politica = nada alcanca pela
-- API publica; o backend usa a chave de servico. O linter marca em INFO
-- porque a mesma configuracao tambem apareceria se alguem tivesse esquecido
-- de criar a politica -- ele nao sabe distinguir intencao de esquecimento.
--
-- Sobraram dois WARN:
--   * `extension_in_public` (vector, do RAG da Solara) -- mover o schema de
--     uma extensao em uso exige recriar os indices; nao vale o risco agora.
--   * `auth_leaked_password_protection` -- BLOQUEADO PELO PLANO gratuito do
--     Supabase. Requer Pro. Decisao do fundador.
