# PRD — Yachts Atlas

> Atualizado em 2026-08-20 (REV-04 — Acesso pago, cobrança e Portal do Proprietário).
> **Novo (REV-04):** **Recorrência passa a valer**: só entra quem pagou, 20 dias de atraso cortam e o pagamento religa sozinho — validado em produção com cartão real. Preço de fundadora agora depende da **origem** (campanha × site oficial), não do estado da marina. **Portal do Proprietário** de verdade: o armador entra com o próprio e-mail e código, e vê só o barco dele. Avisos migraram para **WhatsApp (Evolution) + e-mail pelo domínio próprio**; Telegram removido.
> **REV-03 (2026-07-06):** Alinhamento total painel↔dossiê↔score + Expansão Internacional iniciada.
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
  - Cobrança via **Stripe Payment Links** (conta **Axos Hub / CNPJ**). O `config.py` espelha o modelo (`LAUNCH_SLOTS=20/$200`, `TRADITIONAL_SLOTS=120/$250`).
  - **O preço de fundadora é da CAMPANHA, não do estado da marina.** Quem chega pelo **Lançamento** (`lancamento.yachtsatlas.online`) leva US$ 200 enquanto houver vaga; quem chega pelo **Oficial** paga US$ 250 sempre — mesmo em SC/SP/RJ/ES/BA com vaga livre. Origem desconhecida cai no Oficial de propósito (`ORIGENS_DE_LANCAMENTO` em `leads.py`). Sem isso, a marina **indicada** — que deve entrar por US$ 250 — consumia uma das 20 vagas.
  - **Preço fundador travado por 12 meses**; no 13º mês a assinatura passa a US$ 250, agendado na própria Stripe (`SubscriptionSchedule`) no ato do pagamento.
  - **A vaga é reservada por 3 horas** entre o cadastro e o pagamento, e o prazo é dito à marina na tela.
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
7. **Capitã Solara (IA)**: assistente de **normas** (RAG/pgvector, citando a fonte) **e de suporte ao produto** — "onde cadastro?", "como gero o dossiê?". O conhecimento do produto vive no PROMPT, não no RAG (é pequeno e cabe inteiro), e é **gerado do código** (`conhecimento_produto.py`), com teste que quebra se alguém mudar uma categoria sem regenerar. Responde pergunta misturada inteira: a exigência vem da norma, o caminho vem do produto. Nunca descreve tela que não esteja no conhecimento. O que perguntam fica em `solara_perguntas` — mapa do que está confuso na interface, não métrica de atendimento.
8. **Acesso pago**: `app/core/acesso.py` decide quem pode usar o sistema. **Fail-open** — barra só quem está explicitamente marcado; manutenção, admin e piloto gratuito passam direto. O corte por inadimplência é calculado **na leitura**, não por cron: não depende de rotina estar de pé, e o religamento é automático.
9. **Régua de cobrança**: avisos nos dias 0, 7, 15, 19 e 20 por e-mail e WhatsApp, com registro do que já saiu — rodar duas vezes não duplica, e um dia sem rodar não perde aviso (`cron_cobranca`).
10. **Portal do Proprietário**: o armador entra com o **próprio e-mail** e um código de uso único (e-mail + WhatsApp), sem senha para criar. Vê **somente os barcos com o e-mail dele** e **apenas lê** — não cadastra, não edita, não sela. O vínculo é `ativos.proprietario_email`, e a leitura-apenas é garantida por construção (`incluir_proprietario` em `core/authz.py`, que só endpoints de leitura passam).

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
- [x] **REV-04 — Acesso pago**: só entra quem pagou; 20 dias de atraso cortam; pagamento religa sozinho; cancelamento revoga. **Validado em produção com cartão real** (link recorrente de R$ 1,00) — os cinco caminhos testados de ponta a ponta.
- [x] **REV-04 — Régua de cobrança** (dias 0/7/15/19/20) por e-mail e WhatsApp, com registro do que já saiu
- [x] **REV-04 — Preço por origem**: Lançamento US$ 200 · Oficial US$ 250; reserva de vaga por 3h avisada ao cliente
- [x] **REV-04 — Reajuste do 13º mês** agendado na Stripe no ato do pagamento *(pendente de validação em modo teste)*
- [x] **REV-04 — Portal do Proprietário**: `proprietario_email`/`proprietario_telefone` no ativo, código por e-mail + WhatsApp, listagem restrita e leitura-apenas *(pendente do teste end-to-end do `verifyOtp`)*
- [x] **REV-04 — Avisos por WhatsApp (Evolution) + e-mail**; Telegram removido; e-mail migrado para o domínio próprio com SPF/DKIM/DMARC
- [x] **REV-04 — Contador de vagas fundadoras com dado real** na `/marina-parceira` (era `12` chumbado no código)
- [x] **REV-04 — Registros deixam de ser públicos entre contas**: nenhum endpoint de `registros` autorizava — qualquer conta lia (e escrevia) o histórico selado de qualquer barco sabendo o id, que é previsível. Agora leitura = marina + armador, escrita = só marina, com teste que exige guarda em endpoint novo
- [x] **REV-04 — Portal do Proprietário entrega mais**: capa com a foto do próprio barco (era imagem de banco fixa no código), selo de custódia visível ao dono, e resquício de maquete removido
- [x] **REV-04 — A nota do ativo volta a se mexer**: `calcular_saude_ativo` só rodava num endpoint que o frontend nunca chamava, então o selo ficava parado no valor do cadastro (Marlin Sea: 16 registros, 25 documentos, e "Bronze · Saúde 0%" na tela). Agora recalcula ao selar registro
- [x] **REV-04 — Ativo de demonstração pronto** (`YA-IATE-2015-3A38`, Marlin Sea Focus): 16 registros selados em 11 categorias e 25 documentos, com uma linha do tempo completa incluindo sinistro e desfecho. Base para gerar o **primeiro dossiê de ponta a ponta** — `dossie_saidas` ainda está zerada
- [x] **REV-04 — Sinistros com ficha rica e desfecho** (`resolve_id`): a aba mais grave era a mais pobre (4 campos). Agora registra a ocorrência e o reparo como **dois registros selados**, com sistemas atingidos marcáveis em conjunto e o par de fotos antes/depois. O Casco segue sendo vistoria de rotina
- [x] **REV-04 — Indicação registrada no cadastro**: a página promete que quem indica participa dos dossiês da indicada, mas nada capturava o vínculo — e ele **só existe no momento do cadastro**. Texto cru sempre preservado; casamento automático por e-mail ou nome; liberação do bônus segue manual
- [x] **REV-04 — Régua de cobrança roda sozinha** (`services/agenda.py`, no startup do FastAPI): cron externo some em migração de servidor e ninguém percebe, porque não avisar é indistinguível de não haver devedor. O corte segue sendo do porteiro, na leitura
- [x] **REV-04 — Stripe: assinatura vira "não paga", nunca cancelada** — cancelar quebraria o religamento automático; e-mails de cobrança da Stripe desligados (a régua própria é em português), aviso de cartão a vencer ligado
- [x] **REV-04 — Identidade no link de pagamento** (`client_reference_id`): sem ela a marina pagava e **não recebia acesso**, porque a carteira Link da Stripe usa outro e-mail. Descoberto ao ver `payments` vazia depois de um pagamento real
- [x] **REV-04 — Solara com suporte ao produto** + registro das perguntas (`solara_perguntas`); conhecimento gerado do código e guardado por teste
- [x] **REV-04 — Tela para de piscar a cada troca de aba**: `PrivateRoute` passou a observar o id do usuário, não o objeto da sessão (o Supabase renova o token no foco); conversa da Solara sobrevive à navegação
- [x] **REV-04 — Upload com acento/espaço no nome**: a chave do storage é sanitizada (o nome original segue em `documentos.nome_arquivo`)

## Manutenção Preditiva Semanal
Rotina de verificação em [CHECKLIST-SEMANAL.md](CHECKLIST-SEMANAL.md), ordenada por criticidade — do que derruba o negócio ao que só previne problema futuro. Existe porque **o sistema falha em silêncio**: webhook que parou, e-mail que virou spam, WhatsApp que desconectou. Nada disso apita, e a marina só descobre quando já custou dinheiro ou confiança.

Para rodar: abrir uma sessão e pedir *"roda o checklist semanal"* — as consultas ao banco e aos logs são executadas e só o que estiver fora do normal é reportado. Itens marcados com 👤 dependem do fundador (EasyPanel, Stripe, celular).

## Pendências / Próximos Passos
1. **Revisar gestão de segredos** — rotação das chaves de serviço pendente (decisão do fundador). *A imutabilidade dos registros já protege contra adulteração.*
2. **Desligar o auto-deploy** do EasyPanel (push em `master` reconstrói prod sozinho) — passar para deploy manual.
3. **`VERIFICACAO_SECRET` em produção (BLOQUEIA O LANÇAMENTO)** — sem ele o código cai no literal de desenvolvimento, que está no repositório público. **Verificado em 21/08: produção aceitou uma assinatura forjada com esse literal** — qualquer um pode fabricar um dossiê falso com QR que valida. Configurar **antes do primeiro dossiê**; trocar depois invalida todo QR já emitido.
4. **Privacidade do bucket `media`** — hoje é público; mover documentos sensíveis p/ bucket privado + URL assinada (LGPD).
5. **Soft-delete de ativo** — para imutabilidade **total** (hoje DELETE de ativo apaga registros em cascata).
6. **`audit_logs`** — insert está falhando por RLS (`42501`); ajustar policy para a auditoria gravar de fato.
7. **Higiene de repositório** — imagens grandes (6–12 MB) e arquivos avulsos na raiz; duas cópias locais do repo (com/sem "H").
8. **Portar dossiê premium p/ produção** — o layout premium hoje está só no kit local (`dossie-exemplo/`); levar para `dossie_pdf.py` quando aprovado.
9. **Traduzir os modelos de e-mail do Supabase** — ainda em inglês ("Reset Your Password"). Marca brasileira mandando e-mail em inglês com link de senha é padrão clássico de phishing, e pesou no spam junto com o DKIM que faltava.
10. **Validar o `verifyOtp` do Portal do Proprietário** contra a Supabase real — é o único ponto do fluxo que não dá para testar sem conta de verdade.
11. **Limite de 4 dossiês/ano existe só no frontend** — sem checagem no servidor. Vira regra de verdade quando o 5º dossiê passar a ser cobrado.
12. **Suporte humano é estratégia enquanto forem 20–40 marinas** — a Solara responde o "onde"; o fundador responde o "por quê". Automatizar o resto cedo demais deixa surdo o sinal que corrige a interface. Revisar quando a mesma pergunta chegar 20 vezes ou a resposta demorar mais de um dia.
13. **`alertas.py` órfão** — endpoints de alerta de vencimento sem ninguém chamando, protegidos por admin (cron externo não alcança), sem idempotência e enviando para e-mail fixo. Remover ou reescrever no padrão do `cron_cobranca`.
14. **Decidir o que a nota do ativo significa** — hoje ela mede volume de cadastro, não saúde: o Marlin Sea teve um rombo, ficou interditado, e pontua 87 (Ouro). A escala também é pouco discriminante (preencher tudo uma vez já dá 83). Renomear para *Índice de Custódia* — coerente com o fato de a plataforma **não inspecionar** — ou fazer a nota penalizar atenção, sinistro em aberto e documento vencido.
15. **Marina não consegue cancelar sozinha** — não há botão no painel; hoje ela pede por e-mail/WhatsApp. Decisão consciente enquanto forem 20 marinas.

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
- **Marina (autenticada)**: opera, edita e sela; acessa o dossiê dos próprios ativos (dados + PDF).
- **Armador (Portal do Proprietário)**: entra com o **próprio e-mail** + código de uso único (e-mail e WhatsApp), enxerga **somente os barcos com o e-mail dele** e **apenas lê**. Nunca usa a conta da marina — do contrário veria a frota inteira dela. O primeiro contato é feito **pela marina**, não pelo sistema.
- **Terceiros (broker/comprador/seguradora)**: pedem por formulário aberto (`POST /dossie/solicitar`) → Yachts Atlas libera manualmente → acesso por página mobile protegida por **senha-mestra**; saídas registradas em `dossie_saidas`.

## Flags de Ambiente
- `ALLOWED_ORIGINS` — CORS (inclui `yachtsatlas.online`).
- `MAINTENANCE_USERNAME/PASSWORD/MASTER_TOKEN`, `MAINTENANCE_BYPASS_ENABLED`, `DOSSIER_MASTER_PASSWORD` — acesso de manutenção/admin (**nunca remover sem confirmação do fundador**).
- `SUPABASE_URL`, `SUPABASE_KEY` (publishable), `SUPABASE_SERVICE_KEY` (secret), `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`, `STRIPE_*`.
- `VERIFICACAO_SECRET` — assina o QR de autenticidade do dossiê. **Sem ela o código cai no literal de desenvolvimento, que está no repositório público.** Trocar depois de emitir o primeiro dossiê invalida todos os QR já impressos.
- **E-mail (Hostinger, domínio próprio):** `EMAIL_SENDER` (`contato@yachtsatlas.online`), `EMAIL_PASSWORD`, `EMAIL_SMTP_HOST` (`smtp.hostinger.com`), `EMAIL_SMTP_PORT` (465), `EMAIL_REMETENTE_COBRANCA` (alias `cobranca@`).
- **WhatsApp (Evolution):** `WHATSAPP_PROVIDER`, `EVOLUTION_BASE_URL`, `EVOLUTION_API_KEY`, `EVOLUTION_INSTANCE`, `DDI_PADRAO`.
- **Avisos ao fundador:** `ALERTA_WHATSAPP` (número que recebe), `ALERTA_EMAIL`.
- **Links de pagamento:** `STRIPE_LINK_MARINA_FUNDADORA` ($200) e `STRIPE_LINK_MARINA_OFICIAL` ($250) — ambos na conta do CNPJ.
