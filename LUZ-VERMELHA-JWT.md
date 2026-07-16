# 🔴 Luz Vermelha — JWT Secret vazado e ainda em uso

> **Status:** ABERTO — bloqueador nº 1 de lançamento "pra valer".
> **Diagnóstico:** 2026-07-16.
> **Regra de trabalho:** um item por vez, nada aplicado sem OK explícito do fundador.
> **Não contém segredo** — este arquivo é versionado. Nunca colar o valor da chave aqui.

---

## O que é (em uma frase)

O segredo que assina o **token de administrador da plataforma** (`SUPABASE_JWT_SECRET`)
está publicado no histórico do Git **e continua sendo o valor em uso**. Quem tiver esse
valor consegue **forjar um token `platform_admin`** e entrar em qualquer rota protegida
do backend.

---

## Por que é o bloqueador nº 1

- Não é estética de linter — é **acesso administrativo forjável** sobre dados de donos reais.
- Para 3 marinas com documentos de clientes em jogo, isso é o tipo de coisa que **não pode
  estar aberta no dia da primeira venda**.

---

## Evidência técnica (o que foi confirmado, não achismo)

1. **A chave em uso == a chave vazada.** O `SUPABASE_JWT_SECRET` do `.env` em uso hoje é
   **byte a byte idêntico** ao que foi commitado no histórico público
   (commit `15ac4be`, arquivo `backend/.env`). Confirmado por hash SHA-256 (mesmo digest).
   Nunca foi rotacionado.

2. **Esse segredo dá admin.** Em [`backend/app/core/security.py`](backend/app/core/security.py):
   - Linha 17: `_internal_jwt_secret()` devolve `SUPABASE_JWT_SECRET`.
   - Linha 27/32: o token interno de manutenção é **assinado e validado** com esse segredo (HS256).
   - Linha 68: se o token traz `sub == "maintenance-admin"`, o backend devolve `role = "platform_admin"`.
   - **Logo:** quem conhece o segredo forja `{"sub":"maintenance-admin","type":"access"}` e vira admin.

3. **Segunda face do risco (Supabase).** O mesmo segredo assina as **sessões de usuário**
   no GoTrue. Com ele conhecido, é possível forjar sessão de **qualquer** usuário via a
   própria API do Supabase — independente do backend.

## O que NÃO confundir (já resolvido)

- ✅ A **`service_role`** vazada **já está morta**: testada contra o banco, responde **401**.
- ✅ A **chave anon legada** está **desativada** (`disabled: true`) — Supabase migrou para
  as publishable keys (`sb_publishable_...`).
- ✅ O `.env` **já está no `.gitignore`** (commit `a08cd3c`) — o vazamento novo está estancado.

➡️ **O que sobra vivo é só o `SUPABASE_JWT_SECRET`.** Este documento é sobre ele.

> **Nota:** o repo `Speedpro04/YACHTS-ATLAS-OFICIAL` hoje responde 404 (privado ou renomeado),
> o que reduz a exposição pública **agora**. Mas um segredo que já foi público deve ser tratado
> como comprometido para sempre (forks, cache, crawlers). A correção continua necessária.

---

## Plano de correção (2 metades)

### Metade A — Código: segredo dedicado (fecha o admin forjável)
- Criar variável nova `MAINTENANCE_JWT_SECRET` (valor aleatório novo, **nunca** vazado).
- Alterar `_internal_jwt_secret()` para usar `MAINTENANCE_JWT_SECRET` (não mais o do Supabase).
- Adicionar a variável no EasyPanel (deploy) e redeploy.
- ⚠️ **Efeito colateral:** invalida os tokens de manutenção **já emitidos** → é preciso
  **logar de novo** uma vez no painel de manutenção. **Não se perde o acesso**
  (o `MAINTENANCE_MASTER_TOKEN` e usuário/senha continuam válidos).
- Confirmado: `SUPABASE_JWT_SECRET` **só** é usado nesse ponto do backend — a troca elimina
  100% do uso do segredo vazado no código.

### Metade B — Dashboard Supabase: rotacionar / migrar chaves (fecha a face Supabase)
- Migrar as **JWT signing keys** para chaves assimétricas (ou rotacionar o JWT secret) no
  dashboard do projeto `owzelkiyorumnlaycral`.
- Isso invalida o segredo HS256 vazado do lado do Supabase (impede forjar sessão de usuário).
- ⚠️ **Efeito colateral:** sessões de usuário ativas caem (re-login). Irrelevante em pré-lançamento.

### Ordem correta
**A antes de B.** Primeiro desacoplar o token de manutenção (Metade A), senão a rotação no
Supabase pode confundir o login de manutenção e ainda não resolve o admin forjável (o backend
lê o valor da env, não do Supabase em tempo real).

---

## Checklist de execução

- [ ] **A1.** Gerar `MAINTENANCE_JWT_SECRET` novo (aleatório, forte).
- [ ] **A2.** Editar `security.py` para usar o segredo dedicado.
- [ ] **A3.** Revisar o diff (fundador) antes de qualquer coisa ir pro ar.
- [ ] **A4.** Adicionar a env no EasyPanel + redeploy.
- [ ] **A5.** Testar: login de manutenção volta com re-login; rotas admin OK.
- [ ] **B1.** Rotacionar / migrar signing keys no dashboard Supabase.
- [ ] **B2.** Atualizar env do backend se necessário + redeploy.
- [ ] **B3.** Testar: login de usuário normal, dossiê e painel funcionando.
- [ ] **Fechar** esta luz vermelha.

---

## Referências no código
- [`backend/app/core/security.py`](backend/app/core/security.py) — linhas 14–17, 27, 32, 48–69.
- [`backend/app/core/config.py`](backend/app/core/config.py) — linha 47 (`SUPABASE_JWT_SECRET`).
- Projeto Supabase: `owzelkiyorumnlaycral` (região sa-east-1).
- Commit do vazamento: `15ac4be` (arquivo `backend/.env`, já removido do HEAD e no `.gitignore`).
