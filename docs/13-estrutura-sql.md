# Yachts Atlas — Estrutura SQL (DDL)

## Criar Extensões

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
```

---

## 1. Tabela: usuarios

```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    whatsapp VARCHAR(20),
    role VARCHAR(20) DEFAULT 'dono' CHECK (role IN ('dono', 'admin', 'visualizador')),
    avatar_url TEXT,
    email_verificado BOOLEAN DEFAULT FALSE,
    whatsapp_verificado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_usuarios_email ON usuarios(email);
CREATE INDEX idx_usuarios_role ON usuarios(role);
```

---

## 2. Tabela: ativos

```sql
CREATE TABLE ativos (
    id VARCHAR(50) PRIMARY KEY, -- Format: YA-IATE-2024-0001
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(20) NOT NULL CHECK (tipo IN ('iate', 'lancha', 'veleiro', 'jetski', 'barco_pesca')),
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano_fabricacao INTEGER NOT NULL,
    comprimento DECIMAL(5,2),
    largura DECIMAL(5,2),
    calado DECIMAL(5,2),
    material_casco VARCHAR(20) CHECK (material_casco IN ('fibra', 'aluminio', 'madeira', 'aco')),
    capacidade_passageiros INTEGER,
    modelo_motor VARCHAR(100),
    potencia_motor INTEGER,
    num_motores INTEGER,
    tipo_combustivel VARCHAR(20) CHECK (tipo_combustivel IN ('diesel', 'gasolina')),
    num_cabines INTEGER,
    capacidade_tanque INTEGER,
    nome_reg VARCHAR(100),
    rgp VARCHAR(50), -- Registro Geral de Barcos
    vin VARCHAR(50),
    classificacao VARCHAR(20) DEFAULT 'bronze' CHECK (classificacao IN ('bronze', 'silver', 'gold')),
    progresso INTEGER DEFAULT 0 CHECK (progresso >= 0 AND progresso <= 100),
    status VARCHAR(20) DEFAULT 'ativo' CHECK (status IN ('ativo', 'vendido', 'inativo')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ativos_usuario ON ativos(usuario_id);
CREATE INDEX idx_ativos_tipo ON ativos(tipo);
CREATE INDEX idx_ativos_classificacao ON ativos(classificacao);
CREATE INDEX idx_ativos_status ON ativos(status);
```

---

## 3. Tabela: documentos

```sql
CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id VARCHAR(50) REFERENCES ativos(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('rgp', 'seguro', 'survey', 'manutencao', 'nota_fiscal', 'foto', 'certificado', 'outro')),
    categoria VARCHAR(50) NOT NULL CHECK (categoria IN ('registro', 'seguro', 'manutencao', 'inspecao', 'foto', 'certificado', 'outro')),
    hash_sha256 VARCHAR(64) NOT NULL,
    tamanho_bytes BIGINT,
    mime_type VARCHAR(100),
    storage_path TEXT NOT NULL, -- S3 path
    url_publica TEXT,
    uploaded_by UUID REFERENCES usuarios(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validado_em TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'failed')),
    expiration_date DATE,
    hash_anterior VARCHAR(64), -- Para hash chain
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documentos_ativo ON documentos(ativo_id);
CREATE INDEX idx_documentos_usuario ON documentos(usuario_id);
CREATE INDEX idx_documentos_tipo ON documentos(tipo);
CREATE INDEX idx_documentos_hash ON documentos(hash_sha256);
CREATE INDEX idx_documentos_status ON documentos(status);
```

---

## 4. Tabela: eventos

```sql
CREATE TABLE eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id VARCHAR(50) REFERENCES ativos(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('manutencao', 'reforma', 'inspecao', 'documento', 'seguro', 'venda', 'alerta', 'compra', 'transferencia')),
    subtipo VARCHAR(50),
    titulo VARCHAR(255) NOT NULL,
    descricao TEXT,
    data_evento DATE,
    data_proxima DATE,
    prestador VARCHAR(255),
    custo DECIMAL(12,2),
    moeda VARCHAR(3) DEFAULT 'BRL',
    local VARCHAR(255),
    documento_id UUID REFERENCES documentos(id),
    evento_anterior_id UUID REFERENCES eventos(id),
    hash_evento VARCHAR(64), -- Para hash chain
    criado_por UUID REFERENCES usuarios(id),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_eventos_ativo ON eventos(ativo_id);
CREATE INDEX idx_eventos_tipo ON eventos(tipo);
CREATE INDEX idx_eventos_data ON eventos(data_evento);
CREATE INDEX idx_eventos_anterior ON eventos(evento_anterior_id);
```

---

## 5. Tabela: ativos_usuarios (Relação N:N)

```sql
CREATE TABLE ativos_usuarios (
    ativo_id VARCHAR(50) REFERENCES ativos(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    papel VARCHAR(20) DEFAULT 'dono' CHECK (papel IN ('dono', 'operador', 'visualizador')),
    primario BOOLEAN DEFAULT FALSE,
    desde DATE DEFAULT CURRENT_DATE,
    ate DATE,
    PRIMARY KEY (ativo_id, usuario_id)
);

CREATE INDEX idx_ativos_usuarios_usuario ON ativos_usuarios(usuario_id);
```

---

## 6. Tabela: classificacoes_log

```sql
CREATE TABLE classificacoes_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id VARCHAR(50) REFERENCES ativos(id) ON DELETE CASCADE,
    classificacao_anterior VARCHAR(20),
    classificacao_nova VARCHAR(20),
    progresso_anterior INTEGER,
    progresso_novo INTEGER,
    motivo TEXT,
    alterado_por UUID REFERENCES usuarios(id),
    alterado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_classificacoes_ativo ON classificacoes_log(ativo_id);
CREATE INDEX idx_classificacoes_data ON classificacoes_log(alterado_em);
```

---

## 7. Tabela: integridade_logs

```sql
CREATE TABLE integridade_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID REFERENCES documentos(id) ON DELETE CASCADE,
    acao VARCHAR(20) NOT NULL CHECK (acao IN ('upload', 'verify', 'download', 'alter', 'delete')),
    hash_anterior VARCHAR(64),
    hash_novo VARCHAR(64),
    ip_address VARCHAR(45),
    user_agent TEXT,
    executado_por UUID REFERENCES usuarios(id),
    executado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_integridade_documento ON integridade_logs(documento_id);
CREATE INDEX idx_integridade_data ON integridade_logs(executado_em);
CREATE INDEX idx_integridade_acao ON integridade_logs(acao);
```

---

## 8. Tabela: subscriptions

```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    plano VARCHAR(20) NOT NULL CHECK (plano IN ('free', 'pro', 'pro_annual', 'marina', 'enterprise')),
    stripe_subscription_id VARCHAR(255),
    stripe_customer_id VARCHAR(255),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'canceled', 'past_due', 'trialing')),
    current_period_start TIMESTAMP WITH TIME ZONE,
    current_period_end TIMESTAMP WITH TIME ZONE,
    canceled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_subscriptions_usuario ON subscriptions(usuario_id);
CREATE INDEX idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

---

## 9. Tabela: marinas_parceiras

```sql
CREATE TABLE marinas_parceiras (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nome VARCHAR(255) NOT NULL,
    cnpj VARCHAR(20),
    endereco TEXT,
    cidade VARCHAR(100),
    estado VARCHAR(2),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    telefone VARCHAR(20),
    email VARCHAR(255),
    website VARCHAR(255),
    logo_url TEXT,
    activa BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_marinas_cidade ON marinas_parceiras(cidade);
CREATE INDEX idx_marinas_estado ON marinas_parceiras(estado);
```

---

## 10. Tabela: notificacoes

```sql
CREATE TABLE notificacoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    ativo_id VARCHAR(50) REFERENCES ativos(id) ON DELETE CASCADE,
    tipo VARCHAR(50) NOT NULL CHECK (tipo IN ('seguro_vencendo', 'manutencao_pendente', 'classificacao_mudou', 'documento_vencendo', 'novo_evento')),
    titulo VARCHAR(255) NOT NULL,
    mensagem TEXT,
    lida BOOLEAN DEFAULT FALSE,
    enviada_whatsapp BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_notificacoes_usuario ON notificacoes(usuario_id);
CREATE INDEX idx_notificacoes_lida ON notificacoes(lida);
CREATE INDEX idx_notificacoes_tipo ON notificacoes(tipo);
```

---

## 11. Tabela: lgpd_alteracoes

```sql
CREATE TABLE lgpd_alteracoes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo_alteracao VARCHAR(50) NOT NULL CHECK (tipo_alteracao IN ('acesso', 'correcao', 'exclusao', 'portabilidade')),
    dados_solicitados JSONB,
    executado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    executado_por UUID REFERENCES usuarios(id)
);

CREATE INDEX idx_lgpd_usuario ON lgpd_alteracoes(usuario_id);
CREATE INDEX idx_lgpd_tipo ON lgpd_alteracoes(tipo_alteracao);
```

---

## 12. Row Level Security (RLS)

```sql
-- Habilitar RLS em todas as tabelas
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE ativos ENABLE ROW LEVEL SECURITY;
ALTER TABLE documentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE notificacoes ENABLE ROW LEVEL SECURITY;

-- Usuários só vêem próprios dados
CREATE POLICY "usuarios_view_own" ON usuarios
    FOR SELECT USING (auth.uid() = id);

-- Ativos só do dono
CREATE POLICY "ativos_view_own" ON ativos
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM ativos_usuarios au
            WHERE au.ativo_id = ativos.id
            AND au.usuario_id = auth.uid()
        )
    );

-- Documentos imutáveis (sem UPDATE/DELETE)
CREATE POLICY "documentos_insert" ON documentos
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "documentos_select" ON documentos
    FOR SELECT USING (usuario_id = auth.uid());

CREATE POLICY "documentos_no_update" ON documentos
    FOR UPDATE USING (false);

CREATE POLICY "documentos_no_delete" ON documentos
    FOR DELETE USING (false);

-- Eventos imutáveis
CREATE POLICY "eventos_insert" ON eventos
    FOR INSERT WITH CHECK (usuario_id = auth.uid());

CREATE POLICY "eventos_select" ON eventos
    FOR SELECT USING (usuario_id = auth.uid());

CREATE POLICY "eventos_no_update" ON eventos
    FOR UPDATE USING (false);

CREATE POLICY "eventos_no_delete" ON eventos
    FOR DELETE USING (false);
```

---

## 13. Functions e Triggers

```sql
-- Function: Atualizar updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger: usuarios updated_at
CREATE TRIGGER update_usuarios_updated_at
    BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger: ativos updated_at
CREATE TRIGGER update_ativos_updated_at
    BEFORE UPDATE ON ativos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger: eventos updated_at
CREATE TRIGGER update_eventos_updated_at
    BEFORE UPDATE ON eventos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function: Gerar ID de ativo
CREATE OR REPLACE FUNCTION gerar_id_ativo(tipo_ativo VARCHAR, ano INTEGER)
RETURNS VARCHAR AS $$
DECLARE
    sequencial INTEGER;
    id_gerado VARCHAR;
BEGIN
    SELECT COALESCE(MAX(SUBSTRING(id FROM 19)::INTEGER), 0) + 1
    INTO sequencial
    FROM ativos
    WHERE tipo = tipo_ativo AND SUBSTRING(id FROM 9, 4) = ano::TEXT;
    
    id_gerado := 'YA-' || UPPER(tipo_ativo) || '-' || ano || '-' || LPAD(sequencial::TEXT, 4, '0');
    RETURN id_gerado;
END;
$$ LANGUAGE plpgsql;

-- Trigger: Gerar ID automaticamente
CREATE TRIGGER gerar_id_ativo_trigger
    BEFORE INSERT ON ativos
    FOR EACH ROW
    WHEN (NEW.id IS NULL)
    EXECUTE FUNCTION gerar_id_ativo(NEW.tipo, NEW.ano_fabricacao);
```

---

**Versão:** 1.0
**Data:** 2026-04-25