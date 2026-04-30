# Yachts Atlas — Modelo do Ativo

## 1. Definição de Ativo

Um **ativo** no Yachts Atlas é uma entidade náutica registrada com:

- Identificação única (não repetível)
- Dados técnicos completos
- Dono(s) vinculado(s)
- Histórico completo desde fabricação
- Classificação atual (Bronze/Silver/Gold)
- Barra de progresso

---

## 2. Tipos de Ativo

| Tipo | Descrição | Comprimento Typical | Valor Typical |
|---|---|---|---|
| Iate | Embarcação de luxo com casa de piloto | 10m - 50m+ | R$2MM - R$50MM+ |
| Lancha | Embarcação open ou cabinada | 5m - 12m | R$500K - R$5MM |
| Veleiro | Embarcação a vela | 6m - 30m | R$300K - R$10MM |
| Jet-ski | Motocicleta aquática | 2.5m - 3.5m | R$80K - R$300K |
| Barco de Pesca | Embarcação para pesca esportiva | 5m - 10m | R$200K - R$1MM |

---

## 3. Identificação Único do Ativo

Cada ativo possui um ID único gerado pelo sistema:

```
YA-{Tipo}-{AnoCriação}-{Sequencial}
```

Exemplos:
- `YA-IATE-2024-0001`
- `YA-JETSKI-2024-0150`

**Também pode incluir identificadores externos:**
- RGP (Registro Geral de Barcos)
- VIN (se aplicável)
- Número de série do casco
- Nome de registration (se disponível)

---

## 4. Dados Técnicos do Ativo

### Obrigatórios (todos os tipos)

| Campo | Tipo | Descrição |
|---|---|---|
| tipo | enum | iate, lancha, veleiro, jetski, barco_pesca |
| marca | string | Fabricante (Azimut, Sunseeker, etc.) |
| modelo | string | Modelo específico |
| ano_fabricacao | integer | Ano de fabricação |
| comprimento | float | Comprimento em metros |
| comprimento_pes | float | Comprimento em pés (Principal para categorização) |
| largura | float | Boca em metros |
| calado | float | Calado em metros |
| material_casco | enum | Fibra, alumnio, madeira, aco |
| capacidade_passageiros | integer | Capacidade máxima |

### Opcionais (por tipo)

| Campo | Aplica-se | Descrição |
|---|---|---|
| modelo_motor | todos | Modelo do(s) motor(es) |
| potencia_motor | todos | Potência em HP |
| num_motores | todos | Quantidade de motores |
| tipo_combustivel | todos | Diesel, gasoline |
| num_cabines | iate, lancha, veleiro | Quantidade de cabines |
| capacidade_tanque | todos | Capacidade do tanque em litros |
| nome | todos | Nome de registration |

---

## 5. Classificação do Ativo

| Classificação | Descrição | Requisitos Mínimos |
|---|---|---|
| **Bronze** | Conformidade básica | Documentos obrigatórios + seguro válido |
| **Silver** | Bem documentado | Bronze + histórico de manutenções + fotos + documentos |
| **Gold** | Excelência | Silver + relatórios de survey + dossier completo |

### Barra de Progresso

```
Bronze ──────────────████████████── Silver ──────────────██████████████ Gold
      0%                        50%                        100%
```

**Critérios por classificação:**

| Critério | Bronze | Silver | Gold |
|---|---|---|---|
| Documentos obrigatórios | ✓ | ✓ | ✓ |
| Seguro válido | ✓ | ✓ | ✓ |
| Foto atual | — | ✓ | ✓ |
| Histórico ≥3 manutenções | — | ✓ | ✓ |
| Relatório survey | — | — | ✓ |
| Dossier completo | — | — | ✓ |

---

## 6. Eventos do Ativo

Um **evento** é tudo que acontece com o ativo e fica registrado no histórico.

### Tipos de Evento

| Tipo | Subtipo | Descrição |
|---|---|---|
| manutencao | preventiva | Troca de óleo, filtros, revisão |
| manutencao | corretiva | Reparo, substituição de peça |
| reforma | upgrade | Melhoria (novo motor, pintura) |
| reforma | restauro | Restauração completa |
| inspecao | survey | Inspeção técnica profissional |
| inspecao | vistoria | Vistoria para seguro |
| documento | rgp | Registro Geral de Barcos |
| documento | certificado | Certificado de navegação |
| documento | baixa | Baixa de registro |
| seguro | renovacao | Renovação de seguro |
| seguro | sinistro | Sinistro registrado |
| venda | transferencia | Venda/transferência |
| venda |Compra | Compra do ativo |
| alerta | vencimento | Alerta de documento vencendo |
| alerta | manutencao | Alerta de manutenção pendente |

### Estrutura do Evento

```json
{
  "id": "evt-2024-001",
  "ativo_id": "YA-IATE-2024-0001",
  "tipo": "manutencao",
  "subtipo": "preventiva",
  "titulo": "Troca de óleo e filtros",
  "descricao": "Troca de óleo двигателя e filtros de combustível",
  "data": "2024-03-15",
  "data_proxima": "2024-09-15",
  "prestador": "Yard Marina",
  "custo": 15000,
  "documentos": ["nota_fiscal_2024.pdf"],
  "anexos": ["foto_oleo.jpg"],
  "criado_por": "user-123",
  "criado_em": "2024-03-16T10:30:00Z"
}
```

---

## 7. Histórico do Ativo

O histórico é uma **linha do tempo cronológica** de todos os eventos.

**Características:**
- Imutável (não pode ser apagado)
- Encadeado (cada evento ссылается ao anterior)
- Auditável (quem criou, quando, e validado)
- Completo (do Fabrication até hoje)

### Visualização do Histórico

```
2026-04-15 ━━━━━ Seguro renovação (YA-2026-001)
     │
2025-11-20 ━━━━━ Manutenção preventiva (óleo, filtros)
     │
2025-08-10 ━━━━━ Survey anual — Aprovado
     │
2025-03-05 ━━━━━ Reforma — Novos geradores
     │
2024-12-01 ━━━━━ Seguro renovação
     │
2024-06-20 ━━━━━ Manutenção corretiva (bomba d'água)
     │
2023-09-15 ━━━━━ Venda — Transferência para novo dono
     │
2022-03-10 ━━━━━ Compra do ativo (primeiro registro)
```

---

## 8. Documentos do Ativo

| Categoria | Documento | Obrigatório |
|---|---|---|
| Registro | RGP (Registro Geral de Barcos) | Bronze |
| Registro | Documento único | Bronze |
| Registro | Certificado de navegação | Bronze |
| Seguro | Apólice de seguro | Bronze |
| Seguro | Certidão de seguro | Bronze |
| Manutenção | Notas fiscais | Silver |
| Manutenção | Ordens de serviço | Silver |
| Inspeção | Relatório de survey | Gold |
| Inspeção | Laudo de vistoria | Gold |
| Fotos | Fotos aktuais | Silver |
| Fotos | Fotos históricas | Gold |

---

## 9. Dossier — Estrutura para Negociação

### Dossier Básico

- Capa com dados do ativo
- Fotos atuais
- Cópia do RGP
- Cópia do seguro atual
- Documento único

### Dossier Completo

- Tudo do Básico
- Histórico de manutenções (últimos 3 anos)
- Fotos de manutenção
- Notas fiscais
- Lista de equipamentos
- Declaração de próprio

### Dossier Premium

- Tudo do Completo
- Relatórios de survey (últimos 2 anos)
- Todas as certidões atualizadas
- Hash cryptográfico de cada documento
- Mapa de histórico
- Avaliação estimada de mercado

---

## 10. Integração com Classificação

| Classificação | Permite Gerar Dossier |
|---|---|
| Bronze | Básico |
| Silver | Básico, Completo |
| Gold | Básico, Completo, Premium |

---

## 11. Versão

v0.1 — Modelo do Ativo (rascunho inicial)

---

## 12. Data

2026-04-22