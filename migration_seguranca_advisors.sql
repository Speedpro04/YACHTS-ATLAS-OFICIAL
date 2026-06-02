-- ============================================================
-- Yachts Atlas — Correções de Segurança (Supabase Advisors)
-- ------------------------------------------------------------
-- Corrige os alertas apontados pelos advisors no banco real.
-- Validado: todas as funções abaixo são sem argumentos `()`.
-- NÃO aplicado ainda — revisar (especialmente o item 3, storage).
-- ============================================================

-- 1. search_path mutável em funções (WARN segurança)
--    Fixar o search_path elimina o vetor de ataque por troca de schema.
alter function public.atualizar_progresso_ativo() set search_path = public;
alter function public.handle_new_user()           set search_path = public;
alter function public.update_updated_at_column()   set search_path = public;
alter function public.update_updated_at()          set search_path = public;
alter function public.rls_auto_enable()            set search_path = public;

-- 2. Funções SECURITY DEFINER executáveis por anônimo/autenticado via RPC.
--    São funções de trigger/interno — não devem ser chamáveis pela API.
revoke execute on function public.handle_new_user() from anon, authenticated;
revoke execute on function public.rls_auto_enable() from anon, authenticated;

-- 3. (REVISAR ANTES) Bucket `media` é público e permite LISTAR todos os arquivos.
--    Para acesso por URL pública (getPublicUrl) NÃO é necessária política
--    SELECT ampla em storage.objects. Remover a listagem fecha a exposição
--    sem quebrar o acesso por URL direta.
--    Confirme que o app NÃO lista o bucket antes de aplicar:
-- drop policy if exists "Public Access to Media" on storage.objects;

-- 4. marina_leads: o INSERT público é INTENCIONAL (formulário público de leads).
--    Não alterar. As leituras/edições já são restritas (service role).
--    Mantido aqui só como registro da decisão.

-- ============================================================
-- Após aplicar: rodar advisors de novo para confirmar que os
-- WARNs sumiram (get_advisors / supabase db advisors).
-- ============================================================
