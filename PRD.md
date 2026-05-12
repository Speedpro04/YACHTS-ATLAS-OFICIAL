# PRD — Yachts Atlas

## Project Overview
**Yachts Atlas** is a premium digital platform designed for immutable record-keeping and certification of luxury nautical assets. It provides a secure "Digital Dossier" for yachts, tracking maintenance history, technical documentation, and health metrics using a secure, audit-ready framework.

## Objectives
- Provide asset owners with a verifiable "Digital Identity" for their yachts.
- Enable marinas to manage fleets and generate revenue through certified dossiers.
- Facilitate secure transactions and insurance processes with reliable asset history.

## Technology Stack
- **Frontend**: React (Vite), Tailwind CSS, Lucide Icons, i18next (Multi-language).
- **Backend**: FastAPI (Python), Supabase (Auth, Database, Storage).
- **Payments**: Stripe (Connect for 50/50 splits, Subscriptions for Marinas).
- **Deployment**: Docker (Planned).

## Key Features
1. **Dossier Certification**: 3 levels of certification (Compact, Executive, Superyacht) with cryptographic integrity.
2. **Asset Management**: Full tracking of technical specs, maintenance, and alerts.
3. **Document Vault**: Encrypted storage for critical maritime documents.
4. **Marina Hub**: Dashboard for marinas to monitor managed assets and track revenue shares.
5. **Partner Network**: Integrated directory of brokers and insurance providers.

## Current Implementation Status
- [x] Landing Page & Brand Identity (Premium Dark Theme)
- [x] Authentication (Supabase Integration)
- [x] Dashboard Layout
- [x] Asset Listing & Detailed Forms
- [x] Payment Checkout Flows (Stripe Integration)
- [ ] Checkout Success Pages (Dossier & Onboarding)
- [/] Marina Partner Lead Form
- [ ] Containerization (Dockerfile)

## Deployment Plan
1. Fix missing redirect pages (Success/Cancel).
2. Finalize Dockerfile for EasyPanel/Production.
3. Configure Environment Variables (Supabase, Stripe, API URL).
4. Deploy Frontend (Nginx) and Backend (Uvicorn).

## Checkout Flows
- **Certified Dossier**: 50/50 split between Yachts Atlas and the Marina where the yacht is docked.
- **Marina Onboarding**: $250/mo subscription for full fleet management capabilities.
