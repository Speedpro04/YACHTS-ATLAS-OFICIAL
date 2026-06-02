/**
 * Yachts Atlas — Preços do Dossiê (fonte única de verdade)
 * ------------------------------------------------------------
 * Dossiê ÚNICO, sem classes. O preço acompanha o PORTE do ativo.
 * 8 faixas, cada uma com seu link de pagamento Stripe.
 * A home (escada de preços) e o checkout leem daqui.
 */

export interface FaixaPreco {
  id: string
  label: string
  minPes: number
  maxPes: number | null // null = sem teto (150+)
  precoUSD: number
  stripeLink: string
}

export const FAIXAS_DOSSIE: FaixaPreco[] = [
  { id: 'ate-26',  label: 'até 26 pés',    minPes: 0,   maxPes: 26,   precoUSD: 100,  stripeLink: 'https://buy.stripe.com/cNifZg76S63a8Ya0Mq9IQ0a' },
  { id: '27-35',   label: '27 a 35 pés',   minPes: 27,  maxPes: 35,   precoUSD: 150,  stripeLink: 'https://buy.stripe.com/bJe00i1My2QYb6ibr49IQ0b' },
  { id: '36-45',   label: '36 a 45 pés',   minPes: 36,  maxPes: 45,   precoUSD: 200,  stripeLink: 'https://buy.stripe.com/00w6oG8aW1MUeiufHk9IQ06' },
  { id: '46-60',   label: '46 a 60 pés',   minPes: 46,  maxPes: 60,   precoUSD: 300,  stripeLink: 'https://buy.stripe.com/14AfZg3UG77ecam2Uy9IQ0c' },
  { id: '61-79',   label: '61 a 79 pés',   minPes: 61,  maxPes: 79,   precoUSD: 400,  stripeLink: 'https://buy.stripe.com/14AfZg9f09fm0rE66K9IQ08' },
  { id: '80-99',   label: '80 a 99 pés',   minPes: 80,  maxPes: 99,   precoUSD: 600,  stripeLink: 'https://buy.stripe.com/3cI4gyfDoajq5LYan09IQ09' },
  { id: '100-149', label: '100 a 149 pés', minPes: 100, maxPes: 149,  precoUSD: 900,  stripeLink: 'https://buy.stripe.com/00wfZg9f0dvCdeq1Qu9IQ0d' },
  { id: '150-mais',label: '150+ pés',      minPes: 150, maxPes: null, precoUSD: 1500, stripeLink: 'https://buy.stripe.com/dRm9ASezkcrygqCbr49IQ0e' },
]

/** Retorna a faixa de preço correspondente ao comprimento (em pés). */
export function faixaPorPes(pes: number): FaixaPreco {
  const f = FAIXAS_DOSSIE.find(
    (x) => pes >= x.minPes && (x.maxPes === null || pes <= x.maxPes)
  )
  return f ?? FAIXAS_DOSSIE[FAIXAS_DOSSIE.length - 1]
}

/** Formata o preço em USD para exibição (ex.: "US$ 1.500"). */
export function formatarPreco(valorUSD: number): string {
  return 'US$ ' + valorUSD.toLocaleString('pt-BR')
}
