"""
Yachts Atlas — Gerador de PDF do Dossiê (a partir de dados REAIS do banco).
Renderiza só as seções que têm dado (regra "nenhuma seção vazia").
Estilo Atlas: fundo navy, dourado, sem dados fake.
Consome o pacote de montar_dados_dossie() (dossie_data.py).
"""
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

NAVY = colors.HexColor("#010c20")
SURFACE = colors.HexColor("#021431")
GOLD = colors.HexColor("#c5a059")
GOLD_DIM = colors.HexColor("#8a7038")
WHITE = colors.HexColor("#f0ede6")
WHITE_DIM = colors.HexColor("#9aa0aa")
BORDER = colors.HexColor("#1a2740")

S = {
    "eyebrow": ParagraphStyle("eyebrow", fontName="Helvetica-Bold", fontSize=7, textColor=GOLD_DIM, leading=11),
    "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=26, textColor=WHITE, leading=30),
    "section": ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=11, textColor=GOLD, leading=16, spaceBefore=10, spaceAfter=4),
    "label": ParagraphStyle("label", fontName="Helvetica", fontSize=6.5, textColor=GOLD_DIM, leading=9),
    "value": ParagraphStyle("value", fontName="Helvetica-Bold", fontSize=9.5, textColor=WHITE, leading=13),
    "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9, textColor=WHITE_DIM, leading=13),
    "small": ParagraphStyle("small", fontName="Helvetica", fontSize=7, textColor=WHITE_DIM, leading=10),
}


def _bg(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    canvas.setFillColor(GOLD)
    canvas.rect(0, A4[1] - 6, 14 * mm, 6, fill=1, stroke=0)  # detalhe dourado no topo
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(GOLD_DIM)
    canvas.drawString(20 * mm, 12 * mm, "ATLAS YACHTS — CUSTÓDIA DIGITAL DE ATIVOS NÁUTICOS")
    canvas.drawRightString(A4[0] - 14 * mm, 12 * mm, "yachtsatlas.online")
    canvas.restoreState()


def _section_title(num_txt):
    return Paragraph(num_txt, S["section"])


def _info_table(pairs):
    pairs = [(k, v) for k, v in pairs if v not in (None, "", "None")]
    if not pairs:
        return None
    rows, row = [], []
    for i, (k, v) in enumerate(pairs):
        cell = [Paragraph(str(k).upper(), S["label"]), Paragraph(str(v), S["value"])]
        row.append(cell)
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        row.append("")
        rows.append(row)
    t = Table(rows, colWidths=[88 * mm, 88 * mm])
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _data_table(header, linhas, col_widths):
    rows = [[Paragraph(h, S["label"]) for h in header]]
    for ln in linhas:
        rows.append([Paragraph(str(c) if c not in (None, "") else "—", S["body"]) for c in ln])
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, 0), 0.4, GOLD_DIM),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [NAVY, SURFACE]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def gerar_pdf_dossie(dados: dict) -> bytes:
    """Gera o PDF do dossiê em memória e devolve os bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=20 * mm, rightMargin=14 * mm,
                            topMargin=18 * mm, bottomMargin=20 * mm)
    story = []
    ident = dados.get("identificacao", {}) or {}

    # ── Capa / cabeçalho ──
    story.append(Paragraph("ATLAS YACHTS", ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=18, textColor=GOLD, leading=22)))
    story.append(Paragraph("CUSTÓDIA DIGITAL DE ATIVOS NÁUTICOS", S["eyebrow"]))
    story.append(Spacer(1, 14))
    story.append(Paragraph(str(ident.get("nome") or "Dossiê do Ativo"), S["h1"]))
    story.append(Paragraph("DOSSIÊ YACHTS ATLAS", S["eyebrow"]))
    story.append(Spacer(1, 14))

    # 01 — Identificação
    ti = _info_table([
        ("Nome", ident.get("nome")), ("Tipo", ident.get("tipo")),
        ("Fabricante", ident.get("fabricante")), ("Modelo", ident.get("modelo")),
        ("Ano", ident.get("ano")), ("Comprimento", ident.get("comprimento")),
        ("Nº de Registro", ident.get("registro")), ("Casco (HIN)", ident.get("vin")),
    ])
    if ti:
        story.append(_section_title("01 — Identificação da Embarcação"))
        story.append(ti)

    # 02 — Proprietários
    props = dados.get("proprietarios") or []
    if props:
        story.append(_section_title("02 — Histórico de Proprietários"))
        story.append(_data_table(
            ["ORDEM", "PROPRIETÁRIO", "PERÍODO", "TRANSFERÊNCIA"],
            [[p.get("ordem"), p.get("nome"), p.get("periodo"), p.get("tipo")] for p in props],
            [18 * mm, 70 * mm, 45 * mm, 43 * mm],
        ))

    # 03 — Documentação
    docs = dados.get("documentacao") or []
    if docs:
        story.append(_section_title("03 — Documentação Legal e Fiscal"))
        for d in docs:
            story.append(Paragraph(f"✓  {d}", S["body"]))

    # 04 — Manutenção
    manut = dados.get("manutencao") or []
    if manut:
        story.append(_section_title("04 — Histórico de Manutenção"))
        story.append(_data_table(
            ["DATA", "SERVIÇO", "RESPONSÁVEL", "STATUS"],
            [[m.get("data"), m.get("servico"), m.get("resp"), m.get("status")] for m in manut],
            [22 * mm, 78 * mm, 40 * mm, 36 * mm],
        ))

    # Demais categorias com registro (a partir de registros crus)
    registros = dados.get("registros") or []
    ja_tratadas = {"proprietarios", "documentacao", "manutencao"}
    outras = {}
    for r in registros:
        cat = r.get("categoria")
        if cat in ja_tratadas:
            continue
        outras.setdefault(cat, []).append(r)
    n = 5
    for cat, regs in outras.items():
        story.append(_section_title(f"{n:02d} — {cat.replace('_', ' ').title()}"))
        for r in regs:
            titulo = r.get("titulo") or "Registro"
            obs = r.get("observacao") or ""
            story.append(Paragraph(f"<b>{titulo}</b>", S["value"]))
            if obs:
                story.append(Paragraph(obs, S["small"]))
            story.append(Spacer(1, 4))
        n += 1

    # Assinatura
    story.append(Spacer(1, 16))
    emitido = datetime.utcnow().strftime("%d/%m/%Y")
    story.append(Paragraph("— CERTIFICAÇÃO E CUSTÓDIA DIGITAL", S["section"]))
    story.append(Paragraph(
        "Documento gerado pela plataforma Atlas Yachts a partir dos registros custodiados. "
        f"Emitido em {emitido}. A integridade dos documentos é garantida por hash SHA-256 no momento do upload.",
        S["small"]))

    doc.build(story, onFirstPage=_bg, onLaterPages=_bg)
    return buf.getvalue()
