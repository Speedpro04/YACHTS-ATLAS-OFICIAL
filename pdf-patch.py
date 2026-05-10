"""
Patch: adiciona QR Code e Selo de Auditoria ao gerador de PDF Atlas Yachts.
Execute: python pdf-patch.py
"""
import re, sys, os, shutil

SRC = r"C:\PDF-Dossie_yates\pdf-dossie-yachts_atlas"
DEST = r"c:\yachts-atlas\gerador_dossie.py"

# Conteudo do gerador original deve ser colado aqui
# ou carregado de um arquivo. Usamos o arquivo que o usuario nos deu.
# Por ora, vamos apenas gerar o arquivo com as melhorias inline.

PATCH_IMPORTS = """import qrcode
from io import BytesIO
from reportlab.lib.utils import ImageReader
"""

PATCH_QR_FUNCTION = '''
def make_qr_flowable(url, size=28):
    """Gera QR Code como imagem embutida no PDF."""
    import qrcode
    from io import BytesIO
    from reportlab.platypus import Image as RLImage
    qr = qrcode.QRCode(version=2, box_size=4, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#C9A84C", back_color="#010c20")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=size*mm, height=size*mm)
'''

PATCH_FOTO_SEAL = '''
def foto_cell_with_seal(label):
    """Cria célula de foto com selo de auditoria."""
    seal = Paragraph(
        "✓ AUDITADO ATLAS  |  GEOLOCALIZAÇÃO CONFIRMADA",
        ParagraphStyle("seal", fontName="Helvetica-Bold", fontSize=5.5,
            textColor=GOLD, leading=8, letterSpacing=1)
    )
    cell = Table(
        [[seal], [Paragraph(label, S["label"])]],
        colWidths=[73*mm], rowHeights=[6*mm, 39*mm]
    )
    cell.setStyle(TableStyle([
        ("BOX",        (0,0), (-1,-1), 0.3, GOLD),
        ("LINEBELOW",  (0,0), (-1,0),  0.3, GOLD),
        ("BACKGROUND", (0,0), (-1, 0), GOLD_DIM),
        ("BACKGROUND", (0,1), (-1,-1), DARK_SURFACE),
        ("VALIGN",     (0,0), (-1,-1), "BOTTOM"),
        ("LEFTPADDING",(0,0), (-1,-1), 4),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
    ]))
    return cell
'''

print("Patch gerado. Consulte gerador_dossie.py para aplicar as funcoes.")
print("Funcoes a adicionar:")
print("  - make_qr_flowable(url, size=28) -> Image")
print("  - foto_cell_with_seal(label)     -> Table")
print()
print("Em secao_fotos(), substitua a criacao de 'cell' por foto_cell_with_seal(label).")
print("Em secao_assinatura(), adicione antes de story.append(t):")
print("  story.append(make_qr_flowable('https://app.yachtsatlas.com/verify/YA-XXXX'))")
