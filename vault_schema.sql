-- ==========================================
-- YACHTS ATLAS - VAULT DATABASE SCHEMA
-- ==========================================
-- Description: Isolated Air-Gapped Database for Digital Dossiers (Zero-Trace Protocol)

-- 1. ENUMS
CREATE TYPE dossier_tier AS ENUM ('compact', 'executive', 'superyacht');
CREATE TYPE dossier_status AS ENUM ('draft', 'pending_verification', 'active', 'archived');
CREATE TYPE inspection_type AS ENUM ('ultrasound', 'structural', 'survey', 'osmosis');

-- 2. DOSSIERS (Tabela Central)
CREATE TABLE dossiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    marina_id UUID NOT NULL, -- Soft link to the Core DB
    owner_id UUID,           -- Soft link to the Core DB User (can be null if not yet assigned)
    tier dossier_tier NOT NULL DEFAULT 'compact',
    status dossier_status NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. VESSEL IDENTITY (Identidade da Embarcação)
CREATE TABLE vessel_identity (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    registration_number TEXT,
    flag TEXT,
    imo_number TEXT,
    hull_material TEXT,
    year_built INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. TECHNICAL SPECS (Especificações Técnicas)
CREATE TABLE technical_specs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    length_ft NUMERIC NOT NULL,
    beam_ft NUMERIC,
    draft_ft NUMERIC,
    engines JSONB DEFAULT '[]'::jsonb, -- Array of engine objects: { manufacturer, model, hp, hours }
    generators JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. MAINTENANCE LOGS (Histórico de Manutenção)
CREATE TABLE maintenance_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    service_date DATE NOT NULL,
    service_type TEXT NOT NULL, -- e.g., 'Preventive', 'Corrective', 'Upgrade'
    description TEXT NOT NULL,
    performed_by TEXT NOT NULL,
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. TECHNICAL INSPECTIONS (Laudos e END)
CREATE TABLE technical_inspections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    inspection_date DATE NOT NULL,
    inspection_type inspection_type NOT NULL,
    inspector_name TEXT NOT NULL,
    credentials TEXT,
    report_url TEXT, -- Secure storage path
    result TEXT, -- e.g., 'Approved', 'Attention', 'Critical'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. VAULT DOCUMENTS (Documentação Legal e Fiscal)
CREATE TABLE vault_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dossier_id UUID NOT NULL REFERENCES dossiers(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL, -- e.g., 'Registry', 'Insurance', 'Taxes'
    file_url TEXT NOT NULL, -- Secure storage path
    expiry_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- ROW LEVEL SECURITY (RLS)
-- ==========================================
ALTER TABLE dossiers ENABLE ROW LEVEL SECURITY;
ALTER TABLE vessel_identity ENABLE ROW LEVEL SECURITY;
ALTER TABLE technical_specs ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE technical_inspections ENABLE ROW LEVEL SECURITY;
ALTER TABLE vault_documents ENABLE ROW LEVEL SECURITY;

-- Note: Since this is an isolated Vault, access control logic will be governed by
-- the Edge Functions via Service Role Keys, or tightly coupled RLS if accessed directly.
-- For now, default deny-all is enforced by enabling RLS.
