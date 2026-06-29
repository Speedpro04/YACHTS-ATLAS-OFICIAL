/**
 * Yachts Atlas — Captura de geolocalização do dispositivo no momento do upload.
 * Pede permissão ao navegador; em caso de negação, indisponibilidade ou timeout,
 * resolve `null` (o upload segue normalmente, apenas sem coordenada).
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
