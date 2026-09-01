-- ============================================================
-- migration_rls_initplan_e_indices_fk.sql — 01/09/2026
-- Aplicada em producao (projeto owzelkiyorumnlaycral) via MCP.
-- Arquivada aqui para o historico, no padrao das demais migrations.
--
-- POR QUE: o advisor de performance apontava 21 politicas de RLS
-- reavaliando auth.uid()/auth.role() UMA VEZ POR LINHA lida. Envolver
-- a chamada em (select ...) faz o Postgres resolver como InitPlan --
-- uma vez por consulta. A logica de quem ve o que NAO muda em
-- nenhuma das 21: mesma coluna, mesma comparacao, mesmo resultado.
--
-- CONFERIDO DEPOIS: politicas ainda avaliando por linha = 0;
-- total de politicas = 34, o mesmo de antes (nenhuma criada nem
-- removida, so reescritas). auth_rls_initplan: 21 -> 0.
-- ============================================================

alter policy "Perfis visíveis pelos próprios usuários" on public.profiles
  using ((select auth.uid()) = id);
alter policy "Usuários podem atualizar próprios perfis" on public.profiles
  using ((select auth.uid()) = id);

alter policy "Usuários veem apenas seus ativos" on public.ativos
  using ((select auth.uid()) = usuario_id);
alter policy "Usuários atualizam seus próprios ativos" on public.ativos
  using ((select auth.uid()) = usuario_id);
alter policy "Usuários inserem seus próprios ativos" on public.ativos
  with check ((select auth.uid()) = usuario_id);

alter policy "Usuários veem apenas documentos de seus ativos" on public.documentos
  using ((select auth.uid()) = usuario_id);
alter policy "Usuários inserem documentos em seus ativos" on public.documentos
  with check ((select auth.uid()) = usuario_id);

alter policy "Usuários veem seus próprios logs" on public.audit_logs
  using ((select auth.uid()) = user_id);
alter policy "Admins veem todos os logs" on public.audit_logs
  using (exists (select 1 from public.profiles
                 where profiles.id = (select auth.uid())
                   and profiles.user_role = 'admin'));

alter policy "Usuários veem verificações de seus documentos" on public.integridade_logs
  using (exists (select 1 from public.documentos d
                 where d.id = integridade_logs.documento_id
                   and d.usuario_id = (select auth.uid())));

alter policy "Usuários veem seus próprios pagamentos" on public.payments
  using ((select auth.uid()) = usuario_id);
alter policy "Usuários veem suas próprias assinaturas" on public.subscriptions
  using ((select auth.uid()) = usuario_id);

alter policy "Admins gerenciam seguradoras" on public.insurance_companies
  using (exists (select 1 from public.profiles
                 where profiles.id = (select auth.uid())
                   and profiles.user_role = 'admin'));

alter policy "Brokers veem seus próprios dados" on public.brokers
  using ((select auth.uid()) = user_id);
alter policy "Admins gerenciam brokers" on public.brokers
  using (exists (select 1 from public.profiles
                 where profiles.id = (select auth.uid())
                   and profiles.user_role = 'admin'));

alter policy "Usuários veem integrações de seus ativos" on public.insurance_integrations
  using (exists (select 1 from public.ativos a
                 where a.id = insurance_integrations.ativo_id
                   and a.usuario_id = (select auth.uid())));
alter policy "Seguradoras veem integrações" on public.insurance_integrations
  using (exists (select 1 from public.profiles p
                 where p.id = (select auth.uid())
                   and p.user_role = 'insurance'));

alter policy "Brokers veem suas próprias transações" on public.broker_deals
  using ((select auth.uid()) = (select brokers.user_id from public.brokers
                                where brokers.id = broker_deals.broker_id));
alter policy "Admins veem todas as transações" on public.broker_deals
  using (exists (select 1 from public.profiles
                 where profiles.id = (select auth.uid())
                   and profiles.user_role = 'admin'));

alter policy "leads_select_service_only" on public.marina_leads
  using ((select auth.role()) = 'service_role');
alter policy "leads_update_service_only" on public.marina_leads
  using ((select auth.role()) = 'service_role');

-- ============================================================
-- 10 chaves estrangeiras sem indice de cobertura. Sem indice, todo
-- DELETE/UPDATE no lado pai varre a tabela filha inteira. Atencao:
-- a coluna de registros e `lgpd_solicitacao`, SEM o sufixo _id --
-- deduzir o nome pelo nome da FK quebrou a primeira tentativa.
-- unindexed_foreign_keys: 10 -> 0.
-- ============================================================
create index if not exists idx_ativos_usuario_id                on public.ativos (usuario_id);
create index if not exists idx_documentos_ativo_id              on public.documentos (ativo_id);
create index if not exists idx_documentos_usuario_id            on public.documentos (usuario_id);
create index if not exists idx_documentos_uploaded_by           on public.documentos (uploaded_by);
create index if not exists idx_payments_ativo_id                on public.payments (ativo_id);
create index if not exists idx_registros_created_by             on public.registros (created_by);
create index if not exists idx_registros_lgpd_solicitacao       on public.registros (lgpd_solicitacao);
create index if not exists idx_broker_deals_buyer_id            on public.broker_deals (buyer_id);
create index if not exists idx_broker_deals_seller_id           on public.broker_deals (seller_id);
create index if not exists idx_pagamentos_lancamento_lead_id    on public.pagamentos_lancamento (lead_id);
