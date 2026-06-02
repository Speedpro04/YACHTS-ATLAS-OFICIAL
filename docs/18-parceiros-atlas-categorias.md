# Parceiros Atlas — Categorias do Diretório

> Diretório de parceiros do Yachts Atlas. Hoje o código tem só `broker` e `insurance`
> (`frontend/src/pages/Parceiros.tsx`, `backend/app/schemas/partners.py`).
> Objetivo: expandir para o **ecossistema completo do ciclo de vida do barco**.
>
> **Bônus estratégico:** parceiros físicos (transporte, içamento, refit) tocam o ativo e
> podem virar fonte de procedência/dado para o dossiê (ex: "transportado por X em DD/MM").

## ✅ Confirmadas (9)

| Grupo | Chave | Label |
|-------|-------|-------|
| Papel/dinheiro | `broker` | Brokers *(já existe)* |
| Papel/dinheiro | `insurance` | Seguros *(já existe)* |
| Físico/operacional | `tractor` | Tratores & Içamento |
| Físico/operacional | `forklift` | Empilhadeiras (marina seca) |
| Físico/operacional | `nautical_transport` | Transporte Náutico |
| Físico/operacional | `trailer_manufacturer` | Carretas de Transporte |
| Mecânico/motor | `outboard_motor` | Motores de Popa |
| Mecânico/motor | `engine_rebuild` | Retíficas de Motores |
| Reforma | `refit` | Retrofit & Refit de Embarcações |

## 💡 Sugeridas (aguardando decisão)

Prioridade ⭐ = top 4 recomendadas.

| Grupo | Chave | Label |
|-------|-------|-------|
| Serviço | `shipyard` | Estaleiros / Oficinas Náuticas ⭐ |
| Serviço | `paint_antifouling` | Pintura & Antifouling ⭐ |
| Serviço | `hull_cleaning` | Mergulho / Limpeza de Casco |
| Serviço | `upholstery` | Capotaria & Estofados |
| Equipamentos | `marine_electronics` | Eletrônica Náutica ⭐ |
| Equipamentos | `hvac_generators` | Geradores & Ar-Condicionado |
| Equipamentos | `sails_rigging` | Velas & Cordoaria ⭐ *(diferencial em Ilhabela)* |
| Equipamentos | `chandlery` | Acessórios / Loja Náutica |
| Burocracia/$ | `naval_clearance` | Despachante Naval / Documentação ⭐ |
| Burocracia/$ | `financing` | Financiamento Náutico |
| Burocracia/$ | `charter` | Charter / Afretamento |
| Operação | `fuel` | Combustível / Abastecimento |
| Operação | `towing` | Guincho & Assistência 24h |

## Pendências
- Henrique decidir quais sugeridas entram.
- Definir **modelo de negócio dos parceiros** (pagam listagem / comissão / curadoria grátis).
- Implementar: enum no backend + filtros/ícones/cards no frontend Parceiros.
