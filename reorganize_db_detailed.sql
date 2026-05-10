-- REORGANIZAÇÃO DO BANCO DE DADOS - YACHTS ATLAS DETALHADO
-- Foco: Descrição Geral e Observações de Atenção (Detalhes de Atenção)

-- 1. Atualização da Tabela de Motores
ALTER TABLE engines ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE engines ADD COLUMN IF NOT EXISTS observation_alert TEXT;
COMMENT ON COLUMN engines.observation_alert IS 'Campo para detalhes de atenção crítica que aparecem em destaque no dossiê';

-- 2. Atualização da Tabela de Manutenção
ALTER TABLE maintenance_logs ADD COLUMN IF NOT EXISTS observation_alert TEXT;
ALTER TABLE maintenance_logs RENAME COLUMN servico TO description; -- Padronizando para description
COMMENT ON COLUMN maintenance_logs.observation_alert IS 'Detalhes de atenção para a próxima revisão ou pontos críticos detectados';

-- 3. Criação da Tabela de Inspeções Técnicas (Segurança, Elétrica, Pintura, Interior)
CREATE TABLE IF NOT EXISTS vessel_inspections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ativo_id UUID REFERENCES ativos(id) ON DELETE CASCADE,
    category TEXT NOT NULL, -- 'seguranca', 'eletrica', 'pintura', 'interior'
    description TEXT,
    observation_alert TEXT,
    items_json JSONB DEFAULT '{}'::jsonb, -- Armazena os checklists (checkboxes)
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Habilitar RLS (Row Level Security) para a nova tabela
ALTER TABLE vessel_inspections ENABLE ROW LEVEL SECURITY;

-- 5. Políticas de Acesso
-- Gestores podem tudo
CREATE POLICY "Gestores podem gerenciar inspeções" 
ON vessel_inspections FOR ALL 
USING (auth.uid() IN (SELECT user_id FROM profiles WHERE role = 'marina_manager'));

-- Proprietários podem apenas ver
CREATE POLICY "Proprietários podem ver suas inspeções" 
ON vessel_inspections FOR SELECT 
USING (auth.uid() IN (SELECT owner_id FROM ativos WHERE id = vessel_inspections.ativo_id));

-- 6. Trigger para Atualizar o UpdatedAt
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vessel_inspections_updated_at
    BEFORE UPDATE ON vessel_inspections
    FOR EACH ROW
    EXECUTE PROCEDURE update_updated_at_column();

-- 7. Comentários para documentação
COMMENT ON TABLE vessel_inspections IS 'Armazena detalhes técnicos e alertas de atenção para todas as categorias de inspeção do ativo';
