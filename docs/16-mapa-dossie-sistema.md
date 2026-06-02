# Mapa Mestre — Sincronia Sistema ↔ Dossiê (Contrato de Verdade)

> Fonte única que mantém o **sistema interno** (coleta de dados) e o **dossiê PDF**
> (entregável pago) em perfeita sincronia. Qualquer campo novo entra **primeiro aqui**.
> Princípio: **tiers acumulativos** — tudo que está no Compact aparece no Executive e no
> Superyacht; cada tier superior só **adiciona** seções.

## Estado atual (diagnóstico)

- ✅ **A lógica de tiers acumulativos já existe** no motor do PDF (`dossie_engine/generate.py`).
- 🔴 **Os dados estão chumbados** (mock) no PDF: só 4 de 12 seções recebem dados de fora
  (`secao_identificacao`, `secao_proprietarios`, `secao_documentacao`, `secao_manutencao`).
  As outras 8 (inspeção, sinistros, valuation, seguradora, IMO, casco, due diligence, assinatura)
  têm conteúdo fixo em `dossie_engine/sections.py`.
- 🔴 **O sistema e o PDF não se falam** — o gerador é um script standalone com dicts mock.
- 🟡 O sistema (`TechnicalFormOverlay.tsx`) já coleta parte dos dados nas tabelas Supabase
  (`engines`, `maintenance_logs`, `vessel_inspections`, `documentos`, `geotagged_media`).

## Legenda de status
- ✅ **OK** — coletado no sistema e fluindo (ou pronto para fluir)
- 🟡 **PARCIAL** — existe coleta, mas falta campo/formato/vínculo com o PDF
- 🔴 **FALTA** — não há coleta no sistema (dado só existe chumbado no PDF)
- 🌍 **universal** — vale para qualquer país | 🇧🇷 **BR** — específico do Brasil (parametrizar p/ LatAm/EUA)

---

## Seções por TIER

### COMPACT (base — aparece em TODOS os tiers)

| # | Seção | Dados necessários | Fonte no sistema | Status | País |
|---|-------|-------------------|------------------|--------|------|
| 01 | Identificação | nome, tipo, fabricante, modelo, ano, comprimento, **nº registro**, **bandeira** | `ativos` | 🟡 falta registro+bandeira | reg/bandeira 🇧🇷 |
| 02 | Histórico de Proprietários | ordem, nome, período, tipo transferência | — (sem tabela) | 🔴 FALTA | 🌍 |
| 03 | Documentação Legal e Fiscal | checklist de documentos | `documentos` + checklist `vessel_inspections` | 🟡 parcial | 🇧🇷 (CPAM, CSE, DPEM, Arrais, IPVA) |
| 04 | Histórico de Manutenção | data, serviço, responsável, status | `maintenance_logs` / `manutencao_registros` | ✅ OK | 🌍 |
| 05 | Registro Fotográfico | 6 fotos categorizadas + hash SHA-256 + geo | `geotagged_media` (SecureCameraUpload) | 🟡 falta categorizar/vincular | 🌍 |
| — | Acesso ao Cofre Digital | URL, ID ativo, nível acesso, 2FA | gerado pelo sistema | 🟡 automatizar | 🌍 |
| — | Assinatura Digital | hash SHA-256 do doc + data emissão + QR verify | `cryptographic_seals` | 🔴 hoje chumbado no PDF | 🌍 |

### EXECUTIVE (= Compact + abaixo)

| # | Seção | Dados necessários | Fonte no sistema | Status | País |
|---|-------|-------------------|------------------|--------|------|
| 06 | Inspeção Técnica Certificada | data, inspetor, metodologia, 6 sistemas (status APROVADO/ATENÇÃO + obs) | `inspections` / `vessel_inspections` | 🟡 falta formato status-por-sistema | 🌍 |
| 07 | Histórico de Sinistros e Reparos | data, evento, reparo, valor USD | — (sem tabela) | 🔴 FALTA | 🌍 |
| 08 | Avaliação de Mercado | valor estimado, data, metodologia, fonte | — (sem tabela) | 🔴 FALTA | 🌍 (fonte varia: BUC no 🇧🇷) |
| 09 | Relatório para Seguradora | valor segurado, classe risco, uso, atracação, equip, sinistros | `insurance_ready_reports` (existe!) | 🟡 conectar | 🌍 |

### SUPERYACHT (= Executive + abaixo)

| # | Seção | Dados necessários | Fonte no sistema | Status | País |
|---|-------|-------------------|------------------|--------|------|
| 10 | Compliance Internacional (IMO) | nº IMO, bandeira, classe cert., arqueação, SOLAS, ISM/ISPS/MARPOL/MLC/ITU | — (sem tabela) | 🔴 FALTA | 🌍 (internacional p/ 80+) |
| 11 | Auditoria Estrutural do Casco | método, nº pontos, data, zonas + % integridade | — (sem tabela) | 🔴 FALTA | 🌍 |
| 12 | Suporte à Due Diligence | índice integridade, sinistros 10a, regularidade, compliance, pendências judiciais, dívidas/gravames | **derivado** das seções acima | 🔴 calcular | pendências/gravames 🇧🇷 |

---

## Quem preenche cada dado (a definir com Henrique)
- **Marina** (painel): identificação, manutenção, fotos, inspeção, documentação?
- **Proprietário**: histórico de proprietários, documentos pessoais?
- **Inspetor/estaleiro terceiro**: inspeção técnica, auditoria de casco (laudos com responsável técnico)?
- **Sistema (automático)**: acesso ao cofre, hash/assinatura, índice de due diligence (derivado)?
- **Parceiros Atlas** (brokers/seguradoras): consomem ou alimentam? (a definir)

## Parametrização por país (expansão LatAm → EUA 2029)
A seção **03 (Documentação Legal)** e partes da **01/12** são país-específicas. Desenhar como
**catálogo de documentos por país** (ex.: tabela `country_doc_requirements`) em vez de campos
chumbados em PT-BR. Brasil é o primeiro perfil; Argentina (Prefectura), Chile (DIRECTEMAR),
México (SEMAR), EUA (USCG/HIN) entram como novos perfis sem refatorar o núcleo.

## Próximos passos (ordem sugerida)
1. **Validar este mapa** com Henrique (preenchimento + parceiros).
2. Criar tabelas faltantes: `owner_history`, `incidents`, `valuations`, `imo_compliance`, `hull_audits`.
3. Refatorar `dossie_engine` para receber **um único JSON do ativo** (parâmetros) no lugar dos mocks.
4. Endpoint backend `GET /dossie/{ativo_id}/data?tier=` que monta o JSON a partir do banco.
5. Formulários do sistema espelhando 1:1 as seções por tier.
6. Hash SHA-256 real + QR de verificação por dossiê.
