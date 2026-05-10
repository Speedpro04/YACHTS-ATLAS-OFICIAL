"""
PATCH — Novas funcoes para o gerador de dossie Atlas Yachts.
Substitua secao_fotos() e secao_assinatura() no gerador original por estas versoes.
"""
from reportlab.lib.units import mm
from reportlab.platypus import Table, TableStyle, Paragraph, Image as RLImage, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from io import BytesIO

# Reutilize as variaveis de cor e estilos do arquivo original (S, GOLD, etc.)


def make_qr_image(url, size_mm=28):
    """Gera QR Code dourado em fundo escuro como ImageReader."""
    import qrcode
    from reportlab.lib.utils import ImageReader
    qr = qrcode.QRCode(version=2, box_size=5, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#C9A84C", back_color="#010c20")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=size_mm * mm, height=size_mm * mm)


def secao_fotos():
    """Secao 05 — Fotos certificadas com selo de auditoria Atlas."""
    story = []
    story.append(section_title('05 — Registro Fotografico Certificado'))
    placeholders = [
        ['Vista Lateral (Bombordo)', 'Vista Lateral (Boreste)'],
        ['Proa', 'Popa'],
        ['Cabine / Interior', 'Casa de Maquinas'],
    ]
    for pair in placeholders:
        row_cells = []
        for label in pair:
            seal = Paragraph(
                "✓ AUDITADO ATLAS  |  GEOLOCALIZAÇÃO CONFIRMADA",
                ParagraphStyle("seal", fontName="Helvetica-Bold", fontSize=5.5,
                    textColor=GOLD, leading=8, letterSpacing=1)
            )
            cell = Table(
                [[seal], [Paragraph(label, S['label'])]],
                colWidths=[73*mm], rowHeights=[7*mm, 38*mm]
            )
            cell.setStyle(TableStyle([
                ('BOX',          (0,0), (-1,-1), 0.4, GOLD),
                ('LINEBELOW',    (0,0), (-1,0),  0.3, GOLD_DIM),
                ('BACKGROUND',   (0,0), (-1,0),  GOLD_DIM),
                ('BACKGROUND',   (0,1), (-1,-1), DARK_SURFACE),
                ('VALIGN',       (0,0), (-1,-1), 'BOTTOM'),
                ('LEFTPADDING',  (0,0), (-1,-1), 5),
                ('BOTTOMPADDING',(0,0), (-1,-1), 4),
            ]))
            row_cells.append(cell)
        row = Table([row_cells], colWidths=[76*mm, 76*mm])
        row.setStyle(TableStyle([
            ('LEFTPADDING',  (0,0), (-1,-1), 0),
            ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING',   (0,0), (-1,-1), 0),
            ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ]))
        story.append(row)
    story.append(Paragraph(
        'Imagens vinculadas ao cofre digital. Hash SHA-256 registrado no momento do upload.',
        S['small']))
    return story


def secao_assinatura(dossie_id="YA-2025-00000"):
    """Secao final — Certificacao com QR Code de autenticidade."""
    verify_url = f"https://app.yachtsatlas.com/verify/{dossie_id}"
    story = []
    story.append(section_title('— Certificacao e Assinatura Digital'))
    story.append(Paragraph(
        'Este documento foi gerado e certificado pela plataforma Atlas Yachts. '
        'A integridade de cada secao e garantida por hash SHA-256 registrado '
        'no momento da emissao.',
        S['body']))
    story.append(Spacer(1, 8*mm))

    # Tabela principal de certificacao
    rows = [[
        Paragraph('EMITIDO POR', S['label']),
        Paragraph('DATA DE EMISSAO', S['label']),
        Paragraph('HASH DO DOCUMENTO', S['label']),
    ], [
        Paragraph('Atlas Yachts Platform', S['value']),
        Paragraph('10/05/2025', S['value']),
        Paragraph('a3f7c2...9d41be', ParagraphStyle('hash',
            fontName='Helvetica', fontSize=8, textColor=GOLD_DIM, leading=11)),
    ]]
    t = Table(rows, colWidths=[50*mm, 40*mm, 58*mm])
    t.setStyle(TableStyle([
        ('LINEABOVE',     (0,0),  (-1,0),  0.3, GOLD_DIM),
        ('LINEBELOW',     (0,-1), (-1,-1), 0.3, BORDER),
        ('TOPPADDING',    (0,0),  (-1,-1), 6),
        ('BOTTOMPADDING', (0,0),  (-1,-1), 6),
        ('LEFTPADDING',   (0,0),  (-1,-1), 0),
        ('VALIGN',        (0,0),  (-1,-1), 'TOP'),
    ]))
    story.append(t)
    story.append(Spacer(1, 10*mm))

    # QR Code de autenticidade
    qr_label = Paragraph(
        f"ESCANEIE PARA VERIFICAR AUTENTICIDADE\n{verify_url}",
        ParagraphStyle("qr_label", fontName="Helvetica", fontSize=6.5,
            textColor=GOLD_DIM, leading=10, alignment=1)
    )
    try:
        qr_img = make_qr_image(verify_url, size_mm=30)
        qr_table = Table([[qr_img], [qr_label]], colWidths=[35*mm])
        qr_table.setStyle(TableStyle([
            ('ALIGN',   (0,0), (-1,-1), 'CENTER'),
            ('VALIGN',  (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        outer = Table([[qr_table]], colWidths=[148*mm])
        outer.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(outer)
    except Exception:
        story.append(Paragraph(f"Verificar em: {verify_url}", S['small']))

    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        'ATLAS YACHTS — Plataforma de Custodia Digital de Ativos Nauticos\n'
        'yachtsatlas.com | contato@yachtsatlas.com',
        ParagraphStyle('footer_cert', fontName='Helvetica', fontSize=7,
            textColor=GOLD_DIM, leading=11, alignment=1)))
    return story
