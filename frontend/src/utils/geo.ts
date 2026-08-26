/**
 * Yachts Atlas — Onde o aparelho está, para foto tirada NA HORA.
 *
 * Serve só ao botão Fotografar, que abre a câmera: ali a posição do aparelho é
 * a posição da foto, porque ela está sendo tirada naquele lugar, naquele
 * instante.
 *
 * NÃO usar em envio de arquivo. Arquivo vem do disco — baixado, recebido por
 * e-mail, mandado pelo armador — e onde está quem clica em enviar não diz nada
 * sobre o barco. Nesse caso o servidor lê a coordenada de dentro da própria
 * imagem, que é a que descreve a foto. Gravar a do aparelho ali punha o
 * endereço de um funcionário num dossiê, afirmando ser o lugar do registro.
 *
 * Nunca bloqueia o envio: sem permissão, sem sinal ou passando do tempo,
 * resolve `null` e a foto sobe sem coordenada.
 */
export interface GeoPonto {
  lat: number
  lng: number
  acc?: number
}

export function obterGeo(timeoutMs = 8000): Promise<GeoPonto | null> {
  return new Promise((resolve) => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      resolve(null)
      return
    }
    let resolvido = false
    const done = (v: GeoPonto | null) => { if (!resolvido) { resolvido = true; resolve(v) } }
    try {
      navigator.geolocation.getCurrentPosition(
        (pos) => done({ lat: pos.coords.latitude, lng: pos.coords.longitude, acc: pos.coords.accuracy }),
        () => done(null),
        { enableHighAccuracy: true, timeout: timeoutMs, maximumAge: 60000 },
      )
    } catch {
      done(null)
    }
  })
}
