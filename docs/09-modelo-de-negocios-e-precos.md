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
- **secundária:** BRL (R$) — conversão automática via Stripe
- **为什么：** Estabilidade cambial, apelo internacional

---

## 2. Planos de Preços

### 2.1 Estrutura de Planos

| Plano | Preço | Período | Para Quem |
|---|---|---|---|
| **Free** | $0 | Forever | Aquisição, teste |
| **Marina Standard** | $250/mês | Mensal | Marinas pequenas/médias |
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
| Suporte | Comumidade |

#### Marina Standard ($250/mês)

| Inclui | Limite |
|---|---|
| Ativos gerenciados | unlimited |
| Dashboard agregador | ✓ |
| API access | ✓ |
| Fleet management | ✓ |
| Real-time monitoring | ✓ |
| White-label ready | ✓ |
| Suporte | Prioritário |

#### Dossier Certification (One-time)

| Nível | Preço | Descrição |
|---|---|---|
| **Compact** | $200 | Até 39 pés |
| **Executive** | $400 | 40 a 79 pés |
| **Superyacht** | $600 | 80+ pés |

#### Plano Pro Annual ($900/ano)

| Inclui | Benefício |
|---|---|
| Tudo do Pro | ✓ |
| **Desconto** | 25% ($300 ahorrado) |
| Prioridade suporte | ✓ |
| Beta features | ✓ |

#### Plano Marina (B2B)

| Inclui | Para Marina |
|---|---|
| Ativos gerenciados | unlimited |
| Dashboard agregador | ✓ |
|white-label | sob consulta |
| API access | ✓ |
| Cobrança centralizada | ✓ |
| Relatórios | ✓ |
| Support dedicado | ✓ |

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

### 3.1 Por que $100?

| Comparativo | Valor | % do Custo |
|---|---|---|
| Atracação lancha 30 pés | R$2.500/mês | 0.1-2% |
| Atracação iate 100 pés | R$10.000+/mês | <0.1% |
| Valor do ativo | R$2MM - R$50MM | <0.01% |

### 3.2 Mensagem de Posicionamento

> "Por menos de 0.1% do valor do seu iate,-documents que aumentam o valor de venda em 10-30%."

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
| Quer gerar dossier | Só Pro |
| Quer hash de integridade | Precisa Pro |
| Quer classificar ativo | Precisa Pro |
| Venda do ativo próxima | Upgrade compuls |

### 4.3 Trial

- **Sem trial** — Free forever já é entry
-Usuário pode usar free → sentir valor → upgrade natural

---

## 5. Modelo B2B2C

### 5.1 Como Funciona

```
Marina (cliente B2B)
       │
       ▼
   Paga $100/mês
   por usuário
       │
       ▼
Cliente da marina
   usa Free com
   benefícios Marina
       │
       ▼
Yachts Atlas receita
  $100 × n clientes
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
| Marina small | 10 | $1.000 |
| Marina médios | 50 | $5.000 |
| Marina grande | 100 | $10.000 |
| Rede (ex: BR Marinas) | 500 | $50.000 |

---

## 6. Precificação por Região

### 6.1 Estratégia

| Região | Moeda | Preço | Justificativa |
|---|---|---|---|
| **BR** | USD ($) | $100 | Estabilidade, internacional |
| **LATAM** | USD ($) | $100 | Mesma estratégia |
| **USA** | USD ($) | $100 | Mercado principal |
| **EU** | EUR (€) | €90 | Paridade USD |

### 6.2 Opção Parcelado (BR)

| Parcelas | Valor | Total | Juros |
|---|---|---|---|
| 12x | $108/mês | $1.296 | ~0% (promoção launch) |

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

### 7.2 payment Methods

| Método | Disponível |
|---|---|
| Cartão de crédito | ✓ |
|Cartão debit | ✓ |
| Boleto (BR) | ✓ (future) |
| PIX (BR) | ✓ (future) |
| Apple Pay | ✓ |
| Google Pay | ✓ |

### 7.3 Payout

- Conta Wise EUA (R$0 setup)
- Taxa Stripe: 2.9% + R$0.39

---

## 8. discounts e Campanhas

### 8.1 Discounts

| Discount | Condição |
|---|---|
| 25% annual | Pago anual ($900 vs $1.200) |
| 15% B2B | Marina com 10+ clientes |
| 20% early adopter | Primeiros 100 usuários |

### 8.2 Campanhas possible

| Campanha | Oferta |
|---|---|
| Launch | 50% off primeiro ano |
| Referência | 1 mês free por indicado |
| Marina partnership | 30% off primeiro ano |

---

## 9. Churn e Retenção

### 9.1 Churn

| Métrica | Target |
|---|---|
| Monthly churn | <5% |
| Annual churn | <15% |

### 9.2 Retenção

| Estratégia | Como |
|---|---|
| Valor contínuo | Notificações, alertas, docs vencer |
| Dossier |Gerar dossier = need retorno |
| Classificação | Upgrade = necessidade |
| Rede | Marinas indicam = stickiness |

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