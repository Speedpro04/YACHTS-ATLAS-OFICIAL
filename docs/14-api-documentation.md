# Yachts Atlas — API Documentation

## Base URL

```
Production: https://api.yachtsatlas.com/v1
Staging: https://staging-api.yachtsatlas.com/v1
Local: http://localhost:8000/api/v1
```

---

## Autenticação

Todas as requisições precisam de Bearer Token no header:

```
Authorization: Bearer {access_token}
```

---

## Endpoints

---

## 1. Autenticação

### POST /auth/signup
Registrar novo usuário.

**Request Body:**
```json
{
  "email": "usuario@email.com",
  "password": "senha123",
  "nome": "João Silva",
  "telefone": "+5521999999999",
  "whatsapp": "+5521999999999"
}
```

**Response (201):**
```json
{
  "message": "User created",
  "user_id": "uuid-do-usuario"
}
```

---

### POST /auth/login
Login e obter token.

**Request Body:**
```json
{
  "email": "usuario@email.com",
  "password": "senha123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": "uuid-do-usuario"
}
```

---

### POST /auth/logout
Deslogar usuário.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "message": "Logged out"
}
```

---

### GET /auth/me
Obter dados do usuário logado.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": "uuid-do-usuario",
  "email": "usuario@email.com",
  "nome": "João Silva",
  "telefone": "+5521999999999",
  "role": "dono",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

## 2. Ativos

### GET /ativos
Listar ativos do usuário.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": "YA-IATE-2024-0001",
    "tipo": "iate",
    "marca": "Azimut",
    "modelo": "78 Flybridge",
    "ano_fabricacao": 2018,
    "classificacao": "gold",
    "progresso": 85,
    "status": "ativo",
    "created_at": "2024-01-15T10:00:00Z"
  }
]
```

---

### POST /ativos
Criar novo ativo.

**Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "tipo": "iate",
  "marca": "Azimut",
  "modelo": "78 Flybridge",
  "ano_fabricacao": 2018,
  "comprimento": 24.0,
  "largura": 5.8,
  "material_casco": "fibra",
  "capacidade_passageiros": 12,
  "num_cabines": 4
}
```

**Response (201):**
```json
{
  "id": "YA-IATE-2024-0001",
  "tipo": "iate",
  "marca": "Azimut",
  "modelo": "78 Flybridge",
  "ano_fabricacao": 2018,
  "classificacao": "bronze",
  "progresso": 0,
  "status": "ativo",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### GET /ativos/{id}
Obter detalhes de um ativo.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": "YA-IATE-2024-0001",
  "tipo": "iate",
  "marca": "Azimut",
  "modelo": "78 Flybridge",
  "ano_fabricacao": 2018,
  "comprimento": 24.0,
  "largura": 5.8,
  "calado": 1.8,
  "material_casco": "fibra",
  "capacidade_passageiros": 12,
  "modelo_motor": "MAN V12 1550HP",
  "num_motores": 2,
  "tipo_combustivel": "diesel",
  "num_cabines": 4,
  "nome_reg": "Sea Spirit",
  "rgp": "12345678",
  "classificacao": "gold",
  "progresso": 85,
  "status": "ativo",
  "created_at": "2024-01-15T10:00:00Z"
}
```

---

### DELETE /ativos/{id}
Excluir ativo.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "message": "Ativo deleted"
}
```

---

### GET /ativos/{id}/progresso
Obter progresso de classificação.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "classificacao": "gold",
  "progresso": 85,
  "proximo_nivel": null,
  "itens_pendentes": [
    "Relatório de survey atualizado"
  ]
}
```

---

## 3. Documentos

### GET /documentos/ativo/{ativo_id}
Listar documentos de um ativo.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": "uuid-do-documento",
    "ativo_id": "YA-IATE-2024-0001",
    "nome_arquivo": "seguro_2024.pdf",
    "tipo": "seguro",
    "categoria": "seguro",
    "hash_sha256": "a1b2c3d4e5f6...",
    "tamanho_bytes": 1048576,
    "mime_type": "application/pdf",
    "status": "verified",
    "uploaded_at": "2024-01-15T14:30:00Z"
  }
]
```

---

### POST /documentos/upload/{ativo_id}
Upload de documento.

**Headers:**
```
Authorization: Bearer {token}
Content-Type: multipart/form-data
```

**Form Data:**
| Campo | Tipo | Descrição |
|---|---|---|
| file | File | Arquivo (PDF, JPG, PNG) |
| tipo | string | rgp, seguro, survey, manutencao, nota_fiscal, foto, certificado, outro |
| categoria | string | registro, seguro, manutencao, inspecao, foto, certificado, outro |

**Response (201):**
```json
{
  "id": "uuid-do-documento",
  "hash": "a1b2c3d4e5f6...",
  "storage_path": "ativos/YA-IATE-2024-0001/docs/uuid.pdf",
  "chain_valid": true,
  "storage": "S3 WORM",
  "integrity_verified": true
}
```

---

### GET /documentos/{id}
Obter detalhes do documento.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "id": "uuid-do-documento",
  "ativo_id": "YA-IATE-2024-0001",
  "nome_arquivo": "seguro_2024.pdf",
  "tipo": "seguro",
  "categoria": "seguro",
  "hash_sha256": "a1b2c3d4e5f6...",
  "tamanho_bytes": 1048576,
  "mime_type": "application/pdf",
  "storage_path": "ativos/YA-IATE-2024-0001/docs/uuid.pdf",
  "status": "verified",
  "uploaded_at": "2024-01-15T14:30:00Z",
  "validado_em": "2024-01-15T14:30:02Z",
  "hash_anterior": "hash-do-documento-anterior"
}
```

---

### GET /documentos/{id}/download
Obter URL para download.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "url": "https://s3.amazonaws.com/bucket/path?signature...",
  "expires_in": 3600
}
```

---

## 4. Integridade

### GET /integridade/{doc_id}/verify
Verificar integridade do documento.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "document_id": "uuid-do-documento",
  "hash_original": "a1b2c3d4e5f6...",
  "is_valid": true,
  "storage": "S3 WORM",
  "verified_at": "2024-01-15T14:30:02Z"
}
```

**Response (200) - Inválido:**
```json
{
  "document_id": "uuid-do-documento",
  "hash_original": "a1b2c3d4e5f6...",
  "is_valid": false,
  "storage": "S3 WORM",
  "verified_at": "2024-01-15T14:30:02Z",
  "warning": "Document integrity compromised"
}
```

---

### GET /integridade/ativo/{ativo_id}/relatorio
Gerar relatório de integridade do ativo.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "ativo_id": "YA-IATE-2024-0001",
  "total_documentos": 12,
  "documentos_verificados": 12,
  "documentos_alterados": 0,
  "documentos_pendentes": [],
  "status": "VERIFICADO",
  "storage": "S3 WORM",
  "gerado_em": "2024-01-15T10:00:00Z"
}
```

---

## 5. Assinatura (Stripe)

### POST /payments/checkout/subscription
Criar sessão de checkout Stripe para assinatura.

**Request Body:**
```json
{
  "plan_type": "marina",
  "success_url": "https://...",
  "cancel_url": "https://..."
}
```

---

### POST /payments/checkout/dossier
Criar sessão de checkout Stripe para certificação de dossiê (pagamento único).

**Request Body:**
```json
{
  "dossier_level": "superyacht",
  "ativo_id": "YA-...",
  "success_url": "https://...",
  "cancel_url": "https://..."
}
```

**Response (200):**
```json
{
  "url": "https://checkout.stripe.com/c/pay/...",
  "session_id": "cs_..."
}
```

---

### POST /subscriptions/webhook
Webhook do Stripe para processar eventos.

**Headers:**
```
stripe-signature: {signature}
```

**Eventos processados:**
- `checkout.session.completed`
- `invoice.payment_succeeded`
- `invoice.payment_failed`
- `customer.subscription.deleted`

---

### GET /subscriptions/status
Obter status da assinatura.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
{
  "plano": "pro",
  "status": "active",
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-02-01T00:00:00Z"
}
```

---

## 6. Eventos

### GET /eventos/ativo/{ativo_id}
Listar eventos do ativo.

**Headers:**
```
Authorization: Bearer {token}
```

**Response (200):**
```json
[
  {
    "id": "uuid-do-evento",
    "ativo_id": "YA-IATE-2024-0001",
    "tipo": "manutencao",
    "subtipo": "preventiva",
    "titulo": "Troca de óleo e filtros",
    "data_evento": "2024-01-15",
    "prestador": "Marina da Glória",
    "custo": 15000.00,
    "moeda": "BRL"
  }
]
```

---

### POST /eventos/ativo/{ativo_id}
Criar novo evento.

**Headers:**
```
Authorization: Bearer {token}
```

**Request Body:**
```json
{
  "tipo": "manutencao",
  "subtipo": "preventiva",
  "titulo": "Troca de óleo e filtros",
  "descricao": "Troca de óleo e filtros do motor principal",
  "data_evento": "2024-01-15",
  "prestador": "Marina da Glória",
  "custo": 15000.00,
  "moeda": "BRL"
}
```

**Response (201):**
```json
{
  "id": "uuid-do-evento",
  "ativo_id": "YA-IATE-2024-0001",
  "tipo": "manutencao",
  "subtipo": "preventiva",
  "titulo": "Troca de óleo e filtros",
  "data_evento": "2024-01-15",
  "created_at": "2024-01-15T14:30:00Z"
}
```

---

## 7. Brokers

### POST /brokers/brokers
Criar novo broker (requer privilégios ou solicitação).

**Request Body:**
```json
{
  "user_id": "uuid",
  "company_name": "Oceanic Brokers",
  "license_number": "BR-123456",
  "email": "broker@oceanic.com",
  "phone": "+5511999999999",
  "commission_rate": 0.15
}
```

---

### POST /brokers/deals
Criar nova transação (venda/aluguel).

**Request Body:**
```json
{
  "broker_id": "uuid",
  "deal_type": "sale",
  "ativo_id": "YA-...",
  "deal_value": 5000000.0,
  "dossier_required": true,
  "dossier_level": "superyacht"
}
```

---

## 8. Seguradoras

### POST /insurance/companies
Cadastrar seguradora parceira.

---

### POST /insurance/verify-dossier
Verificar se o dossiê atende aos requisitos da seguradora.

**Request Body:**
```json
{
  "ativo_id": "YA-...",
  "company_id": "uuid"
}
```

---

## Códigos de Erro

| Código | Descrição |
|---|---|
| 400 | Bad Request - Dados inválidos |
| 401 | Unauthorized - Token inválido |
| 403 | Forbidden - Sem permissão |
| 404 | Not Found - Recurso não encontrado |
| 422 | Unprocessable Entity - Validação falhou |
| 500 | Internal Server Error - Erro no servidor |

**Resposta de erro:**
```json
{
  "detail": "Mensagem do erro"
}
```

---

## Rate Limiting

| Endpoint | Limite |
|---|---|
| /auth/* | 5/minuto |
| /ativos/* | 60/minuto |
| /documentos/upload/* | 10/minuto |
| /documentos/* | 30/minuto |
| /integridade/* | 60/minuto |

---

**Versão da API:** v1
**Última atualização:** 2026-04-25