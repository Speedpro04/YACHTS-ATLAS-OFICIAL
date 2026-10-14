/**
 * Yachts Atlas — Preço do serviço (fonte única de verdade)
 * ------------------------------------------------------------
 * A assinatura da Marina. Um preço só, para todas: US$ 140/mês, cobrado em
 * real a R$ 697,00. Travado por 12 meses a partir da assinatura; no 13º mês
 * entra a correção por IPCA + 15%.
 *
 * POR QUE UM ARQUIVO SÓ
 * O valor aparecia escrito à mão em três lugares — a primeira dobra da home,
 * a etapa de pagamento do cadastro e o texto da cobrança em real. Preço
 * repetido é preço que muda em dois lugares e fica velho no terceiro, e o
 * terceiro é sempre o que o cliente lê antes de pagar.
 *
 * O ESPELHO NO BACKEND
 * Quem cobra é a Stripe, e quem fala com ela é `backend/app/core/config.py`
 * (PRECO_MENSAL_USD / PRECO_MENSAL_BRL / PRECO_TRAVADO_MESES / REAJUSTE_*).
 * Estes números aqui são os MESMOS, para a tela não prometer o que a fatura
 * não cumpre. Mudou aqui, muda lá.
 */

export const PRECO_SERVICO = {
  /** Preço anunciado. O dólar é a oferta; o real é forma de pagamento. */
  usd: 140,
  /**
   * O mesmo preço cobrado em real. Travado junto com a oferta: não acompanha
   * o dólar no meio dos 12 meses. Implica câmbio de 4,98 — se o dólar subir
   * muito acima disso, o preço em real é que precisa ser revisto, e ninguém
   * avisa: tem que olhar (ver BRL_TAXA_REVISAR_ACIMA_DE no backend).
   */
  brl: 697,
  /** Meses em que o valor não sobe. Espelha PRECO_TRAVADO_MESES no backend. */
  mesesTravado: 12,
  /** O que corrige o preço no 13º mês. Não é número fixo de propósito: o
   *  IPCA do período só é conhecido na época. */
  reajusteIndice: 'IPCA',
  reajustePercentual: 15,
} as const

/** "US$ 140" */
export function precoEmDolar(): string {
  return 'US$ ' + PRECO_SERVICO.usd.toLocaleString('pt-BR')
}

/** "R$ 697,00" — com os centavos, porque é o valor que entra na fatura. */
export function precoEmReal(): string {
  return (
    'R$ ' +
    PRECO_SERVICO.brl.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })
  )
}
