-- YACHTS ATLAS - SUPABASE SCHEMA
-- Execute este script no SQL Editor do Supabase

-- 1. Tabela de Perfis (Extensão do Auth)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID REFERENCES auth.users ON DELETE CASCADE PRIMARY KEY,
    email TEXT UNIQUE,
    nome TEXT,
    telefone TEXT,
    whatsapp TEXT,
    role TEXT DEFAULT 'marina',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em profiles
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Perfis visíveis pelos próprios usuários" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Usuários podem atualizar próprios perfis" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- 2. Tabela de Ativos (Iates/Lanchas)
CREATE TABLE IF NOT EXISTS public.ativos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    usuario_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    tipo TEXT NOT NULL,
    marca TEXT NOT NULL,
    modelo TEXT NOT NULL,
    ano_fabricacao INTEGER NOT NULL,
    classificacao TEXT DEFAULT 'bronze',
    progresso INTEGER DEFAULT 0,
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
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em ativos
ALTER TABLE public.ativos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem apenas seus ativos" ON public.ativos
    FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Usuários inserem seus próprios ativos" ON public.ativos
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

CREATE POLICY "Usuários atualizam seus próprios ativos" ON public.ativos
    FOR UPDATE USING (auth.uid() = usuario_id);

-- 3. Tabela de Documentos (Dossiê 3 Níveis)
CREATE TABLE IF NOT EXISTS public.documentos (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ativo_id UUID REFERENCES public.ativos ON DELETE CASCADE NOT NULL,
    usuario_id UUID REFERENCES auth.users ON DELETE CASCADE NOT NULL,
    nome_arquivo TEXT NOT NULL,
    url_arquivo TEXT NOT NULL,
    tipo_documento TEXT NOT NULL, -- Ex: 'Seguro', 'Arrais', 'Título de Propriedade'
    nivel INTEGER NOT NULL CHECK (nivel IN (1, 2, 3)), -- Níveis do Dossiê
    status TEXT DEFAULT 'pendente', -- pendente, verificado, rejeitado
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Habilitar RLS em documentos
ALTER TABLE public.documentos ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Usuários veem apenas documentos de seus ativos" ON public.documentos
    FOR SELECT USING (auth.uid() = usuario_id);

CREATE POLICY "Usuários inserem documentos em seus ativos" ON public.documentos
    FOR INSERT WITH CHECK (auth.uid() = usuario_id);

-- 4. Função para atualizar progresso automaticamente (Opcional/Exemplo)
-- Você pode criar triggers depois para aumentar o % do progresso conforme documentos são enviados.
