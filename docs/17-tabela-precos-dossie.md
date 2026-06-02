# Tabela de Preços — Dossiê Yachts Atlas

> **Dossiê único, sem classes.** Existe UM "Dossiê Yachts Atlas" que se adapta ao ativo
> (mostra todas as seções aplicáveis, sempre impecável). A faixa de tamanho define
> **apenas o preço**, conforme a complexidade/trabalho de verificação — não a qualidade.

## Recorrência (marina)
| Produto | Valor |
|---|---|
| Assinatura Marina | **$250 / mês** |

> Modelo B2B2C: Atlas fica com a recorrência; a marina retém 100% da receita dos dossiês
> por 18 meses mediante indicação de nova marina.

## Dossiê — 8 faixas por tamanho

| # | Faixa (comprimento) | Preço (USD) | Status Stripe |
|---|---------------------|-------------|---------------|
| 1 | até 26 pés | **$100** | a criar |
| 2 | 27 – 35 pés | **$150** | a criar |
| 3 | 36 – 45 pés | **$200** | existente |
| 4 | 46 – 60 pés | **$300** | a criar |
| 5 | 61 – 79 pés | **$400** | existente |
| 6 | 80 – 99 pés | **$600** | existente |
| 7 | 100 – 149 pés | **$900** | a criar |
| 8 | 150+ pés | **$1.500** | a criar |

**Range:** $100 → $1.500.

## Lógica
- **Ponta baixa ($100–150):** preço de impulso → volume de ativos no sistema (alimenta o efeito rede).
- **Meio ($200–600):** grosso do mercado.
- **Ponta alta ($900–1.500):** megayacht — margem premium, valor irrelevante para o dono.

## Pendências de implementação
1. Criar no Stripe os 5 novos produtos/links (faixas 1, 2, 4, 7, 8).
2. Reetiquetar os 3 links existentes (36-45 / 61-79 / 80-99).
3. Sistema: mapear automaticamente `comprimento_pes` → faixa → preço/link.
