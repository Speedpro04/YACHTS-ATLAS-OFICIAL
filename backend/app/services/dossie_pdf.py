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

_ROTULO_EVID = {
    "nota_fiscal": "Nota fiscal",
    "peca_nova": "Foto da peça nova",
    "peca_velha": "Foto da peça velha",
    "fotos_servico": "Foto do serviço",
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


def _render_ficha(story, m: dict):
    """Renderiza uma ficha de serviço rica (logbook) com evidências seladas.
    Mesmo layout para TODAS as categorias técnicas (alinhado ao painel)."""
    cab = f"<b>{m.get('servico') or 'Serviço'}</b>"
    if m.get("status"):
        cab += f"  ·  {m.get('status')}"
    story.append(Paragraph(cab, S["value"]))
    ficha = _info_table([
        ("Data", m.get("data")), ("Tipo", m.get("tipo")),
        ("Responsável", m.get("resp")), ("Prestador", m.get("prestador")),
        ("CNPJ", m.get("cnpj")), ("Local", m.get("local")),
        ("Horímetro (motor)", f"{m.get('horimetro')} h" if m.get("horimetro") else None),
        ("Horas trabalhadas", f"{m.get('horas_trabalhadas')} h" if m.get("horas_trabalhadas") else None),
        ("Valor", f"R$ {m.get('valor')}" if m.get("valor") else None),
        ("Próxima revisão", m.get("proxima_revisao")),
        ("Peça trocada", m.get("peca")), ("Part number", m.get("peca_part_number")),
        ("Nº de série", m.get("peca_serie")),
    ])
    if ficha:
        story.append(ficha)
    if m.get("observacao"):
        story.append(Paragraph(m["observacao"], S["small"]))
    for ev in (m.get("evidencias") or []):
        rotulo = _ROTULO_EVID.get(ev.get("slot"), ev.get("slot") or "Evidência")
        h = (ev.get("hash") or "")[:16]
        story.append(Paragraph(f"&#128274; {rotulo} — {ev.get('nome') or ''} · SHA-256 {h}…", S["small"]))
    if m.get("enviado_por"):
        story.append(Paragraph(f"Enviado por {m['enviado_por']} — registro imutável", S["small"]))
    story.append(Spacer(1, 8))


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

    # 04+ — Seções técnicas (todas com a MESMA ficha rica do painel/logbook)
    n = 4
    secoes_tecnicas = dados.get("secoes_tecnicas")
    if secoes_tecnicas is None:
        # Compat: monta a seção de manutenção a partir da chave antiga.
        secoes_tecnicas = [{"titulo": "Histórico de Manutenção", "categoria": "manutencao",
                            "fichas": dados.get("manutencao") or []}]
    categorias_tratadas = {"proprietarios", "documentacao"}
    for sec in secoes_tecnicas:
        fichas = sec.get("fichas") or []
        if not fichas:
            continue
        categorias_tratadas.add(sec.get("categoria"))
        story.append(_section_title(f"{n:02d} — {sec.get('titulo') or 'Registros Técnicos'}"))
        for m in fichas:
            _render_ficha(story, m)
        n += 1

    # Seção fotográfica — galeria selada por categoria (até a capacidade)
    foto = dados.get("fotografico") or {}
    if foto.get("total"):
        cap = foto.get("capacidade") or ""
        story.append(_section_title(f"{n:02d} — Registro Fotográfico"))
        com_geo = foto.get("com_geo") or 0
        story.append(Paragraph(
            f"{foto['total']} imagem(ns) selada(s) e datada(s)"
            + (f" · capacidade de {cap} por embarcação" if cap else "")
            + (f" · {com_geo} geolocalizada(s)" if com_geo else "")
            + " · cada arquivo com hash SHA-256 imutável.", S["body"]))
        cats = foto.get("categorias") or []
        if cats:
            story.append(_data_table(
                ["CATEGORIA", "IMAGENS"],
                [[c.get("label"), c.get("total")] for c in cats],
                [130 * mm, 46 * mm],
            ))
        n += 1

    # Demais categorias com registro não mapeadas acima (fallback)
    registros = dados.get("registros") or []
    outras = {}
    for r in registros:
        cat = r.get("categoria")
        if cat in categorias_tratadas:
            continue
        outras.setdefault(cat, []).append(r)
    for cat, regs in outras.items():
        titulo = TITULOS_DOSSIE.get(cat, str(cat).replace("_", " ").title())
        story.append(_section_title(f"{n:02d} — {titulo}"))
        for r in regs:
            story.append(Paragraph(f"<b>{r.get('titulo') or 'Registro'}</b>", S["value"]))
            d = r.get("dados") or {}
            # Campos estruturados da ficha (ex.: laudo, seguradora, especificações)
            pares = [
                (k.replace("_", " ").title(), v)
                for k, v in d.items()
                if k not in INTERNAS_DADOS and v not in (None, "", [], {})
            ]
            tinfo = _info_table(pares)
            if tinfo:
                story.append(tinfo)
            # Itens marcados no checklist
            for item in (r.get("checklist") or []):
                story.append(Paragraph(f"&#10003; {item}", S["small"]))
            # Anexos selados (laudos/documentos de terceiros)
            for a in (d.get("arquivos") or []):
                if not isinstance(a, dict):
                    continue
                h = (a.get("hash") or "")[:16]
                story.append(Paragraph(f"&#128274; {a.get('nome') or 'Anexo'} · SHA-256 {h}…", S["small"]))
            if r.get("observacao"):
                story.append(Paragraph(r["observacao"], S["small"]))
            story.append(Spacer(1, 6))
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
