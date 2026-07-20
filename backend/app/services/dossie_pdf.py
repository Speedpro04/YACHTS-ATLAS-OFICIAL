"""
Yachts Atlas — Gerador de PDF do Dossiê (a partir de dados REAIS do banco).

Regras que este módulo respeita:
  * "Nenhuma seção vazia": seção sem dado não é renderizada.
  * NUNCA inventa número. Se o dado não existe, o elemento some — jamais
    aparece um placeholder que o leitor possa confundir com fato.
  * Tokens de cor e nomenclatura espelhados do painel técnico
    (frontend/src/components/AssetHealthDashboard.tsx), para a marina ver
    a mesma história na tela e no PDF.

Consome o pacote de montar_dados_dossie() (dossie_data.py).
"""
import os
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable, Image as RLImage, NextPageTemplate,
)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.pdfbase.pdfmetrics import stringWidth

# Data de emissão no fuso do Brasil. Com utcnow() o dossiê gerado das 21h à
# meia-noite (BRT) saía com a data do dia seguinte.
TZ_BR = ZoneInfo("America/Sao_Paulo")

W, H = A4
_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
# Emblema sem o lettering da arte original (que diz "ATLAS YACHTS"): a marca
# correta é "Yachts Atlas", então o nome vai em tipografia, não na imagem.
LOGO = os.path.join(_ASSETS, "emblema-atlas.png")
LOGO_AR = 310.0 / 270.0

# ── Tokens (espelham o painel técnico) ───────────────────────
NAVY        = colors.HexColor("#010c20")
SURFACE     = colors.HexColor("#021a3d")   # bg-[#021a3d] do painel
SURFACE_2   = colors.HexColor("#04122b")
GOLD        = colors.HexColor("#c5a059")
GOLD_LIGHT  = colors.HexColor("#ffcf8a")
GOLD_DIM    = colors.HexColor("#8a7038")
WHITE       = colors.HexColor("#f0ede6")
WHITE_DIM   = colors.HexColor("#9aa0aa")
WHITE_FAINT = colors.HexColor("#5b6472")
BORDER      = colors.HexColor("#1a2740")

# Status — valores Tailwind exatos do AssetHealthDashboard
EMERALD = colors.HexColor("#10b981")
AMBER   = colors.HexColor("#f59e0b")
ROSE    = colors.HexColor("#f43f5e")
BLUE    = colors.HexColor("#3b82f6")
ZINC    = colors.HexColor("#71717a")

SERIF  = "Times-Bold"       # espelha font-serif do painel nos números grandes
SANS   = "Helvetica"
SANS_B = "Helvetica-Bold"

STATUS_COR = {"ok": EMERALD, "warn": AMBER, "crit": ROSE, "info": BLUE, "na": ZINC}
STATUS_TXT = {"ok": "CONFORME", "warn": "ATENÇÃO", "crit": "CRÍTICO",
              "info": "INFO", "na": "NÃO AVALIADO"}

_ROTULO_EVID = {
    "nota_fiscal": "Nota fiscal / Ordem de Serviço",
    "peca_nova": "Foto da peça nova",
    "peca_velha": "Foto da peça velha",
    "fotos_servico": "Foto do serviço",
    # Elétrica / Eletrônica
    "foto_painel": "Painel Elétrico Principal",
    "foto_baterias": "Banco de Baterias",
    "foto_epirb": "EPIRB — Radiobaliza (validade)",
    "laudo_eletrico": "Laudo Técnico Elétrico",
    # Casco
    "foto_fundo_externo": "Fundo Externo / Casco no Seco",
    "video_estrutura_interna": "Vídeo — Estrutura Interna (Porão/Cavernas)",
    "video_sala_maquinas": "Vídeo — Sala de Máquinas",
    "video_quilha_externa": "Vídeo — Quilha e Leme no Seco",
    # Manutenção
    "laudo_tecnico": "Laudo Técnico",
}

# Títulos náuticos das categorias ricas do dossiê (dossieCategorias.ts)
TITULOS_DOSSIE = {
    "especificacoes": "Especificações Técnicas",
    "sistemas_auxiliares": "Sistemas Auxiliares",
    "inspecao_tecnica": "Inspeção Técnica (Laudo de Terceiro)",
    "auditoria_casco": "Auditoria Estrutural do Casco (END)",
    "sinistros": "Histórico de Sinistros e Reparos",
    "avaliacao_mercado": "Avaliação de Mercado",
    "relatorio_seguradora": "Relatório para Seguradora",
    "compliance_imo": "Compliance Internacional (IMO)",
    "tripulacao": "Tripulação",
    "tenders_toys": "Tenders & Toys",
    "areas": "Áreas & Acomodações",
}
# Chaves internas que não devem virar linha da ficha
INTERNAS_DADOS = {"arquivos", "evidencias", "enviado_por", "enviado_em"}


def blend(fg, bg, alpha):
    """Simula rgba(fg, alpha) sobre bg — reportlab não tem alpha em fill de tabela."""
    return colors.Color(
        fg.red * alpha + bg.red * (1 - alpha),
        fg.green * alpha + bg.green * (1 - alpha),
        fg.blue * alpha + bg.blue * (1 - alpha),
    )


def track(text, spaces=1):
    """Letter-spacing manual. Usa NBSP porque o Paragraph colapsa espaços
    normais repetidos e comeria o tracking."""
    NB = " "
    return (NB * spaces).join([NB * 3 if ch == " " else ch for ch in text])


def draw_tracked(c, x, y, text, font, size, color, tracking=0.0, align="left"):
    """Texto com letter-spacing no canvas (Canvas não tem setCharSpace)."""
    w = stringWidth(text, font, size) + tracking * max(len(text) - 1, 0)
    if align == "right":
        x -= w
    elif align == "center":
        x -= w / 2.0
    t = c.beginText()
    t.setTextOrigin(x, y)
    t.setFont(font, size)
    t.setFillColor(color)
    t.setCharSpace(tracking)
    t.textOut(text)
    c.drawText(t)
    return w


S = {
    "h2":      ParagraphStyle("h2", fontName=SANS_B, fontSize=10, textColor=GOLD, leading=14),
    "section": ParagraphStyle("section", fontName=SANS_B, fontSize=10.5, textColor=GOLD,
                              leading=15, spaceBefore=2, spaceAfter=2),
    "label":   ParagraphStyle("label", fontName=SANS, fontSize=6, textColor=GOLD_DIM, leading=9),
    "value":   ParagraphStyle("value", fontName=SANS_B, fontSize=9, textColor=WHITE, leading=12.5),
    "body":    ParagraphStyle("body", fontName=SANS, fontSize=8.5, textColor=WHITE_DIM, leading=12.5),
    "body_j":  ParagraphStyle("body_j", fontName=SANS, fontSize=7.8, textColor=WHITE_DIM,
                              leading=11.5, alignment=TA_JUSTIFY),
    "small":   ParagraphStyle("small", fontName=SANS, fontSize=6.8, textColor=WHITE_FAINT, leading=10),
    "kpi_num": ParagraphStyle("kpi_num", fontName=SERIF, fontSize=19, textColor=WHITE, leading=22),
    "kpi_lbl": ParagraphStyle("kpi_lbl", fontName=SANS_B, fontSize=5.5, textColor=GOLD_DIM, leading=8),
    "card":    ParagraphStyle("card", fontName=SANS_B, fontSize=9.5, textColor=WHITE, leading=13),
}


# ─────────────────────────────────────────────────────────────
# FLOWABLES
# ─────────────────────────────────────────────────────────────
class GaugeBar(Flowable):
    """Espelha a barra 'Índice de Segurança' do AssetHealthDashboard."""

    def __init__(self, pct, width=176 * mm):
        super().__init__()
        self.pct, self.width = pct, width

    def wrap(self, aw, ah):
        return self.width, 7 * mm

    def draw(self):
        c = self.canv
        col = EMERALD if self.pct >= 80 else (AMBER if self.pct >= 50 else ROSE)
        bar_h = 2.4 * mm
        c.saveState()
        c.setFillColor(blend(WHITE, NAVY, 0.05))
        c.setStrokeColor(blend(WHITE, NAVY, 0.10))
        c.setLineWidth(0.4)
        c.roundRect(0, 0, self.width, bar_h, bar_h / 2, fill=1, stroke=1)
        c.setFillColor(col)
        c.roundRect(0, 0, self.width * self.pct / 100.0, bar_h, bar_h / 2, fill=1, stroke=0)
        draw_tracked(c, 0, bar_h + 2.4 * mm, "ÍNDICE DE SEGURANÇA", SANS_B, 6, col, tracking=1.2)
        c.setFont(SERIF, 13)
        c.setFillColor(WHITE)
        c.drawRightString(self.width, bar_h + 2.0 * mm, f"{self.pct}%")
        c.restoreState()


class Rule(Flowable):
    def __init__(self, width=176 * mm, color=BORDER, lw=0.5):
        super().__init__()
        self.width, self.color, self.lw = width, color, lw

    def wrap(self, aw, ah):
        return self.width, self.lw

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.lw)
        self.canv.line(0, 0, self.width, 0)


def sp(h=4):
    return Spacer(1, h * mm)


def _natureza(ficha: dict):
    """Natureza da manutenção: 'programada', 'corretiva' ou None.

    O dado aparece em dois lugares conforme a origem do formulário:
    `campos.natureza_manutencao` (ficha técnica) ou `tipo` (ficha simples).
    """
    c = ficha.get("campos") or {}
    txt = f"{c.get('natureza_manutencao') or ''} {ficha.get('tipo') or ''}".lower()
    if "corretiv" in txt:
        return "corretiva"
    if "preventiv" in txt or "preditiv" in txt or "programad" in txt:
        return "programada"
    return None


def _section_title(num_txt, indexar=True):
    t = Table([[Paragraph(num_txt, S["section"])]], colWidths=[176 * mm])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEBELOW", (0, 0), (-1, -1), 0.6, GOLD_DIM),
    ]))
    if indexar:
        # lido pelo afterFlowable p/ montar o índice com a página real
        t._secao_titulo = num_txt
    return KeepTogether([sp(3), t, sp(2.5)])


def _timeline(eventos, total_w=176 * mm):
    """Cronologia dos registros selados: data · marcador · evento."""
    if not eventos:
        return None
    rows = []
    for data, evento, st in eventos:
        col = STATUS_COR.get(st, EMERALD)
        rows.append([
            Paragraph(data, ParagraphStyle("td", fontName=SANS_B, fontSize=7,
                                           textColor=GOLD, leading=11)),
            Paragraph("&#9679;", ParagraphStyle("tp", fontName=SANS_B, fontSize=7,
                                                textColor=col, leading=11, alignment=TA_CENTER)),
            Paragraph(evento, ParagraphStyle("te", fontName=SANS, fontSize=7.8,
                                             textColor=WHITE_DIM, leading=11.5)),
        ])
    t = Table(rows, colWidths=[22 * mm, 8 * mm, total_w - 30 * mm])
    t.setStyle(TableStyle([
        ("LINEBEFORE", (1, 0), (1, -1), 0.5, BORDER),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 2), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _grade_fotos(categorias, total_w=176 * mm, cols=3):
    """Molduras com selo de auditoria, uma por categoria fotográfica real."""
    if not categorias:
        return None
    cel_w = total_w / cols
    fichas = []
    for c in categorias:
        selo = Table([[
            Paragraph("&#10003; SELADA SHA-256", ParagraphStyle(
                "sl", fontName=SANS_B, fontSize=4.8, textColor=NAVY, leading=7)),
            Paragraph(str(c.get("total") or ""), ParagraphStyle(
                "tg", fontName=SANS_B, fontSize=4.8, textColor=NAVY,
                leading=7, alignment=TA_RIGHT)),
        ]], colWidths=[(cel_w - 8 * mm) * 0.62, (cel_w - 8 * mm) * 0.38])
        selo.setStyle(TableStyle([
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        moldura = Table([[selo], [""], [Paragraph(
            str(c.get("label") or ""), ParagraphStyle(
                "pl", fontName=SANS_B, fontSize=6, textColor=WHITE, leading=9))]],
            colWidths=[cel_w - 4 * mm], rowHeights=[5 * mm, 24 * mm, 7 * mm])
        moldura.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), GOLD),
            ("BACKGROUND", (0, 1), (0, -1), SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.5, blend(GOLD, NAVY, 0.5)),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (0, 0), 1.4), ("BOTTOMPADDING", (0, 0), (0, 0), 1.4),
            ("VALIGN", (0, 2), (0, 2), "MIDDLE"),
        ]))
        fichas.append(moldura)
    linhas = [fichas[i:i + cols] for i in range(0, len(fichas), cols)]
    for ln in linhas:
        while len(ln) < cols:
            ln.append("")
    t = Table(linhas, colWidths=[cel_w] * cols)
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 4 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))
    return t


def _info_grid(pairs, cols=3, total_w=176 * mm):
    """Grade label/valor. Pares sem valor são descartados — nunca vira vazio."""
    pairs = [(k, v) for k, v in pairs if v not in (None, "", "None")]
    if not pairs:
        return None
    cw = total_w / cols
    rows, row = [], []
    for k, v in pairs:
        row.append([Paragraph(str(k).upper(), S["label"]), Paragraph(str(v), S["value"])])
        if len(row) == cols:
            rows.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[cw] * cols)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _kpi_row(items, total_w=176 * mm):
    """Tiles de KPI. `items` = [(numero, rotulo, cor)] já filtrados."""
    if not items:
        return None
    cells = []
    for num, lbl, col in items:
        inner = Table(
            [[Paragraph(str(num), ParagraphStyle("n", parent=S["kpi_num"], textColor=col))],
             [Paragraph(track(lbl.upper()), S["kpi_lbl"])]],
            colWidths=[total_w / len(items) - 3 * mm])
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
            ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
            ("LINEBEFORE", (0, 0), (0, -1), 1.6, col),
            ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (0, 0), 8), ("BOTTOMPADDING", (0, 0), (0, 0), 0),
            ("TOPPADDING", (0, 1), (0, 1), 2), ("BOTTOMPADDING", (0, 1), (0, 1), 8),
        ]))
        cells.append(inner)
    t = Table([cells], colWidths=[total_w / len(items)] * len(items))
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _health_grid(items, total_w=176 * mm, cols=4):
    """Grid das 8 categorias — mesmas cores e rótulos do painel."""
    if not items:
        return None
    cells = []
    for lbl, st in items:
        col = STATUS_COR.get(st, ZINC)
        inner = Table(
            [[Paragraph(track(lbl.upper()), ParagraphStyle(
                "hl", fontName=SANS_B, fontSize=5.8, textColor=col, leading=9, alignment=TA_CENTER))],
             [Paragraph(STATUS_TXT.get(st, "—"), ParagraphStyle(
                 "hs", fontName=SANS_B, fontSize=6.5, textColor=col, leading=10, alignment=TA_CENTER))]],
            colWidths=[total_w / cols - 3 * mm])
        inner.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), blend(col, NAVY, 0.07)),
            ("BOX", (0, 0), (-1, -1), 0.6, blend(col, NAVY, 0.35)),
            ("TOPPADDING", (0, 0), (0, 0), 8), ("BOTTOMPADDING", (0, 0), (0, 0), 2),
            ("TOPPADDING", (0, 1), (0, 1), 0), ("BOTTOMPADDING", (0, 1), (0, 1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ]))
        cells.append(inner)
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    for r in rows:
        while len(r) < cols:
            r.append("")
    t = Table(rows, colWidths=[total_w / cols] * cols)
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _alert(kind, titulo, texto):
    col = STATUS_COR.get(kind, BLUE)
    t = Table([[Paragraph(f"<b>{titulo}</b>  {texto}", ParagraphStyle(
        "al", fontName=SANS, fontSize=7.6, textColor=WHITE, leading=11.5))]], colWidths=[176 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), blend(col, NAVY, 0.10)),
        ("LINEBEFORE", (0, 0), (0, -1), 2, col),
        ("BOX", (0, 0), (-1, -1), 0.4, blend(col, NAVY, 0.3)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return KeepTogether([t, sp(2)])


def _data_table(header, linhas, col_widths):
    rows = [[Paragraph(track(h.upper()), S["label"]) for h in header]]
    for ln in linhas:
        rows.append([Paragraph(str(c) if c not in (None, "") else "—", S["body"]) for c in ln])
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, GOLD_DIM),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [NAVY, SURFACE_2]),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 1), (-1, -1), 0.4, BORDER),
    ]))
    return t


def _qr(url, size_mm=40):
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#c5a059", back_color="#010c20").convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return RLImage(buf, width=size_mm * mm, height=size_mm * mm)


# ─────────────────────────────────────────────────────────────
# CANVAS — header, rodapé e numeração "Página X de Y"
# ─────────────────────────────────────────────────────────────
class _DossieCanvas(pdfcanvas.Canvas):
    """Guarda as páginas para desenhar o total no rodapé (2ª passada)."""

    protocolo = ""
    emitido = ""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for i, state in enumerate(self._saved):
            self.__dict__.update(state)
            self.saveState()
            self._header(hero=(i == 0))
            self._rodape(i + 1, total)
            self.restoreState()
            super().showPage()
        super().save()

    def _header(self, hero=False):
        logo_h = 17 if hero else 11
        logo_w = logo_h * LOGO_AR
        base = H - (18 * mm if hero else 15 * mm)
        x = 16 * mm

        if os.path.exists(LOGO):
            try:
                self.drawImage(LOGO, x, base - (logo_h - 8.5) * mm,
                               width=logo_w * mm, height=logo_h * mm,
                               mask="auto", preserveAspectRatio=True, anchor="sw")
                x += (logo_w + 4) * mm
            except Exception:
                pass

        draw_tracked(self, x, base, "YACHTS ATLAS", SANS_B, 14 if hero else 9.5,
                     GOLD, tracking=2.2)
        draw_tracked(self, x, base - (5.2 * mm if hero else 3.6 * mm),
                     "CURADORIA DE ATIVOS NÁUTICOS DE ALTO VALOR",
                     SANS, 6.5 if hero else 5.3, GOLD_DIM, tracking=1.3)

        rs = 6.5 if hero else 5.3
        gap = 4.2 * mm if hero else 3.3 * mm
        r = W - 16 * mm
        draw_tracked(self, r, base, "DOSSIÊ DE CUSTÓDIA E CONFORMIDADE",
                     SANS, rs, WHITE_DIM, tracking=1.1, align="right")
        if self.protocolo:
            draw_tracked(self, r, base - gap, f"Protocolo {self.protocolo}",
                         SANS, rs, WHITE_FAINT, tracking=0.9, align="right")
        draw_tracked(self, r, base - gap * 2, f"Emitido em {self.emitido}",
                     SANS, rs, WHITE_FAINT, tracking=0.9, align="right")

        y = base - (11 * mm if hero else 7.5 * mm)
        self.setStrokeColor(GOLD_DIM if hero else BORDER)
        self.setLineWidth(0.7 if hero else 0.4)
        self.line(16 * mm, y, W - 16 * mm, y)

    def _rodape(self, page, total):
        self.setStrokeColor(BORDER)
        self.setLineWidth(0.4)
        self.line(16 * mm, 15 * mm, W - 16 * mm, 15 * mm)
        draw_tracked(self, 16 * mm, 11 * mm,
                     "AXOS HUB · CNPJ 26.998.571/0001-50", SANS, 5.5, WHITE_FAINT, tracking=1.1)
        draw_tracked(self, W / 2, 11 * mm, "SELADO POR SHA-256",
                     SANS, 5.5, WHITE_FAINT, tracking=1.1, align="center")
        draw_tracked(self, W - 16 * mm, 11 * mm,
                     f"PÁGINA {page} DE {total}  ·  YACHTSATLAS.ONLINE",
                     SANS, 5.5, WHITE_FAINT, tracking=1.1, align="right")


class _Doc(BaseDocTemplate):
    """Registra em que página cada seção caiu, para montar o índice na 2ª passada."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.mapa_secoes: list[tuple[str, int]] = []

    def afterFlowable(self, flowable):
        titulo = getattr(flowable, "_secao_titulo", None)
        if titulo:
            self.mapa_secoes.append((titulo, self.page))


def _indice(mapa):
    """Índice a partir das páginas reais medidas na 1ª passada."""
    if not mapa:
        return None
    rows = []
    for titulo, pag in mapa:
        rows.append([
            Paragraph(titulo, ParagraphStyle("ix", fontName=SANS, fontSize=8.5,
                                             textColor=WHITE, leading=13)),
            Paragraph(str(pag), ParagraphStyle("ip", fontName=SANS_B, fontSize=8.5,
                                               textColor=GOLD, leading=13,
                                               alignment=TA_RIGHT)),
        ])
    t = Table(rows, colWidths=[156 * mm, 20 * mm])
    t.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, 0), (-1, -2), 0.3, BORDER),
    ]))
    return t


def _fundo(c, doc):
    """Fundo navy — desenhado ANTES do conteúdo (o header vai por cima, na 2ª passada)."""
    c.saveState()
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.restoreState()


def _fundo_capa(c, doc):
    _fundo(c, doc)
    c.saveState()
    c.setFillColor(GOLD)
    c.rect(0, 0, 4 * mm, H, fill=1, stroke=0)
    c.restoreState()


# ─────────────────────────────────────────────────────────────
# FICHA (cartão de serviço)
# ─────────────────────────────────────────────────────────────
def _ficha_card(m: dict):
    """Ficha de serviço como CARTÃO, com faixa de status à esquerda.

    Mesmo layout para TODAS as categorias técnicas (alinhado ao painel).
    """
    situacao = m.get("situacao") or "vigente"
    status_txt = (m.get("status") or "").lower()
    if situacao == "retificado":
        col = AMBER
    elif situacao == "retificador":
        col = BLUE
    elif status_txt in ("atencao", "atenção"):
        col = AMBER
    elif status_txt in ("pendente",):
        col = AMBER
    else:
        col = EMERALD

    inner = []
    cab = m.get("servico") or "Serviço"
    dir_txt = (m.get("status") or "").upper()
    if situacao == "retificado":
        dir_txt = "RETIFICADO"
    elif situacao == "retificador":
        dir_txt = "RETIFICAÇÃO"

    head = Table([[
        Paragraph(cab, S["card"]),
        Paragraph(dir_txt, ParagraphStyle("st", fontName=SANS_B, fontSize=6.5,
                                          textColor=col, leading=10, alignment=TA_RIGHT)),
    ]], colWidths=[124 * mm, 36 * mm])
    head.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    inner.append(head)

    c = m.get("campos") or {}
    nat = c.get("natureza_manutencao") or m.get("tipo")
    if nat:
        badge = Table([[Paragraph(track(str(nat).upper()), ParagraphStyle(
            "bd", fontName=SANS_B, fontSize=5.5, textColor=GOLD_LIGHT, leading=8))]],
            colWidths=[len(str(nat)) * 2.6 * mm + 6 * mm], hAlign="LEFT")
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), blend(GOLD, NAVY, 0.14)),
            ("BOX", (0, 0), (-1, -1), 0.4, blend(GOLD, NAVY, 0.35)),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ]))
        inner += [Spacer(1, 2), badge, Spacer(1, 5)]

    # Diário de bordo tem campos próprios; demais categorias usam a ficha técnica.
    if c.get("condutor") or c.get("hora_saida"):
        tempo = None
        try:
            hs, hr = float(c.get("horimetro_saida")), float(c.get("horimetro_retorno"))
            if hr >= hs:
                tempo = f"{round(hr - hs, 1)} h de motor"
        except (TypeError, ValueError):
            tempo = None
        grid = _info_grid([
            ("Data", m.get("data")), ("Finalidade", c.get("finalidade")),
            ("Local", c.get("local")), ("Condutor", c.get("condutor")),
            ("Habilitação", c.get("habilitacao")), ("CHA nº", c.get("cha_numero")),
            ("Validade CHA", c.get("cha_validade")), ("Pessoas a bordo", c.get("pessoas_bordo")),
            ("Resp. manuseio", c.get("resp_manuseio")), ("Lançou na água", c.get("quem_lancou")),
            ("Saída", c.get("hora_saida")),
            ("Horímetro saída", f"{c.get('horimetro_saida')} h" if c.get("horimetro_saida") else None),
            ("Retorno", c.get("hora_retorno")),
            ("Horímetro retorno", f"{c.get('horimetro_retorno')} h" if c.get("horimetro_retorno") else None),
            ("Tempo de uso", tempo), ("Milhas navegadas", c.get("milhas_navegadas")),
            ("Reboque p/ marina", c.get("quem_reboque")), ("Combustível", c.get("combustivel")),
            ("Condições", c.get("condicoes")), ("Estado no retorno", c.get("retorno_estado")),
            ("Avaria / sinistro", c.get("avaria_desc")),
        ], cols=3, total_w=164 * mm)
    else:
        grid = _info_grid([
            ("Data", m.get("data")), ("Natureza", c.get("natureza_manutencao")),
            ("Sistema afetado", c.get("sistema_afetado")),
            ("Responsável", m.get("resp")), ("Prestador", m.get("prestador")),
            ("CNPJ", m.get("cnpj")), ("Local", m.get("local")),
            ("Horímetro (motor)", f"{m.get('horimetro')} h" if m.get("horimetro") else None),
            ("Horas trabalhadas", f"{m.get('horas_trabalhadas')} h" if m.get("horas_trabalhadas") else None),
            ("Valor", f"R$ {m.get('valor')}" if m.get("valor") else None),
            ("Próxima revisão", m.get("proxima_revisao")),
            ("Peça trocada", m.get("peca")), ("Part number", m.get("peca_part_number")),
            ("Nº de série", m.get("peca_serie")), ("Método", c.get("metodo")),
        ], cols=3, total_w=164 * mm)
    if grid:
        inner.append(grid)

    if m.get("observacao"):
        inner.append(Paragraph(m["observacao"], S["body"]))

    # Cadeia de retificação — o erro e a correção ficam os dois à vista.
    if situacao == "retificado" and m.get("retificado_motivo"):
        inner.append(Spacer(1, 3))
        inner.append(Paragraph(
            f'<font color="#f59e0b"><b>Retificado posteriormente.</b></font> '
            f'Motivo: {m["retificado_motivo"]} '
            f'<i>Este registro permanece selado e íntegro.</i>', S["small"]))
    elif situacao == "retificador" and m.get("motivo_retificacao"):
        inner.append(Spacer(1, 3))
        inner.append(Paragraph(
            f'<font color="#3b82f6"><b>Corrige um registro anterior.</b></font> '
            f'Motivo: {m["motivo_retificacao"]}', S["small"]))

    for ev in (m.get("evidencias") or []):
        rotulo = _ROTULO_EVID.get(ev.get("slot"), ev.get("slot") or "Evidência")
        h = (ev.get("hash") or "")[:16]
        linha = Table([[
            Paragraph("&#9635;", ParagraphStyle("lk", fontName=SANS_B, fontSize=7,
                                                textColor=GOLD, leading=10)),
            Paragraph(f"<b>{rotulo}</b> · {ev.get('nome') or ''}",
                      ParagraphStyle("evn", fontName=SANS, fontSize=6.8,
                                     textColor=WHITE_DIM, leading=10)),
            Paragraph(f"SHA-256 {h}…" if h else "",
                      ParagraphStyle("evh", fontName="Courier", fontSize=6,
                                     textColor=GOLD_DIM, leading=10, alignment=TA_RIGHT)),
        ]], colWidths=[5 * mm, 89 * mm, 70 * mm])
        linha.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), blend(GOLD, NAVY, 0.05)),
            ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        inner += [Spacer(1, 1.5), linha]

    if m.get("enviado_por"):
        inner.append(Spacer(1, 3))
        inner.append(Paragraph(f"Enviado por {m['enviado_por']} — registro imutável", S["small"]))

    card = Table([[inner]], colWidths=[176 * mm])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE_2),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 2, col),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return KeepTogether([card, sp(3)])


# ─────────────────────────────────────────────────────────────
# CAPA
# ─────────────────────────────────────────────────────────────
def _capa(dados: dict, ident: dict) -> list:
    st = [sp(6)]
    st.append(Paragraph(track("DOSSIÊ DE CUSTÓDIA E CONFORMIDADE NÁUTICA"),
                        ParagraphStyle("ct", fontName=SANS_B, fontSize=6.5,
                                       textColor=GOLD_DIM, leading=11)))
    st.append(sp(4))
    st.append(Paragraph(str(ident.get("nome") or "Dossiê do Ativo"),
                        ParagraphStyle("cn", fontName=SERIF, fontSize=42,
                                       textColor=WHITE, leading=46)))

    sub = " · ".join(str(x) for x in [
        ident.get("fabricante"), ident.get("modelo"),
        ident.get("comprimento"), ident.get("ano"),
    ] if x)
    if sub:
        st.append(sp(2))
        st.append(Paragraph(sub, ParagraphStyle("cd", fontName=SANS, fontSize=9.5,
                                                textColor=WHITE_DIM, leading=14)))

    classif = dados.get("classificacao")
    if classif:
        st.append(sp(9))
        badge = Table([[Paragraph(track(f"CLASSIFICAÇÃO {classif}"), ParagraphStyle(
            "cg", fontName=SANS_B, fontSize=7, textColor=GOLD_LIGHT, leading=11))]],
            colWidths=[62 * mm], hAlign="LEFT")
        badge.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), blend(GOLD, NAVY, 0.14)),
            ("BOX", (0, 0), (-1, -1), 0.6, blend(GOLD, NAVY, 0.45)),
            ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        st.append(badge)

    st.append(sp(10))
    st.append(Rule(color=BORDER))
    st.append(sp(5))

    # ── Marina custodiante (perfil real do custodiante; nada inventado) ──
    cust = dados.get("custodiante") or {}
    pares_cust = [
        ("Marina / Empresa", cust.get("empresa")),
        ("Responsável", cust.get("responsavel")),
        ("Contato", cust.get("contato")),
        ("Cadastro", "Verificado pela Yachts Atlas" if cust.get("verificado") else None),
    ]
    grid_cust = _info_grid(pares_cust, cols=2)
    if grid_cust:
        st.append(Paragraph("MARINA CUSTODIANTE", S["h2"]))
        st.append(sp(2.5))
        st.append(grid_cust)
        st.append(sp(3))
        st.append(Rule(color=BORDER))
        st.append(sp(5))

    # ── O ativo em números (tudo derivado do banco) ──
    r = dados.get("resumo") or {}
    tiles = [
        (r.get("investido"), "Investido no ativo", GOLD),
        (r.get("registros"), "Registros selados", WHITE),
        (r.get("imagens"), "Documentos selados", WHITE),
        (r.get("meses_custodia") and f"{r['meses_custodia']}", "Meses de custódia", WHITE),
    ]
    tiles = [(n, l, c) for n, l, c in tiles if n]
    if tiles:
        st.append(Paragraph("O ATIVO EM NÚMEROS", S["h2"]))
        st.append(sp(3))
        st.append(_kpi_row(tiles))
        st.append(sp(6))

    pront = dados.get("prontidao")
    if pront is not None:
        st.append(GaugeBar(pront))
        st.append(sp(11))

    saude = dados.get("saude") or []
    if any(s != "na" for _, s in saude):
        st.append(Paragraph("PRONTIDÃO OPERACIONAL POR SISTEMA", S["h2"]))
        st.append(sp(3))
        st.append(_health_grid(saude))

    return st


# ─────────────────────────────────────────────────────────────
# GERADOR
# ─────────────────────────────────────────────────────────────
def gerar_pdf_dossie(dados: dict) -> bytes:
    """Gera o PDF do dossiê. Duas passadas: a 1ª mede em que página cada seção
    cai, a 2ª monta o índice com os números reais."""
    mapa = _montar(dados, indice=None).mapa_secoes
    doc = _montar(dados, indice=mapa)
    return doc._buffer.getvalue()


def _montar(dados: dict, indice):
    """Constrói o documento. `indice` = mapa da passada anterior (ou None)."""
    buf = BytesIO()
    ident = dados.get("identificacao", {}) or {}
    emitido = datetime.now(TZ_BR).strftime("%d/%m/%Y")
    protocolo = dados.get("ativo_id") or ""

    class Canvas(_DossieCanvas):
        pass
    Canvas.protocolo = protocolo
    Canvas.emitido = emitido

    doc = _Doc(
        buf, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=24 * mm, bottomMargin=20 * mm,
        title=f"Dossiê Yachts Atlas — {ident.get('nome') or protocolo}",
        author="Yachts Atlas · AXOS HUB",
        subject="Dossiê de Custódia e Conformidade Náutica")
    doc.addPageTemplates([
        PageTemplate(id="capa", onPage=_fundo_capa,
                     frames=[Frame(16 * mm, 22 * mm, W - 32 * mm, H - 58 * mm,
                                   leftPadding=0, rightPadding=0,
                                   topPadding=0, bottomPadding=0)]),
        PageTemplate(id="corpo", onPage=_fundo,
                     frames=[Frame(16 * mm, 20 * mm, W - 32 * mm, H - 49 * mm,
                                   leftPadding=0, rightPadding=0,
                                   topPadding=0, bottomPadding=0)]),
    ])

    story = _capa(dados, ident)
    story.append(NextPageTemplate("corpo"))
    story.append(PageBreak())

    # ── Sumário executivo: 2ª linha de KPIs + pendências reais ──
    r = dados.get("resumo") or {}
    tiles2 = [
        (r.get("horimetro"), "Horímetro atual", WHITE),
        (r.get("pendencias") if r.get("pendencias") else None, "Pendências abertas", AMBER),
        (r.get("integridade"), "Hashes íntegros", EMERALD),
        (r.get("custodia_desde"), "Custódia desde", WHITE),
    ]
    tiles2 = [(n, l, c) for n, l, c in tiles2 if n]
    pendentes = [
        reg for reg in (dados.get("registros") or [])
        if reg.get("status") in ("pendente", "atencao")
    ]
    if tiles2 or pendentes:
        story.append(_section_title("Sumário Executivo do Ativo", indexar=False))
        story.append(Paragraph(
            "Indicadores calculados sobre os registros selados — os mesmos números que a "
            "marina vê no painel técnico.", S["body"]))
        story.append(sp(4))
        if tiles2:
            story.append(_kpi_row(tiles2))
            story.append(sp(6))
        if pendentes:
            story.append(Paragraph("PENDÊNCIAS EM ABERTO", S["h2"]))
            story.append(sp(3))
            for reg in pendentes[:8]:
                kind = "warn" if reg.get("status") == "pendente" else "crit"
                titulo = reg.get("titulo") or "Registro"
                obs = reg.get("observacao") or ""
                story.append(_alert(kind, f"{titulo} —", obs or "Requer acompanhamento."))
            if len(pendentes) > 8:
                story.append(Paragraph(
                    f"…e mais {len(pendentes) - 8} pendência(s) detalhada(s) nas seções "
                    "técnicas a seguir.", S["small"]))
        story.append(sp(3))

    # ── Preâmbulo legal ──
    story.append(_section_title("Preâmbulo Legal", indexar=False))
    story.append(Paragraph(
        "Este Dossiê é documento privado de custódia e conformidade digital, elaborado em "
        "observância à Lei nº 9.537/1997 (LESTA), ao seu regulamento (RLESTA, Dec. 2.596/1998) "
        "e às Normas da Autoridade Marítima (NORMAM/DPC) da Marinha do Brasil. Reúne, organiza "
        "e sela a história documental e operacional da embarcação. <b>Não substitui os documentos "
        "oficiais emitidos pela Autoridade Marítima/Capitania dos Portos</b> — complementa-os, "
        "com cadeia de custódia e integridade verificável.", S["body_j"]))
    story.append(sp(4))

    # ── Índice em página própria ──
    # O PageBreak ANTES é incondicional: a 1ª passada (sem tabela) precisa ter
    # o mesmo fluxo de páginas da 2ª, senão os números medidos saem deslocados.
    story.append(PageBreak())
    if indice:
        tabela_indice = _indice(indice)
        if tabela_indice:
            story.append(_section_title("Índice do Dossiê", indexar=False))
            story.append(tabela_indice)
    story.append(PageBreak())

    n = 1

    # 01 — Identificação
    ti = _info_grid([
        ("Nome", ident.get("nome")), ("Tipo", ident.get("tipo")),
        ("Fabricante", ident.get("fabricante")), ("Modelo", ident.get("modelo")),
        ("Ano", ident.get("ano")), ("Comprimento", ident.get("comprimento")),
        ("Nº de Registro", ident.get("registro")), ("Casco (HIN)", ident.get("vin")),
    ], cols=3)
    if ti:
        story.append(_section_title(f"{n:02d} — Identificação da Embarcação"))
        story.append(ti)
        n += 1

    # 02 — Proprietários
    props = dados.get("proprietarios") or []
    if props:
        story.append(_section_title(f"{n:02d} — Histórico de Proprietários"))
        story.append(_data_table(
            ["Ordem", "Proprietário", "Período", "Transferência"],
            [[p.get("ordem"), p.get("nome"), p.get("periodo"), p.get("tipo")] for p in props],
            [18 * mm, 76 * mm, 40 * mm, 42 * mm]))
        n += 1

    # 03 — Documentação
    docs = dados.get("documentacao") or []
    if docs:
        story.append(_section_title(f"{n:02d} — Documentação Legal e Fiscal"))
        rows = [[Paragraph("&#10003;", ParagraphStyle("ck", fontName=SANS_B, fontSize=8,
                                                      textColor=EMERALD, leading=11)),
                 Paragraph(str(d), ParagraphStyle("cl", fontName=SANS, fontSize=8,
                                                  textColor=WHITE, leading=11.5))]
                for d in docs]
        t = Table(rows, colWidths=[7 * mm, 169 * mm])
        t.setStyle(TableStyle([
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [NAVY, SURFACE_2]),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOX", (0, 0), (-1, -1), 0.4, BORDER),
        ]))
        story.append(t)
        n += 1

    story.append(PageBreak())

    # ── Seções técnicas: uma página cada, fichas em cartão ──
    secoes_tecnicas = dados.get("secoes_tecnicas")
    if secoes_tecnicas is None:
        secoes_tecnicas = [{"titulo": "Histórico de Manutenção", "categoria": "manutencao",
                            "fichas": dados.get("manutencao") or []}]
    categorias_tratadas = {"proprietarios", "documentacao"}

    for sec in secoes_tecnicas:
        fichas = sec.get("fichas") or []
        if not fichas:
            continue
        categorias_tratadas.add(sec.get("categoria"))
        story.append(_section_title(f"{n:02d} — {sec.get('titulo') or 'Registros Técnicos'}"))

        cat = sec.get("categoria", "")
        if cat in ("manutencao", "eletrica"):
            label = "Manutenção" if cat == "manutencao" else "Elétrica / Eletrônica"
            # Métricas só sobre o que vale hoje: registro retificado foi
            # substituído pela correção — contar os dois inflaria o total.
            vigentes = [f for f in fichas if (f.get("situacao") or "vigente") != "retificado"]
            retificados = len(fichas) - len(vigentes)
            prog = sum(1 for f in vigentes if _natureza(f) == "programada")
            corr = sum(1 for f in vigentes if _natureza(f) == "corretiva")
            classificados = prog + corr

            if classificados == 0:
                # Sem classificação não se afirma nada: dizer "100% corretiva"
                # com o campo vazio é acusar o dono de negligência.
                story.append(_alert("na", f"Indicador de Saúde — {label}:",
                                    f"natureza não classificada em {len(vigentes)} registro(s). "
                                    "Classifique os serviços como preventivo, preditivo ou "
                                    "corretivo para habilitar este indicador."))
            else:
                pct = round(prog / classificados * 100)
                kind = "ok" if pct >= 70 else ("warn" if pct >= 40 else "crit")
                extra = f" · {retificados} retificado(s)" if retificados else ""
                story.append(_alert(kind, f"Indicador de Saúde — {label}:",
                                    f"{pct}% Preventiva / Programada · {100 - pct}% Corretiva "
                                    f"({classificados} de {len(vigentes)} classificado(s), "
                                    f"selado(s) com SHA-256{extra})"))

            # Recorrência corretiva por sistema
            recorrentes: dict = {}
            for f in vigentes:
                cmps = f.get("campos") or {}
                if _natureza(f) == "corretiva" and cmps.get("sistema_afetado"):
                    s = cmps["sistema_afetado"]
                    recorrentes[s] = recorrentes.get(s, 0) + 1
            for sist, qtd in recorrentes.items():
                if qtd > 1:
                    story.append(_alert("crit", "Recorrência corretiva:",
                                        f"O sistema <i>{sist}</i> registrou {qtd} falhas "
                                        "corretivas. Recomenda-se auditoria técnica detalhada "
                                        "deste componente."))

            # Conformidade NORMAM (aba elétrica)
            if cat == "eletrica":
                for f in fichas:
                    cmps = f.get("campos") or {}
                    if cmps.get("epirb_instalada") == "Sim" and \
                       "Pendente" in (cmps.get("epirb_anatel") or ""):
                        story.append(_alert("crit", "NORMAM-02 / ANATEL:",
                                            "EPIRB instalada, mas <b>cadastro ANATEL pendente</b>. "
                                            "Embarcação em situação irregular — regularize antes "
                                            "da próxima saída ao mar."))
                        break
                for f in fichas:
                    if "Não" in ((f.get("campos") or {}).get("vhf_dsc_canal16") or ""):
                        story.append(_alert("crit", "NORMAM-02 / DPC:",
                                            "Canal 16 VHF DSC não monitorado. Monitoramento "
                                            "obrigatório por lei durante toda a navegação."))
                        break
            story.append(sp(2))

        for m in fichas:
            story.append(_ficha_card(m))
        n += 1
        story.append(PageBreak())

    # ── Registro fotográfico ──
    foto = dados.get("fotografico") or {}
    if foto.get("total"):
        story.append(_section_title(f"{n:02d} — Registro Fotográfico Certificado"))
        cap, geo = foto.get("capacidade"), foto.get("com_geo") or 0
        story.append(Paragraph(
            f"{foto['total']} imagem(ns) selada(s) e datada(s)"
            + (f" · capacidade de {cap} por embarcação" if cap else "")
            + (f" · {geo} geolocalizada(s)" if geo else "")
            + " · cada arquivo com hash SHA-256 imutável.", S["body"]))
        cats = foto.get("categorias") or []
        if cats:
            story.append(sp(4))
            grade = _grade_fotos(cats)
            if grade:
                story.append(grade)
            story.append(sp(2))
            story.append(_data_table(["Categoria", "Imagens"],
                                     [[c.get("label"), c.get("total")] for c in cats],
                                     [130 * mm, 46 * mm]))
        n += 1
        story.append(PageBreak())

    # ── Demais categorias não mapeadas (fallback) ──
    outras: dict = {}
    for r in (dados.get("registros") or []):
        c = r.get("categoria")
        if c in categorias_tratadas:
            continue
        outras.setdefault(c, []).append(r)
    for cat, regs in outras.items():
        titulo = TITULOS_DOSSIE.get(cat, str(cat).replace("_", " ").title())
        story.append(_section_title(f"{n:02d} — {titulo}"))
        for r in regs:
            story.append(Paragraph(f"<b>{r.get('titulo') or 'Registro'}</b>", S["value"]))
            d = r.get("dados") or {}
            pares = [(k.replace("_", " ").title(), v) for k, v in d.items()
                     if k not in INTERNAS_DADOS and v not in (None, "", [], {})]
            g = _info_grid(pares, cols=3)
            if g:
                story.append(g)
            for item in (r.get("checklist") or []):
                story.append(Paragraph(f"&#10003; {item}", S["small"]))
            for a in (d.get("arquivos") or []):
                if isinstance(a, dict):
                    story.append(Paragraph(
                        f"&#9635; {a.get('nome') or 'Anexo'} · SHA-256 "
                        f"{(a.get('hash') or '')[:16]}…", S["small"]))
            if r.get("observacao"):
                story.append(Paragraph(r["observacao"], S["small"]))
            story.append(Spacer(1, 6))
        n += 1
        story.append(PageBreak())

    # ── Linha do tempo da custódia ──
    eventos = []
    for reg in (dados.get("registros") or []):
        dd = reg.get("dados") or {}
        # `data` (ficha técnica) ou `data_servico` (form rápido do painel).
        # created_at é só fallback — é a data do cadastro, não a do serviço.
        d = dd.get("data") or dd.get("data_servico") or str(reg.get("created_at") or "")[:10]
        if not d:
            continue
        # ISO (2024-03-12) -> 03/2024
        partes = str(d)[:10].split("-")
        rotulo = f"{partes[1]}/{partes[0]}" if len(partes) == 3 else str(d)[:10]
        st = {"atencao": "crit", "pendente": "warn"}.get(reg.get("status"), "ok")
        eventos.append((str(d)[:10], rotulo, reg.get("titulo") or "Registro", st))
    eventos.sort(key=lambda e: e[0])
    if eventos:
        story.append(_section_title(f"{n:02d} — Linha do Tempo da Custódia"))
        story.append(Paragraph(
            "Cronologia dos eventos selados. Cada marco corresponde a um registro imutável "
            "com data, autoria e hash.", S["body"]))
        story.append(sp(4))
        story.append(_timeline([(rot, tit, st) for _, rot, tit, st in eventos]))
        n += 1
        story.append(PageBreak())

    # ── Cadeia de custódia digital ──
    cadeia = []
    for r in (dados.get("registros") or []):
        for ev in ((r.get("dados") or {}).get("evidencias") or []):
            if isinstance(ev, dict) and ev.get("hash"):
                cadeia.append([ev.get("nome") or "—", str(r.get("created_at") or "")[:10],
                               ev["hash"][:32]])
    if cadeia:
        story.append(_section_title(f"{n:02d} — Cadeia de Custódia Digital"))
        story.append(Paragraph(
            "Relação dos arquivos selados. O hash é calculado no momento do upload; qualquer "
            "alteração posterior produz hash divergente e é imediatamente detectável.", S["body"]))
        story.append(sp(3))
        story.append(_data_table(["Arquivo", "Selado em", "Hash SHA-256"],
                                 cadeia, [66 * mm, 30 * mm, 80 * mm]))
        n += 1
        story.append(PageBreak())

    # ── Termo + verificação de autenticidade ──
    story.append(_section_title("Termo de Custódia e Integridade Digital"))
    story.append(Paragraph(
        "Declara-se que os registros, documentos e imagens deste Dossiê foram selados por hash "
        "criptográfico SHA-256 no momento do registro, com data e autoria, constituindo cadeia "
        "de custódia digital verificável. Os registros são gravados em modo <i>append-only</i>: "
        "uma vez selados, não podem ser editados nem excluídos — nem pela própria plataforma. "
        "Correções são feitas por <b>retificação</b>, e o registro original permanece visível "
        "ao lado da correção.", S["body_j"]))
    story.append(sp(6))
    r = dados.get("resumo") or {}
    story.append(_info_grid([
        ("Emitido por", "Yachts Atlas · AXOS HUB"),
        ("CNPJ", "26.998.571/0001-50"),
        ("Protocolo", protocolo),
        ("Data de emissão", emitido),
        ("Custódia desde", r.get("custodia_desde")),
        ("Algoritmo", "SHA-256 · append-only"),
    ], cols=3))
    story.append(sp(8))

    verify_url = f"https://app.yachtsatlas.online/verificar/{protocolo}"
    story.append(_section_title("Verificação de Autenticidade"))
    try:
        qr_img = _qr(verify_url, 40)
    except Exception:
        qr_img = Paragraph(f"Verificar em: {verify_url}", S["small"])
    bloco = Table([[
        qr_img,
        [Paragraph("COMO VERIFICAR ESTE DOCUMENTO", S["h2"]),
         Spacer(1, 5),
         Paragraph("1. Aponte a câmera para o QR ao lado, ou acesse o endereço abaixo.<br/>"
                   "2. Informe o protocolo do dossiê.<br/>"
                   "3. O sistema recalcula os hashes e confirma se a cadeia está íntegra.",
                   S["body"]),
         Spacer(1, 6),
         Paragraph(track("ENDEREÇO DE VERIFICAÇÃO"), S["label"]),
         Paragraph(verify_url, ParagraphStyle("vu", fontName="Courier", fontSize=7,
                                              textColor=GOLD_LIGHT, leading=11)),
         ],
    ]], colWidths=[46 * mm, 130 * mm])
    bloco.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), SURFACE),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("LINEBEFORE", (0, 0), (0, -1), 2, GOLD),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(bloco)
    story.append(sp(6))
    story.append(Paragraph(
        "Documento gerado pela plataforma Yachts Atlas a partir dos registros custodiados. "
        f"Protocolo {protocolo}. Emitido em {emitido}. "
        "Yachts Atlas é uma plataforma AXOS HUB · CNPJ 26.998.571/0001-50.", S["small"]))

    doc.build(story, canvasmaker=Canvas)
    doc._buffer = buf
    return doc
