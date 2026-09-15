# -*- coding: utf-8 -*-
"""
A miniatura é conveniência, nunca prova.

O original da câmera continua sendo o que sobe, o que é hasheado e o que vai ao
dossiê — decisão 3.3 do PRD do Atlas Pré-Data, resolvida em 11/09/2026. O que
esta função resolve é outra coisa: a tela de revisão baixava os 3 MB da câmera
para desenhar um quadradinho de 80px, três vezes por serviço.

O que estes testes protegem, se alguém mexer aqui depois:

  • a miniatura sai MENOR que o original — é a única razão de ela existir;
  • arquivo que não é imagem não vira miniatura, e isso não é erro;
  • falha na geração devolve None em vez de estourar: a foto é o trabalho de
    alguém no píer, e não pode ser perdida por causa de um thumbnail.
"""
import io

import pytest

from app.services import miniatura

pytest.importorskip("PIL", reason="Pillow não instalado neste ambiente")


def _imagem(largura=2400, altura=1800, formato="JPEG") -> bytes:
    from PIL import Image

    img = Image.new("RGB", (largura, altura), (30, 60, 120))
    # Ruído leve para o JPEG não comprimir a imagem inteira em 2 KB e o teste
    # de tamanho virar tautologia.
    for x in range(0, largura, 7):
        for y in range(0, altura, 11):
            img.putpixel((x, y), ((x * 3) % 255, (y * 5) % 255, (x + y) % 255))
    saida = io.BytesIO()
    img.save(saida, format=formato)
    return saida.getvalue()


def test_a_miniatura_e_muito_menor_que_o_original():
    original = _imagem()
    mini = miniatura.gerar(original, "image/jpeg")

    assert mini is not None
    assert len(mini) < len(original) / 5, (
        f"miniatura de {len(mini)} bytes para original de {len(original)} — "
        "não compensa a ida ao storage"
    )


def test_cabe_no_lado_maximo():
    from PIL import Image

    mini = miniatura.gerar(_imagem(3000, 1000), "image/jpeg")
    img = Image.open(io.BytesIO(mini))
    assert max(img.size) <= miniatura.LADO_MAXIMO
    # Proporção preservada: miniatura esticada faz a pessoa não reconhecer a
    # própria foto, que é justamente o que ela precisa fazer para aprovar.
    assert abs((img.size[0] / img.size[1]) - 3.0) < 0.05


def test_png_tambem_vira_miniatura_jpeg():
    from PIL import Image

    mini = miniatura.gerar(_imagem(formato="PNG"), "image/png")
    assert mini is not None
    assert Image.open(io.BytesIO(mini)).format == "JPEG"


def test_o_que_nao_e_imagem_nao_tem_miniatura():
    """PDF e vídeo seguem como estão. Não é falha — é ausência de pergunta."""
    assert miniatura.gerar(b"%PDF-1.7 ...", "application/pdf") is None
    assert miniatura.gerar(b"\x00\x00", "video/mp4") is None
    assert miniatura.gerar(b"qualquer", None) is None


def test_arquivo_corrompido_nao_estoura():
    """A foto é o trabalho de alguém no píer. Um thumbnail que não sai não
    pode derrubar o upload que já deu certo."""
    assert miniatura.gerar(b"isto nao e um jpeg", "image/jpeg") is None


def test_o_caminho_e_derivado_do_original():
    """Convenção em vez de coluna nova: foto antiga simplesmente não encontra
    o arquivo e a tela cai no original."""
    caminho = "ativos/YA-IATE-2021-5A4E/docs/abc_foto.jpg"
    assert miniatura.caminho_da_miniatura(caminho) == caminho + ".mini.jpg"
    assert miniatura.caminho_da_miniatura(caminho).startswith(caminho)


def test_o_upload_nao_hasheia_a_miniatura():
    """Se a miniatura entrar no cálculo do hash, ela vira prova — e o PRD 3.3
    diz que a prova é o byte que saiu da câmera."""
    import inspect
    from app.api.v1 import documentos

    fonte = inspect.getsource(documentos.upload_documento)
    hash_em = fonte.index("calculate_hash")
    mini_em = fonte.index("caminho_da_miniatura")
    assert hash_em < mini_em, "a miniatura passou para antes do hash do original"
