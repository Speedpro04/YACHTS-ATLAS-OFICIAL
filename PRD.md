# PRD — Yachts Atlas

> Atualizado em 2026-07-06 (REV-03 — Alinhamento total painel↔dossiê↔score + Expansão Internacional iniciada).
> **Novo (REV-03):** Abas **Casco** e **Drenagem/Porão** agora entram como seções no Dossiê PDF (antes a marina preenchia e não aparecia). **Asset Score** corrigido — cruzava taxonomia antiga contra os registros reais, zerando abrangência/profundidade; agora usa a taxonomia do painel como fonte única. Header ganhou as **3 portas de entrada internacionais** (Latan/USA/Europa). Ver [Expansão Internacional](#expansão-internacional-3-versões).
> **REV-02:** Abas Manutenção e Elétrica com classificação Preditiva/Corretiva, sistemas náuticos afetados e alertas automáticos de recorrência no Dosiê PDF.
> Ver detalhes das especificações em [PAINEL-TÉCNICO-MELHORIAS-REV-01.md](file:///c:/YACTHS-ATLAS-OFICIAL/PAINEL-T%C3%89CNICO-MELHORIAS-REV-01.md)

## Project Overview
**Yachts Atlas** é uma plataforma de **custódia digital e conformidade** de ativos náuticos de alto valor. Cada embarcação ganha um **Dossiê** — registro selado e **imutável** de histórico técnico, operação, documentação e fotos — entregue **pela marina** ao proprietário/comprador/seguradora.

Documento de custódia **privado**, elaborado em observância à **LESTA (Lei 9.537/97)**, ao **RLESTA** e às **NORMAM/DPC** da Marinha do Brasil (não substitui documentos oficiais — complementa, com cadeia de custódia verificável).

- Produto da **AXOS HUB** (CNPJ 26.998.571/0001-50 — empresa solo).
- Domínio de produção: **https://yachtsatlas.online** (EasyPanel, Docker único: Nginx + FastAPI).

## Modelo de Negócio (DEFINITIVO)
- **Recorrência é o produto.** A marina assina; **100% do dossiê é da marina** (negócio marina ↔ dono é direto, fora da plataforma).
- **Preços (só dois):**
  - **20 marinas de lançamento → $200/mês**
  - **até 120 marinas restantes → $250/mês** (total 140)
  - Cobrança via **Stripe Payment Links** (limites de uso travam as 20 e as 120). O `config.py` espelha o modelo (`LAUNCH_SLOTS=20/$200`, `TRADITIONAL_SLOTS=120/$250`).
- **O dossiê NÃO é vendido pela plataforma** (checkout de dossiê está desativado — HTTP 410). Liberação para terceiros é por pedido + liberação manual + senha-mestra.
- **Piloto atual:** 3 marinas rodando **grátis por 6 meses** como **prova social** antes do lançamento das fundadoras.

## Technology Stack
- **Frontend**: React (Vite), Tailwind, Lucide, i18next (PT/EN/ES).
- **Backend**: FastAPI (Python), Supabase (Auth, Postgres 17, Storage bucket `media`).
- **RAG / IA (Capitã Solara)**: pgvector + `text-embedding-3-small`, corpus de normas náuticas (20 normas / 46 seções); pipeline de embeddings em Polars (`backfill_embeddings.py`).
- **Pagamentos**: Stripe (Payment Links + Subscriptions; webhook persiste em `payments` e cadastra marina fundadora via RPC). *Ainda em modo TEST.*
- **Chaves Supabase**: migrado para o formato novo — **publishable** (`sb_publishable_…`) no front, **secret** (`sb_secret_…`) no backend; as chaves legadas JWT (`eyJ…`) foram **desativadas pela Supabase** em jun/2026.
- **Deploy**: Dockerfile unificado (Nginx serve o front e faz proxy de `/api` p/ Uvicorn) no EasyPanel, **auto-deploy observando o branch `master`**.

## Key Features
1. **Dossiê de Custódia (PDF)**: gerado a partir do **painel técnico real** (`registros` + `documentos`), espelhando as categorias do painel — "nenhuma seção vazia". Layout **premium/institucional**: capa, **Marina Custodiante** (nome, CNPJ, responsável, endereço), preâmbulo legal, **Quadro de Conformidade Regulatória** (NORMAM), seções técnicas, avaliação de mercado, registro fotográfico, **Termo de Custódia e Integridade**. Header/rodapé com logo dourada + CNPJ + protocolo. *(Kit de dossiê-modelo fictício mantido em `dossie-exemplo/`, fora do versionamento.)*
2. **Painel Técnico**: fichas seladas (logbook) por categoria — manutenção, diário de bordo, motor, velame, **casco**, **drenagem/porão**, elétrica, segurança, pintura, interior, seguro — todas no mesmo molde rico (config-driven em `servicosCategorias.ts` → `AtivoHub` lê dinâmico), com upload de evidências (SHA-256). **Fonte única de taxonomia**: painel, dossiê (`CATEGORIAS_TECNICAS`) e Asset Score (`asset_score_service`) usam as mesmas chaves — toda aba preenchida vira seção no dossiê e conta no score. **Destaque: Manutenção e Elétrica classificadas por Natureza (Preditiva vs Corretiva) e Sistema Náutico Afetado, gerando dashboard de confiabilidade e alertas automáticos de recorrência no Dosiê. Aba Elétrica com cobertura total de instrumentação: VHF DSC (NORMAM-02), EPIRB com validade e cadastro ANATEL, AIS Classe B, GPS/Ploter, Sonda, Piloto Automático, Radar e Luzes de Navegação (RIPEAM/COLREGS 1972).**
3. **Diário de Bordo (Operação)**: registro rigoroso de cada **ida ao mar** — condutor + habilitação/CHA, manuseio, lançamento, horímetros saída/retorno (tempo de uso), reboque, estado/avaria — com evidências seladas. Flui para o dosiê. *(Pensado para seguradoras, cruzando com os alertas de preventiva/corretiva do painel técnico.)*
4. **Imutabilidade real** (`registros`): cada registro recebe **hash SHA-256 no insert** (trigger) e o banco **bloqueia qualquer UPDATE** (append-only / anti-adulteração) — vale até para a `service_role`. *DELETE segue permitido por causa do cascade de exclusão de ativo (soft-delete pendente para imutabilidade total).*
5. **Cofre de Documentos**: Supabase Storage, SHA-256 por arquivo, **descrição do que é cada documento** no upload.
6. **Cobertura Fotográfica**: até **430 fotos por embarcação** (400 cobertura + 30 vitrine), geolocalizadas no upload.
7. **Capitã Solara (IA)**: assistente de normas náuticas via RAG (pgvector), tom técnico-profissional, com guard-rails anti-alucinação.

## Status de Implementação
- [x] Landing Page & identidade (tema dark premium, True Blue #010c20) + i18n PT/EN/ES
- [x] Auth unificada (Supabase session Bearer; token de manutenção p/ admin)
- [x] Painel técnico com fichas seladas (mesmo molde para todas as categorias)
- [x] **Diário de Bordo (operação / idas ao mar)** + seção no dossiê
- [x] **Imutabilidade real** dos registros (hash SHA-256 + trigger append-only, UPDATE bloqueado) — *aplicada direto no banco*
- [x] **Descrição de documento** no cofre (Documentação)
- [x] Geolocalização das imagens no upload; cobertura fotográfica (430)
- [x] Dossiê (dados + PDF) com controle de acesso por ativo; layout premium
- [x] Pagamento: webhook Stripe persiste em `payments` + cadastra marina fundadora (RPC)
- [x] RAG Solara (pgvector, 46/46 seções embeddadas)
- [x] Correção de performance (dedupe/cache de GET — chamadas repetidas viram 1)
- [x] Hardening: `search_path` fixo nas funções do banco
- [x] Containerização + deploy de produção
- [x] **REV-03 — Alinhamento painel↔dossiê↔score**: `casco` e `drenagem` incluídas no dossiê; Asset Score/health map corrigidos (taxonomia do painel como fonte única + alias `velame→motor`); remoção de código morto (`TechnicalFormOverlay.tsx`, `registros_checklists.py`)
- [x] **REV-03 — Header internacional**: 3 botões de mercado (Latan/USA/Europa) responsivos (desktop + mobile), a partir da constante `REGIOES`

## Pendências / Próximos Passos
1. **Revisar gestão de segredos** — rotação das chaves de serviço pendente (decisão do fundador). *A imutabilidade dos registros já protege contra adulteração.*
2. **Desligar o auto-deploy** do EasyPanel (push em `master` reconstrói prod sozinho) — passar para deploy manual.
3. **Stripe live** — trocar chaves test→live e confirmar os 2 Payment Links ($200 fundadora c/ `metadata.programa=marina_fundadora` · $250).
4. **Privacidade do bucket `media`** — hoje é público; mover documentos sensíveis p/ bucket privado + URL assinada (LGPD).
5. **Soft-delete de ativo** — para imutabilidade **total** (hoje DELETE de ativo apaga registros em cascata).
6. **`audit_logs`** — insert está falhando por RLS (`42501`); ajustar policy para a auditoria gravar de fato.
7. **Higiene de repositório** — imagens grandes (6–12 MB) e arquivos avulsos na raiz; duas cópias locais do repo (com/sem "H").
8. **Portar dossiê premium p/ produção** — o layout premium hoje está só no kit local (`dossie-exemplo/`); levar para `dossie_pdf.py` quando aprovado.

## Expansão Internacional (3 Versões)
Estratégia multi-região pensada **desde a arquitetura**: o mesmo DNA (custódia selada + dossiê imutável + SHA-256) replicado em **3 sistemas independentes**, cada um com idioma, banco, subdomínio e conformidade regulatória próprios. As **portas de entrada** já vivem no header (botões dourados `Latan-Atlas · USA-Atlas · Europa-Atlas`), hoje como placeholders visuais a partir da constante `REGIOES` (`Header.tsx`).

| Versão | Mercado | Idioma | Subdomínio | Banco (Supabase) | Normas / Conformidade | Repositório |
|---|---|---|---|---|---|---|
| **Latan-Atlas** | América Latina | Espanhol (LatAm) | próprio | novo (isolado) | normas do continente (por país) | separado |
| **USA-Atlas** | Estados Unidos | Inglês americano | próprio | novo (isolado) | USCG / ABYC / NMMA | separado |
| **Europa-Atlas** | Europa | Inglês britânico | próprio | novo (isolado) | RCD (2013/53/UE) / ISO | separado |

**Faseamento:**
1. Concluir o deploy e a validação da versão BR (`master` → produção).
2. Cada versão nasce em **repositório SEPARADO** (não misturar com o app principal), com **banco Supabase próprio**, **subdomínio dedicado** e tradução do RAG/normas (Capitã Solara) para a localidade.
3. Aplicar a **conformidade regulatória de cada continente** no corpus de normas e nos textos legais do dossiê.
4. Ligar cada botão do header ao seu subdomínio de destino.

> Princípio: reaproveitar o núcleo (painel config-driven + imutabilidade + dossiê PDF) e trocar apenas a camada de idioma, dados e conformidade por região.

## Acesso ao Dossiê
- **Dono/marina (autenticado)**: acessa o próprio dossiê livremente (dados + PDF).
- **Terceiros (broker/comprador/seguradora)**: pedem por formulário aberto (`POST /dossie/solicitar`) → Yachts Atlas libera manualmente → acesso por página mobile protegida por **senha-mestra**; saídas registradas em `dossie_saidas`.

## Flags de Ambiente
- `ALLOWED_ORIGINS` — CORS (inclui `yachtsatlas.online`).
- `MAINTENANCE_USERNAME/PASSWORD/MASTER_TOKEN`, `MAINTENANCE_BYPASS_ENABLED`, `DOSSIER_MASTER_PASSWORD` — acesso de manutenção/admin (**nunca remover sem confirmação do fundador**).
- `SUPABASE_URL`, `SUPABASE_KEY` (publishable), `SUPABASE_SERVICE_KEY` (secret), `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `STRIPE_*`, `TELEGRAM_*`.
