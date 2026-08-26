/**
 * Que arquivo o cofre aceita — uma lista, um lugar.
 *
 * Havia OITO listas espalhadas pelas telas, e elas discordavam entre si: a
 * Documentação recusava WEBP, a ficha de serviço recusava, a galeria recusava,
 * o cadastro de categoria aceitava qualquer imagem. A marina salvava uma foto,
 * conseguia subir numa tela e era barrada na outra, sem entender por quê.
 *
 * WEBP entra porque é foto como qualquer outra: mostra o documento igual a um
 * JPG, e é o formato que celular e site mais produzem hoje. Recusar não protege
 * nada — só faz a marina converter arquivo à mão.
 *
 * Vai tipo E extensão na mesma lista: seletor de arquivo do Windows e de Android
 * antigo às vezes ignora o tipo e só olha o final do nome.
 *
 * Nota importante: isto é conforto, não segurança. O servidor **não** valida
 * tipo nenhum — grava o que chegar. A lista do navegador só evita que a pessoa
 * escolha um arquivo que não serve.
 */

/** Imagens aceitas em qualquer lugar do sistema. */
export const IMAGENS = [
  'image/jpeg', 'image/png', 'image/webp',
  '.jpg', '.jpeg', '.png', '.webp',
] as const

/** Galeria e vitrine: só imagem — PDF ali não tem o que mostrar. */
export const ACEITA_IMAGEM = IMAGENS.join(',')

/** Documento do cofre: imagem OU PDF. */
export const ACEITA_DOCUMENTO = [...IMAGENS, 'application/pdf', '.pdf'].join(',')

/** O que o texto da tela promete. Deriva da lista, para nunca divergir dela. */
export const ROTULO_IMAGEM = 'PNG, JPG, WEBP'
export const ROTULO_DOCUMENTO = 'PDF, PNG, JPG, WEBP'

/** Teto de tamanho, em MB — o mesmo texto que aparece ao lado do botão. */
export const TAMANHO_MAXIMO_MB = 10
