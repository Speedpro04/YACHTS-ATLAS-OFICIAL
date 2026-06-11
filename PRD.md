# PRD — Yachts Atlas

## Project Overview
**Yachts Atlas** is a premium digital platform designed for immutable record-keeping and certification of luxury nautical assets. It provides a secure "Digital Dossier" for yachts, tracking maintenance history, technical documentation, and health metrics using a secure, audit-ready framework.

Production domain: **https://yachtsatlas.online** (deployed on EasyPanel, single Docker service: Nginx + FastAPI).

## Objectives
- Provide asset owners with a verifiable "Digital Identity" for their yachts.
- Enable marinas to manage fleets and generate revenue through certified dossiers.
- Facilitate secure transactions and insurance processes with reliable asset history.

## Technology Stack
- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons, i18next (PT/EN/ES).
- **Backend**: FastAPI (Python), Supabase (Auth, Database, Storage — bucket `media`).
- **Payments**: Stripe (Connect for 50/50 splits, Subscriptions for Marinas). *Currently in TEST mode.*
- **Deployment**: Unified Dockerfile (Nginx serves frontend, proxies `/api` to Uvicorn) on EasyPanel.

## Key Features
1. **Dossier Certification**: 3 levels (Compact $200, Executive $400, Superyacht $600), generated as PDF from real custody data (`registros` + `documentos`), sections appear by vessel size — "no empty sections" rule.
2. **Asset Management**: Tracking of technical specs, maintenance, and expiry alerts.
3. **Document Vault**: Supabase Storage with SHA-256 integrity hash per file; authenticated users can upload but cannot update/delete stored objects (WORM-style policy).
4. **Marina Hub**: Dashboard for marinas to monitor managed assets and track revenue shares.
5. **Partner Network**: Directory of brokers and insurance providers, with contact-click tracking for lead billing.

## Current Implementation Status
- [x] Landing Page & Brand Identity (Premium Dark Theme, True Blue #010c20)
- [x] Authentication — unified: frontend and backend both validate Supabase session tokens (Bearer); maintenance-admin token for platform ops
- [x] Dashboard Layout
- [x] Asset Listing & Detailed Forms (CategoriaForm aligned to the 17 dossier categories)
- [x] Payment Checkout Flows (Stripe) — completed checkouts are persisted to the `payments` table via webhook
- [x] Dossier data + PDF endpoints with per-asset access control; optional payment gate (`DOSSIER_REQUIRE_PAYMENT`)
- [x] Checkout Success Pages (Dossier & Onboarding)
- [x] Marina Partner Lead Form (public insert; admin-only listing)
- [x] Containerization (unified Dockerfile) and production deploy
- [x] Backend test suite: health + auth-protection tests (all protected endpoints require Bearer token)

## Known Gaps / Next Steps (from June 2026 audit)
1. **DB schema drift (blocker)**: live `ativos` table uses `usuario_id`/`comprimento`; newer code paths expect `marina_id`/`owner_id`/`comprimento_pes` and a `marinas` table that does not exist yet. Creating assets via the API fails until the alignment migration is applied. Document/dossier endpoints were made tolerant to both schemas.
2. **Stripe live mode**: switch publishable/secret/webhook keys from `pk_test`/test to live before charging real customers; then set `DOSSIER_REQUIRE_PAYMENT=true` to gate PDF delivery on payment.
3. **Secrets exposure**: `backend/.env` (Supabase service key + JWT secret) exists in the public repo's git history; keys must be rotated in the Supabase dashboard (owner decision pending).
4. **Storage privacy**: bucket `media` is public-read; sensitive documents should move to a private bucket + signed URLs (backend already generates signed URLs).
5. **RegistroForm (Registros page)**: its 9 service categories don't map to the 17 dossier categories, and its photo/receipt dropzones are decorative (no file input wired). Align or remove.
6. **Responsiveness**: Tailwind breakpoints across all pages; tables outside `Ativos.tsx` still need `overflow-x-auto` for narrow screens. Visual device pass pending.
7. **Repo hygiene**: large images (6–12 MB) and stray one-byte files at repo root; SQL migrations live at root without a versioned `supabase/migrations` folder.

## Checkout Flows
- **Certified Dossier**: one-time payment; 50/50 split (Stripe Connect) with the marina where the yacht is docked — split activates only when the marina has a `stripe_account_id` (requires the `marinas` table from the alignment migration).
- **Marina Onboarding**: $250/mo subscription for full fleet management capabilities.

## Environment Flags
- `ALLOWED_ORIGINS` — CORS allowlist (defaults include `yachtsatlas.online`).
- `DOSSIER_REQUIRE_PAYMENT` — when `true`, dossier PDF only for assets with a completed `payments` row (`payment_type='dossier'`).
- `MAINTENANCE_USERNAME/PASSWORD/MASTER_TOKEN`, `MAINTENANCE_BYPASS_ENABLED` — platform-admin maintenance access.
