-- YACHTS ATLAS - SUPABASE SCHEMA
-- Execute este script no SQL Editor do Supabase
-- Execute em ordem sequencial para garantir que todas as tabelas sejam criadas

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. Tabela de Perfis (Extensão do Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE,
    nome TEXT,
    telefone TEXT,
    whatsapp TEXT,
    user_role TEXT DEFAULT 'user', -- user, marina, insurance, broker, admin
    stripe_customer_id TEXT,
    subscription_plan TEXT, -- free, marina, enterprise
    subscription_status TEXT, -- active, past_due, canceled, trialing
    subscription_ends_at TIMESTAMP WITH TIME ZONE,
    company_name TEXT, -- Nome da empresa (marina, seguradora, broker)
    company_type TEXT, -- marina, insurance, broker
    verified BOOLEAN DEFAULT false,
    verification_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Perfis visíveis pelos próprios usuários" ON public.profiles;
DROP POLICY IF EXISTS "Usuários podem atualizar próprios perfis" ON public.profiles;

CREATE POLICY "Perfis visíveis pelos próprios usuários" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Usuários podem atualizar próprios perfis" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- 2. Tabela de Ativos (Iates/Lanchas)
CREATE TABLE IF NOT EXISTS public.ativos (
    id TEXT PRIMARY KEY, -- ID customizado como YA-TIPO-ANO-XXXX
    usuario_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    tipo TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano_fabricacao INTEGER NOT NULL,
    classificacao TEXT DEFAULT 'bronze',
    progresso INTEGER DEFAULT 0,
    status TEXT DEFAULT 'ativo',
    -- Dados técnicos
    comprimento DECIMAL,
    largura DECIMAL,
    calado DECIMAL,
    material_casco TEXT,
    capacidade_passageiros INTEGER,
    modelo_motor TEXT,
    potencia_motor INTEGER,
    num_motores INTEGER,
    tipo_combustivel TEXT,
    num_cabines INTEGER,
    capacidade_tanque INTEGER,
    -- Documentação
    nome_reg TEXT,
    rgp TEXT,
    vin TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em ativos
ALTER TABLE public.ativos ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem apenas seus ativos" ON public.ativos;
DROP POLICY IF EXISTS "Usuários inserem seus próprios ativos" ON public.ativos;
DROP POLICY IF EXISTS "Usuários atualizam seus próprios ativos" ON public.ativos;

CREATE POLICY "Usuários veem apenas seus ativos" ON public.ativos
    FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Usuários inserem seus próprios ativos" ON public.ativos
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Usuários atualizam seus próprios ativos" ON public.ativos
    FOR UPDATE USING (auth.uid() = usuario_id);

CREATE POLICY "Usuários deletam seus próprios ativos" ON public.ativos
    FOR DELETE USING (auth.uid() = usuario_id);

-- 3. Tabela de Documentos (Dossiê 3 Níveis)
CREATE TABLE IF NOT EXISTS public.documentos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos ON DELETE CASCADE NOT NULL,
    usuario_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    nome_arquivo TEXT NOT NULL,
    url_arquivo TEXT,
    storage_path TEXT NOT NULL,
    tipo TEXT NOT NULL, -- Tipo do documento
    categoria TEXT NOT NULL, -- Categoria do documento
    nivel INTEGER NOT NULL CHECK (nivel IN (1, 2, 3)), -- Níveis do Dossiê
    status TEXT DEFAULT 'pendente', -- pendente, verificado, rejeitado
    -- Integridade e Hash
    hash_sha256 TEXT NOT NULL,
    hash_anterior TEXT,
    tamanho_bytes BIGINT NOT NULL,
    mime_type TEXT,
    uploaded_by UUID REFERENCES auth.users ON DELETE SET NULL,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    validado_em TIMESTAMP WITH TIME ZONE,
    s3_version_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em documentos
ALTER TABLE public.documentos ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem apenas documentos de seus ativos" ON public.documentos;
DROP POLICY IF EXISTS "Usuários inserem documentos em seus ativos" ON public.documentos;

CREATE POLICY "Usuários veem apenas documentos de seus ativos" ON public.documentos
    FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Usuários inserem documentos em seus ativos" ON public.documentos
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

-- 4. Tabela de Auditoria (Rastreamento Completo)
CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    action TEXT NOT NULL, -- login, logout, document_upload, document_download, etc.
    user_id UUID REFERENCES auth.users ON DELETE SET NULL,
    ip_address TEXT NOT NULL,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    severity TEXT DEFAULT 'info', -- info, warning, error, critical
    success BOOLEAN DEFAULT true,
    error_message TEXT,
    details JSONB DEFAULT '{}',
    location JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON public.audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON public.audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp ON public.audit_logs(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_severity ON public.audit_logs(severity);
CREATE INDEX IF NOT EXISTS idx_audit_logs_ip_address ON public.audit_logs(ip_address);

-- Habilitar RLS em audit_logs
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem seus próprios logs" ON public.audit_logs;
DROP POLICY IF EXISTS "Admins veem todos os logs" ON public.audit_logs;

-- Política: Usuários podem ver seus próprios logs
CREATE POLICY "Usuários veem seus próprios logs" ON public.audit_logs
    FOR SELECT USING (auth.uid() = user_id);

-- Política: Apenas admin pode ver todos os logs
CREATE POLICY "Admins veem todos os logs" ON public.audit_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND user_role = 'admin'
        )
    );

-- 5. Tabela de Integridade (Verificações de Hash)
CREATE TABLE IF NOT EXISTS public.integridade_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    documento_id UUID REFERENCES public.documentos ON DELETE CASCADE NOT NULL,
    usuario_id UUID REFERENCES auth.users ON DELETE SET NULL,
    hash_esperado TEXT NOT NULL,
    hash_atual TEXT NOT NULL,
    valido BOOLEAN NOT NULL,
    verificado_em TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    metadata JSONB DEFAULT '{}'
);

-- Índices para integridade
CREATE INDEX IF NOT EXISTS idx_integridade_documento_id ON public.integridade_logs(documento_id);
CREATE INDEX IF NOT EXISTS idx_integridade_usuario_id ON public.integridade_logs(usuario_id);
CREATE INDEX IF NOT EXISTS idx_integridade_verificado_em ON public.integridade_logs(verificado_em DESC);

-- Habilitar RLS em integridade_logs
ALTER TABLE public.integridade_logs ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem verificações de seus documentos" ON public.integridade_logs;

CREATE POLICY "Usuários veem verificações de seus documentos" ON public.integridade_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.documentos d
            WHERE d.id = integridade_logs.documento_id 
            AND d.usuario_id = auth.uid()
        )
    );

-- 6. Tabela de Pagamentos (Stripe)
CREATE TABLE IF NOT EXISTS public.payments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    stripe_payment_intent_id TEXT UNIQUE,
    stripe_checkout_session_id TEXT UNIQUE,
    stripe_subscription_id TEXT,
    amount DECIMAL NOT NULL,
    currency TEXT DEFAULT 'usd',
    status TEXT DEFAULT 'pending', -- pending, completed, failed, refunded
    payment_type TEXT NOT NULL, -- subscription, dossier
    plan_type TEXT, -- free, pro, marina
    dossier_level TEXT, -- compact, executive, superyacht
    ativo_id TEXT REFERENCES public.ativos ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para pagamentos
CREATE INDEX IF NOT EXISTS idx_payments_usuario_id ON public.payments(usuario_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_payment_intent_id ON public.payments(stripe_payment_intent_id);
CREATE INDEX IF NOT EXISTS idx_payments_stripe_subscription_id ON public.payments(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON public.payments(status);

-- Habilitar RLS em payments
ALTER TABLE public.payments ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem seus próprios pagamentos" ON public.payments;

CREATE POLICY "Usuários veem seus próprios pagamentos" ON public.payments
    FOR SELECT USING (auth.uid() = usuario_id);

-- 7. Tabela de Assinaturas (Stripe)
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    stripe_subscription_id TEXT UNIQUE NOT NULL,
    stripe_customer_id TEXT NOT NULL,
    plan_type TEXT NOT NULL, -- free, pro, marina
    status TEXT NOT NULL, -- active, past_due, canceled, incomplete, trialing
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    cancel_at_period_end BOOLEAN DEFAULT false,
    canceled_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para assinaturas
CREATE INDEX IF NOT EXISTS idx_subscriptions_usuario_id ON public.subscriptions(usuario_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe_subscription_id ON public.subscriptions(stripe_subscription_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);

-- Habilitar RLS em subscriptions
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem suas próprias assinaturas" ON public.subscriptions;

CREATE POLICY "Usuários veem suas próprias assinaturas" ON public.subscriptions
    FOR SELECT USING (auth.uid() = usuario_id);

-- 8. Função para atualizar progresso automaticamente
CREATE OR REPLACE FUNCTION public.atualizar_progresso_ativo()
RETURNS TRIGGER AS $$
BEGIN
    -- Calcular progresso baseado em documentos verificados
    UPDATE public.ativos
    SET progresso = (
        SELECT COALESCE(
            ROUND(
                (COUNT(*) FILTER (WHERE status = 'verificado')::NUMERIC / 
                NULLIF(COUNT(*), 0)) * 100
            ), 0
        )
        FROM public.documentos
        WHERE ativo_id = NEW.ativo_id
    ),
    updated_at = timezone('utc'::text, now())
    WHERE id = NEW.ativo_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar progresso quando documento é inserido ou atualizado
DROP TRIGGER IF EXISTS trigger_atualizar_progresso ON public.documentos;
CREATE TRIGGER trigger_atualizar_progresso
    AFTER INSERT OR UPDATE ON public.documentos
    FOR EACH ROW
    EXECUTE FUNCTION public.atualizar_progresso_ativo();

-- 9. Função para criar perfil automaticamente
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, nome, telefone, whatsapp)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'nome',
        NEW.raw_user_meta_data->>'telefone',
        NEW.raw_user_meta_data->>'whatsapp'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger para criar perfil automaticamente
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- 10. Tabela de Seguradoras (Parceiras)
CREATE TABLE IF NOT EXISTS public.insurance_companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name TEXT NOT NULL,
    cnpj TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'BR',
    website TEXT,
    logo_url TEXT,
    status TEXT DEFAULT 'active', -- active, inactive, pending
    api_key TEXT UNIQUE,
    webhook_url TEXT,
    commission_rate DECIMAL DEFAULT 0.10, -- 10% comissão padrão
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para seguradoras
CREATE INDEX IF NOT EXISTS idx_insurance_companies_status ON public.insurance_companies(status);
CREATE INDEX IF NOT EXISTS idx_insurance_companies_api_key ON public.insurance_companies(api_key);

-- Habilitar RLS em insurance_companies
ALTER TABLE public.insurance_companies ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Admins gerenciam seguradoras" ON public.insurance_companies;

CREATE POLICY "Admins gerenciam seguradoras" ON public.insurance_companies
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND user_role = 'admin'
        )
    );

-- 11. Tabela de Brokers (Multiplicadores)
CREATE TABLE IF NOT EXISTS public.brokers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    company_name TEXT NOT NULL,
    license_number TEXT UNIQUE,
    email TEXT,
    phone TEXT,
    whatsapp TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    country TEXT DEFAULT 'BR',
    website TEXT,
    logo_url TEXT,
    status TEXT DEFAULT 'active', -- active, inactive, pending, suspended
    commission_rate DECIMAL DEFAULT 0.15, -- 15% comissão padrão
    total_deals INTEGER DEFAULT 0,
    total_value DECIMAL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para brokers
CREATE INDEX IF NOT EXISTS idx_brokers_user_id ON public.brokers(user_id);
CREATE INDEX IF NOT EXISTS idx_brokers_status ON public.brokers(status);
CREATE INDEX IF NOT EXISTS idx_brokers_license_number ON public.brokers(license_number);

-- Habilitar RLS em brokers
ALTER TABLE public.brokers ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Brokers veem seus próprios dados" ON public.brokers;
DROP POLICY IF EXISTS "Admins gerenciam brokers" ON public.brokers;

CREATE POLICY "Brokers veem seus próprios dados" ON public.brokers
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Admins gerenciam brokers" ON public.brokers
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND user_role = 'admin'
        )
    );

-- 12. Tabela de Integrações Seguradoras
CREATE TABLE IF NOT EXISTS public.insurance_integrations (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos ON DELETE CASCADE NOT NULL,
    insurance_company_id UUID REFERENCES public.insurance_companies ON DELETE SET NULL NOT NULL,
    policy_number TEXT UNIQUE,
    policy_type TEXT, -- comprehensive, liability, hull
    coverage_amount DECIMAL,
    premium_amount DECIMAL,
    deductible_amount DECIMAL,
    start_date DATE,
    end_date DATE,
    status TEXT DEFAULT 'active', -- active, expired, cancelled, pending
    dossier_required BOOLEAN DEFAULT true,
    dossier_verified BOOLEAN DEFAULT false,
    dossier_verified_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para integrações de seguros
CREATE INDEX IF NOT EXISTS idx_insurance_integrations_ativo_id ON public.insurance_integrations(ativo_id);
CREATE INDEX IF NOT EXISTS idx_insurance_integrations_insurance_company_id ON public.insurance_integrations(insurance_company_id);
CREATE INDEX IF NOT EXISTS idx_insurance_integrations_policy_number ON public.insurance_integrations(policy_number);
CREATE INDEX IF NOT EXISTS idx_insurance_integrations_status ON public.insurance_integrations(status);

-- Habilitar RLS em insurance_integrations
ALTER TABLE public.insurance_integrations ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Usuários veem integrações de seus ativos" ON public.insurance_integrations;
DROP POLICY IF EXISTS "Seguradoras veem integrações" ON public.insurance_integrations;

CREATE POLICY "Usuários veem integrações de seus ativos" ON public.insurance_integrations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.ativos a
            WHERE a.id = insurance_integrations.ativo_id 
            AND a.usuario_id = auth.uid()
        )
    );

CREATE POLICY "Seguradoras veem integrações" ON public.insurance_integrations
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles p
            WHERE p.id = auth.uid() AND p.user_role = 'insurance'
        )
    );

-- 13. Tabela de Transações Brokers
CREATE TABLE IF NOT EXISTS public.broker_deals (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    broker_id UUID REFERENCES public.brokers ON DELETE CASCADE NOT NULL,
    ativo_id TEXT REFERENCES public.ativos ON DELETE SET NULL,
    seller_id UUID REFERENCES auth.users ON DELETE SET NULL,
    buyer_id UUID REFERENCES auth.users ON DELETE SET NULL,
    deal_type TEXT NOT NULL, -- sale, purchase, lease
    deal_value DECIMAL,
    commission_rate DECIMAL,
    commission_amount DECIMAL,
    dossier_required BOOLEAN DEFAULT true,
    dossier_level TEXT, -- compact, executive, superyacht
    dossier_purchased BOOLEAN DEFAULT false,
    dossier_purchased_at TIMESTAMP WITH TIME ZONE,
    status TEXT DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    start_date DATE,
    close_date DATE,
    notes TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Índices para transações de brokers
CREATE INDEX IF NOT EXISTS idx_broker_deals_broker_id ON public.broker_deals(broker_id);
CREATE INDEX IF NOT EXISTS idx_broker_deals_ativo_id ON public.broker_deals(ativo_id);
CREATE INDEX IF NOT EXISTS idx_broker_deals_status ON public.broker_deals(status);
CREATE INDEX IF NOT EXISTS idx_broker_deals_close_date ON public.broker_deals(close_date);

-- Habilitar RLS em broker_deals
ALTER TABLE public.broker_deals ENABLE ROW LEVEL SECURITY;

-- Drop policies if they exist
DROP POLICY IF EXISTS "Brokers veem suas próprias transações" ON public.broker_deals;
DROP POLICY IF EXISTS "Admins veem todas as transações" ON public.broker_deals;

CREATE POLICY "Brokers veem suas próprias transações" ON public.broker_deals
    FOR SELECT USING (auth.uid() = (
        SELECT user_id FROM public.brokers WHERE id = broker_deals.broker_id
    ));

CREATE POLICY "Admins veem todas as transações" ON public.broker_deals
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.profiles 
            WHERE id = auth.uid() AND user_role = 'admin'
        )
    );

-- 14. Triggers para updated_at nas novas tabelas
DROP TRIGGER IF EXISTS update_insurance_companies_updated_at ON public.insurance_companies;
CREATE TRIGGER update_insurance_companies_updated_at
    BEFORE UPDATE ON public.insurance_companies
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_brokers_updated_at ON public.brokers;
CREATE TRIGGER update_brokers_updated_at
    BEFORE UPDATE ON public.brokers
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_insurance_integrations_updated_at ON public.insurance_integrations;
CREATE TRIGGER update_insurance_integrations_updated_at
    BEFORE UPDATE ON public.insurance_integrations
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_broker_deals_updated_at ON public.broker_deals;
CREATE TRIGGER update_broker_deals_updated_at
    BEFORE UPDATE ON public.broker_deals
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();
