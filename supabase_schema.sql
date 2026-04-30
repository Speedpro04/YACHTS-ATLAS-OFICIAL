-- YACHTS ATLAS - SUPABASE SCHEMA (B2B2C VERSION)
-- Marinas as Primary Clients
-- Version 2.0 - April 2026

-- ==========================================
-- 0. EXTENSIONS & SETUP
-- ==========================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Function for updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- ==========================================
-- 1. CORE: PROFILES & MARINAS
-- ==========================================

-- 1.1 Profiles (Extension of Auth.Users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE,
    nome TEXT,
    telefone TEXT,
    whatsapp TEXT,
    user_role TEXT DEFAULT 'user' CHECK (user_role IN ('admin', 'marina_manager', 'broker', 'insurance_agent', 'owner')),
    marina_id UUID, -- Linked if user belongs to a marina
    verified BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 1.2 Marinas (The B2B Client)
CREATE TABLE IF NOT EXISTS public.marinas (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    cnpj TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    website TEXT,
    logo_url TEXT,
    subscription_status TEXT DEFAULT 'trialing' CHECK (subscription_status IN ('active', 'past_due', 'canceled', 'trialing')),
    subscription_plan TEXT DEFAULT 'marina_basic' CHECK (subscription_plan IN ('marina_basic', 'marina_pro', 'marina_enterprise')),
    stripe_customer_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.profiles ADD CONSTRAINT fk_profiles_marina FOREIGN KEY (marina_id) REFERENCES public.marinas(id) ON DELETE SET NULL;

-- ==========================================
-- 2. ASSETS: ATIVOS (Vessels)
-- ==========================================

CREATE TABLE IF NOT EXISTS public.ativos (
    id TEXT PRIMARY KEY, -- YA-TIPO-ANO-XXXX
    marina_id UUID REFERENCES public.marinas(id) ON DELETE CASCADE NOT NULL,
    owner_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL, -- Individual owner
    tipo TEXT NOT NULL CHECK (tipo IN ('iate', 'lancha', 'veleiro', 'jetski', 'barco_pesca')),
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano_fabricacao INTEGER NOT NULL,
    comprimento_metres DECIMAL,
    comprimento_pes DECIMAL NOT NULL, -- Feet for categorization
    classificacao TEXT DEFAULT 'bronze' CHECK (classificacao IN ('bronze', 'silver', 'gold')),
    porte_categoria TEXT GENERATED ALWAYS AS (
        CASE 
            WHEN comprimento_pes <= 45 THEN 'compact'
            WHEN comprimento_pes > 45 AND comprimento_pes <= 79 THEN 'executive'
            ELSE 'superyacht'
        END
    ) STORED,
    progresso INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ativo' CHECK (status IN ('ativo', 'inativo', 'vendido', 'manutencao')),
    -- Additional Tech Specs
    largura DECIMAL,
    calado DECIMAL,
    material_casco TEXT,
    capacidade_passageiros INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 3. PRODUCTS: DOSSIÊS
-- ==========================================

CREATE TABLE IF NOT EXISTS public.dossies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    serial_number VARCHAR(30) UNIQUE NOT NULL,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    marina_id UUID REFERENCES public.marinas(id) ON DELETE CASCADE NOT NULL,
    requested_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    dossie_type TEXT NOT NULL CHECK (dossie_type IN ('venda', 'seguradora', 'armador')),
    porte_level TEXT NOT NULL CHECK (porte_level IN ('compact', 'executive', 'superyacht')),
    language VARCHAR(10) NOT NULL DEFAULT 'pt-BR',
    price_charged DECIMAL NOT NULL, -- $200, $400, or $600
    sha256_hash CHAR(64) NOT NULL,
    s3_url TEXT NOT NULL,
    status TEXT DEFAULT 'valid' CHECK (status IN ('valid', 'expired', 'revoked')),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    vessel_snapshot JSONB NOT NULL, -- Immutable snapshot at generation time
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 4. PARTNERS: BROKERS & INSURANCE
-- ==========================================

CREATE TABLE IF NOT EXISTS public.brokers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    profile_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE NOT NULL,
    company_name TEXT NOT NULL,
    license_number TEXT UNIQUE,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

CREATE TABLE IF NOT EXISTS public.insurance_companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    cnpj TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 5. DOCUMENTS & INTEGRITY
-- ==========================================

CREATE TABLE IF NOT EXISTS public.documentos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    marina_id UUID REFERENCES public.marinas(id) ON DELETE CASCADE NOT NULL,
    tipo TEXT NOT NULL,
    categoria TEXT NOT NULL,
    url_arquivo TEXT,
    storage_path TEXT NOT NULL,
    hash_sha256 TEXT NOT NULL,
    status TEXT DEFAULT 'pendente',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 6. AUDIT & LOGS
-- ==========================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL,
    user_id UUID REFERENCES auth.users ON DELETE SET NULL,
    ip_address TEXT,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 7. TRIGGERS
-- ==========================================

CREATE TRIGGER update_marinas_updated_at BEFORE UPDATE ON public.marinas FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_ativos_updated_at BEFORE UPDATE ON public.ativos FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- RLS (Basic setup, should be refined per role)
ALTER TABLE public.marinas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ativos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.dossies ENABLE ROW LEVEL SECURITY;
