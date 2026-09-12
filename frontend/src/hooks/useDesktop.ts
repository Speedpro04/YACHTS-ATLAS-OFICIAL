import { useEffect, useState } from 'react'

/**
 * Se esta tela pode EMITIR dossiê.
 *
 * Decisão do fundador (12/09/2026): o Dossiê Atlas é gerado somente no
 * computador. Ver e consultar continua em qualquer tela — a trava é sobre
 * emitir.
 *
 * Três condições juntas, porque cada uma sozinha erra:
 *  - largura mínima: a conferência do dossiê pede tela, não uma coluna;
 *  - ponteiro fino: mouse ou trackpad, o que separa computador de aparelho de
 *    toque melhor do que qualquer medida de largura;
 *  - nome do aparelho: tablet grande em paisagem passa nas duas primeiras, e
 *    tablet não emite. É o mesmo teste que o servidor aplica, para a tela não
 *    liberar um botão que a API vai recusar.
 */
const LARGURA_MINIMA = 1024
const APARELHO_DE_MAO = /android|iphone|ipod|ipad|mobile|windows\s*phone|tablet|silk|kindle|playbook/i

export function podeEmitirDossie(): boolean {
  if (typeof window === 'undefined') return false
  if (APARELHO_DE_MAO.test(navigator.userAgent)) return false
  return window.matchMedia(`(min-width: ${LARGURA_MINIMA}px) and (pointer: fine)`).matches
}

/** Versão reativa: acompanha quem redimensiona a janela com o painel aberto. */
export function useDesktop(): boolean {
  const [desktop, setDesktop] = useState(podeEmitirDossie)

  useEffect(() => {
    const mq = window.matchMedia(`(min-width: ${LARGURA_MINIMA}px) and (pointer: fine)`)
    const recalcular = () => setDesktop(podeEmitirDossie())
    mq.addEventListener('change', recalcular)
    return () => mq.removeEventListener('change', recalcular)
  }, [])

  return desktop
}

/** A frase que a pessoa lê. A mesma que o servidor devolve, palavra por palavra. */
export const AVISO_SO_DESKTOP =
  'Geração não autorizada em dispositivo mobile ou tablet. O Dossiê Atlas é emitido no computador — abra o painel em tela cheia para gerar.'
