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

-- 2. Funções SECURITY DEFINER executáveis via RPC.
--    São funções de trigger/interno — não devem ser chamáveis pela API.
--    IMPORTANTE: revogar do role `public` (anon/authenticated herdam dele;
--    revogar só dos filhos NÃO remove o acesso). Triggers não dependem
--    de EXECUTE, então isso não quebra o signup.
revoke execute on function public.handle_new_user() from public;
revoke execute on function public.rls_auto_enable() from public;

-- 3. Bucket `media` permitia LISTAR todos os arquivos. Removida a política
--    de listagem — arquivos seguem acessíveis por URL direta (getPublicUrl),
--    mas ninguém lista o bucket inteiro. (APLICADO)
--    Futuro: tornar bucket privado + signed URLs para dados sensíveis.
drop policy if exists "Public Access to Media" on storage.objects;

-- 4. marina_leads: o INSERT público é INTENCIONAL (formulário público de leads).
--    Não alterar. As leituras/edições já são restritas (service role).
--    Mantido aqui só como registro da decisão.

-- ============================================================
-- Após aplicar: rodar advisors de novo para confirmar que os
-- WARNs sumiram (get_advisors / supabase db advisors).
-- ============================================================
