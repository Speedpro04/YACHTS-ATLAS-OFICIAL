# 17. Especificação Técnica — Dossiês PDF Atlas Yachts

## 1. Visão Geral
Os dossiês são documentos PDF gerados sob demanda pelo gerente da marina, disponíveis apenas após confirmação de pagamento pelo armador. Existem três modalidades:

| Modalidade | Destinatário Principal | Finalidade |
| :--- | :--- | :--- |
| **Dossiê de Venda** | Comprador / Corretor | Apresentação comercial do ativo |
| **Dossiê de Seguradora** | Seguradora / Broker de seguros | Avaliação de risco e cobertura |
| **Dossiê do Armador** | Marina / Despachante / Capitania | Conformidade operacional e legal |

## 2. Categorização por Porte (Modelo B2B2C)
No modelo B2B2C, as marinas gerenciam a frota e emitem dossiês certificados. Os dossiês são segmentados em três categorias baseadas no comprimento em pés, definindo a complexidade e a precificação:

| Categoria | Faixa de Comprimento | Nível de Serviço | Valor do Dossiê |
| :--- | :--- | :--- | :--- |
| **Até 45 Pés** | ≤ 45 pés | Compact | **$200** |
| **46 a 79 Pés** | 46 — 79 pés | Executive | **$400** |
| **80 Pés ou Mais** | ≥ 80 pés | Superyacht | **$600** |

## 3. Regras Globais de Geração

### 2.1 Pré-requisitos para geração
*   Pagamento confirmado na assinatura do armador (status `subscription.active`)
*   Foto principal da embarcação presente no vault (obrigatória — geração bloqueada sem foto)
*   Dados mínimos obrigatórios preenchidos no cadastro da embarcação

### 2.2 Controle de acesso
*   Apenas o perfil **gerente de marina** pode solicitar a geração
*   O armador (Login 2) não pode solicitar dossiês — apenas visualizá-los se compartilhados
*   Nenhum campo pode ser editado na tela de geração — o PDF espelha fielmente o vault

### 2.3 Seleção na geração (único input do gerente)
*   [ ] Tipo de dossiê: Venda | Seguradora | Armador
*   [ ] Idioma: Português (pt-BR) | Español Latino (es-419) | English US (en-US)
*   **[ Gerar Dossiê ]**

### 2.4 Validade do documento
*   Todos os dossiês têm validade de **60 dias** a partir da data de geração
*   Data de expiração impressa na capa e no rodapé de cada página
*   Após expiração, o QR Code de verificação retorna status **EXPIRADO**

## 3. Identidade Visual — Papel Timbrado Atlas Yachts

### 3.1 Paleta de cores
| Token | Hex | Uso |
| :--- | :--- | :--- |
| `color-primary` | `#07070D` | Fundo do header, texto principal |
| `color-gold` | `#C9A84C` | Linhas decorativas, destaques, bordas douradas |
| `color-ruby` | `#9B1B30` | Alertas de conformidade, status expirado |
| `color-emerald` | `#046A38` | Status válido, documentos em dia |
| `color-white` | `#FFFFFF` | Texto sobre fundo escuro |
| `color-light` | `#F5F3EE` | Fundo de páginas de conteúdo |

### 3.2 Tipografia
| Elemento | Fonte | Tamanho | Peso |
| :--- | :--- | :--- | :--- |
| Nome da embarcação (capa) | Cormorant Garamond | 36pt | Regular |
| Títulos de seção | Montserrat | 14pt | SemiBold |
| Subtítulos | Montserrat | 11pt | Medium |
| Corpo do texto | Montserrat | 10pt | Regular |
| Labels de campo | Montserrat | 8pt | Medium, uppercase |
| Número de série / hash | Courier New | 8pt | Regular |

### 3.3 Estrutura de páginas
*   **PÁGINA 1 — CAPA**
    *   Foto da embarcação (full-bleed ou card central)
    *   Logo Atlas Yachts (canto superior direito)
    *   Nome da embarcação em destaque
    *   Tipo do dossiê (badge colorido)
    *   Nome da marina emissora
    *   Data de geração / Validade (60 dias)
    *   Número de série do documento
*   **PÁGINAS 2..N — CONTEÚDO**
    *   **HEADER (toda página):** Logo mini (esq) | Nome embarcação (centro) | Nº série (dir) | Linha dourada separadora
    *   **CORPO:** Seções de dados (ver seção 4)
    *   **MARCA D'ÁGUA:** Logo Atlas Yachts diagonal, opacidade 6%, cinza, em todas as páginas
    *   **FOOTER (toda página):** Página X de Y | Validade: DD/MM/AAAA | atlasyachts.com.br | [QR Code 20x20mm] | "Documento confidencial — uso restrito"
*   **PÁGINA FINAL — ENCERRAMENTO E AUTENTICIDADE**
    *   Bloco de emissão: marina, CNPJ, responsável
    *   Hash SHA-256 do documento (visível)
    *   QR Code de verificação (40x40mm, centralizado)
    *   Linha de assinatura da marina
    *   Aviso de validade e aviso legal
    *   Data de expiração em destaque (ruby)

## 4. Campos por Modalidade de Dossiê

### 4.1 Dossiê de Venda
| Seção | Campo | Tipo | Fonte no vault | Obrigatório |
| :--- | :--- | :--- | :--- | :--- |
| **1 — Identificação** | Nome da embarcação | string | `vessel.name` | sim |
| | Tipo / categoria | enum | `vessel.type` | sim |
| | Ano de fabricação | year (int) | `vessel.year_built` | sim |
| | Comprimento total — LOA | decimal (m) | `vessel.loa_meters` | sim |
| | Fabricante / estaleiro | string | `vessel.manufacturer` | sim |
| | Número de inscrição (CF) | string | `vessel.registration_number` | sim |
| **2 — Documentação Legal** | TIE — Título de Inscrição da Embarcação | file (PDF/img) | `docs.tie` | sim |
| | Licença de Estação de Navio (ANATEL) | file | `docs.anatel` | sim |
| | Licença de Tráfego Aquaviário | file | `docs.trafico` | sim |
| | Certidão negativa de débitos | file | `docs.certidao_negativa` | sim |
| | Doc. de alienação fiduciária | file | `docs.alienacao` | não |
| | Comprovante de origem (NF ou contrato) | file | `docs.origem` | sim |
| **3 — Estado Técnico** | Relatório de vistoria do casco | file | `inspections.hull_report` | não |
| | Histórico de manutenção do motor | text + file | `maintenance.engine_log` | não |
| | Equipamentos de segurança — status | enum | `safety.status` | não |
| | Laudo elétrico e eletrônico | file | `inspections.electrical` | não |
| | Estado do velame | text | `vessel.sailplan_status` | não |
| **4 — Galeria de Imagens** | Foto principal | image | `media.cover_photo` | obrigatória |
| | Fotos externas | image[] | `media.exterior_photos` | 0 (rec. 10) |
| | Fotos internas | image[] | `media.interior_photos` | 0 (rec. 8) |
| | Foto do motor / casa de máquinas | image[] | `media.engine_photos` | 0 |
| | Planta da embarcação | file (PDF/img) | `docs.layout_plan` | não |

### 4.2 Dossiê de Seguradora
*Reusa Seção 1 do Dossiê de Venda*
| Seção | Campo | Tipo | Fonte no vault | Obrigatório |
| :--- | :--- | :--- | :--- | :--- |
| **1 — Avaliação** | Valor venal / de mercado | decimal (R$) | `vessel.market_value` | sim |
| | Valor de reposição declarado | decimal (R$) | `vessel.replacement_value` | sim |
| | Ano do último reparo estrutural | year (int) | `maintenance.last_structural_repair` | sim |
| | Local de guarda habitual | string | `vessel.home_port` | sim |
| **2 — Histórico de Sinistros** | Histórico de sinistros (últimos 5 anos) | text + file[] | `claims.history` | sim |
| | Apólices anteriores | file[] | `docs.previous_policies` | sim |
| | Laudos de peritagem de sinistros | file[] | `claims.expert_reports` | não |
| | Declaração de ausência de sinistros | file (assinado) | `claims.no_claims_declaration` | sim |
| **3 — Inspeção Técnica** | Laudo do casco (máx. 12 meses) | file + date | `inspections.hull_report` | não |
| | Laudo do sistema de propulsão | file | `inspections.propulsion` | não |
| | Laudo sistema de combustível | file | `inspections.fuel_system` | não |
| | Cert. de equipamentos de salvatagem | file + date | `safety.salvage_cert` | sim |
| | Relatório sistema contra incêndio | file | `safety.fire_report` | não |
| **4 — Proprietário e Operação** | Dados do proprietário / empresa | string + doc | `owner.profile` | sim |
| | Perfil de uso declarado | enum | `vessel.use_profile` | sim |
| | Área de navegação habitual | enum | `vessel.navigation_area` | sim |
| | Habilitação do skipper principal | string + file | `crew.main_skipper` | sim |
| | Número de tripulantes habituais | int | `crew.usual_count` | não |

### 4.3 Dossiê do Armador
| Seção | Campo | Tipo | Fonte no vault | Obrigatório |
| :--- | :--- | :--- | :--- | :--- |
| **1 — Dados Cadastrais** | Razão social / nome completo | string | `owner.name` | sim |
| | CNPJ / CPF | string | `owner.tax_id` | sim |
| | Endereço da sede / domicílio | string | `owner.address` | sim |
| | Representante legal | string + contato | `owner.legal_representative` | sim |
| | Embarcações do portfólio | list (nome + CF) | `owner.vessels[]` | sim |
| **2 — Conformidade** | TIE atualizado | file + date | `docs.tie` | sim |
| | Licença de navegação vigente | file + date | `docs.nav_license` | sim |
| | CSE — Certificado de Segurança (Marinha) | file + date | `docs.cse` | sim |
| | Certificado IOPP | file | `docs.iopp` | não |
| | Habilitação dos tripulantes | file[] | `crew.certifications[]` | sim |
| | Apólice de seguro vigente | file + date | `docs.insurance_policy` | sim |
| **3 — Histórico Manutenção** | Log de manutenção preventiva | text + file | `maintenance.preventive_log` | não |
| | Ordens de serviço últimos 24 meses | file[] | `maintenance.service_orders` | não |
| | Data última antifouling / slipagem | date | `maintenance.last_slipping` | não |
| | Registro de consumíveis e peças | text | `maintenance.parts_log` | não |
| | Relatórios de inspeção periódica | file[] | `inspections.periodic[]` | não |
| **4 — Tripulação e Acesso** | Lista de tripulantes habilitados | list + file[] | `crew.members[]` | sim |
| | Contratos de tripulação | file[] | `crew.contracts[]` | não |
| | Níveis de acesso por perfil | list | `crew.access_levels[]` | sim |
| | Contatos de emergência (24h) | string + tel | `owner.emergency_contacts` | sim |

## 5. Segurança e Autenticidade

### 5.1 Número de série
*   Formato: `ATY-[ANO][MÊS]-[TIPO]-[6 dígitos aleatórios]`
*   Exemplo: `ATY-202604-VND-847291`
*   Tipos: `VND` (venda), `SEG` (seguradora), `ARM` (armador)

### 5.2 Hash SHA-256
O hash é calculado sobre o snapshot completo dos dados da embarcação no momento da geração, garantindo que qualquer alteração posterior no vault invalide o hash original gravado no documento.

```python
def generate_document_hash(vessel_data: dict, dossie_type: str, generated_at: str) -> str:
    payload = json.dumps({
        "vessel_id": vessel_data["id"],
        "dossie_type": dossie_type,
        "generated_at": generated_at,
        "fields_snapshot": vessel_data
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

### 5.3 QR Code de verificação
*   URL: `https://verify.atlasyachts.com.br/doc/{numero_serie}`
*   Retorna status: **VÁLIDO** (verde) | **EXPIRADO** (ruby) | **INVÁLIDO** (vermelho)

## 6. Internacionalização (i18n)
*   **Idiomas Suportados:** pt-BR, es-419, en-US.
*   **Formatos de Data:**
    *   pt-BR / es-419: `DD/MM/AAAA`
    *   en-US: `MM/DD/YYYY`

## 7. Fluxo de Geração — Backend (FastAPI)
1. Validar pré-condições (vault, pagamento, foto).
2. Buscar snapshot no Supabase e calcular Hash SHA-256.
3. Gerar número de série e renderizar template via **WeasyPrint** (Jinja2).
4. Gerar QR Code e aplicar marca d'água.
5. Upload para **AWS S3** com **Object Lock (WORM)** para imutabilidade jurídica.
6. Gravar registro na tabela `dossies`.

## 8. Banco de Dados — Tabela de Dossiês
```sql
CREATE TABLE dossies (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  serial_number    VARCHAR(30) UNIQUE NOT NULL,
  vessel_id        UUID NOT NULL REFERENCES vessels(id),
  marina_id        UUID NOT NULL REFERENCES marinas(id),
  requested_by     UUID NOT NULL REFERENCES users(id),
  dossie_type      VARCHAR(20) NOT NULL CHECK (dossie_type IN ('venda','seguradora','armador')),
  language         VARCHAR(10) NOT NULL CHECK (language IN ('pt-BR','es-419','en-US')),
  sha256_hash      CHAR(64) NOT NULL,
  s3_url           TEXT NOT NULL,
  generated_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at       TIMESTAMPTZ NOT NULL,
  status           VARCHAR(20) NOT NULL DEFAULT 'valid' CHECK (status IN ('valid','expired','revoked')),
  vessel_snapshot  JSONB NOT NULL,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---
*Documento baseado na especificação técnica Versão 1.0 (Abril 2026).*
