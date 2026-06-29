/**
 * Yachts Atlas — Cobertura Fotográfica do Dossiê
 * ------------------------------------------------------------------
 * O dossiê suporta até MAX_FOTOS imagens por embarcação, organizadas por
 * categoria. A "cobertura" é o nível de preenchimento — geral (total/400)
 * e por categoria (count/mínimo). Quanto maior a cobertura, mais peso o
 * dossiê tem na negociação e na seguradora.
 *
 * Os mínimos abaixo somam exatamente MAX_FOTOS e refletem o peso de cada
 * área no valor do ativo (ponderado).
 */

export const MAX_FOTOS = 400

/** Limiar de "cobertura premium" — argumento comercial (negociação/seguradora). */
export const COBERTURA_PREMIUM = 80

export interface CoberturaCat {
  key: string
  label: string
  /** Mínimo recomendado de fotos nesta categoria. */
  minimo: number
}

export const COBERTURA_CATS: CoberturaCat[] = [
  { key: 'casco_exterior', label: 'Casco / Exterior', minimo: 80 },
  { key: 'motor', label: 'Motor / Propulsão', minimo: 70 },
  { key: 'interior', label: 'Interior', minimo: 60 },
  { key: 'pintura', label: 'Pintura', minimo: 40 },
  { key: 'eletronica', label: 'Eletrônica / Navegação', minimo: 40 },
  { key: 'antes_depois', label: 'Antes e Depois', minimo: 40 },
  { key: 'notas_fiscais', label: 'Notas Fiscais', minimo: 40 },
  { key: 'outros', label: 'Outros', minimo: 30 },
]

/** Normaliza a categoria gravada (ex.: 'galeria_motor', 'fotos') para uma chave de cobertura. */
export function normalizarCategoria(categoria: string | undefined | null): string {
  const k = String(categoria || '').replace('galeria_', '')
  return COBERTURA_CATS.some((c) => c.key === k) ? k : 'outros'
}
