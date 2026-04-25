# Yachts Atlas — Segurança e Conformidade

## 1. Filosofia de Segurança

> **"Dados que entram, não saem. Dados que são salvos, não mudam. Tudo é rastreável. Nada é burlável."**

O Yachts Atlas segue o princípio de **defesa em profundidade**. Não confiamo em uma einzige camada. Cada dado tem múltiplas camadas de proteção.

---

## 2. Camadas de Segurança

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CAMADAS DE SEGURANÇA YACHTS ATLAS                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Camada 1: Rede                                                              │
│  ├── Firewall (WAF)                                                         │
│  ├── Rate Limiting                                                          │
│  ├── IP Whitelist (só IPs autorizados)                                       │
│  ├── DDoS Protection                                                        │
│                                                                             │
│  Camada 2: Aplicação                                                         │
│  ├── JWT com expiração curta                                                   │
│  ├── CSRF Protection                                                         │
│  ├── Input Validation (Pydantic)                                                 │
│  ├── SQL Injection Prevention                                              │
│  ├── XSS Prevention                                                         │
│                                                                             │
│  Camada 3: Banco de Dados                                                    │
│  ├── RLS (Row Level Security)                                              │
│  ├── Criptografia em repouso                                               │
│  ├── Imutabilidade aplicada                                                │
│  ├── Timestamps imutáveis                                                  │
│                                                                             │
│  Camada 4: Arquivos                                                         │
│  ├── Criptografia AES-256                                                  │
│  ├── Hash SHA-256 imutável                                                  │
│  ├── Assinatura digital (opcional)                                            │
│  ├── Immutable Storage (S3 Object Lock)                                      │
│                                                                             │
│  Camada 5: Monitoramento                                                     │
│  ├── Logs de auditoria                                                      │
│  ├── Alertas de anomalias                                                  │
│  ├── Backups imutáveis                                                     │
│  ├── Detecção de intruder                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Criptografia

### 3.1 Criptografia em Trânsito (TLS 1.3)

```
Todas as comunicações = HTTPS obrigatório

Frontend → Backend:    HTTPS (TLS 1.3)
Backend → Supabase:   HTTPS (TLS 1.3)
Backend → Evolution:  HTTPS (TLS 1.3)
API externa:          HTTPS (TLS 1.3)
```

**Configuração SSL:**

```nginx
# SSL/TLS config
ssl_protocols TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_tickets off;
```

### 3.2 Criptografia em Repouso (AES-256)

```
Supabase: Criptografia automática (AES-256)
AWS S3: Server-side encryption (SSE-S3 ou SSE-KMS)
```

**Configuração S3:**

```python
# Upload com criptografia
s3.put_object(
    Bucket='yachts-docs',
    Key=path,
    Body=file_bytes,
    ServerSideEncryption='AES256'
)
```

### 3.3 Criptografia de Arquivos (SHA-256)

Cada documento tem hash SHA-256 **imutável**:

```
┌─────────────────────────────────────────────────────────────────┐
│  IMPUTÁVEL = NÃO PODE SER ALTERADO EM HIPÓTESE ALGUMA            │
└─────────────────────────────────────────────────────────────────┘
```

**Register:**

```python
import hashlib

def calcular_hash(arquivo_bytes: bytes) -> str:
    return hashlib.sha256(arquivo_bytes).hexdigest()

def registrar_documento(arquivo, hash_calculado):
    # Hash NUNCA pode ser alterado após registro
    # Qualquer tentativa = FRAUDE = DETECTÁVEL
```

### 3.4 Criptografia de Campos Sensíveis

| Campo | Criptografia | Quem Pode Ver |
|---|---|---|
| CPF/CNPJ | Supabase encryption + masking | ONLY owner |
|Telefone| Supabase encryption | Owner + visualizadores autorizados |
|Endereço| Supabase encryption | ONLY owner |
|Documentos| Hash (não conteúdo) | Dono pode ver, outros não |
|Notas fiscais| Hash + accesso controlado | ONLY owner |

**Máscara para display:**

```python
def mascarar_documento(documento: str) -> str:
    if len(documento) == 11:  # CPF
        return f"***.{documento[3:6]}.{documento[6:9]}-**"
    elif len(documento) == 14:  # CNPJ
        return f"**.{documento[2:5]}.{documento[5:8]}/{documento[8:12]}-**"
    return "****"
```

---

## 4. Autenticação JWT

### 4.1 Configuração do JWT

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt

SECRET_KEY = os.environ["JWT_SECRET"]
ALGORITHM = "HS256"

# Token expira em 15 minutos
ACCESS_TOKEN_EXPIRE_MINUTES = 15
# Refresh token expira em 7 dias
REFRESH_TOKEN_EXPIRE_DAYS = 7
```

### 4.2 Criação do Token

```python
def criar_access_token(usuario_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": usuario_id,
        "role": role,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def criar_refresh_token(usuario_id: str) -> str:
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": usuario_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
```

### 4.3 Validação do Token

```python
def verificar_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token inválido")

        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token expirado ou inválido")
```

### 4.4 Refresh Token Flow

```
1. Usuário faz login
   ─────────────────────────
   { "email": "...", "senha": "..." }
   │
   ▼
   Retorna: { "access_token": "...", "refresh_token": "..." }

2. Access expira (15 min)
   ─────────────────────────
   Request com access_token → 401 Unauthorized
   │
   ▼
3. Refresh automático
   ─────────────────────────
   { "refresh_token": "..." } → Novo access_token

4. Refresh expira (7 dias)
   ─────────────────────────
   Usuário precisa fazer login novamente
```

### 4.5 Segurança Adicional JWT

| Medida | Descrição |
|---|---|
| Expiração curta | 15 minutos = menos tempo para roubar |
| Tipo de token | "access" vs "refresh" validation |
| IP binding |(Token inclui IP) — invalida se IP mudar |
| Device fingerprint | Invalidar se device mudar |
| Logout destrói tokens | Refresh INVALIDADO no logout |
| Revogação forçada | Admin pode-invalidar todos os tokens |

---

## 5. Row Level Security (RLS) — Supabase

### 5.1 Políticas RLS

```sql
-- ============================================
-- POLÍTICAS RLS - SUPABASE
-- ============================================

-- Usuários só vêem seus próprios dados
CREATE POLICY "Usuários vêem próprios dados"
ON usuarios
FOR SELECT
USING (auth.uid() = id);

-- Ativos só pertencem ao dono
CREATE POLICY "Donos vêem próprios ativos"
ON ativos
FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM ativos_usuarios
        WHERE ativo_id = ativos.id
        AND usuario_id = auth.uid()
        AND papel = 'dono'
    )
);

-- Documentos: só dono acessa
CREATE POLICY "Documentos acesso restrito"
ON documentos
FOR ALL
USING (
    usuario_id = auth.uid()
);
```

### 5.2 Política RLS por Tipo de Operação

```sql
-- SELECT: Dono ou visualizadores autorizados
CREATE POLICY "Select documentos"
ON documentos
FOR SELECT
USING (
    usuario_id = auth.uid()
    OR
    EXISTS (
        SELECT 1 FROM ativos_usuarios au
        JOIN ativos a ON a.id = au.ativo_id
        JOIN documentos d ON d.ativo_id = a.id
        WHERE au.usuario_id = auth.uid()
        AND au.visualizador = TRUE
    )
);

-- INSERT: Apenas dono
CREATE POLICY "Insert documentos"
ON documentos
FOR INSERT
WITH CHECK (usuario_id = auth.uid());

-- UPDATE: NUNCA (imutável)
CREATE POLICY "Update documentos"
ON documentos
FOR UPDATE
USING (false);

-- DELETE: NUNCA (imutável)
CREATE POLICY "Delete documentos"
ON documentos
FOR DELETE
USING (false);
```

---

## 6. Imutabilidade de Dados

### 6.1 Dados que NÃO PODEM ser alterados

| Dado | Imutável? | Por quê |
|---|---|---|
| Hash SHA-256 | ✅ SIM | Identidade do arquivo |
| Timestamp upload | ✅ SIM | Prova temporal |
| Eventos do histórico | ✅ SIM | Linha do tempo |
| Documentos uploadados | ✅ SIM | Prova jurídica |
| Registros de seguro | ✅ SIM | Prova de vigência |
| Relatórios de survey | ✅ SIM | Documento técnico |
| Logs de auditoria | ✅ SIM | Rastreabilidade |
| Classificação anterior | ✅ SIM | Histórico evolução |

### 6.2 Dados que PODEM ser alterados

| Dado | Pode alterar? | Com |
|---|---|---|
| Fotos do ativo | SIM | Nova versão |
| Dados técnicos | SIM | Novo registro + versão |
| Contato do dono | SIM | Update simples |
| Notas fiscais | SIM | Adicionar, não alterar |

### 6.3 Política de Imutabilidade

```sql
-- Tabela de eventos = TODOS os dados são APPEND-ONLY
-- Não existe UPDATE ou DELETE

-- Para alterar: CRIA NOVO REGISTRO

-- Exemplo: Classificação
INSERT INTO classificacoes_log (
    ativo_id,
    classificacao_anterior,
    classificacao_nova,
    alterado_por
) VALUES (
    'YA-IATE-2024-0001',
    'bronze',
    'silver',
    'user-123'
);

-- O histórico fica: bronze → silver (completo, auditável)
```

### 6.4 Impossível Alterar Dados

```
┌─────────────────────────────────────────────────────────────────┐
│  PROTEÇÃO COMPLETA CONTRA ALTERAÇÃO                          │
│                                                              │
│  • Tabela de documentos: NO UPDATE                          │
│  • Tabela de eventos: NO UPDATE                            │
│  • Tabela de logs: NO UPDATE                               │
│  • Timestamps: READ-ONLY                                   │
│  • Hash: IMPOSSÍVEL ALTERAR                                │
└─────────────────────────────────────────────────────────────────┘

Tentativa de alteração
├── Sistema recusa (RLS)
├── Log de auditoria registra
├── Alerta dispara
└── Admin é notificado
```

---

## 7. LGPD — Conformidade

### 7.1 Dados Coletados

| Dado | Finalidade | Base Legal |
|---|---|---|
| Nome | Identificação | Consentimento |
| Email | Login, contato | Consentimento |
| Telefone | Autenticação, alertas | Consentimento |
| CPF | Documentação fiscal | Obrigação legal |
| Endereço | Correspondência | Consentimento |
| Dados do ativo | Registro do ativo | Consentimento |
| Documentos | Dossier | Consentimento |

### 7.2 Direitos do Titular

| Direito | Como Exercê-lo |
|---|---|
| Confirmação | Ver dados → Dashboard |
| Acesso | Ver todos os dados |
| Correção | Solicitar correção |
| Exclusão | "Quero excluir minha conta" |
| Portabilidade | Exportar todos os dados |
| Revogação consentimento | Configurações |

### 7.3 Implementação de Direitos

```python
# Exemplo: Exportar dados do usuário
@router.get("/meus-dados/export")
def exportar_dados(usuario_id: str = Depends(get_current_user)):
    usuario = get_usuario(usuario_id)
    ativos = get_ativos_do_usuario(usuario_id)
    documentos = get_documentos_do_usuario(usuario_id)

    return {
        "usuario": usuario,
        "ativos": ativos,
        "documentos": documentos,
        "exportado_em": datetime.utcnow()
    }

# Exemplo: Excluir conta
@router.delete("/conta/excluir")
def excluir_conta(usuario_id: str = Depends(get_current_user)):
    # soft delete + anonymization
    anonymize_usuario(usuario_id)
    deactivate_tokens(usuario_id)

    return {"status": "conta excluída"}
```

### 7.4 LGPD: Dados Não Podem Ser Alterados

```sql
-- LOG de alterações (para compliance)
CREATE TABLE lgpd_alteracoes (
    id UUID PRIMARY KEY,
    usuario_id UUID,
    tipo_alteracao VARCHAR(50), -- acesso, correção, exclusão, portabilidade
    dados_solicitados JSON,
    executado_em TIMESTAMP,
    executado_por UUID
);
```

---

## 8. Anti-Fraude

### 8.1 Prevenção de Fraude

| Fraude | Prevenção |
|---|---|
| Alterar documento | Hash imutável, RLS blocks UPDATE |
| Mudar data de upload | Timestamp only, não editável |
| Classificação falsa | Logs + auditoria |
| Usurpação de identidade | 2FA obrigatório |
| Duplicate upload | Hash duplicate detection |

### 8.2 Detecção de Anomalias

```python
# Sistema de detecção de anomalias
class DetectorFraude:
    def __init__(self):
        self.alertas = []

    def detectar_duplicata(self, hash_sha256):
        """Documento já exists?"""
        return buscar_por_hash(hash_sha256) is not None

    def detectar_data_inconsistente(self, data_evento):
        """Data faz sentido?"""
        if data_evento > datetime.utcnow():
            return True  # Data futura = fraude
        if data_evento < datetime(2000, 1, 1):
            return True  #Data muito antiga = erro
        return False

    def detectar_ip_inconsistente(self, usuario_id, ip):
        """Mesmo usuário de IPs muito diferentes?"""
        ultimo_ip = get_ultimo_ip(usuario_id)
        if ultimo_ip and ip != ultimo_ip:
            # Alertar, mas não bloquear
            self.alertas.append(f"IP change: {ultimo_ip} → {ip}")
        return False
```

### 8.3 Cadeia de Auditoria

```
┌─────────────────────────────────────────────────────────────────┐
│              CADEIA COMPLETA DE AUDITORIA                        │
│                                                              │
│  TODO registro = COMPLETO com:                                   │
│  ├── Quem criou                                                 │
│  ├── Quando criou                                              │
│  ├── De qual IP                                                │
│  ├── De qual device                                            │
│  ├── Que dados enviou                                          │
│  └── Hash do que foi salvo                                     │
└────────────────────────────────────────��─��──────────────────────┘
```

---

## 9. Logs de Auditoria

### 9.1 Tudo É Logado

| Ação | Logado | Retenção |
|---|---|---|
| Login | ✓ | 1 ano |
| Logout | ✓ | 1 ano |
| Token refresh | ✓ | 1 ano |
| Criar ativo | ✓ | Permanente |
| Upload documento | ✓ | Permanente |
| Alterar dado | ✓ | Permanente |
| Tentativa de alteração negada | ✓ | 1 ano |
| Tentativa de acesso negada | ✓ | 1 ano |
| Exclusão de conta | ✓ | Permanente |

### 9.2 Estrutura do Log

```python
# Log de auditoria
{
    "id": "log-2024-001",
    "acao": "UPLOAD_DOCUMENTO",
    "usuario_id": "user-123",
    "ativo_id": "YA-IATE-2024-0001",
    "documento_id": "doc-2024-001",
    "ip_address": "192.168.1.1",
    "user_agent": "Mozilla/5.0...",
    "timestamp": "2024-01-15T14:30:00Z",
    "sucesso": True,
    "detalhes": "..."
}
```

---

## 10. Rate Limiting

```python
from fastapi import FastAPI
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@router.post("/upload")
@limiter.limit("10/minuto")  # Max 10 uploads por minuto
async def upload_documento(request: Request):
    # ...
```

| Endpoint | Limite |
|---|---|
| /auth/login | 5/minuto |
| /upload | 10/minuto |
| /api/ativos | 60/minuto |
| /api/documentos | 30/minuto |

---

## 11. 2FA (Two-Factor Authentication)

### 11.1 2FA Obrigatório

```
Cadastro → Verificar email (obrigatório)
           Verificar WhatsApp (obrigatório)
```

### 11.2 Implementação

```python
# Enviar código por WhatsApp (Evolution API)
def enviar_codigo_2fa(telefone: str) -> str:
    codigo = gerar_codigo(6 digitos)

    # Armazenar hash do código (não o código em si)
    hash_codigo = hashlib.sha256(codigo.encode()).hexdigest()

    # Enviar por WhatsApp
    evolution_api.enviar_mensagem(
        telefone,
        f"Seu código Yachts Atlas: {codigo}"
    )

    return hash_codigo

def validar_codigo(codigo: str, hash_armazenado: str) -> bool:
    return hashlib.sha256(codigo.encode()).hexdigest() == hash_armazenado
```

---

## 12. Backup e Recuperação

### 12.1 Backup Automático

| Tipo | Frequência | Retenção |
|---|---|---|
| Supabase | Diário | 30 dias |
| Arquivos (S3) | Diário | 90 dias |
| Logs | Diário | 1 ano |

### 12.2 Backup Imutável

```
Backups = Imutáveis (não podem ser alterados ou apagados)
├── Criptografados
├──armazenados em bucket separado
├──Accesso apenas por admin
└──Verificação de integridade
```

---

## 13. Monitoramento e Alertas

### 13.1 Alertas Automáticos

| Condição | Alerta |
|---|---|---|
| Login de novo dispositivo | Notificação |
| Múltiplos logins falhados | Alerta + bloquear temporário |
| Upload de documento duplicado | Alerta |
| Tentativa de acesso não autorizado | Alerta crítico |
| Alteração de dado protegido | Alerta crítico |

### 13.2 Dashboard de Segurança

```
┌────────────────────────────────────────────┐
│        SECURITY DASHBOARD                  │
├────────────────────────────────────────────┤
│ Usuários ativos: 150                      │
│ Logins hoje: 234                          │
│ Tentativas falhas: 3                       │
│ Dokumentos uploadados: 1.234              │
│ Último backup: 2h atrás                  │
│ Status: ✓ SEGURO                         │
└───────────────────────────────────────���─���──┘
```

---

## 14. Resumo de Segurança

```
╔════════════════════════════════════════════════════════════════════════╗
║              YACHTS ATLAS: SEGURANÇA MILITAR                          ║
╠════════════════════════════════════════════════════════════════════════╣
║                                                                ║
║  ✓ TLS 1.3 — comunicação impossível de interceptar                ║
║  ✓ AES-256 — dados impossíveis de descriptografar                ║
║  ✓ SHA-256 — documento impossível de alterar                   ║
║  ✓ JWT 15min — token expira antes de roubar                      ║
║  ✓ RLS — dados belongcem apenas a quem de direito               ║
║  ✓ Imutabilidade — NADA pode ser alterado                        ║
║  ✓ LGPD — dados são do usuário, não nosso                        ║
║  ✓ 2FA — autenticação em duas etapas                           ║
║  ✓ Logs — TODO registro auditável                                ║
║  ✓ Backups imutáveis — recuperação garantida                  ║
║  ✓ Anti-fraude — tentativa = detecção                            ║
║                                                                ║
║  "Dados que entram, não saem. Dados que salvam, não mudam."       ║
║                                                                ║
╚════════════════════════════════════════════════════════════════════════╝
```

---

## 15. Versão

v0.1 — Segurança e Conformidade

---

## 16. Data

2026-04-22