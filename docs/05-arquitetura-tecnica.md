# Yachts Atlas — Arquitetura Técnica

## 1. Visão Geral da Arquitetura

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         YACHTS ATLAS                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐           ┌──────────────┐           ┌────────���─────┐  │
│   │   Frontend   │           │   Backend   │           │    Supabase  │  │
│   │  (Vite/React)│◀────────▶│  (FastAPI)  │◀────────▶│   (DB +      │  │
│   │             │           │             │           │    Storage)  │  │
│   └──────────────┘           └──────┬─────┘           └──────────────┘  │
│         │                          │                          │               │
│         │                    ┌─────┴─────┐                    │               │
│         │                    │           │                    │               │
│         ▼                    ▼           ▼                    ▼               │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   │ Evolution    │    │   AWS S3      │    │   Polars     │    │    AWS       │
│   │ API (WhatsApp)   │   (WORM)      │    │   (Análise)  │    │   CloudTrail │
│   └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

**IMPORTANTE:** Documentos são armazenados no AWS S3 com Object Lock (WORM). Supabase armazena apenas metadados.

---

## 2. Estrutura do Projeto

```
yachts-atlas/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── ativos.py
│   │   │   │   ├── documentos.py
│   │   │   │   ├── eventos.py
│   │   │   │   ├── usuarios.py
│   │   │   │   ├── integridade.py
│   │   │   │   └── dossier.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── supabase.py
│   │   ├── models/
│   │   │   ├── ativo.py
│   │   │   ├── documento.py
│   │   │   ├── evento.py
│   │   │   └── usuario.py
│   │   ├── services/
│   │   │   ├── ativo_service.py
│   │   │   ├── documento_service.py
│   │   │   ├── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   └── integridade_service.py
│   │   ├── integridae/ (corrigir para integridade_service)
│   │   │   └── integridade_service.py
│   │   │   └── integridade_service.py
│   │   │   └── integridade_service.py
│   │   │   └── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   └── integridade_service.py
│   │   │   ├── integridade_service.py
│   │   │   └── integridade_service.py
│   │   ├── schemas/ (Pydantic)
│   │   │   ├── ativo.py
│   │   │   ├── documento.py
│   │   │   ├── evento.py
│   │   │   └── usuario.py
│   │   └── main.py
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── types/
│   │   └── App.tsx
│   ├── public/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
└── docker-compose.yml
```

---

## 3. Modelo de Dados (Supabase/PostgreSQL)

### Tabela: usuarios

```sql
CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    nome VARCHAR(255) NOT NULL,
    telefone VARCHAR(20),
    whatsapp VARCHAR(20),
    role VARCHAR(20) DEFAULT 'dono', -- dono, admin, visualizar
    avatar_url TEXT,
    email_verificado BOOLEAN DEFAULT FALSE,
    whatsapp_verificado BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabela: ativos

```sql
CREATE TABLE ativos (
    id VARCHAR(50) PRIMARY KEY, -- YA-IATE-2024-0001
    usuario_id UUID REFERENCES usuarios(id),
    tipo VARCHAR(20) NOT NULL, -- iate, lancha, veleiro, jetski, barco_pesca
    marca VARCHAR(100) NOT NULL,
    modelo VARCHAR(100) NOT NULL,
    ano_fabricacao INTEGER NOT NULL,
    comprimento DECIMAL(5,2),
    largura DECIMAL(5,2),
    calado DECIMAL(5,2),
    material_casco VARCHAR(20),
    capacidade_passageiros INTEGER,
    modelo_motor VARCHAR(100),
    potencia_motor INTEGER,
    num_motores INTEGER,
    tipo_combustivel VARCHAR(20),
    num_cabines INTEGER,
    capacidade_tanque INTEGER,
    nome_reg VARCHAR(100),
    rgp VARCHAR(50),
    vin VARCHAR(50),
    classificacao VARCHAR(20) DEFAULT 'bronze',
    progresso INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ativo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabela: documentos

```sql
CREATE TABLE documentos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id VARCHAR(50) REFERENCES ativos(id),
    usuario_id UUID REFERENCES usuarios(id),
    nome_arquivo VARCHAR(255) NOT NULL,
    tipo VARCHAR(50) NOT NULL, -- rgp, seguro, survey, manutencao, nota_fiscal, foto
    categoria VARCHAR(50) NOT NULL, -- registro, seguro, manutencao, inspecao, foto
    hash_sha256 VARCHAR(64) NOT NULL,
    tamanho_bytes BIGINT,
    mime_type VARCHAR(100),
    storage_path TEXT,
    url_publica TEXT,
    uploaded_by UUID REFERENCES usuarios(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validado_em TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, verified, failed
    expiration_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabela: eventos

```sql
CREATE TABLE eventos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id VARCHAR(50) REFERENCES ativos(id),
    usuario_id UUID REFERENCES usuarios(id),
    tipo VARCHAR(50) NOT NULL, -- manutencao, reforma, inspecao, documento, seguro, venda, alerta
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
    hash_evento VARCHAR(64),
    criado_por UUID REFERENCES usuarios(id),
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabela: ativos_usuarios (relação many-to-many)

```sql
CREATE TABLE ativos_usuarios (
    ativo_id VARCHAR(50) REFERENCES ativos(id),
    usuario_id UUID REFERENCES usuarios(id),
    papel VARCHAR(20) DEFAULT 'dono', -- dono, operador,visualizador
    primario BOOLEAN DEFAULT FALSE,
    desde DATE,
    ate DATE,
    PRIMARY KEY (ativo_id, usuario_id)
);
```

### Tabela: classificacoes_log

```sql
CREATE TABLE classificacoes_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ativo_id VARCHAR(50) REFERENCES ativos(id),
    classificacao_anterior VARCHAR(20),
    classificacao_nova VARCHAR(20),
    progresso_anterior INTEGER,
    progresso_novo INTEGER,
    motivo TEXT,
    alterado_por UUID REFERENCES usuarios(id),
    alterado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Tabela: integridade_logs

```sql
CREATE TABLE integridade_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    documento_id UUID REFERENCES documentos(id),
    acao VARCHAR(20) NOT NULL, -- upload, verify, download, alter
    hash_anterior VARCHAR(64),
    hash_novo VARCHAR(64),
    ip_address VARCHAR(45),
    user_agent TEXT,
    executado_por UUID REFERENCES usuarios(id),
    executado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 4. API Endpoints (FastAPI)

### Autenticação

| Método | Endpoint | Descrição |
|---|---|---|
| POST | /auth/signup | Cadastrar usuário |
| POST | /auth/login | Login (retorna token) |
| POST | /auth/logout | Logout |
| POST | /auth/reset-password |.Resetar senha |
| GET | /auth/me | Dados do usuário logado |

### Ativos

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /ativos | Listar ativos do usuário |
| POST | /ativos | Criar novo ativo |
| GET | /ativos/{id} | Detalhes do ativo |
| PUT | /ativos/{id} | Atualizar ativo |
| DELETE | /ativos/{id} | Excluir ativo |
| GET | /ativos/{id}/progresso | Ver progresso de classificação |
| GET | /ativos/{id}/classificacao | Ver classificação atual |

### Documentos

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /ativos/{id}/documentos | Listar documentos do ativo |
| POST | /ativos/{id}/documentos | Upload de documento |
| GET | /documentos/{id} | Detalhes do documento |
| DELETE | /documentos/{id} | Excluir documento |
| GET | /documentos/{id}/verificar | Verificar integridade |
| GET | /documentos/{id}/download | Download do arquivo |

### Eventos

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /ativos/{id}/eventos | Listar histórico do ativo |
| POST | /ativos/{id}/eventos | Criar novo evento |
| GET | /eventos/{id} | Detalhes do evento |
| PUT | /eventos/{id} | Atualizar evento |

### Dossier

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /ativos/{id}/dossier | Gerar dossier (escolhe tipo) |
| GET | /ativos/{id}/dossier/basico | Dossier Básico |
| GET | /ativos/{id}/dossier/completo | Dossier Completo |
| GET | /ativos/{id}/dossier/premium | Dossier Premium |
| GET | /ativos/{id}/dossier/pdf | Gerar PDF do dossier |

### Integridade

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /integridade/{doc_id}/verify | Verificar hash do documento |
| GET | /integridade/{ativo_id}/relatorio | Relatório de integridade completo |
| HEAD | /integridade/{doc_id}/hash | Verificar se documento existe |

---

## 5. Fluxo de Upload de Documento

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     FLUXO DE UPLOAD                          │
└─────────────────────────────────────────────────────────────────────────────┘

1. Frontend                              2. Backend
   ┌──────────────┐                         ┌──────────────┐
   │ Seleciona     │                         │ Recebe      │
   │ arquivo      │── POST /documentos ─────▶│ arquivo    │
   │ (PDF/Foto)   │   (multipart/form)     │            │
   └──────────────┘                         └──────┬─────┘
                                                   │
                                                   ▼
                                          ┌──────────────┐
                                          │ Calcula      │
                                          │ SHA-256      │
                                          │ do arquivo  │
                                          └──────┬─────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │ Gera         │
                                          │ UUID         │
                                          │ storage_path │
                                          └──────┬���────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │ Upload      │──▶ Supabase Storage
                                          │ para S3    │    (bucket: yachts-docs)
                                          └──────┬─────┘
                                                 │
                                                 ▼
                                          ┌──────────────┐
                                          │ Registra     │
                                          │ no banco    │──▶ PostgreSQL
                                          │ (documentos)│
                                          └──────┬─────┘
                                                 │
                                                 ▼
                                          3. Response
                                          ┌──────────────┐
                                          │ {           │
                                          │   id,       │
                                          │   hash,     │
                                          │   url,      │
                                          │   status   │
                                          │ }           │
                                          └──────────────┘
```

---

## 6. Fluxo de Autenticação

```
┌─────────────────────────────────────────────────────────────────────────────┐
│               FLUXO DE AUTENTICAÇÃO (Supabase Auth)                  │
└─────────────────────────────────────────────────────────────────────────────┘

1. POST /auth/signup
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ {          │────▶│ Cria         │────▶│ Envia        │
   │ email,     │     │ usuário no  │     │ email de    │
   │ senha      │     │ Supabase    │     │ verificação │
   └──────────────┘     └──────────────┘     └──────────────┘

2. POST /auth/login
   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
   │ {          │────▶│ Valida       │────▶│ Retorna     │
   │ email,     │     │ credenciais │     │ JWT token   │
   │ senha      │     │ e gera token│     │            │
   └──────────────┘     └──────────────┘     └──────────────┘

3. Frontend menyimpan token
   ┌──────────────┐
   │ token      │──▶ localStorage / httpOnly cookie
   │ JWT       │
   └──────────────┘
              │
              ▼
4. todas API requests
   ┌──────────────┐
   │ Authorization│──▶ Bearer {token}
   │ : Bearer    │
   └──────────────┘
```

---

## 7. Integração com Evolution API (WhatsApp)

### Tipos de Notificação

| Trigger | Mensagem | Quando |
|---|---|---|
| seguro_vence | "Seu seguro vence em X dias" | 30 dias antes |
| manutencao_pendente | "Manutenção pendente: X" | Quando identificada |
| classificacao_mudou | "Parabéns! Seu ativo agora é Silver" | Ao subir nível |
| documento_excluido | "Documento X foi removido" | Após exclusão |
| vigilancia_ativada | "Novo evento registrado no seu ativo" | Quando adiciona evento |

### Estrutura da Mensagem

```json
{
  "phoneNumber": "+5521999999999",
  "message": "🔔 *Yachts Atlas*\n\nSeu iate *Azimut 78* agora está no nível *Silver*!\n\n*Próximo passo:* Complete o relatório de survey para atingir Gold.",
  "mediaUrl": null
}
```

---

## 8. Análise de Dados com Polars

### Uso do Polars

| Análise | Query | Output |
|---|---|---|
| Ativos por tipo | `df.group_by("tipo").len()` | Quantos iates, lanchas, etc. |
| Classificação distribuição | `df.group_by("classificacao").len()` | Bronze/Silver/Gold count |
| Eventos por mês | `df.group_by("mes").len()` | Timeline |
| Valor médio | `df.select("valor_estimado").mean()` | Média por tipo |
| Documentos por tipo | `df.group_by("tipo_documento").len()` | Stats |

### Exemplo de Query

```python
import polars as pl

df = pl.DataFrame(ativos_data)

# Ativos por classificação
result = df.group_by("classificacao").agg(
    pl.len().alias("quantidade"),
    pl.col("valor_estimado").mean().alias("valor_medio")
)

print(result)
```

---

## 9. Segurança

### Autenticação

- JWT (JSON Web Token)
- Supabase Auth
- Rate limiting via FastAPI

### Autorização

- RBAC (Role-Based Access Control)
- Usuário só vê seus próprios ativos
- Dono pode adicionar visualizadores

### Dados

- Criptografia em trânsito: TLS 1.3
- Criptografia em repouso: Supabase Encryption
- Backup diário via Supabase

### Logs

- CloudTrail (AWS) ou similar
- Todos os acessos registrados
- Retenção: 1 ano

---

## 10. Variáveis de Ambiente

```env
# Backend
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=xxx
JWT_SECRET=xxx
DATABASE_URL=postgresql://xxx

# Evolution API
EVOLUTION_API_URL=http://evolution-api:8080
EVOLUTION_API_KEY=xxx

# AWS (opcional)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_REGION=us-east-1
```

---

## 11. Docker

### Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    env_file:
      - .env
    volumes:
      - ./frontend:/app
    depends_on:
      - backend
```

---

## 12. Estrutura de Buckets (Storage)

### 12.1 Supabase Storage (Metadados)

| Bucket | Tipo | Acesso | Descrição |
|---|---|---|---|
| yachts-docs | documentos | private | Documentos dos ativos |
| yachts-fotos | imagens | public | Fotos dos ativos |
| yachts-dossier | pdf | private | Relatórios gerados |

### 12.2 AWS S3 (Arquivos Reais com WORM)

```
┌─────────────────────────────────────────────────────┐
│  S3 BUCKET: yachts-docs-prod                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Configuração:                                      │
│  ├── Object Lock: HABILITADO                        │
│  ├── Default Retention:                             │
│  │   ├── Mode: COMPLIANCE                          │
│  │   └── Days: 365 (mínimo 1 ano)                  │
│  ├── Versioning: HABILITADO                         │
│  ├── CloudTrail: HABILITADO (logs de acesso)       │
│  └── SSE: AES-256 (criptografia em repouso)        │
│                                                     │
│  Resultado:                                         │
│  • Impossível alterar arquivos                     │
│  • Impossível deletar arquivos                     │
│  • Todos os acessos logados                         │
│  • Juridicamente defensável                         │
└─────────────────────────────────────────────────────┘
```

### 12.3 Configuração S3 Object Lock

```python
import boto3

s3 = boto3.client('s3')

# Criar bucket com Object Lock
s3.create_bucket(
    Bucket='yachts-docs-prod',
    ObjectLockEnabledForBucket=True
)

# Configurar lifecycle para versionamento
s3.put_bucket_lifecycle_configuration(
    Bucket='yachts-docs-prod',
    LifecycleConfiguration={
        'Rules': [{
            'ID': 'DocumentRetention',
            'Status': 'Enabled',
            'Filter': {'Prefix': 'ativos/'},
            'Expiration': {'Days': 3650}  # 10 anos
        }]
    }
)
```

### 12.4 CloudTrail (Logs de Auditoria AWS)

```python
# CloudTrail registra TODOS os acessos ao S3
cloudtrail = boto3.client('cloudtrail')

# Query de logs
logs = cloudtrail.lookup_events(
    LookupAttributes=[{
        'AttributeKey': 'ResourceName',
        'AttributeValue': 'yachts-docs-prod'
    }],
    StartTime='2024-01-01',
    EndTime='2024-12-31'
)

# Para cada acesso:
# - Quem acessou (IAM user)
# - Quando acessou (timestamp)
# - De onde acessou (IP)
# - O que fez (GetObject, PutObject, etc)
```

### 12.5 Fluxo de Storage Recomendado

```
┌─────────────────────────────────────────────────────┐
│           FLUXO DE STORAGE MVP                     │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Upload documento                                   │
│       │                                            │
│       ▼                                            │
│  ┌──────────────┐                                   │
│  │  FastAPI     │                                   │
│  │  • Calcula   │                                   │
│  │    SHA-256   │                                   │
│  │  • Valida    │                                   │
│  │    arquivo   │                                   │
│  └──────┬───────┘                                   │
│         │                                           │
│         ├──────────────────────────┐                │
│         ▼                          ▼                │
│  ┌──────────────┐         ┌──────────────┐         │
│  │  Supabase    │         │  AWS S3       │         │
│  │  • Metadata  │         │  • Arquivo    │         │
│  │  • Hash chain│         │  • WORM lock  │         │
│  │  • Logs      │         │  • CloudTrail │         │
│  └──────────────┘         └──────────────┘         │
│                                                     │
│  Consulta documento                                 │
│       │                                            │
│       ▼                                            │
│  ┌──────────────┐                                   │
│  │  CloudTrail  │──▶ Log de auditoria              │
│  └──────────────┘                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 12.6 Custo Estimado (MVP)

| Serviço | Uso | Custo/mês |
|---|---|---|
| AWS S3 | 10 GB storage | ~$0.10 |
| S3 Object Lock | Incluso | $0 |
| CloudTrail | 1 trail | ~$2.00 |
| Data Transfer | Mínimo | ~$0.50 |
| **Total** | | **~$2.60/mês** |

---

## 13. Versionamento

v0.2 — Arquitetura Técnica (com S3 WORM)

---

## 14. Data

2026-04-25