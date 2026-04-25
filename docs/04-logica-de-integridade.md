# Yachts Atlas — Lógica de Integridade

## 1. Conceito

A integridade é o que diferencia o Yachts Atlas de "um Google Drive melhorado".

Cada documento tem **prova criptográfica** de que não foi alterado desde o momento do upload.

**IMPORTANTE:** Supabase e criptografia sozinhos NÃO garantem imutabilidade real.

- **Supabase** = banco PostgreSQL — qualquer admin pode fazer UPDATE/DELETE
- **Criptografia** = garante confidencialidade, NÃO que o dado não foi alterado

Para imutabilidade real, usamos **3 níveis progressivos**.

---

## 1.5. Níveis de Imutabilidade

### Nível 1 — Hash Chain (Mínimo Viável)

```
┌────────────────────────────────────────────────────��┐
│  CADA REGISTRO REFERENCIA O ANTERIOR                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Documento 001 ──hash──▶ Documento 002             │
│       │                        │                    │
│       │                        │                    │
│   hash_001                 hash_002                 │
│   (anterior: null)       (anterior: hash_001)      │
│                                                     │
│  Se alterar doc 001 → todos os hashes quebram      │
│  Detecção automática, mas dependo de mim como custódio│
└─────────────────────────────────────────────────────┘
```

### Nível 2 — S3 Object Lock (RECOMENDADO)

```
┌─────────────────────────────────────────────────────┐
│  AWS S3 COM OBJECT LOCK (WORM)                      │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Bucket: yachts-docs                                │
│  ├── Modo: WORM (Write Once Read Many)              │
│  ├── Retention: 1 ano mínimo                        │
│  └── Legal Hold: permanente se necessário           │
│                                                     │
│  Resultado:                                         │
│  • Impossível alterar arquivo (nem eu, nem AWS)    │
│  • Impossível deletar arquivo                      │
│  • CloudTrail registra cada acesso                  │
│  • Juridicamente defensável                         │
│  • Custo: ~$0.01/GB/mês                             │
└─────────────────────────────────────────────────────┘
```

### Nível 3 — Âncora Blockchain (Future/Enterprise)

```
┌─────────────────────────────────────────────────────┐
│  HASH NO BLOCKCHAIN PÚBLICO                        │
├─────────────────────────────────────────────────────┤
│                                                     │
│  S3: documento.pdf (arquivo)                        │
│       │                                            │
│       ▼                                            │
│  SHA-256 → "a1b2c3d4e5f6..."                        │
│       │                                            │
│       ▼                                            │
│  Blockchain (Polygon/Ethereum)                      │
│  ├── Transação registra o hash                     │
│  ├── Bloco: imutável permanentemente                │
│  └── Qualquer pessoa verifica sem depender de mim   │
│                                                     │
│  Custo: ~$0.01 por transação                        │
│  Disponibilidade: Enterprise (futuro)               │
└─────────────────────────────────────────────────────┘
```

### Resumo Comparativo

| Nível | Imutabilidade | Custo | Complexidade | Quando Usar |
|---|---|---|---|---|
| **Hash Chain** | Detectável | $0 | Baixa | MVP |
| **S3 WORM** | Juridicamente prova | $0.01/GB | Média | MVP+ |
| **Blockchain** | Publicamente verificável | $0.01/tx | Alta | Enterprise |

---

## 2. Implementação Recomendada (MVP)

Para o MVP, usamos **Nível 1 + Nível 2**:

```
┌─────────────────────────────────────────────────────┐
│              ARQUITETURA MVP                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  FRONTEND                                           │
│     │                                               │
│     ▼                                               │
│  BACKEND (FastAPI)                                  │
│     │                                               │
│     ├──▶ Supabase                                  │
│     │    ├── Metadados (hash chain)                │
│     │    ├── Histórico de eventos                  │
│     │    └── Logs de auditoria                     │
│     │                                               │
│     └──▶ AWS S3 (Object Lock WORM)                  │
│          ├── Documentos reais                      │
│          ├── CloudTrail (logs de acesso)           │
│          └── Impossível alterar/deletar           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### Fluxo de Upload (Com Imutabilidade Real)

```python
# 1. Recebe arquivo
arquivo = request.files['documento']

# 2. Calcula SHA-256
hash_arquivo = sha256(arquivo.read())

# 3. Busca hash do último documento (para chain)
ultimo_hash = get_ultimo_hash_do_ativo(ativo_id)

# 4. Gera nome único no S3
storage_path = f"ativos/{ativo_id}/docs/{uuid}.pdf"

# 5. Upload para S3 com Object Lock
s3.put_object(
    Bucket='yachts-docs',
    Key=storage_path,
    Body=arquivo,
    ObjectLockMode='COMPLIANCE',  # WORM
    ObjectLockRetentionPeriodDays=365
)

# 6. Registra no Supabase (metadados + chain)
registrar_documento(
    ativo_id=ativo_id,
    hash_sha256=hash_arquivo,
    hash_anterior=ultimo_hash,
    storage_path=storage_path,
    uploaded_by=user_id
)

# 7. Retorna ao usuário
return {
    "id": doc_id,
    "hash": hash_arquivo,
    "chain_valid": True,
    "storage": "S3 WORM",
    "integrity_verified": True
}
```

---

## 5. O Que Pode Ser Alterado

| Dado | Pode Alterar? | Por Quê |
|---|---|---|
| Classificação do ativo | Sim | Evolução natural |
| Fotos do ativo | Sim | Atualizações |
| Dados técnicos | Sim | correction |
| Contato do dono | Sim | Mudança de dados |
| Notas fiscais | Sim | Inserção atrasada |

---

## 6. O Que NUNCA Pode Ser Alterado

| Dado | Não Pode Alterar? | Motivo |
|---|---|---|
| Documentos uploadados | NÃO | Prova jurídica |
| Hash do documento | NÃO | Identidade do arquivo |
| Timestamp de upload | NÃO | Data real |
| Eventos do histórico | NÃO | Linha do tempo |
| Registros de seguro | NÃO | Prova de vigência |
| Relatórios de survey | NÃO | Documento técnico |

---

## 7. Como Um Registro Nasce

```
┌─────────────────┐
│  Usuário uploading │
│    arquivo.pdf    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Servidor calcula │
│  SHA-256 do file  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Gera timestamp   │
│  UTC + timezone   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Registra no      │
│  banco + storage │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Retorna hash    │
│  + proof ao user │
└─────────────────┘
```

---

## 8. Algoritmo de Hash

### SHA-256

Cada arquivo recebe um hash único:

```
SHA-256(arquivo) = a1b2c3d4e5f6...
```

**Exemplo real:**

```
Arquivo: seguro_2024.pdf
Hash SHA-256: 8f6e9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1
```

Se alguém modificar **1 byte** do arquivo, o hash muda completamente.

---

## 9. Estrutura do Registro de Integridade

```json
{
  "id": "doc-2024-001",
  "ativo_id": "YA-IATE-2024-0001",
  "nome_arquivo": "seguro_2024.pdf",
  "tipo": "seguro",
  "hash_sha256": "8f6e9a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1",
  "tamanho_bytes": 1048576,
  "mime_type": "application/pdf",
  "storage_path": "assets/YA-IATE-2024-0001/docs/seguro_2024.pdf",
  "uploaded_by": "user-123",
  "uploaded_at": "2024-01-15T14:30:00Z",
  "timestamp_blockchain": null,
  "status": "verified",
  "validado_em": "2024-01-15T14:30:02Z",
  "checksum_original": true
}
```

---

## 10. Verificação de Integridade

### Verificação Automática

A qualquer momento, o sistema pode verificar se o documento é original:

```python
def verificar_integridade(doc_id: str) -> bool:
    doc = buscar_documento(doc_id)
    arquivo_atual = baixar_do_storage(doc.storage_path)

    hash_atual = sha256(arquivo_atual)
    hash_original = doc.hash_sha256

    return hash_atual == hash_original
```

### Verificação Manual (para o usuário)

O usuário pode verificar qualquer documento:

1. Baixar o arquivo
2. Calcular SHA-256 localmente
3. Comparar com o hash shown no sistema

---

## 11. Timestamp e Carimbo de Tempo

### Timestamp UTC

Todo registro tem timestamp preciso:

```
uploaded_at: 2024-01-15T14:30:00Z
```

Formato: ISO 8601 com UTC (Z = Zulu = UTC)

### Carimbo de Tempo (Timestamp Authority)

Para documentos jurídicos, o timestamp pode ser validado por uma TSA (Timestamp Authority):

```
carimbo_ts = {
    "timestamp": "2024-01-15T14:30:00Z",
    "tsa": "https://timestamp.autoridade.br",
    "assinatura_digital": "...",
    "certificado_tsa": "..."
}
```

---

## 12. Encadeamento de Eventos (Hash Chain)

Cada evento referencia o anterior, criando uma **cadeia imutável**:

```
┌─────────────────────────────────────────────────┐
│  Evento 001: Compra                              │
│  hash: a1b2c3...                                │
│  anterior: null                                 │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  Evento 002: Manutenção                          │
│  hash: d4e5f6...                                 │
│  anterior: a1b2c3...  (referencia ao evento 001)  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│  Evento 003: Seguro                               │
│  hash: g7h8i9...                                 │
│  anterior: d4e5f6...  (referencia ao evento 002)  │
└─────────────────────────────────────────────────┘
```

Se alguém tentar alterar um evento antigo, a cadeia quebra.

---

## 13. Versionamento

### Documentos com Versão

Para dados que PODEM ser alterados (não documentos):

```json
{
  "ativo_id": "YA-IATE-2024-0001",
  "campo": "/modelo",
  "versoes": [
    {
      "valor": "78 Flybridge",
      "alterado_por": "user-123",
      "alterado_em": "2024-01-10T10:00:00Z"
    },
    {
      "valor": "80 Flybridge",
      "alterado_por": "user-456",
      "alterado_em": "2024-03-15T14:30:00Z"
    }
  ],
  "versao_atual": 2
}
```

**Regras:**
- Valor anterior nunca é apagado
- Quem alterou =Registrado
- Quando alterou = Registrado
- Por quê alterou = Opcional (campo descrição)

---

## 14. Logs de Auditoria

| Ação | Logado | Quem Pode Ver |
|---|---|---|
| Upload documento | ✓ | Dono, admins |
| Download documento | ✓ | Dono |
| Alteração dado | ✓ | Dono |
| Verificação hash | ✓ | Dono |
| Exclusão documento | ✓ | Dono, admins |
| Classificação alterada | ✓ | Dono |

---

## 15. Prova de Integridade (Para o Dossier)

No dossier premium, inclui-se **relatório de integridade**:

```
══════════════════════════════════════════════════════════
        RELATÓRIO DE INTEGRIDADE — YACHTS ATLAS
══════════════════════════════════════════════════════════

Ativo: YA-IATE-2024-0001
Iate: Azimut 78 Flybridge (2018)
Dono: João Silva
Relatório gerado em: 2024-05-01T10:00:00Z

───────────────────────────────────────────────────────
DOCUMENTOS VERIFICADOS
───────────────────────────────────────────────────────

✓ RGP — hash verificado em 2024-05-01
✓ Seguro 2024 — hash verificado em 2024-05-01
✓ Survey 2023 — hash verificado em 2024-05-01
✓ Nota fiscal manutenção — hash verificado em 2024-05-01

───────────────────────────────────────────────────────
INTEGRIDADE GERAL
───────────────────────────────────────────────────────

Status: VERIFICADO
Total documentos: 12
Documentos íntegros: 12
Documentos alterados: 0

══════════════════════════════════════════════════════════
```

---

## 16. Assinatura Digital (Opcional Premium)

ParaMaximum de segurança, documentos podem ser assinados digitalmente:

```
├── Documento PDF
├── Hash SHA-256
├── Assinatura do Yachts Atlas (chave privada)
├── Certificado digital (ICP-Brasil)
└── Timestamp da assinatura
```

**Benefício:**
- Prova jurídica de autenticidade
- Não repúdio (dono não pode negar que assinou)

---

## 17. Resumo: Fluxo de Integridade

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Upload     │────▶│    Hash      │────▶│  Registro   │
│  Arquivo     │     │   SHA-256    │     │   Completo  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                  │
                     ┌──────────────┐               ▼
                     │  Verificação │◀────┌──────────────┐
                     │    manual    │     │   Storage    │
                     └──────────────┘     │  + Banco     │
                                          └──────────────┘
```

---

## 18. Versão

v0.2 — Lógica de Integridade (com S3 WORM)

---

## 19. Data

2026-04-25