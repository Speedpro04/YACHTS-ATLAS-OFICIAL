# Supabase Integration and System Improvements

**Goal**: Modernizar o sistema Yacht usando Supabase como backend único para uploads, gerenciamento de arquivos e controle de acesso, além de corrigir a UI (botão “+ novo ativo”) e melhorar a experiência geral.

## User Review Required
> [!IMPORTANT]
> Este plano envolve alterações em várias áreas (backend, frontend, banco de dados, políticas RLS). Preciso da sua aprovação para prosseguir com a implementação.

## Open Questions
> [!WARNING]
> 1. Qual bucket do Supabase deve ser usado para os uploads de imagens/documentos? (ex.: `yacht-uploads`)
> 2. As senhas de liberação de dossiês são duas chaves distintas? Preciso dos valores ou de uma estratégia de geração.
> 3. Alguma política de retenção de arquivos (ex.: excluir após 18 meses) deve ser aplicada automaticamente?
> 4. Deseja que o botão “+ novo ativo” abra um modal ou redirecione a uma página específica?

## Proposed Changes
---
### 1. Database (Supabase)
- **Create/Update bucket**: Script SQL para `storage.buckets` (via Supabase CLI ou dashboard).
- **Add tables** (if missing) for `upload_sessions` e `passwords`:
```sql
CREATE TABLE IF NOT EXISTS public.upload_sessions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES public.profiles(id),
    file_path TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.dossie_passwords (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    dossie_id UUID REFERENCES public.dossies(id),
    password_type TEXT CHECK (password_type IN ('primary','secondary')) NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);
```
- **RLS Policies** para garantir que apenas usuários autorizados (marina_manager ou owner) possam gerar/usar as senhas.
- **Triggers** para definir `expires_at` = `created_at + interval '18 months'` nos dossiês.

---
### 2. Backend (Python FastAPI / Flask?)
- Instalar `supabase-py` (add to `requirements.txt`).
- Criar módulo `supabase_client.py` com funções de upload, listagem e geração/verificação de senhas.
- Substituir lógica atual de upload (provavelmente salva em disco) por upload ao bucket Supabase.
- Expor endpoint `/api/upload` que recebe `multipart/form-data`, faz upload ao Supabase e registra em `upload_sessions`.
- Atualizar endpoint de criação de dossiê para aceitar duas senhas, armazenar hashes em `dossie_passwords` e gerar URL pre‑signed do bucket.
- Implementar verificação de senha ao solicitar download do dossiê.

---
### 3. Frontend (React? Vue? – ver `frontend` folder)
- Atualizar componente de upload (`UploadComponent.jsx`) para chamar o novo endpoint e exibir progresso.
- Adicionar campo de seleção de senha (primary/secondary) no formulário de criação de dossiê.
- Corrigir/implantar botão “+ novo ativo”:
  - Se ainda não existir, criar componente `AddAssetButton.jsx` que abre modal com formulário de criação de ativo.
  - Estilizar com design premium (gradiente, animações, tipografia Inter).
- Garantir que mensagens de erro sejam amigáveis.

---
### 4. UI/UX Enhancements
- Aplicar design de cores vibrantes (ex.: cor base `hsl(210, 40%, 15%)` escura + gradientes `linear-gradient(135deg, hsl(210, 40%, 25%), hsl(210, 60%, 35%))`).
- Incluir fonte Google **Inter** no `<head>`.
- Micro‑animações de hover nos botões e transição suave nas áreas de upload.
- Testar responsividade.

---
### 5. DevOps / CI
- Atualizar `Dockerfile` para instalar dependência `supabase-py`.
- Incluir script de migração para criar as novas tabelas (`migration_supabase_extra.sql`).
- Documentar variáveis de ambiente (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`).

## Verification Plan
- **Automated tests**: adicionar testes unitários para `supabase_client.upload_file` e para verificação de senhas.
- **Manual QA**: upload de imagem, ver URL gerada, tentativa de download com senha correta/incorreta, criação de novo ativo via botão.
- **Check expiry**: confirmar que dossiês criados têm `expires_at` 18 meses depois.

---
*Após sua aprovação, criarei os arquivos necessários, atualizarei o schema e implementarei as alterações no backend e frontend.*
