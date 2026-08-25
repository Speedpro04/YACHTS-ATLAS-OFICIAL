/**
 * Telefone brasileiro — uma regra, um lugar.
 *
 * O estado guarda só DÍGITOS de DDD + número (10 ou 11). O "+55" é rótulo na
 * tela, não conteúdo do campo, e é isso que mata a ambiguidade na origem:
 * `55978138934` é indistinguível de um celular legítimo do DDD 55 (Santa
 * Maria/RS), e nenhum algoritmo resolve o empate. Tirando o DDI do campo, a
 * pergunta deixa de existir.
 *
 * Vive aqui, e não dentro de cada página, porque esta regra JÁ se dividiu:
 * em 24/08/2026 ela entrou na MarinaParceira e na LP de Lançamento e não
 * entrou no RegistroMarina — que é justamente a página do cadastro PAGO. Em
 * 25/08 uma marina pagou US$ 250 com o telefone gravado vazio, e o telefone
 * é por onde ela seria atendida.
 */

/** Deixa só DDD + número, no máximo 11 dígitos. */
export function soDDDeNumero(bruto: string): string {
  let d = bruto.replace(/\D/g, '')
  // Colou o número inteiro, com DDI? O "+55" já está fixo ao lado; manter o 55
  // digitado produziria "+55 55 978138934" — DDD 55, que ninguém quis digitar.
  if (d.length > 11 && d.startsWith('55')) d = d.slice(2)
  return d.slice(0, 11)
}

/** `12991187251` -> `(12) 99118-7251`. Formata parcial enquanto digita. */
export function mascaraTelefone(d: string): string {
  if (d.length <= 2) return d
  if (d.length <= 6) return `(${d.slice(0, 2)}) ${d.slice(2)}`
  if (d.length <= 10) return `(${d.slice(0, 2)}) ${d.slice(2, 6)}-${d.slice(6)}`
  return `(${d.slice(0, 2)}) ${d.slice(2, 7)}-${d.slice(7)}`
}

/**
 * DDD + celular = 11 dígitos. Fixo (10) é recusado de propósito.
 *
 * Este número é por onde a marina é atendida, recebe o código de acesso do
 * armador e é abordada na prospecção — tudo por WhatsApp, que fixo não recebe.
 * Aceitar 10 grava um contato que nunca vai funcionar, e o silêncio é total:
 * a Evolution aceita a chamada e não entrega nada.
 *
 * Foi por isso que o limite subiu de 10 para 11 em 25/08/2026: `1299187251`
 * — um celular com um dígito a menos — passava como se fosse fixo válido.
 */
export const TELEFONE_DIGITOS_MINIMO = 11

export function telefoneCompleto(d: string): boolean {
  return d.length >= TELEFONE_DIGITOS_MINIMO
}

export const MSG_TELEFONE_INCOMPLETO =
  'WhatsApp incompleto. Informe DDD + celular com 9 dígitos, ex.: (12) 97813-8934.'

/** O que sai para o backend: 55 + DDD + número, a única forma sem inferência. */
export function comDDI(d: string): string {
  return `55${d}`
}

/**
 * E-mail conferido na tela, com mensagem própria. Quem recusa de verdade é o
 * backend, mas ele responde 422 genérico e a marina não descobre qual campo
 * está errado — aconteceu com "marinasolares@gmailcom", sem o ponto.
 */
export function emailValido(email: string): boolean {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email.trim())
}

export const MSG_EMAIL_INVALIDO =
  'E-mail inválido. Confira se não falta um ponto ou uma letra.'
