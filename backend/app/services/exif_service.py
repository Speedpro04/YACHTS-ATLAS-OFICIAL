"""
Yachts Atlas — De onde veio a foto, lido de dentro dela.

Toda foto de celular guarda, dentro do próprio arquivo, a coordenada de onde
foi tirada (o padrão EXIF). É esse dado que vale num dossiê de custódia: ele
descreve a FOTO, não quem a enviou.

Antes daqui, o sistema gravava a posição do NAVEGADOR no instante do envio.
Para foto tirada no píer os dois valores coincidem, e ninguém nota. Para foto
vinda do disco — baixada, recebida por e-mail, mandada pelo armador — o que
ficava selado era o endereço de quem clicou em enviar. Duas consequências, as
duas ruins: o dossiê marcava GEO afirmando um lugar que não era o da foto, e o
endereço de um funcionário da marina ficava guardado para sempre numa tabela
que não aceita UPDATE nem DELETE.

Aqui só sai coordenada que estava dentro da imagem.
"""
from __future__ import annotations

import io

# Tags do bloco GPS no EXIF (padrão, valem para JPEG, WEBP, TIFF, PNG).
_GPS_IFD = 0x8825
_LAT_REF, _LAT, _LNG_REF, _LNG = 1, 2, 3, 4


def _para_decimal(valor, referencia) -> float | None:
    """
    EXIF grava (graus, minutos, segundos) + hemisfério. O banco quer decimal.

    Sul e Oeste são negativos — sem isso, uma marina em Santa Catarina apareceria
    no hemisfério norte.
    """
    try:
        graus, minutos, segundos = (float(x) for x in valor)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    decimal = graus + minutos / 60 + segundos / 3600
    if str(referencia).strip().upper() in ("S", "W"):
        decimal = -decimal
    return decimal


def coordenada_da_imagem(conteudo: bytes) -> tuple[float, float] | None:
    """
    Devolve (latitude, longitude) se a imagem trouxer isso dentro; senão None.

    Nunca levanta exceção e nunca bloqueia um upload: arquivo corrompido, formato
    que o Pillow não conhece, PDF, EXIF truncado — tudo cai em None e a foto sobe
    sem coordenada. Registro sem geo é bom; registro que não sobe é inútil.

    Só lê o cabeçalho: `Image.open` é preguiçoso e não decodifica os pixels, então
    o custo não depende do tamanho da imagem.
    """
    if not conteudo:
        return None
    try:
        from PIL import Image

        with Image.open(io.BytesIO(conteudo)) as img:
            exif = img.getexif()
            if not exif:
                return None
            gps = exif.get_ifd(_GPS_IFD)
            if not gps:
                return None

        lat = _para_decimal(gps.get(_LAT), gps.get(_LAT_REF))
        lng = _para_decimal(gps.get(_LNG), gps.get(_LNG_REF))
    except Exception:
        return None

    if lat is None or lng is None:
        return None
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return None
    # (0, 0) é o lixo clássico de câmera sem sinal — fica no meio do Atlântico,
    # a 600 km da costa da África. Nenhuma marina está lá.
    if lat == 0 and lng == 0:
        return None
    return lat, lng


# Fonte que o cliente pode declarar. Lista fechada de propósito: o valor chega
# de fora, e o "dispositivo" das versões antigas significava outra coisa —
# a posição de quem enviava. Aceitá-lo agora seria continuar o mesmo erro.
FONTES_ACEITAS_DO_CLIENTE = frozenset({"captura"})


def _no_mapa(lat, lng) -> bool:
    """Coordenada que existe de verdade — cliente pode mandar qualquer número."""
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return False
    return -90 <= lat <= 90 and -180 <= lng <= 180 and not (lat == 0 and lng == 0)


def geo_para_selar(
    conteudo: bytes,
    latitude: float | None = None,
    longitude: float | None = None,
    geo_precisao: float | None = None,
    geo_fonte: str | None = None,
) -> dict:
    """
    As colunas de geolocalização que vão para o selo — ou nada.

    Ordem: o que está dentro da imagem ganha sempre, porque descreve a foto. A
    posição do aparelho só entra quando a foto acabou de ser tirada pela câmera,
    e aí as duas são a mesma coisa.

    Devolve dicionário vazio quando não há coordenada confiável. Vazio é o certo:
    documento é append-only, então coordenada errada gravada aqui fica no dossiê
    para sempre, sem UPDATE que a conserte.
    """
    coordenada = coordenada_da_imagem(conteudo)
    if coordenada:
        return {
            "latitude": coordenada[0],
            "longitude": coordenada[1],
            "geo_precisao": None,
            "geo_fonte": "exif",
        }
    if (
        latitude is not None
        and longitude is not None
        and geo_fonte in FONTES_ACEITAS_DO_CLIENTE
        and _no_mapa(latitude, longitude)
    ):
        return {
            "latitude": latitude,
            "longitude": longitude,
            "geo_precisao": geo_precisao,
            "geo_fonte": geo_fonte,
        }
    return {}
