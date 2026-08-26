"""
Onde a foto foi tirada — e onde ela NÃO foi.

Estes testes existem por causa de um defeito real, achado em 26/08/2026 no
dossiê do Dom Rafael: 14 fotos baixadas da internet foram seladas com a
coordenada -22.9206, -45.4517 — o escritório de quem as enviou — e o PDF
marcava GEO ao lado delas, afirmando ser o lugar do registro.

Como `documentos` é append-only, nada disso podia ser corrigido depois. Por isso
a regra aqui é conservadora: na dúvida, sem coordenada.
"""
import io

from PIL import Image

from app.services.exif_service import coordenada_da_imagem, geo_para_selar


def _foto(gps: dict | None = None) -> bytes:
    """JPEG mínimo, com ou sem o bloco GPS que a câmera grava."""
    imagem = Image.new("RGB", (8, 8), "navy")
    buffer = io.BytesIO()
    if gps is None:
        imagem.save(buffer, "JPEG")
    else:
        exif = Image.Exif()
        exif[0x8825] = gps
        imagem.save(buffer, "JPEG", exif=exif)
    return buffer.getvalue()


# Ilhabela/SP — 23°46'44"S, 45°21'29"W. Sul e Oeste, como toda marina brasileira.
GPS_ILHABELA = {1: "S", 2: (23.0, 46.0, 44.0), 3: "W", 4: (45.0, 21.0, 29.0)}


# ---------------------------------------------------------------- ler a imagem

def test_coordenada_sai_de_dentro_da_foto():
    lat, lng = coordenada_da_imagem(_foto(GPS_ILHABELA))
    assert round(lat, 3) == -23.779
    assert round(lng, 3) == -45.358


def test_hemisferio_sul_e_oeste_sao_negativos():
    """Sem isto, uma marina de Santa Catarina apareceria no Canadá."""
    lat, lng = coordenada_da_imagem(_foto(GPS_ILHABELA))
    assert lat < 0 and lng < 0


def test_foto_baixada_da_internet_nao_tem_coordenada():
    """O caso do Dom Rafael: imagem do Google não carrega onde foi tirada."""
    assert coordenada_da_imagem(_foto()) is None


def test_zero_zero_e_lixo_de_camera_sem_sinal():
    """(0,0) fica no meio do Atlântico. Nenhuma marina está lá."""
    assert coordenada_da_imagem(_foto({1: "N", 2: (0.0, 0.0, 0.0), 3: "E", 4: (0.0, 0.0, 0.0)})) is None


def test_arquivo_que_nao_e_imagem_nao_derruba_o_upload():
    """PDF, arquivo corrompido, vazio — tudo vira None, nada levanta exceção."""
    for lixo in (b"%PDF-1.4 sou um pdf", b"", b"\x00\x01\x02", b"nao sou nada"):
        assert coordenada_da_imagem(lixo) is None


# --------------------------------------------------------- o que vai para o selo

def test_o_que_esta_dentro_da_foto_ganha_do_aparelho():
    selo = geo_para_selar(_foto(GPS_ILHABELA), latitude=-22.9206, longitude=-45.4517,
                          geo_precisao=30.0, geo_fonte="captura")
    assert selo["geo_fonte"] == "exif"
    assert round(selo["latitude"], 3) == -23.779


def test_camera_ao_vivo_pode_usar_a_posicao_do_aparelho():
    """Foto tirada agora: onde o aparelho está É onde ela foi tirada."""
    selo = geo_para_selar(_foto(), latitude=-23.7789, longitude=-45.3581,
                          geo_precisao=12.0, geo_fonte="captura")
    assert selo["geo_fonte"] == "captura"
    assert selo["geo_precisao"] == 12.0


def test_dispositivo_das_versoes_antigas_e_descartado():
    """
    O defeito em si. Frontend antigo mandava "dispositivo" em envio de arquivo,
    e a posição do escritório era selada como lugar da foto.
    """
    assert geo_para_selar(_foto(), latitude=-22.9206, longitude=-45.4517,
                          geo_fonte="dispositivo") == {}


def test_envio_de_arquivo_nao_grava_coordenada_nenhuma():
    """Sem EXIF e sem fonte declarada: nada. Vazio é melhor que errado."""
    assert geo_para_selar(_foto()) == {}


def test_coordenada_impossivel_do_cliente_e_descartada():
    """Latitude 999 não existe; o valor chega de fora e ninguém validava."""
    assert geo_para_selar(_foto(), latitude=999.0, longitude=-45.0, geo_fonte="captura") == {}
    assert geo_para_selar(_foto(), latitude=None, longitude=-45.0, geo_fonte="captura") == {}


def test_fonte_inventada_nao_passa():
    """Lista fechada — não basta mandar um texto qualquer."""
    for fonte in ("exif", "gps", "", None, "CAPTURA"):
        assert geo_para_selar(_foto(), latitude=-23.7, longitude=-45.3, geo_fonte=fonte) == {}
