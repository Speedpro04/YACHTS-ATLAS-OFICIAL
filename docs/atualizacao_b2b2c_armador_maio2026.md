# Documentação de Atualização - Yachts Atlas (Maio 2026)
## Foco: Modelo B2B2C, Cofre do Armador e Segurança Operacional

Esta documentação resume as implementações arquiteturais e de interface realizadas na plataforma Yachts Atlas para consolidação do modelo de negócios B2B2C (Marina + Armador).

### 1. Transparência Jurídica e Modelo de Negócios (Landing Page)
- **Adequação de Copywriting:** Atualização dos arquivos de internacionalização (`pt.json` e `en.json`) para explicitar o modelo B2B2C na Landing Page.
- **Clareza de Custos:** Deixou-se absolutamente transparente que a Marina paga uma licença de software (US$ 250/mês) e o Armador paga sob demanda pelos Dossiês de Integridade.
- **Split de Receita:** Documentado na interface o modelo de repartição de receitas (50/50) viabilizado via Stripe Connect entre a plataforma e a marina parceira.

### 2. Portal Restrito do Armador ("Cofre Digital")
- **Isolamento de Dados (Supabase RLS):** Confirmação das políticas *Row Level Security* garantindo que cada armador visualize estritamente os ativos vinculados ao seu próprio CPF/ID.
- **Login Exclusivo (`LoginArmador.tsx`):**
  - Criação de uma página de login com identidade visual diferenciada (Fundo "Azul Oceano Oceânico" e partículas "Sky Blue") para evitar confusão com o painel da Marina.
  - Acesso simplificado de alta segurança: Nome da Embarcação + CPF + PIN de Segurança (sem necessidade de senhas complexas tradicionais).
- **Dashboard Restrito (`PortalArmador.tsx`):**
  - Implementação da tela do proprietário limitando a atenção a apenas 3 pilares vitais:
    1. Prontidão Operacional (Status de navegação).
    2. Dossiês Oficiais (Download via Blockchain SHA-256).
    3. Atualização de Status (Vistoria via câmera).

### 3. Integração de Câmera Mobile Direta
- **Componente `SecureCameraUpload.tsx`:** 
  - Interface desenvolvida em React utilizando a API nativa HTML5 (`capture="environment"`) para abrir diretamente a câmera do dispositivo móvel sem salvar a foto na galeria pessoal.
  - Fluxo seguro: Captura -> FormData -> Endpoint FastAPI `/upload` -> Cálculo SHA-256 -> Armazenamento WORM (S3/Supabase).

### 4. Relatório Básico de Prontidão de Navegação
- **Evolução do `AssetHealthDashboard.tsx`:**
  - Inclusão do `mode="operational"`, que filtra itens puramente estéticos ou burocráticos (Dossiê, Documentos, Pintura, Interior).
  - A barra de progresso (Índice de Segurança) agora é calculada focando 100% na segurança da vida humana no mar: **Motor, Elétrica, Segurança e Manutenção**.
  - Feedback visual por cores: Verde (>80%), Amarelo (>50%), Vermelho (<50%).

### 5. Backend (FastAPI + Python)
- A infraestrutura já existente foi validada. O sistema já está preparado (WORM, AuditLogs, S3, Stripe Webhooks, Row Level Security) para absorver o novo fluxo frontend de envio criptografado e repasse de pagamentos.

---
**Data da Documentação:** Maio de 2026
**Status:** Pronto para Produção / Testes de Usuário
