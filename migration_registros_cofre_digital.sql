-- YACHTS ATLAS - COFRE DIGITAL DE REGISTROS DE EMBARCAÇÕES
-- Sistema de arquivamento imutável de histórico de embarcações
-- Foco: Transparência total para o proprietário do ativo
-- Author: Yachts Atlas Team
-- Date: 2026-05-21

-- ==========================================
-- 0. EXTENSÕES E PREPARAÇÃO
-- ==========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabela auxiliar para tipagem de categorias
CREATE TYPE registro_categoria AS ENUM (
    'documentacao_legal',
    'motor_propulsao',
    'manutencao_mecanica',
    'eletrica_eletronica',
    'seguranca_salvatagem',
    'integridade_estrutural',
    'pintura_acabamento',
    'rastreabilidade_servicos',
    'interior_acomodacoes',
    'navegabilidade'
);

-- Tabela auxiliar para tipagem de status
CREATE TYPE registro_status AS ENUM (
    'em_aberto',
    'concluido',
    'agendado',
    'cancelado'
);

-- ==========================================
-- 1. TABELA PRINCIPAL: REGISTROS
-- ==========================================
-- Esta é a tabela central que armazena TODOS os registros de forma imutável
CREATE TABLE IF NOT EXISTS public.registros (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    marina_id UUID REFERENCES public.marinas(id) ON DELETE CASCADE NOT NULL,
    registrado_por UUID REFERENCES public.profiles(id) ON DELETE SET NULL,

    -- Categoria do registro (uma das 10)
    categoria registro_categoria NOT NULL,

    -- Subcategoria para detalhamento (ex: 'troca_oleo', 'revisao_filtros')
    subcategoria TEXT NOT NULL,

    -- Título descritivo (ex: "Troca de óleo - Motor Volvo Penta D6-370")
    titulo TEXT NOT NULL,

    -- Descrição detalhada do serviço realizado
    descricao TEXT NOT NULL,

    -- Data em que o serviço foi executado
    data_execucao DATE NOT NULL,

    -- Leituras no momento do serviço
    horometro_leitura DECIMAL,
    kilometragem_leitura DECIMAL,

    -- Próximos vencimentos
    proximo_vencimento DATE,
    proximo_vencimento_horometro DECIMAL,
    proximo_vencimento_km DECIMAL,

    -- Informações do técnico/empresa que executou
    tecnico_nome TEXT,
    tecnico_empresa TEXT,
    tecnico_cnpj_cpf TEXT,
    tecnico_registro VARCHAR(50), -- Registro profissional se aplicável

    -- Status do registro
    status registro_status DEFAULT 'concluido',

    -- Observações e recomendações técnicas
    observacoes_tecnicas TEXT,
    recomendacoes_proximas TEXT,

    -- Snapshot imutável no momento do registro
    vessel_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,

    -- Hash SHA-256 para integridade (calculado no backend)
    hash_sha256 CHAR(64) NOT NULL,

    -- Metadados de sistema
    criado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,
    atualizado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()),

    -- Imutabilidade: após 24h, registro não pode mais ser editado
    imutavel_apos TIMESTAMPTZ GENERATED ALWAYS AS (criado_em + interval '24 hours') STORED
);

-- Índice para consultas rápidas por ativo
CREATE INDEX IF NOT EXISTS idx_registros_ativo ON public.registros(ativo_id);
CREATE INDEX IF NOT EXISTS idx_registros_marina ON public.registros(marina_id);
CREATE INDEX IF NOT EXISTS idx_registros_categoria ON public.registros(categoria);
CREATE INDEX IF NOT EXISTS idx_registros_data ON public.registros(data_execucao);

-- ==========================================
-- 2. TABELA: EVIDÊNCIAS (FOTOS, RECIBOS, LAUDOS)
-- ==========================================
-- Armazena links para arquivos de evidência de cada registro
CREATE TABLE IF NOT EXISTS public.registro_evidencias (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    registro_id UUID REFERENCES public.registros(id) ON DELETE CASCADE NOT NULL,

    -- Tipo de evidência
    tipo TEXT NOT NULL CHECK (
        tipo IN (
            'foto_antes',
            'foto_durante',
            'foto_depois',
            'peca_velha',
            'peca_nova',
            'recibo',
            'nota_fiscal',
            'laudo_tecnico',
            'comprovante_pagamento',
            'outro'
        )
    ),

    -- Descrição opcional da evidência
    descricao TEXT,

    -- Caminho no storage (ex: registros/{ativo_id}/{registro_id}/evidencia.jpg)
    storage_path TEXT NOT NULL,

    -- URL pública ou signed
    url_arquivo TEXT,

    -- Hash do arquivo para integridade
    hash_sha256 CHAR(64) NOT NULL,

    -- Tamanho do arquivo em bytes
    tamanho_bytes INTEGER NOT NULL,

    -- Ordem de exibição
    ordem_exibicao INTEGER DEFAULT 0,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL,

    -- Imutabilidade
    imutavel_apos TIMESTAMPTZ DEFAULT (timezone('utc'::text, now()) + interval '24 hours')
);

CREATE INDEX IF NOT EXISTS idx_evidencias_registro ON public.registro_evidencias(registro_id);

-- ==========================================
-- 3. TABELA: PEÇAS TROCADAS
-- ==========================================
-- Registro detalhado de peças substituídas
CREATE TABLE IF NOT EXISTS public.registro pecas_trocadas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    registro_id UUID REFERENCES public.registros(id) ON DELETE CASCADE NOT NULL,

    -- Nome da peça
    nome_peca TEXT NOT NULL,

    -- Número de série ou parte
    numero_serie VARCHAR(100),
    numero_peca VARCHAR(100),

    -- Fornecedor/marca
    marca TEXT,
    fornecedor TEXT,

    -- Quantidade
    quantidade INTEGER DEFAULT 1,

    -- Custo (opcional, para histórico de valor)
    custo_unitario DECIMAL(10,2),
    custo_total DECIMAL(10,2),

    -- Garantia
    garantia_meses INTEGER,
    garantia_km_horas DECIMAL,

    -- Descrição
    descricao TEXT,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_pecas_registro ON public.registro_pecas_trocadas(registro_id);

-- ==========================================
-- 4. TABELA: CHECKLIST POR CATEGORIA
-- ==========================================
-- Itens de checklist específicos para cada tipo de registro
CREATE TABLE IF NOT EXISTS public.registro_checklists (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    registro_id UUID REFERENCES public.registros(id) ON DELETE CASCADE NOT NULL,

    -- Nome do item de checklist (ex: "Nível de óleo")
    item_nome TEXT NOT NULL,

    -- Categoria do item (para organização)
    item_categoria TEXT,

    -- Tipo de valor
    item_tipo TEXT CHECK (
        item_tipo IN (
            'checkbox',
            'texto',
            'numero',
            'data',
            'selecao',
            'medicao'
        )
    ) DEFAULT 'checkbox',

    -- Valor registrado
    item_valor TEXT,

    -- Unidade de medida (ex: "mm", "PSI", "litros")
    unidade_medida TEXT,

    -- Valor de referência/esperado
    valor_referencia TEXT,

    -- Status (ok, atencao, critico)
    status_item TEXT CHECK (status_item IN ('ok', 'atencao', 'critico')) DEFAULT 'ok',

    -- Ordem
    ordem INTEGER DEFAULT 0,

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_checklists_registro ON public.registro_checklists(registro_id);

-- ==========================================
-- 5. TABELA: AUDIT LOG (Rastreabilidade Completa)
-- ==========================================
-- Toda ação nos registros é auditada
CREATE TABLE IF NOT EXISTS public.registros_audit_log (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    registro_id UUID REFERENCES public.registros(id) ON DELETE SET NULL,

    -- Usuário que realizou a ação
    user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,

    -- Ação realizada
    acao TEXT NOT NULL CHECK (
        acao IN (
            'criado',
            'visualizado',
            'impresso',
            'exportado',
            'tentativa_edicao',
            'tentativa_exclusao'
        )
    ),

    -- Detalhes da ação (JSON)
    detalhes JSONB DEFAULT '{}'::jsonb,

    -- IP e user agent
    ip_address TEXT,
    user_agent TEXT,
    localizacao TEXT,

    -- Hash do registro no momento da ação
    hash_no_momento CHAR(64),

    -- Timestamp
    criado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_registro ON public.registros_audit_log(registro_id);
CREATE INDEX IF NOT EXISTS idx_audit_user ON public.registros_audit_log(user_id);

-- ==========================================
-- 6. TABELA: ALERTAS E LEMBRETES
-- ==========================================
-- Alertas automáticos baseados em registros
CREATE TABLE IF NOT EXISTS public.registro_alertas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    registro_id UUID REFERENCES public.registros(id) ON DELETE CASCADE,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE,

    -- Tipo de alerta
    tipo_alerta TEXT CHECK (
        tipo_alerta IN (
            'vencimento_proximo',
            'vencido',
            'recomendacao_tecnico',
            'pecas_garantia',
            'manutencao_preventiva'
        )
    ) NOT NULL,

    -- Título e descrição
    titulo TEXT NOT NULL,
    descricao TEXT,

    -- Data do alerta
    data_alerta DATE NOT NULL,
    data_vencimento DATE,

    -- Prioridade
    prioridade TEXT CHECK (prioridade IN ('baixa', 'media', 'alta', 'critica')) DEFAULT 'media',

    -- Status
    status_alerta TEXT CHECK (status_alerta IN ('pendente', 'visualizado', 'resolvido', 'ignorado')) DEFAULT 'pendente',

    -- Metadados
    criado_em TIMESTAMPTZ DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_alertas_ativo ON public.registro_alertas(ativo_id);
CREATE INDEX IF NOT EXISTS idx_alertas_status ON public.registro_alertas(status_alerta);

-- ==========================================
-- 7. Gatilho: Atualizar timestamp
-- ==========================================
CREATE OR REPLACE FUNCTION update_registro_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_registros_timestamp
BEFORE UPDATE ON public.registros
FOR EACH ROW
EXECUTE FUNCTION update_registro_timestamp();

-- ==========================================
-- 8. Gatilho: Validar Imutabilidade
-- ==========================================
-- Impede UPDATE/DELETE após período de carência (24h)
CREATE OR REPLACE FUNCTION validate_registro_imutability()
RETURNS TRIGGER AS $$
BEGIN
    -- Permite operações durante as primeiras 24h
    IF TG_OP = 'UPDATE' AND OLD.criado_em + interval '24 hours' > NOW() THEN
        RETURN NEW;
    END IF;

    -- Bloqueia após 24h
    IF TG_OP = 'UPDATE' AND OLD.criado_em + interval '24 hours' <= NOW() THEN
        RAISE EXCEPTION 'Registro é imutável após 24 horas da criação. Para correções, crie um novo registro.';
    END IF;

    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'Registros não podem ser excluídos. Crie um novo registro com status "cancelado" se necessário.';
    END IF;

    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trg_registro_imutabilidade
BEFORE UPDATE OR DELETE ON public.registros
FOR EACH ROW
EXECUTE FUNCTION validate_registro_imutabilidade();

-- ==========================================
-- 9. COMENTÁRIOS DE DOCUMENTAÇÃO
-- ==========================================
COMMENT ON TABLE public.registros IS 'Cofre digital de registros imutáveis de embarcações - histórico vitalício documentado';
COMMENT ON TABLE public.registro_evidencias IS 'Evidências fotográficas e documentais dos registros (fotos, recibos, laudos)';
COMMENT ON TABLE public.registro_pecas_trocadas IS 'Peças substituídas em cada serviço - histórico de componentes';
COMMENT ON TABLE public.registro_checklists IS 'Itens de checklist específicos por tipo de serviço';
COMMENT ON TABLE public.registros_audit_log IS 'Log completo de auditoria - toda ação é rastreada';
COMMENT ON TABLE public.registro_alertas IS 'Alertas e lembretes baseados em registros (vencimentos, recomendações)';

-- ==========================================
-- 10. VISÕES ÚTEIS
-- ==========================================
-- Visão: Histórico completo por ativo
CREATE OR REPLACE VIEW public.vw_historico_ativo AS
SELECT
    r.id,
    r.ativo_id,
    r.categoria,
    r.subcategoria,
    r.titulo,
    r.descricao,
    r.data_execucao,
    r.tecnico_nome,
    r.tecnico_empresa,
    r.hash_sha256,
    r.criado_em,
    COUNT(DISTINCT e.id) as total_evidencias,
    COUNT(DISTINCT p.id) as total_pecas
FROM public.registros r
LEFT JOIN public.registro_evidencias e ON r.id = e.registro_id
LEFT JOIN public.registro_pecas_trocadas p ON r.id = p.registro_id
GROUP BY r.id, r.ativo_id, r.categoria, r.subcategoria, r.titulo, r.descricao, r.data_execucao, r.tecnico_nome, r.tecnico_empresa, r.hash_sha256, r.criado_em;

-- ==========================================
-- 11. RLS - Row Level Security
-- ==========================================
ALTER TABLE public.registros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registro_evidencias ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registro_pecas_trocadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registro_checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registros_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.registro_alertas ENABLE ROW LEVEL SECURITY;

-- Políticas para registros
-- Admin: acesso total
CREATE POLICY "Admin total access" ON public.registros FOR ALL
USING (
    EXISTS (
        SELECT 1 FROM public.profiles
        WHERE profiles.id = auth.uid()
        AND profiles.user_role = 'admin'
    )
);

-- Marina Manager: vê registros das marinas que gerencia
CREATE POLICY "Marina managers view their records" ON public.registros FOR SELECT
USING (
    marina_id IN (
        SELECT marina_id FROM public.profiles
        WHERE profiles.id = auth.uid()
        AND profiles.user_role = 'marina_manager'
    )
    OR
    ativo_id IN (
        SELECT id FROM public.ativos WHERE owner_id = auth.uid()
    )
);

-- Marina Manager: cria registros
CREATE POLICY "Marina managers create records" ON public.registros FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.profiles
        WHERE profiles.id = auth.uid()
        AND profiles.user_role IN ('marina_manager', 'admin')
    )
);

-- Owner: vê registros dos próprios ativos
CREATE POLICY "Owners view their records" ON public.registros FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM public.ativos
        WHERE id = registros.ativo_id
        AND owner_id = auth.uid()
    )
);

-- Owner: cria registros para próprios ativos
CREATE POLICY "Owners create records for their assets" ON public.registros FOR INSERT
WITH CHECK (
    EXISTS (
        SELECT 1 FROM public.ativos
        WHERE id = (registros).ativo_id
        AND owner_id = auth.uid()
    )
    OR
    EXISTS (
        SELECT 1 FROM public.profiles
        WHERE profiles.id = auth.uid()
        AND profiles.user_role IN ('marina_manager', 'admin')
    )
);

-- ==========================================
-- 12. INSERIR DADOS DE EXEMPLO (Opcional)
-- ==========================================
-- Este bloco é opcional - remove se não quiser dados de exemplo
-- DELETE FROM public.registros WHERE id IN (SELECT id FROM public.registros WHERE tecnico_nome = 'Exemplo');

-- ==========================================
-- FIM DO SCRIPT
-- ==========================================
