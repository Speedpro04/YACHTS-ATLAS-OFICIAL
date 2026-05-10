"""
ATLAS YACHTS — Motor de Geração de Dossiês (Core)
Cores, estilos, canvas e flowables auxiliares.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Image as RLImage
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Flowable
from io import BytesIO

# ─── CORES ───────────────────────────────────────────────
NEAR_BLACK   = colors.HexColor('#010c20')
GOLD         = colors.HexColor('#C9A84C')
GOLD_LIGHT   = colors.HexColor('#E8D5A3')
GOLD_DIM     = colors.HexColor('#6B5A2A')
WHITE        = colors.HexColor('#F0EDE6')
WHITE_DIM    = colors.HexColor('#9A9690')
RUBY         = colors.HexColor('#9B1B30')
EMERALD      = colors.HexColor('#046A38')
DARK_SURFACE = colors.HexColor('#0D0D18')
BORDER       = colors.HexColor('#2A2410')

W, H = A4

# ─── ESTILOS ─────────────────────────────────────────────
def make_styles():
    return {
        'eyebrow': ParagraphStyle('eyebrow',
            fontName='Helvetica', fontSize=7, textColor=GOLD,
            spaceAfter=4, spaceBefore=0, leading=10, letterSpacing=3),
        'title_xl': ParagraphStyle('title_xl',
            fontName='Helvetica-Bold', fontSize=26, textColor=WHITE,
            spaceAfter=6, leading=30),
        'title_lg': ParagraphStyle('title_lg',
            fontName='Helvetica-Bold', fontSize=18, textColor=WHITE,
            spaceAfter=4, leading=22),
        'title_md': ParagraphStyle('title_md',
            fontName='Helvetica-Bold', fontSize=13, textColor=WHITE,
            spaceAfter=3, leading=17),
        'title_gold': ParagraphStyle('title_gold',
            fontName='Helvetica-Bold', fontSize=13, textColor=GOLD,
            spaceAfter=3, leading=17),
        'body': ParagraphStyle('body',
            fontName='Helvetica', fontSize=9, textColor=WHITE_DIM,
            spaceAfter=4, leading=14),
        'body_white': ParagraphStyle('body_white',
            fontName='Helvetica', fontSize=9, textColor=WHITE,
            spaceAfter=4, leading=14),
        'label': ParagraphStyle('label',
            fontName='Helvetica', fontSize=7, textColor=GOLD_DIM,
            spaceAfter=2, leading=10, letterSpacing=2),
        'value': ParagraphStyle('value',
            fontName='Helvetica-Bold', fontSize=10, textColor=WHITE,
            spaceAfter=6, leading=13),
        'section_header': ParagraphStyle('section_header',
            fontName='Helvetica-Bold', fontSize=8, textColor=GOLD,
            spaceAfter=6, leading=11, letterSpacing=2),
        'center': ParagraphStyle('center',
            fontName='Helvetica', fontSize=9, textColor=WHITE_DIM,
            alignment=TA_CENTER, leading=14),
        'right': ParagraphStyle('right',
            fontName='Helvetica', fontSize=9, textColor=WHITE_DIM,
            alignment=TA_RIGHT, leading=14),
        'gold_lg': ParagraphStyle('gold_lg',
            fontName='Helvetica-Bold', fontSize=20, textColor=GOLD,
            spaceAfter=2, leading=24),
        'small': ParagraphStyle('small',
            fontName='Helvetica', fontSize=7.5, textColor=WHITE_DIM,
            spaceAfter=3, leading=11),
        'status_ok': ParagraphStyle('status_ok',
            fontName='Helvetica-Bold', fontSize=8, textColor=EMERALD, leading=11),
        'status_alert': ParagraphStyle('status_alert',
            fontName='Helvetica-Bold', fontSize=8, textColor=RUBY, leading=11),
    }

S = make_styles()

# ─── BACKGROUND CANVAS ───────────────────────────────────
def dark_canvas(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NEAR_BLACK)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(14*mm, 14*mm, 0.5, H - 28*mm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#4A3F1E'))
    canvas.setFont('Helvetica', 6)
    canvas.drawString(20*mm, 10*mm, 'ATLAS YACHTS — DOCUMENTO CONFIDENCIAL')
    canvas.drawRightString(W - 14*mm, 10*mm, f'Página {doc.page}')
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.3)
    canvas.line(14*mm, 13*mm, W - 14*mm, 13*mm)
    canvas.restoreState()

def cover_canvas(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NEAR_BLACK)
    canvas.rect(0, 0, W, H, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 0, 6*mm, H, fill=1, stroke=0)
    canvas.setFillColor(DARK_SURFACE)
    canvas.rect(0, 0, W, 30*mm, fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, 30*mm, W, 0.3, fill=1, stroke=0)
    canvas.setFont('Helvetica', 6)
    canvas.setFillColor(colors.HexColor('#4A3F1E'))
    canvas.drawString(20*mm, 10*mm, 'ATLAS YACHTS — CUSTÓDIA DIGITAL DE ATIVOS NÁUTICOS')
    canvas.drawRightString(W - 14*mm, 10*mm, 'yachtsatlas.com')
    canvas.restoreState()

# ─── HELPER FLOWABLES ────────────────────────────────────
class GoldLine(Flowable):
    def __init__(self, width=None, opacity=1.0):
        super().__init__()
        self.line_width = width
        self.opacity = opacity
        self.height = 1
    def draw(self):
        w = self.line_width or self.canv._pagesize[0] - 28*mm
        self.canv.saveState()
        self.canv.setStrokeColor(GOLD if self.opacity == 1.0 else BORDER)
        self.canv.setLineWidth(0.4)
        self.canv.line(0, 0, w, 0)
        self.canv.restoreState()

def spacer(h=4):
    return Spacer(1, h*mm)

def section_title(text):
    return KeepTogether([spacer(5), Paragraph(text.upper(), S['section_header']), GoldLine(opacity=0.3), spacer(3)])

def field_row(label, value, style='value'):
    return KeepTogether([Paragraph(label.upper(), S['label']), Paragraph(value, S[style]), spacer(2)])

def info_table(data, col_widths=None):
    cw = col_widths or [70*mm, 70*mm]
    rows = []
    for i in range(0, len(data), 2):
        pair = data[i:i+2]
        row = []
        for label, value in pair:
            row.append([Paragraph(label.upper(), S['label']), Paragraph(value, S['value'])])
        if len(row) == 1:
            row.append('')
        rows.append(row)
    t = Table(rows, colWidths=cw)
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    return t

def checklist_table(items, checked=None):
    rows = []
    for i, item in enumerate(items):
        ok = checked[i] if checked else True
        mark = '✓' if ok else '○'
        color = EMERALD if ok else WHITE_DIM
        rows.append([
            Paragraph(mark, ParagraphStyle('m', fontName='Helvetica-Bold', fontSize=9, textColor=color, leading=13)),
            Paragraph(item, S['body_white']),
        ])
    t = Table(rows, colWidths=[8*mm, 130*mm])
    t.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    return t

def make_qr_image(url, size_mm=28):
    """Gera QR Code dourado em fundo escuro."""
    import qrcode
    qr = qrcode.QRCode(version=2, box_size=5, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#C9A84C", back_color="#010c20")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=size_mm*mm, height=size_mm*mm)
