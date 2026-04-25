# Yachts Atlas — Roadmap e MVP

## 1. Visão do Produto

### 1.1 Produto Mínimo Viável (MVP)

O MVP deve ter o suficientes para:
- Demonstrar o diferencial (hash + classificação)
- Gerar primeiras conversões
- Validar o modelo

### 1.2 Definição do MVP

| Feature | Prioridade | Justificativa |
|---|---|---|
| Cadastro de ativo | Must have | Core do produto |
| Upload documentos | Must have | Feature básica |
| Hash SHA-256 | Must have | DIFERENCIAL |
| Classificação Bronze/Silver/Gold | Must have | DIFERENCIAL |
| Barra de progresso | Must have | UI/UX |
| Histórico do ativo | Must have | Core |
| Login/Autenticação | Must have | Segurança |
| Dashboard básico | Should have | UX |
| Download documentos | Should have | UX |
| Dossier Basic | Could have | V1 |
| Notifications | Could have | V2 |

---

## 2. Roadmap de Features

### 2.1 V1: MVP (Meses 1-3)

```
┌─────────────────────────────────────────────────────────────────┐
│                    MVP — MINIMUM VIABLE PRODUCT                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Cadastro   │  │   Upload    │  │    Hash    │        │
│  │   Ativo     │  │  Documento  │  │  SHA-256   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                │                │                       │
│         ▼                ▼                ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Classificação │  │  Histórico  │  │   Login   │        │
│  │Bronze/Silver │  │            │  │           │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│         │                │                                  │
│         ▼                ▼                                  │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │    Dash      │  │   Progress  │                        │
│  │   Board     │  │   Bar      │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 V2: Produto Completo (Meses 4-6)

| Feature | Descrição |
|---|---|
| Dossier Basic | Gerar relatório |
| Dossier Completo | + Histórico |
| Dossier Premium | + Hash, survey |
| Download PDF | Dossier em PDF |
| Notifications | Alertas docs vencendo |
| WhatsApp integration | Evolution API |
| Multi-idioma | PT/EN/ES |
| Search | Buscar documentos |
| TAGS | Organizar documentos |

### 2.3 V3: Escala (Meses 7-12)

| Feature | Descrição |
|---|---|
| API |para desenvolvedores |
| Integração EasyMarine | API conjunta |
| Plano Marina | white-label |
| Dashboard Marina | Gestão multiplas |
| Enterprise | Seguradoras |
| AI suggestions | Recomendações |
| Marketplace | Integração futura |

---

## 3. Cronograma Visual

### 3.1 Timeline

```
Mês:    1   2   3   4   5   6   7   8   9   10  11  12
        │   │   │   │   │   │   │   │   │   │   │   │
MVP:    ████████████████
V2:                     ████████████
V3:                                  ████████████████████
```

### 3.2 Marcos (Milestones)

| Marco | Mês | Critério |
|---|---|---|
| Beta Fechado | 2 | 10 usuários ativos |
| Alpha | 3 | 50 usuários |
| MVP Launch | 4 | Produto USável |
| 100 Usuários | 6 | 100 usuarios free |
| 10% Conversion | 6 | 10% free → Pro |
| 50 Marinas | 12 | Parcerias |
| 200 Usuários Pro | 12 | Receita estável |

---

## 4. Priorização de Features

### 4.1 Matriz de Priorização

| Feature | Valor | Esforço | Prioridade |
|---|---|---|---|
| Hash SHA-256 | Alto | Baixo | **Must** |
| Classificação | Alto | Médio | **Must** |
| Upload | Alto | Médio | **Must** |
| Login | Alto | Baixo | **Must** |
| Dashboard | Médio | Médio | **Should** |
| Dossier | Alto | Alto | **Should** |
| Notifications | Médio | Médio | **Could** |
| API | Médio | Alto | **Could** |
| white-label | Alto | Alto | **Future** |

### 4.2 RICE Scoring

| Feature | Reach | Impact | Confidence | Effort | Score |
|---|---|---|---|---|---|
| Hash | 100% | 10 | 100% | 2 | 500 |
| Classificação | 90% | 10 | 90% | 5 | 162 |
| Dossier | 70% | 10 | 80% | 8 | 70 |
| API | 50% | 8 | 70% | 10 | 28 |

---

## 5. Stack Técnica (Confirmada)

| Componente | Tecnologia |
|---|---|
| Backend | FastAPI |
| Database | Supabase |
| Storage | Supabase Storage |
| Auth | Supabase Auth |
| Analytics | Polars |
| WhatsApp | Evolution API |
| Frontend | Vite + React + Tailwind |
| Payments | Stripe |
| Hosting | EasyPanel/Docker |

---

## 6. Estrutura de Dados (Confirmada)

### 6.1 Tabelas Principais

- usuarios
- ativos
- documentos
- eventos
- ativos_usuarios
- classificacoes_log
- integridade_logs

### 6.2 APIs Principais

- /auth (signup, login, logout)
- /ativos (CRUD)
- /documentos (upload, download, verify)
- /eventos (CRUD)
- /dossier (gerar)
- /integridade (verify)

---

## 7. Critérios de Qualidade

### 7.1 Requisitos Não-Funcionais

| Requisito | Meta |
|---|---|
| Uptime | 99.5% |
| Load time | <2s |
| Upload | <5s (até 10MB) |
| Mobile | Responsivo |
| Browser | Modernos |
| Segurança | OWASP Top 10 |

### 7.2 Testes

| Tipo | Cobertura |
|---|---|
| Unitário | 80% |
| Integração | 60% |
| E2E | Happy path |
| Loading | 100 usuários |

---

## 8. Releases

### 8.1 Release Cycle

| Versão | Data | Mudanças |
|---|---|---|
| 0.1 | 2026-04 | Fundamentos |
| 0.2 | 2026-05 | Concorrência, modelo |
| 0.3 | 2026-06 | GTM, roadmap |
| 0.4 | 2026-07 | MVP |
| 0.5 | 2026-08 | Beta |
| 1.0 | 2026-09 | Launch |

### 8.2 Versionamento

```
MAJOR.MINOR.PATCH
  │    │    │
  │    │    └── Fixes, typos
  │    └── Novas features (backwards compatible)
  └── Breaking changes
```

---

## 9. Dependencies

### 9.1 Dependencies Técnicas

| Dependência | Versão | Uso |
|---|---|---|
| FastAPI | 0.100+ | Backend |
| Supabase | Latest | DB + Auth |
| Stripe | Latest | Payments |
| Tailwind | 3+ | CSS |
| React | 18+ | Frontend |

### 9.2 Dependencies Externas

| Serviço | Necessário | Prioridade |
|---|---|---|
| Stripe | Sim | Beta |
| Supabase | Sim | MVP |
| Evolution API | Sim | V2 |
| EasyPanel | Sim | Deploy |

---

## 10. Riscos

| Risco | Probabilidade | Impacto | Mitigação |
|---|---|---|---|
| Stripe nãoapproved | Média | Alto | PayPal backup |
| Concorrente copia | Média | Médio | Patent, first mover |
| Supabase downtime | Baixa | Alto | Backup strategy |
| Taxa cambio | Alta | Médio | USD pricing only |
| Early adopters slow | Alta | Médio | Referral bonus |

---

## 11. Versão

v0.1 — Roadmap e MVP

---

## 12. Data

2026-04-25