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
