# -*- coding: utf-8 -*-
"""
Yachts Atlas — miniaturas para as telas de revisão.

O PROBLEMA. A foto do píer sobe como saiu da câmera: 2 a 5 MB. É decisão
escrita (PRD 3.3, resolvida em 11/09/2026) e ela está certa — o SHA-256 é
calculado sobre os bytes que chegam, então não mexer no arquivo faz a prova ser
o que a câmera produziu.

Só que as telas de revisão pediam esse mesmo arquivo para desenhar um
quadradinho de 80 pixels. Três fotos de um serviço = 10 MB baixados para
conferir três miniaturas, toda vez que alguém abre a aba. Foi o que deixou o
painel lento em 15/09/2026.

A MINIATURA NÃO É A PROVA, e isso precisa ficar claro para quem mexer aqui
depois:

  • o original continua intacto no storage, com WORM e o hash que já tinha;
  • a miniatura é derivada, tem caminho próprio e NUNCA é hasheada;
  • ela não entra no dossiê nem em nada que precise valer como evidência —
    serve para a pessoa reconhecer a foto antes de aprovar;
  • se ela falhar, sumir ou nem existir, a tela cai no original. Pior caso é
    a lentidão de hoje, nunca uma foto que não aparece.

Por convenção de caminho, e não por coluna nova: `<caminho>.mini.jpg`. Assim
não há migração, e foto antiga — que não tem miniatura — simplesmente não
encontra o arquivo e usa o original.
"""
import io
import logging

logger = logging.getLogger(__name__)

# 480px atende a maior miniatura que as telas usam hoje (a da mesa de trabalho,
# que abre em ~160px) com folga para telas retina. Qualidade 72 porque isto é
# reconhecimento visual, não leitura de número de série — para ler o número, a
# pessoa abre o original.
LADO_MAXIMO = 480
QUALIDADE = 72

# Só imagem. PDF, vídeo e o resto seguem como estão — miniatura de PDF exigiria
# rasterizador, que é outra dependência e outro problema.
MIMES_COM_MINIATURA = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/heic"}


def caminho_da_miniatura(storage_path: str) -> str:
    """O caminho derivado. Convenção, para não precisar de coluna nem migração."""
    return f"{storage_path}.mini.jpg"


def tem_miniatura(mime: str | None) -> bool:
    return (mime or "").lower() in MIMES_COM_MINIATURA


def gerar(bytes_originais: bytes, mime: str | None = None) -> bytes | None:
    """Devolve o JPEG da miniatura, ou None se não der para gerar.

    None nunca é erro de verdade: quem chama segue com o original. Um arquivo
    que o Pillow não abre (HEIC sem plugin, imagem corrompida) não pode
    impedir o upload — a foto é o trabalho de alguém no píer.
    """
    if not tem_miniatura(mime):
        return None
    try:
        from PIL import Image, ImageOps

        img = Image.open(io.BytesIO(bytes_originais))
        # A orientação vive no EXIF; sem isto a miniatura sai deitada e a
        # pessoa não reconhece a própria foto.
        img = ImageOps.exif_transpose(img)
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.LANCZOS)

        saida = io.BytesIO()
        # optimize + progressive: a miniatura aparece antes de terminar de
        # chegar, que é o que a pessoa percebe como "rápido".
        img.save(saida, format="JPEG", quality=QUALIDADE, optimize=True, progressive=True)
        return saida.getvalue()
    except Exception as e:  # pragma: no cover - degradação proposital
        logger.info(f"Sem miniatura para este arquivo ({mime}): {e}")
        return None
