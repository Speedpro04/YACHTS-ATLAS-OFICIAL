# Yachts Atlas — Product Requirements Document (PRD)

## 1. Visão Geral do Produto

O **Yachts Atlas** é uma infraestrutura de dados e um registro digital imutável para ativos náuticos (iates, lanchas, veleiros, jet-skis). Ele atua como um repositório centralizado onde toda a documentação, histórico de manutenção e certificações do ativo são armazenados de forma segura e com integridade criptográfica.

Recentemente, a plataforma expandiu seu foco para um **modelo B2B2C**, capacitando **Marinas e Clubes Náuticos** a gerenciarem as frotas de seus clientes. Ao centralizar essas informações, o Yachts Atlas não apenas facilita a gestão diária, mas aumenta o valor de revenda do ativo ao garantir um dossiê completo e auditável.

---

## 2. Problema e Solução

### O Problema
Atualmente, a documentação de ativos náuticos é fragmentada e desorganizada (papéis físicos, e-mails, pendrives). Na hora da venda ou do acionamento de seguro, a falta de histórico estruturado resulta em:
- Desvalorização do ativo em 10% a 30%.
- Atrasos na transferência e due diligence.
- Manutenções duplicadas ou esquecidas.

### A Solução
Um ambiente digital onde o proprietário e a Marina podem manter um **histórico único e verificável**. Cada documento inserido recebe um *hash* criptográfico (SHA-256), garantindo sua integridade. O sistema permite gerar um **Dossiê Automático**, provando o histórico de cuidados do barco, aumentando instantaneamente sua liquidez e valor no mercado.

---

## 3. Personas e Casos de Uso

### 3.1. Personas
1. **A Marina / Clube Náutico (B2B):** Precisa gerenciar a frota sob seus cuidados, monitorar os vencimentos de documentos dos clientes e oferecer um serviço de valor agregado premium.
2. **O Proprietário do Ativo (B2C):** Quer proteger seu investimento, ter acesso rápido aos documentos para fiscalização e maximizar o valor de revenda através do Dossiê.
3. **Brokers / Seguradoras:** Interessados na due diligence e validação do risco do ativo, confiando na integridade dos dados gerados.

### 3.2. Casos de Uso Principais
- **Gestão de Frota pela Marina:** Visualização em painel do status de dezenas de iates simultaneamente.
- **Dossier Certification:** A Marina ou o proprietário gera um certificado digital/PDF autenticado compilando todos os dados, vistorias e documentos de um iate antes de sua venda.
- **Validação de Integridade:** Um comprador acessa a plataforma para verificar se o laudo de manutenção não sofreu alterações desde que foi emitido.

---

## 4. Modelo de Negócios e Precificação

O Yachts Atlas atua com diferentes fluxos de receita (Stripe integration):

**1. Assinatura para Marinas (B2B2C):**
- **Plano Marina Standard:** ~$250/mês para gestão de frota, dashboard agregador, API e painel white-label. Permite que a Marina ofereça o sistema aos seus clientes.

**2. Geração de Dossiê / Certificação (Pagamento Avulso):**
Cobrança dinâmica baseada no tamanho do barco (pés):
- **Compact (até 39 pés):** $200
- **Executive (40 a 79 pés):** $400
- **Superyacht (80+ pés):** $600

**3. ROI dos Dossiês (B2B2C):**
- **Regra comercial padrão:** split de receita/ROI dos dossiês em **50/50** entre Yachts Atlas e Marina parceira.

---

## 5. Requisitos Funcionais (Épicos e Histórias)

### Épico 1: Gestão B2B de Marinas
- **RF01:** O sistema deve permitir o cadastro de contas corporativas (Marinas).
- **RF02:** A Marina deve ter um dashboard exibindo métricas da frota gerenciada (total de ativos, pés totais, alertas de documentos vencendo).
- **RF03:** A Marina deve poder convidar (onboarding) proprietários para o ecossistema.
- **RF11:** O sistema deve oferecer um **Checklist de Segurança Digital** para marinheiros.
- **RF12:** O sistema deve gerar **Alertas de Manutenção Preditiva** (motores, extintores, balsas) integrados à agenda da marina.

### Épico 2: Gestão de Ativos
- **RF04:** O sistema deve permitir o cadastro de ativos especificando tipo (iate, lancha, etc), marca, modelo, ano de fabricação e comprimento em pés.
- **RF05:** O sistema deve exibir a Classificação do ativo (Bronze, Silver, Gold) com base na completude de suas informações.

### Épico 3: Gestão de Documentos e Integridade
- **RF06:** Usuários e Marinas devem poder fazer upload de documentos e laudos.
- **RF07:** O backend deve gerar um Hash SHA-256 para o arquivo no momento do upload.
- **RF08:** O sistema deve verificar a validade de documentos temporais (ex: seguros) e exibir status (ativo, vencendo, vencido).

### Épico 4: Geração de Dossiês de Certificação
- **RF09:** O sistema deve calcular o preço da geração do dossiê baseado no comprimento em pés do ativo cadastrado.
- **RF10:** Após o pagamento (checkout via Stripe), o sistema deve compilar os dados do ativo, documentos, linha do tempo e hashes em um relatório PDF premium.

---

## 6. Requisitos Não-Funcionais

- **RNF01 (Segurança):** Todos os uploads devem passar por verificação. O sistema deve aderir ao OWASP Top 10 e os dados sensíveis devem ser encriptados no banco de dados.
- **RNF02 (Integridade):** A verificação de hashes de arquivos deve ocorrer em tempo de execução para atestar "nenhuma adulteração".
- **RNF03 (Performance):** A renderização inicial do dashboard das Marinas deve ocorrer em menos de 2 segundos.
- **RNF04 (Integração de Pagamentos):** Transações financeiras e gestão de assinaturas não serão feitas no banco local, delegando-se a conformidade PCI-DSS ao provedor Stripe.

---

## 7. Arquitetura e Stack Tecnológica

O sistema utiliza uma arquitetura moderna distribuída em microsserviços/serviços desacoplados:

- **Frontend:** React + Vite, Tailwind CSS (Design system premium focado em UX).
- **Backend:** Python + FastAPI (Alta performance, tipagem forte, assíncrono).
- **Banco de Dados:** Supabase (PostgreSQL) para dados relacionais e gerenciamento de permissões (RLS - Row Level Security).
- **Storage:** Supabase Storage para armazenamento de arquivos e imagens.
- **Autenticação:** Supabase Auth (Suporte a B2B/B2C tokens).
- **Pagamentos:** Stripe Checkout.
- **Infraestrutura / Deploy:** Docker gerenciado via EasyPanel.

---

## 8. Cronograma e Fases de Lançamento (Roadmap)

- **Fase 1 (MVP - Concluído/Atual):** Cadastro de ativos, upload de documentos, hash SHA-256, login, dashboard básico.
- **Fase 2 (B2B Pivot):** Implementação de perfis de Marina, dashboard de métricas de frota, precificação dinâmica por pés.
- **Fase 3 (Monetização e Escala):** Checkout Stripe da geração de dossiês premium ($200/$400/$600), envio automático de alertas e expansão de parcerias white-label.

---

**Autor:** Equipe de Produto Yachts Atlas  
**Data:** Maio de 2026  
**Status:** Rascunho / Em validação
