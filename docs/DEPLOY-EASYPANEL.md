# Deploy — Yachts Atlas no EasyPanel (Docker unificado)

Deploy como **serviço único** usando o `Dockerfile` da **raiz** (Nginx serve o
frontend + faz proxy de `/api` para o FastAPI, ambos no mesmo container).

## Passos no EasyPanel
1. **New App** → fonte: repositório GitHub `Speedpro04/YACHTS-ATLAS-OFICIAL`
2. **Build**: tipo Dockerfile → caminho `./Dockerfile` (o da raiz) → contexto `.` (raiz)
3. **Porta**: `80`
4. Configurar **Build Args** e **Environment** (abaixo)
5. Deploy

> Importante: as `VITE_*` são **Build Args** (entram no build do frontend, ficam
> embutidas no bundle). As do backend são **Environment** (runtime).

---

## Build Args (frontend — injetadas no build)

| Variável | Valor |
|---|---|
| `VITE_SUPABASE_URL` | `https://owzelkiyorumnlaycral.supabase.co` |
| `VITE_SUPABASE_ANON_KEY` | a **chave publicável** nova → `sb_publishable_...` |

## Environment (backend — runtime)

| Variável | Valor |
|---|---|
| `SUPABASE_URL` | `https://owzelkiyorumnlaycral.supabase.co` |
| `SUPABASE_KEY` | **publicável** → `sb_publishable_...` |
| `SUPABASE_SERVICE_KEY` | **secreta** → `sb_secret_...` (NUNCA expor no frontend) |
| `SUPABASE_JWT_SECRET` | JWT secret do projeto (Settings → JWT Keys), se ainda usado |
| `STRIPE_SECRET_KEY` | `sk_live_...` (chave secreta do Stripe) |
| `STRIPE_WEBHOOK_SECRET` | `whsec_...` (do webhook do Stripe) |
| `ALLOWED_ORIGINS` | domínio(s) de produção, ex.: `https://yachts.axoshub.com,https://yachtsatlas.com` |

### Opcionais (têm default no código — só se for usar)
| Variável | Uso |
|---|---|
| `EMAIL_SENDER`, `EMAIL_PASSWORD` | envio de e-mails de alerta |
| `MAINTENANCE_USERNAME`, `MAINTENANCE_PASSWORD` | login de manutenção |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `S3_BUCKET_NAME` | só se usar S3 (hoje o storage é Supabase) |

---

## Mapa das chaves novas (sistema sb_)
- `sb_publishable_...` (segura p/ navegador) → `SUPABASE_KEY` **e** `VITE_SUPABASE_ANON_KEY`
- `sb_secret_...` (NUNCA no frontend) → `SUPABASE_SERVICE_KEY`
- As chaves legadas (`eyJ...`) foram **desativadas** — não usar mais.

## Checklist antes de subir
- [ ] Chaves `sb_` configuradas (build args + env)
- [ ] `ALLOWED_ORIGINS` com o domínio real de produção
- [ ] Stripe (secret + webhook) configurados
- [ ] SQLs aplicadas no Supabase (registros, owner_access, partner_leads, partner_clicks, segurança)
- [ ] Edge Function `verify-owner-secret` deployada (`supabase functions deploy verify-owner-secret`)

## Pós-deploy
- Testar: site abre, login marina (usuário real no Supabase Auth), formulários de lead gravam
- Validar SEO/sitemap e submeter o sitemap no Google Search Console

## Deploy manual na semana de lançamento

Hoje o EasyPanel reconstrói a produção a cada push em `master`. Isso é ótimo
enquanto só nós usamos, e é exatamente o que não se quer com marina pagante
dentro: qualquer commit — um ajuste de texto, um teste, um engano — vira deploy
na hora, sem ninguém decidir.

**Desligar** (fazer na sexta antes do lançamento): EasyPanel → serviço
`yachts-atlas` → aba **Source** (ou **Git**) → desmarcar **Auto Deploy** →
Save. O webhook do GitHub pode ficar; sem o auto deploy ele não dispara build.

**Subir a partir daí**, quando você decidir: EasyPanel → o mesmo serviço →
**Deploy** (ou **Rebuild**). Ele puxa o `master` atual e reconstrói. O commit que
vai ao ar é o último que estiver no GitHub — então `git push` continua sendo o
passo anterior, só deixa de ser o gatilho.

**Como saber que subiu:** a aba **Logs** mostra o nginx reiniciando
(`start worker processes`). No navegador, recarregue com cache limpo — o
`index.html` não é cacheado, mas os `assets/*.js` têm hash no nome e o antigo
fica.

**Rollback:** o EasyPanel reconstrói do Git, não guarda imagem anterior. Para
voltar, `git revert` do commit ruim, push, e Deploy de novo. Por isso commit
pequeno e por assunto importa mais na semana de lançamento do que em qualquer
outra: dá para reverter um sem levar junto o que estava certo.
