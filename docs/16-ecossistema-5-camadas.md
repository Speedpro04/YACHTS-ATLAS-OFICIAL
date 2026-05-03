# Yachts Atlas — Ecossistema de 5 Camadas

## Visão Geral

O Yachts Atlas opera como um ecossistema de 5 camadas interconectadas, criando um efeito de rede onde cada camada fortalece as outras:

```
┌─────────────────────────────────────────────────────────────────┐
│                    ECOSISTEMA YACHTS ATLAS                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Camada 1: Yachts Atlas (Plataforma)                           │
│  ├─ Tecnologia de integridade                                   │
│  ├─ Infraestrutura S3 WORM                                     │
│  ├─ API e integrações                                          │
│  └─ Dashboard e relatórios                                      │
│                                                                 │
│  Camada 2: Marinas (Clientes B2B)                              │
│  ├─ $250/mês (Standard) ou $500/mês (Enterprise)               │
│  ├─ Gestão completa da frota                                   │
│  ├─ Monitoramento em tempo real                                │
│  └─ Revenda + comissão nos dossiês                            │
│                                                                 │
│  Camada 3: Proprietários (Clientes Finais)                     │
│  ├─ Acesso via marina                                          │
│  ├─ Proteção de ativos de milhões                              │
│  ├─ Valorização 10-30% na venda                               │
│  └─ Dossiês: $200-$600                                         │
│                                                                 │
│  Camada 4: Seguradoras (Parceiras)                             │
│  ├─ Dossiê aceito como documento válido                        │
│  ├─ Reduz sinistros — interesse mútuo                         │
│  ├─ Churn zero — exigência de mercado                         │
│  └─ Comissão: 10%                                             │
│                                                                 │
│  Camada 5: Brokers (Multiplicadores)                           │
│  ├─ Checklist padrão — como Carfax                            │
│  ├─ Dossiê condição de negociação                              │
│  ├─ CAC zero — brokers prospectam                             │
│  └─ Comissão: 15%                                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Camada 1: Yachts Atlas (Plataforma)

### Responsabilidades
- Fornecer tecnologia de integridade e rastreamento
- Manter infraestrutura S3 WORM imutável
- Desenvolver API e integrações
- Criar dashboard e relatórios

### Tecnologias
- **Backend:** FastAPI + Supabase
- **Storage:** AWS S3 WORM
- **Pagamentos:** Stripe
- **Frontend:** React + Vite + Tailwind

### APIs Disponíveis
- `/api/v1/auth` - Autenticação
- `/api/v1/ativos` - Gestão de ativos
- `/api/v1/documentos` - Upload e download
- `/api/v1/integridade` - Verificação de hash
- `/api/v1/payments` - Pagamentos Stripe
- `/api/v1/insurance` - Integração seguradoras
- `/api/v1/brokers` - Gestão de brokers

## Camada 2: Marinas (Clientes B2B)

### Modelo de Negócio
- **Mensalidade:** $250/mês (Standard) ou $500/mês (Enterprise)
- **Receita Adicional:** Comissão nos dossiês vendidos
- **Custo:** Baixo em relação ao valor dos ativos gerenciados

### Benefícios para Marinas
- Gestão completa da frota em um só lugar
- Monitoramento em tempo real
- Dashboard multi-ativos
- Suporte prioritário
- Diferencial competitivo no mercado
- Receita adicional com dossiês

### Fluxo de Integração
1. Marina contrata serviço ($250/mês)
2. Marina cadastra ativos dos clientes
3. Proprietários acessam via marina
4. Marina ganha comissão nos dossiês

### KPIs
- Número de ativos gerenciados
- Taxa de adoção dos proprietários
- Receita de comissões
- Churn (meta: <5%)

## Camada 3: Proprietários (Clientes Finais)

### Modelo de Acesso
- Acesso via marina (gratuito ou custo incluído)
- Dossiês comprados diretamente ($200-$600)

### Benefícios para Proprietários
- Proteção de ativos de milhões
- Valorização 10-30% na venda
- Seguro mais barato (redução de prêmio)
- Documentação imutável e rastreável
- Conveniência e centralização

### Níveis de Dossiê
- **Compact (até 45 pés):** $200
  - Lanchas esportivas
  - Day cruisers
- **Executive (46-79 pés):** $400
  - Iates de cruzeiro
  - Lazer familiar
- **Superyacht (80+ pés):** $600
  - Ultra-luxo
  - Alta complexidade

### Fluxo de Uso
1. Proprietário acessa via marina
2. Cadastra ativos e documentos
3. Sistema calcula progresso
4. Proprietário compra dossiê quando necessário
5. Dossiê é usado em negociações

## Camada 4: Seguradoras (Parceiras)

### Modelo de Parceria
- **Comissão:** 10% sobre prêmios de seguro
- **Integração:** API para verificação de dossiês
- **Benefício Mútuo:** Redução de sinistros

### Benefícios para Seguradoras
- Dossiê aceito como documento válido
- Redução de sinistros (documentação completa)
- Processo de cotação mais rápido
- Menos fraudes
- Churn zero (exigência de mercado)

### Fluxo de Integração
1. Seguradora se cadastra na plataforma
2. Recebe API key para integração
3. Verifica dossiês via API
4. Oferece descontos para ativos com dossiê
5. Processa pagamentos de comissão

### API de Integração
- `POST /api/v1/insurance/companies` - Criar seguradora
- `GET /api/v1/insurance/companies/{id}` - Obter seguradora
- `POST /api/v1/insurance/verify-dossier` - Verificar dossiê
- `GET /api/v1/insurance/companies/{id}/integrations` - Listar integrações

### KPIs
- Número de seguradoras parceiras
- Volume de prêmios processados
- Taxa de redução de sinistros
- Receita de comissões

## Camada 5: Brokers (Multiplicadores)

### Modelo de Parceria
- **Comissão:** 15% sobre comissões de transação
- **Integração:** Dashboard para gestão de deals
- **Benefício:** CAC zero (brokers prospectam)

### Benefícios para Brokers
- Checklist padrão (como Carfax)
- Dossiê condição de negociação
- Gestão de deals em um só lugar
- Comissão adicional
- Diferencial no mercado

### Fluxo de Integração
1. Broker se cadastra na plataforma
2. Cria deals para transações
3. Exige dossiê como condição
4. Ganha comissão na venda
5. Rastreia todas as transações

### API de Integração
- `POST /api/v1/brokers/brokers` - Criar broker
- `GET /api/v1/brokers/brokers/{id}` - Obter broker
- `POST /api/v1/brokers/deals` - Criar deal
- `GET /api/v1/brokers/brokers/{id}/deals` - Listar deals
- `POST /api/v1/brokers/deals/{id}/complete` - Completar deal

### KPIs
- Número de brokers ativos
- Volume de transações
- Taxa de conversão com dossiê
- Receita de comissões

## Efeito de Rede

### Como as Camadas se Fortalecem

**Marinas → Proprietários**
- Marinas oferecem acesso aos proprietários
- Proprietários usam dossiês em negociações
- Marinas ganham comissão

**Proprietários → Seguradoras**
- Proprietários com dossiê pagam menos seguro
- Seguradoras reduzem sinistros
- Seguradoras exigem dossiê

**Seguradoras → Marinas**
- Seguradoras exigem dossiê
- Marinas precisam do Atlas
- Churn zero

**Brokers → Proprietários**
- Brokers exigem dossiê em negociações
- Proprietários compram dossiê
- Brokers ganham comissão

**Brokers → Marinas**
- Brokers recomendam marinas com Atlas
- Marinas ganham novos clientes
- Network effect

### Barreira de Entrada

**Tempo como Barreira**
- Quanto mais ativos na plataforma, mais valioso o histórico
- Difícil replicar a base de dados
- Efeito de rede de dados

**Padrão de Mercado**
- Dossiê vira exigência (como Carfax)
- Difícil competir com padrão estabelecido
- Churn zero

**Integrações**
- Seguradoras integradas não mudam facilmente
- Brokers com workflow estabelecido
- Marinas com processos automatizados

## Estratégia de Lançamento

### Fase 1: Marinas (Meses 1-3)
- Focar em 5-10 marinas piloto
- Validar modelo B2B2C
- Testar preços $250/mês
- Meta: 5 marinas ativas

### Fase 2: Seguradoras (Meses 4-6)
- Fechar 2-3 parcerias com seguradoras
- Integrar APIs
- Criar programa de descontos
- Meta: 3 seguradoras parceiras

### Fase 3: Brokers (Meses 7-12)
- Recrutar 10-20 brokers
- Criar programa de comissões
- Integrar com fluxo de trabalho
- Meta: 15 brokers ativos

### Fase 4: Escala (Ano 2+)
- Expandir internacionalmente
- White-label para grandes redes
- Marketplace de ativos
- Meta: 50+ marinas, 10+ seguradoras, 50+ brokers

## Métricas de Sucesso

### Métricas de Ecossistema
- **Marinas Ativas:** 50 em 12 meses
- **Seguradoras Parceiras:** 10 em 12 meses
- **Brokers Ativos:** 50 em 12 meses
- **Taxa de Adoção:** 80% de transações com dossiê

### Métricas Financeiras
- **MRR:** $25K em 12 meses
- **Transacional:** $30K/mês em 12 meses
- **Total:** $55K/mês em 12 meses
- **LTV:CAC:** >3:1

### Métricas de Produto
- **Ativos Registrados:** 500+ em 12 meses
- **Dossiês Emitidos:** 100+/mês em 12 meses
- **TVC (Total Value Custodied):** $100M+ em 12 meses

## Conclusão

O ecossistema de 5 camadas cria um efeito de rede onde cada participante beneficia os outros:

- **Marinas** ganham receita e diferencial
- **Proprietários** protegem seus ativos
- **Seguradoras** reduzem sinistros
- **Brokers** facilitam transações
- **Yachts Atlas** escala com churn zero

Este modelo cria barreiras de entrada significativas e posiciona o Yachts Atlas como padrão de mercado.

---
*Última atualização: 2026-04-28*