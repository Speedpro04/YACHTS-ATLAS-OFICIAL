-- migration_high_ticket.sql

-- ==========================================
-- Yachts Atlas — High‑Ticket Technical Tables
-- ==========================================

-- 1. yacht_components (componentes físicos críticos)
CREATE TABLE IF NOT EXISTS public.yacht_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    categoria TEXT NOT NULL CHECK (
        categoria IN (
            'seguranca_salvamento',
            'mecanica_propulsao',
            'eletrica_navegacao',
            'conforto_hotel',
            'integridade_fisica'
        )
    ),
    subcategoria TEXT NOT NULL CHECK (
        subcategoria IN (
            -- segurança & salvamento
            'extintor', 'balsa_salvavidas', 'pirotecnia_sinalizadores', 'epirb_sart', 'colete_salvavidas',
            -- mecânica avançada
            'motor_principal', 'motor_gerador', 'sistema_arrefecimento', 'anodo_sacrificio', 'transmissao',
            -- elétrica & navegação
            'radar_sonar', 'gps_chartplotter', 'banco_baterias', 'comunicacao_vhf_ais', 'shore_power',
            -- conforto / hotel
            'climatizacao_chiller', 'eletrodomestico_bordo', 'agua_saneamento_dessalinizador', 'entretenimento_som',
            -- integridade física
            'casco_gelcoat', 'deck_teca', 'vidros_vigias', 'moveis_estofados_marcenaria'
        )
    ),
    nome VARCHAR(255) NOT NULL,
    marca VARCHAR(150),
    modelo VARCHAR(150),
    numero_serie VARCHAR(100),
    data_fabricacao DATE,
    data_instalacao DATE,
    data_ultima_revisao DATE,
    data_proxima_revisao DATE NOT NULL,
    qr_code_uid UUID UNIQUE DEFAULT gen_random_uuid(),
    status VARCHAR(30) DEFAULT 'operacional' CHECK (status IN ('operacional','manutencao_pendente','vencido','critico')),
    especificacoes_tecnicas JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_yacht_components_ativo ON public.yacht_components(ativo_id);
CREATE INDEX IF NOT EXISTS idx_yacht_components_qr ON public.yacht_components(qr_code_uid);
CREATE INDEX IF NOT EXISTS idx_yacht_components_status ON public.yacht_components(status);
CREATE INDEX IF NOT EXISTS idx_yacht_components_proxima_revisao ON public.yacht_components(data_proxima_revisao);

-- 2. manutencao_registros (registro de manutenção e inspeção)
CREATE TABLE IF NOT EXISTS public.manutencao_registros (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    component_id UUID REFERENCES public.yacht_components(id) ON DELETE CASCADE,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    executado_por UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    tipo_manutencao VARCHAR(50) DEFAULT 'preventiva' CHECK (tipo_manutencao IN ('preventiva','corretiva','inspecao_obrigatoria','calibracao')),
    prestador_nome VARCHAR(255) NOT NULL,
    prestador_cnpj VARCHAR(20),
    tecnico_nome VARCHAR(255) NOT NULL,
    tecnico_registro VARCHAR(50),
    descricao TEXT NOT NULL,
    custo DECIMAL(12,2),
    moeda VARCHAR(3) DEFAULT 'BRL',
    horas_motor INTEGER,
    data_servico DATE NOT NULL,
    assinatura_digital_hash TEXT,
    assinatura_metadados JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_manutencao_componente ON public.manutencao_registros(component_id);
CREATE INDEX IF NOT EXISTS idx_manutencao_ativo ON public.manutencao_registros(ativo_id);

-- 3. geotagged_media (fotos com GPS e timestamp)
CREATE TABLE IF NOT EXISTS public.geotagged_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    manutencao_id UUID REFERENCES public.manutencao_registros(id) ON DELETE CASCADE,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    tipo_evidencia VARCHAR(30) CHECK (tipo_evidencia IN ('antes','depois','etiqueta_qr','laudo_assinado')),
    storage_path TEXT NOT NULL,
    url_publica TEXT,
    hash_sha256 CHAR(64) NOT NULL,
    latitude DECIMAL(10,8) NOT NULL,
    longitude DECIMAL(11,8) NOT NULL,
    foto_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    dispositivo_modelo VARCHAR(150),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_geotagged_manutencao ON public.geotagged_media(manutencao_id);
CREATE INDEX IF NOT EXISTS idx_geotagged_ativo ON public.geotagged_media(ativo_id);

-- 4. cryptographic_seals (hash chain dos dossiês)
CREATE TABLE IF NOT EXISTS public.cryptographic_seals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossie_id UUID REFERENCES public.dossies(id) ON DELETE CASCADE NOT NULL,
    sha256_hash CHAR(64) UNIQUE NOT NULL,
    hash_anterior CHAR(64) NOT NULL,
    bloco_indice BIGSERIAL NOT NULL,
    assinatura_plataforma TEXT NOT NULL,
    timestamp_carimbo TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_seals_dossie ON public.cryptographic_seals(dossie_id);
CREATE INDEX IF NOT EXISTS idx_seals_hash ON public.cryptographic_seals(sha256_hash);

-- 5. insurance_ready_reports (score de conformidade para seguradoras)
CREATE TABLE IF NOT EXISTS public.insurance_ready_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    dossie_id UUID REFERENCES public.dossies(id) ON DELETE CASCADE,
    compliance_score INTEGER NOT NULL CHECK (compliance_score >= 0 AND compliance_score <= 100),
    allianz_status VARCHAR(30) DEFAULT 'non_compliant' CHECK (allianz_status IN ('compliant','warnings','non_compliant')),
    zurich_status VARCHAR(30) DEFAULT 'non_compliant' CHECK (zurich_status IN ('compliant','warnings','non_compliant')),
    bradesco_status VARCHAR(30) DEFAULT 'non_compliant' CHECK (bradesco_status IN ('compliant','warnings','non_compliant')),
    detalhes_conformidade JSONB NOT NULL DEFAULT '{}'::jsonb,
    gerado_em TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_insurance_ativo ON public.insurance_ready_reports(ativo_id);

-- ==========================================
-- Row Level Security (RLS) Policies
-- ==========================================

ALTER TABLE public.yacht_components ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.manutencao_registros ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.geotagged_media ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cryptographic_seals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.insurance_ready_reports ENABLE ROW LEVEL SECURITY;

-- Marina managers manage components & related data
CREATE POLICY "marina_manage_components"
ON public.yacht_components FOR ALL USING (
    ativo_id IN (
        SELECT id FROM public.ativos WHERE marina_id IN (
            SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
        )
    )
);

CREATE POLICY "owner_view_components"
ON public.yacht_components FOR SELECT USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE owner_id = auth.uid())
);

-- Manutenção (maintenance) policies
CREATE POLICY "marina_manage_maintenance"
ON public.manutencao_registros FOR ALL USING (
    ativo_id IN (
        SELECT id FROM public.ativos WHERE marina_id IN (
            SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
        )
    )
);

CREATE POLICY "owner_view_maintenance"
ON public.manutencao_registros FOR SELECT USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE owner_id = auth.uid())
);

-- Geotagged media policies
CREATE POLICY "marina_manage_media"
ON public.geotagged_media FOR ALL USING (
    ativo_id IN (
        SELECT id FROM public.ativos WHERE marina_id IN (
            SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
        )
    )
);

CREATE POLICY "owner_view_media"
ON public.geotagged_media FOR SELECT USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE owner_id = auth.uid())
);

-- Cryptographic seals are read‑only (only system can insert)
CREATE POLICY "read_seals" ON public.cryptographic_seals FOR SELECT USING (true);
CREATE POLICY "no_update_seals" ON public.cryptographic_seals FOR UPDATE USING (false);
CREATE POLICY "no_delete_seals" ON public.cryptographic_seals FOR DELETE USING (false);

-- Insurance reports read‑only for owners & managers
CREATE POLICY "read_insurance_reports" ON public.insurance_ready_reports FOR SELECT USING (
    ativo_id IN (
        SELECT id FROM public.ativos WHERE owner_id = auth.uid()
        UNION ALL
        SELECT id FROM public.ativos WHERE marina_id IN (
            SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
        )
    )
);

-- ==========================================
-- Triggers – controle de status baseado na data da próxima revisão
-- ==========================================

CREATE OR REPLACE FUNCTION public.check_component_revisions()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.data_proxima_revisao < CURRENT_DATE THEN
        NEW.status := 'vencido';
    ELSIF NEW.data_proxima_revisao <= (CURRENT_DATE + INTERVAL '30 days') THEN
        NEW.status := 'manutencao_pendente';
    ELSE
        NEW.status := 'operacional';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_yacht_components_revision_check
BEFORE INSERT OR UPDATE ON public.yacht_components
FOR EACH ROW EXECUTE FUNCTION public.check_component_revisions();

-- ==========================================
-- End of migration_high_ticket.sql
-- ==========================================
