-- ============================================================================
-- POR QUE 13 TABELAS TÊM RLS SEM POLÍTICA
-- ============================================================================
-- 31/08/2026 — resposta escrita para a primeira pergunta de qualquer auditoria
-- de SOC 2 / ISO 27001 / SUSEP sobre o schema.
--
-- O QUE O AUDITOR VÊ
-- ------------------
-- O linter do Supabase reporta 13 vezes: "RLS enabled, but no policies exist".
-- Lido sem contexto, isso parece configuração pela metade — alguém ligou a
-- trava e esqueceu de escrever as regras.
--
-- O QUE ISSO REALMENTE É
-- ----------------------
-- RLS ligado SEM política é `deny all`: no Postgres, quem passa pelo RLS só
-- alcança a linha que alguma política PERMITE. Sem nenhuma, ninguém alcança
-- nada. É a configuração MAIS restritiva possível, não a menos.
--
-- Estas 13 tabelas são de backend puro. Nenhuma é lida pelo navegador com a
-- chave anônima: quem escreve e lê é o servidor, com a chave de serviço, que
-- por definição não passa pelo RLS. Escrever política aqui seria criar uma
-- porta que hoje não existe — e porta que existe é porta que alguém erra.
--
-- A DECISÃO, DITA DE UMA VEZ
-- --------------------------
-- Preferimos `deny all` + acesso exclusivo do backend a políticas permissivas
-- espalhadas. Cada política é uma superfície a revisar em toda mudança de
-- schema; a ausência delas é uma superfície a menos.
--
-- Quando uma destas tabelas precisar ser lida direto pelo cliente, a política
-- entra JUNTO com essa necessidade — nunca antes, "por precaução".
--
-- Os comentários abaixo preservam o que já estava escrito sobre cada tabela e
-- acrescentam essa justificativa, para que ela chegue ao auditor pelo próprio
-- banco, e não pela memória de quem estiver na sala.
-- ============================================================================

do $$
declare
  nota constant text :=
    E'\n\nACESSO: RLS ligado SEM politica = deny all. Tabela de backend puro — '
    'nenhuma leitura do navegador com chave anonima; quem le e escreve e o '
    'servidor, com a chave de servico, que nao passa pelo RLS. A ausencia de '
    'politica e deliberada e e a configuracao MAIS restritiva possivel: '
    'politica so entra junto com a necessidade real de acesso pelo cliente. '
    'Ver migration_documenta_deny_all.sql (31/08/2026).';

  -- Descrição de cada tabela. As que já tinham comentário mantêm o texto
  -- original; as seis sem comentário ganham a descrição do que guardam,
  -- lida das próprias colunas.
  descricoes constant jsonb := jsonb_build_object(
    'dossie_emitidos',
      'Impressao digital de cada dossie emitido. APPEND-ONLY: nunca UPDATE nem DELETE — e a prova de que um PDF em maos e o que a plataforma emitiu.',
    'dossie_saidas',
      'Trilha de COMPARTILHAMENTO do dossie: uma linha por envio a terceiro, com destinatario, finalidade, canal e IP. E o registro que responde "quem recebeu este dossie, quando e para que" — pergunta de LGPD e de auditoria de seguradora.',
    'dossie_solicitacoes',
      'Pedidos de acesso ao dossie feitos por terceiros (corretor, comprador, seguradora), com finalidade declarada, status de liberacao, quem liberou e contagem de acessos.',
    'lgpd_solicitacoes',
      'Solicitações de titulares (LGPD Art. 18). Toda redação em registro selado aponta para uma linha daqui.',
    'marinas_fundadoras',
      'As 20 vagas do Programa Marinas Fundadoras: condicoes comerciais por marina (preco, meses de promocao, meses de dossie, permanencia minima), UF e reserva com prazo.',
    'marinas_lancamento',
      'Slots do Lancamento, com o sistema de indicacao: quantas indicacoes a marina precisa, quantas fez, e o bonus de dossie liberado por elas.',
    'pagamentos_lancamento',
      'Pagamentos confirmados do Stripe (webhook) para o Programa Marinas Fundadoras. Uma linha por evento Stripe (idempotente por stripe_event_id).',
    'partner_clicks',
      'Telemetria de contato com parceiros: qual parceiro, por qual canal, a partir de qual ativo. Mede se a rede de parceiros gera negocio de verdade.',
    'partner_leads',
      'Prestadores de servico nautico que pedem para entrar na rede (estaleiro, corretor, seguradora), com categoria e status de triagem.',
    'solara_perguntas',
      'O que perguntam a Capita Solara. Mapa do que esta confuso no produto, ordenado por frequencia. respondida=false e o sinal mais valioso.',
    'vega_leads',
      'Leads do WhatsApp atendidos pela Vega (Programa Marinas Fundadoras).',
    'vega_mensagens',
      'Cada mensagem trocada com a Vega no WhatsApp.',
    'whatsapp_blocklist',
      'Numeros que pediram para nao receber prospeccao. Consultar antes de qualquer disparo.'
  );

  t record;
  texto text;
begin
  for t in
    select c.oid, c.relname
    from pg_class c join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public' and c.relkind = 'r' and c.relrowsecurity
      and (select count(*) from pg_policy p where p.polrelid = c.oid) = 0
  loop
    -- Tabela nova que apareça com deny all e ainda não esteja descrita aqui
    -- também recebe a nota: a justificativa não pode depender de alguém
    -- lembrar de voltar neste arquivo.
    texto := coalesce(descricoes ->> t.relname,
                      'Tabela de backend. Descricao pendente — ver PRD.') || nota;
    execute format('comment on table public.%I is %L', t.relname, texto);
    raise notice 'documentada: %', t.relname;
  end loop;
end $$;
