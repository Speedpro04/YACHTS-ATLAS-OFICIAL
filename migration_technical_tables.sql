-- ==========================================
-- YACHTS ATLAS — MIGRAÇÃO: Tabelas Técnicas
-- Cole este SQL no Editor SQL do Supabase
-- ==========================================

-- ==========================================
-- 1. MOTORES (engines)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.engines (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    posicao TEXT DEFAULT 'principal' CHECK (posicao IN ('principal', 'auxiliar', 'gerador')),
    fabricante TEXT NOT NULL,
    modelo TEXT NOT NULL,
    potencia_hp INTEGER NOT NULL,
    horas_uso DECIMAL DEFAULT 0,
    combustivel TEXT DEFAULT 'diesel' CHECK (combustivel IN ('diesel', 'gasolina', 'eletrico', 'hibrido')),
    ano_instalacao INTEGER,
    numero_serie TEXT,
    ultima_revisao DATE,
    status TEXT DEFAULT 'operacional' CHECK (status IN ('operacional', 'manutencao', 'substituir')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 2. HISTÓRICO DE MANUTENÇÃO
-- ==========================================
CREATE TABLE IF NOT EXISTS public.maintenance_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    marina_id UUID REFERENCES public.marinas(id) ON DELETE SET NULL,
    data_servico DATE NOT NULL,
    servico TEXT NOT NULL,
    descricao TEXT,
    responsavel TEXT NOT NULL,
    empresa TEXT,
    valor_usd DECIMAL,
    nota_fiscal TEXT,
    status TEXT DEFAULT 'concluido' CHECK (status IN ('concluido', 'pendente', 'agendado', 'cancelado')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 3. INSPEÇÕES TÉCNICAS (END / Ultrassom)
-- ==========================================
CREATE TABLE IF NOT EXISTS public.inspections (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id TEXT REFERENCES public.ativos(id) ON DELETE CASCADE NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('ultrassom', 'visual', 'eletrica', 'mecanica', 'seguranca', 'completa')),
    data_inspecao DATE NOT NULL,
    inspetor_nome TEXT NOT NULL,
    inspetor_registro TEXT,
    metodologia TEXT,
    resultado TEXT NOT NULL CHECK (resultado IN ('aprovado', 'aprovado_ressalvas', 'reprovado')),
    integridade_percentual DECIMAL,
    observacoes TEXT,
    laudo_url TEXT,
    laudo_hash_sha256 TEXT,
    validade DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- ==========================================
-- 4. TRIGGERS DE UPDATED_AT
-- ==========================================
CREATE TRIGGER update_engines_updated_at
    BEFORE UPDATE ON public.engines
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- ==========================================
-- 5. RLS (Segurança)
-- ==========================================
ALTER TABLE public.engines ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.maintenance_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.inspections ENABLE ROW LEVEL SECURITY;

-- Marina managers gerenciam os dados dos seus ativos
CREATE POLICY "Marina manages engines" ON public.engines FOR ALL USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE marina_id IN (
        SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
    ))
);

CREATE POLICY "Marina manages maintenance" ON public.maintenance_logs FOR ALL USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE marina_id IN (
        SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
    ))
);

CREATE POLICY "Marina manages inspections" ON public.inspections FOR ALL USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE marina_id IN (
        SELECT marina_id FROM public.profiles WHERE profiles.id = auth.uid() AND user_role = 'marina_manager'
    ))
);

-- Proprietários visualizam dados dos seus barcos
CREATE POLICY "Owners view engines" ON public.engines FOR SELECT USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE owner_id = auth.uid())
);

CREATE POLICY "Owners view maintenance" ON public.maintenance_logs FOR SELECT USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE owner_id = auth.uid())
);

CREATE POLICY "Owners view inspections" ON public.inspections FOR SELECT USING (
    ativo_id IN (SELECT id FROM public.ativos WHERE owner_id = auth.uid())
);

-- ==========================================
-- 6. ÍNDICES PARA PERFORMANCE
-- ==========================================
CREATE INDEX idx_engines_ativo ON public.engines(ativo_id);
CREATE INDEX idx_maintenance_ativo ON public.maintenance_logs(ativo_id);
CREATE INDEX idx_maintenance_data ON public.maintenance_logs(data_servico DESC);
CREATE INDEX idx_inspections_ativo ON public.inspections(ativo_id);
CREATE INDEX idx_inspections_data ON public.inspections(data_inspecao DESC);
