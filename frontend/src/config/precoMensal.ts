// Preço único da mensalidade, para todas as Marinas. O valor cobrado mora no
// link da Stripe (STRIPE_LINK_MARINA_BRL): mudou aqui, muda lá.
export const PRECO_MENSAL_VALOR = 897
// Valor real até 05/11/2026. É a âncora do "de/por" da página inicial.
export const PRECO_ANTERIOR_VALOR = 1250

export const emReais = (valor: number) => 'R$ ' + valor.toLocaleString('pt-BR')

export const PRECO_MENSAL = emReais(PRECO_MENSAL_VALOR)
export const PRECO_ANTERIOR = emReais(PRECO_ANTERIOR_VALOR)
