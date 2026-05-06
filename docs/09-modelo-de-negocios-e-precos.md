# Yachts Atlas — Modelo de Negócios e Preços

## 1. Modelo de Receita

### 1.1 Tipo de Receita

| Tipo | Descrição |
|---|---|
| **SaaS Recorrente** | Assinatura mensal/anual em USD |
| **Freemium** | Plano free para aquisição |
| **B2B2C** | Marina paga → cliente dela usa |

### 1.2 Moeda de Cobrança

- **Primária:** USD ($)
- **Secundária:** BRL (R$) — conversão automática via Stripe
- **Motivo:** Estabilidade cambial e posicionamento internacional

---

## 2. Planos de Preços

### 2.1 Estrutura de Planos

| Plano | Preço | Período | Para Quem |
|---|---|---|---|
| **Free** | $0 | Permanente | Aquisição e teste |
| **Marina Standard** | $250/mês | Mensal | Marinas (Trojan Horse) |
| **Enterprise** | $500/mês | Mensal | Grandes redes, seguradoras |

### 2.2 Detalhamento de Planos

#### Plano Free

| Inclui | Limite |
|---|---|
| Registro de 1 ativo | 1 |
| Dados básicos | ✓ |
| Documentos | 3 |
| Histórico | 6 meses |
| **Hash de integridade** | ✗ |
| **Dossier** | ✗ |
| **Classificação** | ✗ |
| Suporte | Comunidade |

#### Marina Standard ($250/mês)

| Inclui | Limite |
|---|---|
| Ativos gerenciados | Ilimitado |
| Dashboard agregador | ✓ |
| API | ✓ |
| Gestão de frota | ✓ |
| Monitoramento em tempo real | ✓ |
| White-label ready | ✓ |
| Suporte | Prioritário |

#### Dossier Certification (One-time)

| Nível | Preço | Descrição |
|---|---|---|
| **Compact** | $200 | Até 39 pés |
| **Executive** | $400 | 40 a 79 pés |
| **Superyacht** | $600 | 80+ pés |

#### Plano Enterprise

| Inclui | Para Seguradoras/Frotas |
|---|---|
| Tudo do Marina | ✓ |
| API completa | ✓ |
| Integração customizada | ✓ |
| Account manager | ✓ |
| SLA garantido | ✓ |
| Audit trail completo | ✓ |

---

## 3. Estratégia de Preços

### 3.1 Por que $250/mês?

| Comparativo | Valor | % do Custo |
|---|---|---|
| Atracação lancha 30 pés | R$2.500/mês | 0.1-2% |
| Atracação iate 100 pés | R$10.000+/mês | <0.1% |
| Valor do ativo | R$2MM - R$50MM | <0.01% |

### 3.2 Mensagem de Posicionamento

> "Por uma fração do valor do ativo, sua marina organiza a operação e ainda monetiza dossiês com split 50/50."

### 3.3 Justificativa de ROI

- Ativo de R$5MM com documentação completa vende 15-30% mais rápido
- Seguradora com histórico verificado reduz prêmio
- Dossier premium = vantagem na negociação

---

## 4. Freemium Strategy

### 4.1 Funil de Conversão

```
Plano Free              Plano Pro              Plano Marina
    │                      │                       │
    ▼                      ▼                       ▼
┌────────┐           ┌────────┐            ┌────────┐
│ Usuário │    10%   │ Usuário │    5%    │ Marina │
│ Free   │────────▶│ Pro    │────────▶│ Enterprise│
└────────┘           └────────┘            └────────┘
```

### 4.2 Gatilhos de Upgrade

| Gatilho | Quando |
|---|---|
| Limite de documentos | Depois de 3 docs |
| Quer gerar dossiê | Plano pago |
| Quer hash de integridade | Plano pago |
| Quer classificar ativo | Plano pago |
| Venda do ativo próxima | Upgrade natural |

### 4.3 Trial

- **Sem trial** — o Free permanente já cumpre essa função
- Usuário entra no Free, percebe valor e evolui para plano pago

---

## 5. Modelo B2B2C

### 5.1 Como Funciona

```
Marina (cliente B2B)
       │
       ▼
   Paga $250/mês
       │
       ▼
   Revende Dossiês
   ($200 - $600)
       │
       ▼
Yachts Atlas compartilha
50% de ROI (split 50/50)
```

### 5.2 Marina Como Cliente

| Para Marina | Benefício |
|---|---|
| Gerenciar ativos clientes | ✓ |
| Dashboard agregador | ✓ |
| Valor agregado | Oferecer doc premium |
| Diferencial |Marina com Yachts Atlas |

### 5.3 Exemplo de Receita

| Cenário | Clientes | Receita/mês |
|---|---|---|
| Marina pequena | 10 | $1.000 |
| Marina média | 50 | $5.000 |
| Marina grande | 100 | $10.000 |
| Rede (ex: BR Marinas) | 500 | $50.000 |

---

## 6. Precificação por Região

### 6.1 Estratégia

| Região | Moeda | Preço | Justificativa |
|---|---|---|---|
| **BR** | USD ($) | $250 | Estabilidade, internacional |
| **LATAM** | USD ($) | $250 | Mesma estratégia |
| **USA** | USD ($) | $250 | Mercado principal |
| **EU** | EUR (€) | €225 | Referência cambial do plano |

### 6.2 Opção Parcelado (BR)

| Parcelas | Valor | Total | Juros |
|---|---|---|---|
| 12x | $250/mês | $3.000 | Sob política comercial |

---

## 7. Payment Setup

### 7.1 Stripe Configurado

| Integração | Status |
|---|---|
| Stripe Checkout | ✓ Código pronto |
| Assinaturas recorrentes | ✓ |
| Webhook | ✓ |
| Multi-moeda | ✓ |
| Conversão automática BRL | ✓ |

### 7.2 Métodos de Pagamento

| Método | Disponível |
|---|---|
| Cartão de crédito | ✓ |
| Cartão de débito | ✓ |
| Boleto (BR) | ✓ (futuro) |
| PIX (BR) | ✓ (futuro) |
| Apple Pay | ✓ |
| Google Pay | ✓ |

### 7.3 Payout

- Conta Wise EUA (R$0 setup)
- Taxa Stripe: 2.9% + R$0.39

---

## 8. Descontos e Campanhas

### 8.1 Descontos

| Desconto | Condição |
|---|---|
| 25% anual | Pago anual sob política comercial |
| 15% B2B | Marina com 10+ clientes |
| 20% early adopter | Primeiras 100 marinas |

### 8.2 Campanhas Possíveis

| Campanha | Oferta |
|---|---|
| Launch | 50% off no primeiro ciclo |
| Referência | 1 mês free por indicado |
| Marina partnership | 30% off no primeiro ciclo |

---

## 9. Churn e Retenção

### 9.1 Churn

| Métrica | Target |
|---|---|
| Churn mensal | <5% |
| Churn anual | <15% |

### 9.2 Retenção

| Estratégia | Como |
|---|---|
| Valor contínuo | Notificações, alertas e documentos a vencer |
| Dossiê | Geração recorrente de valor para marina e proprietário |
| Classificação | Upgrade = necessidade |
| Rede | Marinas indicam novas marinas (efeito de rede) |

---

## 10. MRR Projections

### 10.1 Cenário Conservador

| Ano | Usuários | MRR | Annual |
|---|---|---|---|
| 1 | 100 | $10.000 | $120.000 |
| 2 | 500 | $50.000 | $600.000 |
| 3 | 1.500 | $150.000 | $1.8M |

### 10.2 Cenário Otimista

| Ano | Usuários | MRR | Annual |
|---|---|---|---|
| 1 | 500 | $50.000 | $600.000 |
| 2 | 2.000 | $200.000 | $2.4M |
| 3 | 5.000 | $500.000 | $6M |

---

## 11. Versão

v0.1 — Modelo de Negócios e Preços

---

## 12. Data

2026-04-25
