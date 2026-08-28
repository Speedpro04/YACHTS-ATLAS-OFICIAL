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
import logging
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
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

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
# Clareados em 28/08/2026 por reclamação de legibilidade no dossiê impresso.
# Medido em contraste WCAG contra a superfície do documento (#021a3d), que é
# o pior caso dos dois fundos: GOLD_DIM estava em 3,66:1 e WHITE_FAINT em
# 2,88:1 — abaixo do mínimo de 4,5:1 para corpo de texto, e eles carregam
# justamente o texto MIÚDO (5,5 a 7 pt): rótulos de tabela, selo de foto
# (data · GEO · hash) e rodapé. Texto pequeno e apagado ao mesmo tempo é o
# que não se lê. Agora os dois estão em 4,6:1, com o mesmo matiz.
GOLD_DIM    = colors.HexColor("#9e8040")
WHITE       = colors.HexColor("#f0ede6")
WHITE_DIM   = colors.HexColor("#9aa0aa")
WHITE_FAINT = colors.HexColor("#7a8595")
BORDER      = colors.HexColor("#1a2740")

# Status — valores Tailwind exatos do AssetHealthDashboard
EMERALD = colors.HexColor("#10b981")
AMBER   = colors.HexColor("#f59e0b")
ROSE    = colors.HexColor("#f43f5e")
BLUE    = colors.HexColor("#3b82f6")
ZINC    = colors.HexColor("#71717a")

# ─────────────────────────────────────────────────────────────
# FONTES
# ─────────────────────────────────────────────────────────────
# Helvetica e Times-Bold são fontes base-14 do PDF: não exigem arquivo, mas
# só conhecem Latin-1. Fora dele o ReportLab troca o caractere por um QUADRADO
# PRETO — sem erro, sem log. "Dvořák" saía "Dvo■ák" no nome do proprietário,
# num documento selado por SHA-256 que afirma integridade. Medido em
# 28/08/2026, junto com romeno (Ștefan), polonês (Łukasz) e turco (Yıldız).
#
# Arial tem as MESMAS MEDIDAS da Helvetica, e Times New Roman as de Times-Bold:
# a troca não move uma quebra de linha do dossiê. Medido nos textos reais do
# documento: +0,01% de largura no pior caso.
#
# A cadeia existe porque o servidor NÃO é o Windows — em produção o dossiê sai
# de um container Debian (`python:3.11-slim-bookworm`), que instala
# `fonts-liberation` no Dockerfile: mesmas medidas da Arial, licença livre.
# As base-14 ficam como último recurso; se a execução cair nelas o quadrado
# preto volta, e é exatamente por isso que o log abaixo grita em ERROR.
_DIRS_FONTES = (
    r"C:\Windows\Fonts",                          # dev (Windows)
    "/usr/share/fonts/truetype/msttcorefonts",     # Arial, se instalada
    "/usr/share/fonts/truetype/liberation",        # produção (Debian)
    "/usr/share/fonts/truetype/liberation2",
    "/usr/share/fonts/truetype/dejavu",
)

# Ordem de preferência por papel. O nome interno é fixo para que os estilos
# não precisem saber qual arquivo venceu.
_FAMILIAS = {
    "AtlasSans":   (["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf"],
                    "Helvetica"),
    "AtlasSansB":  (["arialbd.ttf", "Arial_Bold.ttf", "LiberationSans-Bold.ttf"],
                    "Helvetica-Bold"),
    "AtlasSerifB": (["timesbd.ttf", "Times_New_Roman_Bold.ttf",
                     "LiberationSerif-Bold.ttf"], "Times-Bold"),
}


def _achar_fonte(nomes):
    for d in _DIRS_FONTES:
        for nome in nomes:
            caminho = os.path.join(d, nome)
            if os.path.exists(caminho):
                return caminho
    return None


def _registrar_fontes():
    """Registra a melhor fonte disponível para cada papel.

    SANS regular e bold são registradas em conjunto: se uma faltar, as duas
    caem para a base-14. Meia troca deixaria o documento com dois desenhos
    de letra diferentes na mesma linha.
    """
    escolhidas, faltando = {}, []
    for papel, (candidatas, base14) in _FAMILIAS.items():
        caminho = _achar_fonte(candidatas)
        if not caminho:
            faltando.append(papel)
            escolhidas[papel] = base14
            continue
        try:
            pdfmetrics.registerFont(TTFont(papel, caminho))
            escolhidas[papel] = papel
        except Exception as e:                      # fonte corrompida, sem permissão
            logger.warning(f"Fonte {caminho} não pôde ser registrada: {e}")
            faltando.append(papel)
            escolhidas[papel] = base14

    # Meia troca no par SANS é pior que troca nenhuma.
    if "AtlasSans" in faltando or "AtlasSansB" in faltando:
        escolhidas["AtlasSans"] = _FAMILIAS["AtlasSans"][1]
        escolhidas["AtlasSansB"] = _FAMILIAS["AtlasSansB"][1]

    if any(escolhidas[p] != p for p in _FAMILIAS):
        logger.error(
            "DOSSIÊ-ATLAS sem fonte Unicode — caindo para as base-14 do PDF. "
            "Nome com caractere fora de Latin-1 (Dvořák, Łukasz, Ștefan) sairá "
            "com QUADRADO PRETO no lugar da letra. Instale `fonts-liberation` "
            "no ambiente. Papéis afetados: "
            + ", ".join(p for p in _FAMILIAS if escolhidas[p] != p))
    return escolhidas


_FONTES = _registrar_fontes()
SERIF  = _FONTES["AtlasSerifB"]   # espelha font-serif do painel nos números grandes
SANS   = _FONTES["AtlasSans"]
SANS_B = _FONTES["AtlasSansB"]


def _glifos_ausentes(texto, fonte):
    """Caracteres que a fonte NÃO desenha — viram quadrado preto no PDF."""
    try:
        mapa = pdfmetrics.getFont(fonte).face.charToGlyph
    except Exception:
        # base-14 não expõe charToGlyph: o critério lá é caber em Latin-1.
        return {c for c in texto
                if c.encode("cp1252", errors="replace") == b"?"}
    return {c for c in texto if ord(c) > 127 and ord(c) not in mapa}

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


# Acima desta razão (tracking ÷ corpo da fonte) o extrator de texto do PDF
# desiste de juntar as letras e devolve "P r o t o c o l o Y A - I A T E".
# Medido em 28/08/2026 nos quatro tamanhos usados no dossiê — o ponto de
# ruptura ficou em 0,151 / 0,164 / 0,154 / 0,158. 0.14 fica abaixo dos quatro.
#
# Não é preciosismo tipográfico: no dossiê emitido do Ferretti 780, o rodapé
# saía "C N P J 2 6 . 9 9 8 . 5 7 1 / 0 0 0 1 - 5 0" e o cabeçalho
# "Y A - I A T E", que lido corrido vira "YA HATE" — foi assim que um
# revisor externo relatou "CNPJ divergente" e "protocolo corrompido" num
# documento que estava impresso corretamente.
#
# Quem depende disto: o comprador que COPIA o protocolo para colar na página
# de verificação, o Ctrl+F dentro do PDF, o leitor de tela e qualquer
# sistema de corretora ou seguradora que processe o arquivo.
TRACKING_MAX_RATIO = 0.14


def draw_tracked(c, x, y, text, font, size, color, tracking=0.0, align="left",
                 decorativo=False):
    """Texto com letter-spacing no canvas (Canvas não tem setCharSpace).

    `decorativo=True` libera o tracking cheio — só para texto que NÃO é dado:
    a marca e a assinatura da capa, que ninguém copia e que ninguém busca.
    Todo o resto é aparado ao teto para continuar copiável.
    """
    if not decorativo:
        tracking = min(tracking, size * TRACKING_MAX_RATIO)
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
    # Corpo do dossiê: +1pt em cada estilo e entrelinha em ~1,6x o tamanho da
    # fonte (antes ficava em ~1,45x). O documento é lido impresso e por
    # comprador, corretor e perito — não por quem já conhece o conteúdo. Texto
    # apertado num PDF de 19 páginas cansa antes da metade, e o que se perde é
    # justamente a leitura das seções técnicas, que é onde está o valor.
    "label":   ParagraphStyle("label", fontName=SANS, fontSize=7, textColor=GOLD_DIM, leading=11),
    "value":   ParagraphStyle("value", fontName=SANS_B, fontSize=10, textColor=WHITE, leading=15),
    "body":    ParagraphStyle("body", fontName=SANS, fontSize=9.5, textColor=WHITE_DIM, leading=15),
    "body_j":  ParagraphStyle("body_j", fontName=SANS, fontSize=8.8, textColor=WHITE_DIM,
                              leading=14, alignment=TA_JUSTIFY),
    "small":   ParagraphStyle("small", fontName=SANS, fontSize=7.8, textColor=WHITE_FAINT, leading=12),
    "kpi_num": ParagraphStyle("kpi_num", fontName=SERIF, fontSize=19, textColor=WHITE, leading=22),
    "kpi_lbl": ParagraphStyle("kpi_lbl", fontName=SANS_B, fontSize=6.5, textColor=GOLD_DIM, leading=9.5),
    "card":    ParagraphStyle("card", fontName=SANS_B, fontSize=10.5, textColor=WHITE, leading=15),
}


# ─────────────────────────────────────────────────────────────
# FLOWABLES
# ─────────────────────────────────────────────────────────────
class GaugeBar(Flowable):
    """Barra do Índice de Custódia. UMA só, e de propósito.

    Mostra SEMPRE o denominador — "3 de 8 sistemas avaliados" — logo abaixo da
    barra. Sem ele, um Netuno II com três sistemas conformes e cinco NÃO
    AVALIADOS exibia "ÍNDICE DE SEGURANÇA 100%" com a barra verde cheia,
    ao lado de um selo BRONZE. O número está certo pela própria definição
    (média do que foi avaliado), mas quem lê entende "este barco está 100%".

    Aqui existe barra só para a COBERTURA, que varia de barco para barco.
    A conformidade sai como número e frase (`_conformidade_texto`): ela é
    quase sempre 100% e uma linha cheia de ponta a ponta afirma "completo"
    antes de qualquer legenda ser lida — forma vence cor, e o leitor típico é
    o comprador olhando no celular, com pressa. Tentou-se antes deixá-la fina
    e em dourado apagado; não bastou. Não devolver a barra para cá.

    É a mesma armadilha que motivou renomear "Classificação" para "Índice de
    Custódia": o número dizia uma coisa e era lido como outra. Percentual sem
    denominador promete mais do que mediu.
    """

    def __init__(self, pct, rotulo, legenda=None, width=176 * mm):
        super().__init__()
        self.pct, self.width = pct, width
        self.rotulo, self.legenda = rotulo, legenda

    def wrap(self, aw, ah):
        return self.width, (10 * mm if self.legenda else 7 * mm)

    def draw(self):
        c = self.canv
        # Fina de propósito: barra grossa rouba atenção do texto que explica
        # o número, e é o texto que sustenta o número.
        bar_h = 1.5
        col = EMERALD if self.pct >= 80 else (AMBER if self.pct >= 50 else ROSE)
        # A LINHA sai suavizada contra o fundo; o RÓTULO fica na cor cheia.
        # A linha é indicativa, não alarme — em cor sólida ela puxava o olho
        # antes do número e do texto que o explica. Já a letra precisa de
        # contraste para ser lida, então não pode levar a mesma suavização.
        col_linha = blend(col, NAVY, 0.72)
        base = 3 * mm if self.legenda else 0
        c.saveState()
        if self.legenda:
            draw_tracked(c, 0, 0, self.legenda, SANS_B, 5.5, WHITE_DIM, tracking=1.0)
        c.setFillColor(blend(WHITE, NAVY, 0.05))
        c.setStrokeColor(blend(WHITE, NAVY, 0.10))
        c.setLineWidth(0.4)
        c.roundRect(0, base, self.width, bar_h, bar_h / 2, fill=1, stroke=1)
        c.setFillColor(col_linha)
        c.roundRect(0, base, self.width * self.pct / 100.0, bar_h, bar_h / 2, fill=1, stroke=0)
        draw_tracked(c, 0, base + bar_h + 2.4 * mm, self.rotulo, SANS_B,
                     6, col, tracking=1.2)
        c.setFont(SERIF, 13)
        c.setFillColor(WHITE)
        c.drawRightString(self.width, base + bar_h + 2.0 * mm, f"{self.pct}%")
        c.restoreState()


def _conformidade_texto(pct, avaliados, total):
    """Conformidade sem barra: rótulo, número e a frase que o qualifica.

    Ver GaugeBar — barra cheia aqui era lida como "barco completo" mesmo com a
    maioria dos sistemas sem registro. Sem forma cheia não há o que ler errado,
    e o denominador vira texto em vez de legenda de 5,5pt.

    A frase NÃO afirma conformidade: diz sobre quantos sistemas o percentual
    foi calculado. Vale para 100% e para 40% igualmente — frase que só serve
    para o caso bom é a armadilha de novo, por outro caminho.
    """
    def plural(n, sing, plur):
        return f"{n} {sing if n == 1 else plur}"

    linha = Table(
        [[Paragraph(track("CONFORMIDADE"), ParagraphStyle(
            "cfl", fontName=SANS_B, fontSize=6, textColor=GOLD_LIGHT, leading=9)),
          Paragraph(f"{pct}%", ParagraphStyle(
              "cfn", fontName=SERIF, fontSize=11, textColor=WHITE_DIM, leading=14,
              alignment=TA_RIGHT))]],
        colWidths=[130 * mm, 46 * mm])
    linha.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))

    if avaliados and total and total > avaliados:
        faltam = total - avaliados
        frase = (f"Calculado sobre {avaliados} de {total} sistemas — "
                 f"{plural(faltam, 'sistema sem registro não entra', 'sistemas sem registro não entram')} "
                 "na conta.")
    elif avaliados and total:
        frase = f"Calculado sobre os {total} sistemas aplicáveis, todos com registro."
    else:
        frase = "Calculado apenas sobre os sistemas com registro selado."

    return [linha, Paragraph(frase, S["small"])]


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


def _pluralizar(n, singular, plural):
    """"1 dias" e "1 MESES" já custaram caro a este documento — o segundo saiu
    num dossiê real. Número e substantivo andam juntos, sempre."""
    return f"{n} {singular if abs(n) == 1 else plural}"


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


def _como_ler_indice():
    """Publica o critério de Cobertura e Conformidade dentro do documento.

    O dossiê estampava CONFORME / ATENÇÃO / CRÍTICO / NÃO AVALIADO em caixas
    coloridas e um percentual ao lado, e em nenhum lugar dizia como aquilo foi
    decidido. A regra existe em `dossie_data._saude_por_categoria` e é boa —
    mas só vivia no código, onde quem lê o PDF não alcança.

    Critério invisível é opinião; critério publicado é metodologia. É o que
    permite à marina defender o número quando o comprador contestar, em vez de
    ter que ligar para a plataforma e explicar de memória.

    ESTE TEXTO ESPELHA `dossie_data._saude_por_categoria` E `_prontidao`.
    Mexeu na regra lá, corrige aqui — critério publicado errado é pior do que
    critério não publicado.
    """
    st = [_section_title("Como Ler Cobertura e Conformidade", indexar=False)]
    st.append(Paragraph(
        "<b>Cobertura de Verificação</b> e <b>Conformidade</b>, na primeira página, resumem o "
        "estado dos sistemas da embarcação a partir <b>exclusivamente</b> dos registros selados "
        "neste Dossiê. Não são vistoria, laudo pericial nem avaliação de valor de mercado: medem "
        "o que foi registrado e verificado, não o que existe a bordo.", S["body_j"]))
    st.append(sp(4))
    st.append(Paragraph(
        "<b>Não confundir com o selo <i>Índice de Custódia</i></b>, na capa (Bronze, Silver, "
        "Gold). Aquele mede outra coisa: <b>quanto</b> da embarcação está documentado — "
        "abrangência das categorias com registro, volume de manutenção, documentos e presença "
        "de laudo de casco. Ele descreve o trabalho de custódia da marina; os dois indicadores "
        "abaixo descrevem o estado do que foi registrado. São perguntas diferentes e podem "
        "divergir: uma embarcação bem documentada com avaria em aberto tem selo alto e "
        "conformidade baixa.", S["body_j"]))
    st.append(sp(4))
    st.append(_data_table(
        ["Estado", "O que significa", "Peso"],
        [["CONFORME", "Todos os registros da categoria estão concluídos, sem "
                      "pendência ou ressalva.", "100"],
         ["ATENÇÃO", "Há registro pendente ou com ressalva técnica na categoria.", "50"],
         ["CRÍTICO", "Há ressalva em categoria de risco direto à segurança "
                     "(ver agravamento, abaixo).", "0"],
         ["NÃO AVALIADO", "A categoria não possui nenhum registro selado.",
          "fora da média"]],
        [30 * mm, 116 * mm, 30 * mm]))
    st.append(sp(5))
    st.append(Paragraph(
        "<b>Cálculo.</b> O Índice é a média aritmética dos pesos das categorias avaliadas. "
        "Categoria sem registro não entra na conta — não soma nem penaliza. Por isso o Índice "
        "deve ser lido sempre junto da <b>Cobertura de Verificação</b>, que informa quantas "
        "categorias possuem registro: um índice alto sobre poucas categorias avaliadas descreve "
        "uma amostra pequena, não uma embarcação em ordem.", S["body_j"]))
    st.append(sp(4))
    st.append(Paragraph(
        "<b>Agravamento para CRÍTICO.</b> Ressalva em <b>Casco</b> ou <b>Sinistros</b> não é "
        "meio-termo: casco avariado e sinistro em aberto valem zero, não cinquenta. Em "
        "<b>Segurança</b>, ressalva acompanhada de EPIRB com homologação ANATEL pendente recebe "
        "o mesmo tratamento — sem homologação válida, o sinal de socorro não é atendido.",
        S["body_j"]))
    st.append(sp(4))
    st.append(Paragraph(
        "<b>Categorias que não se aplicam.</b> A lista varia conforme o tipo de embarcação: "
        "veleiro registra em Velame &amp; Rigging no lugar de Motor; embarcação a motor não "
        "possui Velame. Categoria que não existe no tipo não é exibida nem contabilizada, para "
        "não figurar como lacuna permanente.", S["body_j"]))
    st.append(sp(4))
    st.append(Paragraph(
        "<b>Retificações.</b> Registro retificado sai das métricas: quem vale é a correção. "
        "O registro original permanece visível no Dossiê, ao lado dela.", S["body_j"]))
    return st


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


# Fotos: quanto cada imagem ocupa e com que resolução entra no PDF.
#
# 3 colunas de 56mm cabem na largura útil. A 150 dpi isso pede ~330px; usamos
# 520 para o zoom da tela não estourar em pixel. Capacidade é de 430 fotos por
# embarcação e TODAS entram — o controle de tamanho é a compressão, não o
# corte: um dossiê que fala das fotos e não as mostra é o defeito que isto veio
# consertar.
FOTO_COLS = 3
FOTO_LARGURA_MM = 56

# Proporção fixa das celas da galeria (4:3).
#
# Antes cada foto entrava com a altura que tinha. Uma imagem em retrato no
# meio da linha empurrava as vizinhas e abria um buraco: nas páginas 15 e 16
# do dossiê do Ferretti 780 sobrava de um terço a 40% de página em branco, e
# as legendas de uma mesma linha ficavam em alturas diferentes.
#
# A imagem é encaixada INTEIRA na cela (contain), centralizada sobre o fundo
# do documento — nunca recortada. Num dossiê de custódia a foto é evidência:
# cortar para preencher pode cortar justamente a avaria que ela registra.
FOTO_AR = 4 / 3
FOTO_PX_MAX = 520
# Cor do letterbox da galeria: a mesma superfície do documento, para a faixa
# não aparecer como moldura em volta da foto.
FOTO_FUNDO_RGB = (int(SURFACE.red * 255), int(SURFACE.green * 255),
                  int(SURFACE.blue * 255))
FOTO_JPEG_Q = 72
FOTO_TIMEOUT = 12.0


# Cache das fotos já baixadas nesta emissão.
#
# gerar_pdf_dossie monta o documento DUAS vezes — a 1ª para descobrir em que
# página cai cada seção, a 2ª para escrever o índice com os números reais. Sem
# cache, cada foto é baixada duas vezes: com 430 fotos seriam 860 downloads, e
# a primeira medição já custou 102 s com apenas 8.
_CACHE_FOTOS: dict = {}


def _prefetch_fotos(urls: list[str]) -> None:
    """Baixa as fotos em paralelo antes de montar o documento.

    Sequencial, o tempo é a soma das latências; em paralelo, é a da mais lenta.
    O limite de 8 é para não abrir centenas de conexões contra o Storage e
    virar o problema que se queria resolver.
    """
    pendentes = [u for u in dict.fromkeys(urls) if u not in _CACHE_FOTOS]
    if not pendentes:
        return
    from concurrent.futures import ThreadPoolExecutor
    import httpx

    # UM cliente para todos os downloads. Medido: abrindo conexão nova a cada
    # foto, um arquivo de 11 KB levava os mesmos 4,7 s que um de 803 KB — o
    # custo era o aperto de mão TLS, não o tamanho. Reaproveitando a conexão,
    # esse custo é pago uma vez só.
    limites = httpx.Limits(max_connections=8, max_keepalive_connections=8)
    with httpx.Client(timeout=FOTO_TIMEOUT, follow_redirects=True,
                      limits=limites) as cliente:
        with ThreadPoolExecutor(max_workers=8) as pool:
            resultados = pool.map(lambda u: _baixar_foto_sem_cache(u, cliente), pendentes)
            for url, resultado in zip(pendentes, resultados):
                _CACHE_FOTOS[url] = resultado


def _baixar_foto(url: str):
    """Versão com cache — é esta que o renderizador usa."""
    if url not in _CACHE_FOTOS:
        _CACHE_FOTOS[url] = _baixar_foto_sem_cache(url)
    guardado = _CACHE_FOTOS[url]
    if guardado is None:
        return None
    # BytesIO é consumido na leitura: a 2ª passada receberia um buffer no fim
    # do arquivo e a imagem sairia vazia. Rebobinar é obrigatório.
    buf, tam = guardado
    buf.seek(0)
    return buf, tam


def _encaixar(img, _novo):
    """Encaixa a imagem numa cela 4:3 sem recortar (contain), sobre o fundo
    do documento. Ver FOTO_AR: uniformiza a grade sem sacrificar evidência."""
    lw, lh = img.size
    if lh <= 0 or lw <= 0:
        return img
    alvo_w = max(lw, int(round(lh * FOTO_AR)))
    alvo_h = max(lh, int(round(lw / FOTO_AR)))
    if (alvo_w, alvo_h) == (lw, lh):
        return img
    fundo = _novo("RGB", (alvo_w, alvo_h), FOTO_FUNDO_RGB)
    fundo.paste(img, ((alvo_w - lw) // 2, (alvo_h - lh) // 2))
    return fundo


def _baixar_foto_sem_cache(url: str, cliente=None):
    """Baixa e reduz uma foto. Devolve None se não der — nunca levanta.

    Best-effort por necessidade: o dossiê tem que sair mesmo com uma imagem
    fora do ar. Uma foto faltando é uma lacuna visível; uma exceção aqui é o
    dossiê inteiro que não é emitido.
    """
    try:
        import httpx
        from PIL import Image
        if cliente is not None:
            r = cliente.get(url)
        else:
            r = httpx.get(url, timeout=FOTO_TIMEOUT, follow_redirects=True)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        # webp e png com alfa não sobrevivem ao JPEG sem fundo: achatamos sobre
        # branco em vez de deixar o alfa virar preto.
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            fundo = Image.new("RGB", img.size, (255, 255, 255))
            fundo.paste(img, mask=img.split()[-1])
            img = fundo
        else:
            img = img.convert("RGB")
        img.thumbnail((FOTO_PX_MAX, FOTO_PX_MAX), Image.LANCZOS)
        img = _encaixar(img, Image.new)
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=FOTO_JPEG_Q, optimize=True)
        buf.seek(0)
        return buf, img.size
    except Exception as e:
        logger.warning(f"Foto do dossiê não pôde ser embutida ({url[:60]}...): {e}")
        return None


def _celula_foto(foto: dict, larg_mm: float):
    """Uma foto com a legenda que a torna prova, e não ilustração."""
    baixada = _baixar_foto(foto["url"])
    larg = larg_mm * mm
    if not baixada:
        # Lacuna honesta: diz que a foto existe e está selada, e que só a
        # imagem não pôde ser embutida agora.
        corpo = Paragraph("Imagem indisponível no momento da emissão — "
                          "registro selado permanece íntegro.", S["small"])
    else:
        buf, (pw, ph) = baixada
        alt = larg * (ph / pw)
        corpo = RLImage(buf, width=larg, height=alt)

    # "SELADO EM", não a data nua.
    #
    # A data é `uploaded_at` — o relógio do servidor quando a marina enviou o
    # arquivo — e vinha impressa ao lado de GEO e do hash. Lado a lado, o
    # leitor entende as três como propriedades da FOTO: quando foi tirada,
    # onde, e o selo. Só que GEO foi consertado em 26/08 e passou a sair do
    # EXIF da imagem, e a data não: uma foto do casco tirada em 2019 e enviada
    # hoje saía "2026-08-26", num documento cujo argumento é justamente provar
    # a condição do ativo ao longo do tempo. Metade do par foi corrigida e a
    # outra metade ficou prometendo o mesmo.
    #
    # Ler a data de captura do EXIF exige coluna nova e backfill — está em
    # Pendências. Até lá o rótulo diz o que o dado é, em vez de deixá-lo
    # passar por outra coisa.
    _d = foto.get("data")
    if _d and len(_d) == 10 and _d[4] == "-":
        _d = "SELADO EM " + "/".join(reversed(_d.split("-")))
    elif _d:
        _d = "SELADO EM " + _d
    selo = " · ".join(x for x in [
        _d,
        "GEO" if foto.get("geo") else None,
        foto.get("hash"),
    ] if x)
    linhas = [[corpo], [Paragraph(track(str(foto.get("label", "")).upper()), S["label"])]]
    if selo:
        linhas.append([Paragraph(selo, ParagraphStyle(
            "fotosel", fontName="Courier", fontSize=6.2, textColor=WHITE_FAINT, leading=9))])
    if foto.get("descricao"):
        linhas.append([Paragraph(str(foto["descricao"]), S["small"])])

    t = Table(linhas, colWidths=[larg])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, 0), 0), ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING", (0, 1), (-1, -1), 1), ("BOTTOMPADDING", (0, 1), (-1, -1), 1),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def _galeria_de_imagens(fotos: list[dict]):
    """Todas as fotos numa grade de 3 colunas, agrupadas por categoria.

    Antes desta seção existir, uma grade de molduras vazias (`_grade_fotos`)
    ocupava este espaço: um retângulo azul de 24 mm por categoria, com selo em
    cima e rótulo embaixo, e NADA no meio. Fazia sentido enquanto o PDF ainda
    não mostrava imagem nenhuma — era um lugar reservado. Depois que as fotos
    passaram a sair de verdade, virou um terço de página de caixa vazia
    repetindo o que a tabela de contagem, no fim da seção, já diz melhor.
    Removida em 23/08/2026. O que ela dizia era:
    CONTAGEM por categoria ("Motor / Propulsão · 3"); esta desenha as IMAGENS.
    Os dois nomes quase iguais foram um deslize meu — renomeado para que quem
    mexer aqui depois não troque um pelo outro.

    KeepTogether por LINHA, não pela grade inteira: uma grade de 430 fotos que
    não pode ser quebrada não caberia em página nenhuma e o ReportLab
    desistiria de renderizar.
    """
    if not fotos:
        return []
    saida = []
    for i in range(0, len(fotos), FOTO_COLS):
        bloco = fotos[i:i + FOTO_COLS]
        celulas = [_celula_foto(f, FOTO_LARGURA_MM) for f in bloco]
        while len(celulas) < FOTO_COLS:
            celulas.append("")
        linha = Table([celulas],
                      colWidths=[FOTO_LARGURA_MM * mm + 4 * mm] * FOTO_COLS)
        linha.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        saida.append(KeepTogether(linha))
    return saida


def _credenciais_verificacao(protocolo: str, codigo: str, emitido: str):
    """As três credenciais que a verificação manual exige, lado a lado.

    Existem juntas de propósito. A API pede protocolo, código e data de
    emissão; o card antigo mostrava só o código e mandava "informe o protocolo
    e o código" — o protocolo estava noutro bloco da página e a data nem era
    citada. Quem não conseguisse ler o QR ficava sem os dados para digitar.
    """
    rot = ParagraphStyle("credlabel", fontName=SANS_B, fontSize=5.6,
                         textColor=WHITE_DIM, leading=8)
    val = ParagraphStyle("credvalor", fontName="Courier", fontSize=8.2,
                         textColor=GOLD_LIGHT, leading=11)
    t = Table([
        [Paragraph(track("PROTOCOLO"), rot),
         Paragraph(track("CÓDIGO"), rot),
         Paragraph(track("EMISSÃO"), rot)],
        [Paragraph(protocolo, val), Paragraph(codigo, val), Paragraph(emitido, val)],
    ], colWidths=[52 * mm, 38 * mm, 30 * mm])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 1), ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
        ("VALIGN", (0, 0), (-1, -1), "BOTTOM"),
    ]))
    return t


def _qr(url, size_mm=40):
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(url)
    qr.make(fit=True)
    # Módulos ESCUROS sobre fundo CLARO, como a ISO/IEC 18004 exige.
    #
    # Antes era o inverso (dourado claro sobre o navy da marca), e testado com
    # zxing sobre o PDF real: leitor sem detecção de inversão — ZXing/ZBar
    # padrão, câmera nativa de Android de fabricante, app de vistoria — NÃO
    # lia. iPhone e Google Lens liam. Invertendo, os dois leem.
    #
    # O navy da marca continua presente: ele agora é a cor dos MÓDULOS, o que
    # preserva a identidade e ainda respeita a spec. E isto vai para papel
    # impresso: QR ilegível num dossiê já emitido não tem correção retroativa.
    img = qr.make_image(fill_color="#010c20", back_color="#ffffff").convert("RGB")
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

        # Marca e assinatura: decorativas de propósito — o tracking largo é a
        # identidade da capa, e ninguém copia nem busca por elas.
        draw_tracked(self, x, base, "YACHTS ATLAS", SANS_B, 14 if hero else 9.5,
                     GOLD, tracking=2.2, decorativo=True)
        draw_tracked(self, x, base - (5.2 * mm if hero else 3.6 * mm),
                     "CURADORIA DE ATIVOS NÁUTICOS DE ALTO VALOR",
                     SANS, 6.5 if hero else 5.3, GOLD_DIM, tracking=1.3,
                     decorativo=True)

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

    # Redação LGPD — declarada, nunca silenciosa. O registro técnico permanece
    # íntegro; só o dado pessoal foi removido por direito do titular.
    if m.get("redacao_lgpd"):
        campos = ", ".join(
            str(c).replace("_", " ") for c in (m.get("redigido_campos") or [])
        )
        quando = str(m.get("redigido_em") or "")[:10]
        quando = "/".join(reversed(quando.split("-"))) if quando else ""
        inner.append(Spacer(1, 3))
        inner.append(Paragraph(
            f'<font color="#71717a"><b>Dado pessoal removido a pedido do titular</b></font> '
            f'(LGPD art. 18, VI){f" em {quando}" if quando else ""}'
            f'{f": {campos}" if campos else ""}. '
            f'<i>O registro técnico permanece íntegro e o hash foi recalculado; '
            f'o selo original está preservado para auditoria.</i>', S["small"]))

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
        # "Índice de Custódia", não "Classificação": o número mede abrangência
        # de registro, não a condição da embarcação. Ver Verificacao.tsx.
        #
        # A CAIXA ACOMPANHA O TEXTO, e não o contrário. Era `colWidths=[62*mm]`
        # fixo, e "ÍNDICE DE CUSTÓDIA: SILVER" com tracking passa disso. Como o
        # `track()` usa espaço não-quebrável, o ReportLab não podia quebrar
        # entre as letras — então quebrou DENTRO da palavra: "SILV / ER". Nome
        # de grau partido ao meio, na primeira página do documento que o
        # comprador recebe.
        #
        # O grau sai 2pt maior que o rótulo: é ele que se procura na página.
        FONTE_ROTULO, FONTE_GRAU = 7, 9
        rotulo = track("ÍNDICE DE CUSTÓDIA: ")
        grau = track(str(classif))
        texto_badge = (
            f'{rotulo}<font size="{FONTE_GRAU}">{grau}</font>'
        )
        largura = (
            stringWidth(rotulo, SANS_B, FONTE_ROTULO)
            + stringWidth(grau, SANS_B, FONTE_GRAU)
            + 24  # padding (10+10) e uma folga, em pontos
        )
        badge = Table([[Paragraph(texto_badge, ParagraphStyle(
            "cg", fontName=SANS_B, fontSize=FONTE_ROTULO, textColor=GOLD_LIGHT,
            leading=FONTE_GRAU + 4))]],
            colWidths=[min(largura, 150 * mm)], hAlign="LEFT")
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
        # "Investido" é gasto em manutenção e reparo; "Cobertura" é o valor
        # segurado. Ficavam somados no mesmo tile, e a capa anunciava R$ 2,5 mi
        # investidos num barco cujo gasto real foi R$ 89,3 mil — 27 vezes mais.
        # Duas coisas diferentes, dois tiles.
        (r.get("investido"), "Investido no ativo", GOLD),
        (r.get("cobertura"), "Cobertura segurada", WHITE),
        # A primeira conta que um comprador faz. O dado sempre esteve aqui.
        (r.get("custo_mensal"), "Custo médio / mês", WHITE),
        (r.get("registros"), "Registros selados", WHITE),
        # Conta SÓ documentos. Antes era a tabela `documentos` inteira, com as
        # fotos dentro: a capa dizia 28 e a seção listava 10.
        (r.get("documentos"), "Documentos selados", WHITE),
        # Valor e rótulo vêm juntos de dossie_data: "12 · Dias em custódia" ou
        # "3 · Meses de custódia". O rótulo era fixo no plural e saía "1 MESES"
        # num barco com um dia de custódia.
        (r.get("custodia_valor"), r.get("custodia_rotulo") or "Tempo em custódia", WHITE),
    ]
    tiles = [(n, l, c) for n, l, c in tiles if n]
    if tiles:
        st.append(Paragraph("O ATIVO EM NÚMEROS", S["h2"]))
        st.append(sp(3))
        st.append(_kpi_row(tiles))
        st.append(sp(6))

    # UMA barra, e a ORDEM é deliberada.
    #
    # Cobertura tem barra porque é ela que varia — e é a primeira coisa em que
    # o olho pousa que ancora o julgamento. Uma barra verde de 100% no topo
    # faria o leitor concluir "está tudo bem" antes de processar qualquer
    # texto, e só depois descobrir que sete sistemas nunca foram olhados.
    #
    # Conformidade vem embaixo SEM barra: ela é quase sempre 100% (só entra na
    # conta o que tem registro), e uma linha cheia de ponta a ponta afirmava
    # "completo" com força maior do que a legenda que a desmentia.
    pront = dados.get("prontidao")
    avaliados = dados.get("prontidao_avaliados")
    total = dados.get("prontidao_total")
    if pront is not None:
        if avaliados is not None and total:
            cobertura = round(avaliados / total * 100)
            st.append(GaugeBar(
                cobertura, "COBERTURA DE VERIFICAÇÃO",
                legenda=f"{avaliados} DE {total} SISTEMAS COM REGISTRO"))
            st.append(sp(7))
        st.extend(_conformidade_texto(pront, avaliados, total))
        st.append(sp(11))

    saude = dados.get("saude") or []
    if any(s != "na" for _, s in saude):
        st.append(Paragraph("PRONTIDÃO OPERACIONAL POR SISTEMA", S["h2"]))
        st.append(sp(3))
        st.append(_health_grid(saude))
        # O critério não pode morar só na seção do fim: o comprador que olha
        # esta grade no celular não vai à página 12 procurar a metodologia.
        st.append(sp(2))
        st.append(Paragraph(
            "Conforme = 100 · Atenção = 50 · Crítico = 0. Categoria sem registro fica fora "
            "da média. Critério completo em “Como Ler Cobertura e Conformidade”, ao final.",
            S["small"]))

    return st


# ─────────────────────────────────────────────────────────────
# GERADOR
# ─────────────────────────────────────────────────────────────
def _avisar_glifos(dados, _limite=40):
    """Avisa ANTES de emitir se algum texto tem caractere que a fonte não
    desenha — emoji, por exemplo, que nenhuma fonte de texto cobre.

    Não bloqueia a emissão: quem decide se o dossiê sai é a marina, não o
    gerador. Mas o operador precisa saber que aquele nome vai imprimir com um
    quadrado no meio, em vez de descobrir pelo comprador.
    """
    achados, vistos = set(), 0

    def varrer(v):
        nonlocal vistos
        if vistos > 4000 or len(achados) >= _limite:
            return
        if isinstance(v, str):
            vistos += 1
            achados.update(_glifos_ausentes(v, SANS))
        elif isinstance(v, dict):
            for x in v.values():
                varrer(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                varrer(x)

    try:
        varrer(dados)
    except Exception:                      # aviso nunca derruba a emissão
        return
    if achados:
        logger.warning(
            "DOSSIÊ-ATLAS: %d caractere(s) sem glifo na fonte %s sairão como "
            "quadrado no PDF: %s", len(achados), SANS,
            " ".join(sorted(achados)))


def gerar_pdf_dossie(dados: dict) -> bytes:
    """Gera o PDF do dossiê. Duas passadas: a 1ª mede em que página cada seção
    cai, a 2ª monta o índice com os números reais."""
    _CACHE_FOTOS.clear()
    _avisar_glifos(dados)
    _prefetch_fotos([f["url"] for f in (dados.get("fotografico") or {}).get("fotos") or []])
    try:
        mapa = _montar(dados, indice=None).mapa_secoes
        doc = _montar(dados, indice=mapa)
        return doc._buffer.getvalue()
    finally:
        # As imagens já estão dentro do PDF; segurá-las na memória depois disso
        # é vazamento — 430 fotos por emissão, em servidor de container.
        _CACHE_FOTOS.clear()


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
        # "Atual" prometia a leitura mais recente de um horímetro único; a
        # embarcação tem vários (motores e geradores). Com mais de uma leitura
        # o rótulo diz isso em vez de escolher uma e chamá-la de a do barco.
        (r.get("horimetro"),
         "Horímetro · última leitura" if (r.get("horimetro_leituras") or 0) > 1
         else "Horímetro", WHITE),
        (r.get("pendencias") if r.get("pendencias") else None, "Pendências abertas", AMBER),
        # "Hashes íntegros" prometia conferência; o número mede quantos
        # registros têm selo gravado. O rótulo agora diz o que a conta faz.
        (r.get("integridade"), "Registros com selo", EMERALD),
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

        # Titular da custódia. O dossiê dizia quem CUSTODIA (a marina, na capa)
        # e nunca de quem é o barco — num documento cujo leitor é comprador,
        # corretor e seguradora, é a primeira pergunta que se faz.
        #
        # Nome e documento MASCARADO, e nada de contato: e-mail e telefone são
        # chave de acesso ao Portal, e este PDF circula. O comprador precisa
        # saber de quem é o barco, não como ligar para o dono — o contato passa
        # pela marina, que é o modelo do negócio.
        titular = dados.get("titular") or {}
        tt = _info_grid([
            ("Titular", titular.get("nome")),
            ("CPF / CNPJ", titular.get("documento")),
        ], cols=3)
        if tt:
            story.append(sp(5))
            story.append(Paragraph(track("TITULAR DA CUSTÓDIA"), S["label"]))
            story.append(sp(2))
            story.append(tt)

        # Especificações e motorização — dez colunas que existiam no banco e
        # nunca chegavam ao documento. É a primeira coisa que uma seguradora
        # confere (material do casco, motorização) e que um comprador precisa
        # saber (boca para a vaga, calado para o canal, quantos passageiros).
        # Um dossiê de "conformidade náutica" que não diz a boca do barco está
        # incompleto.
        esp = dados.get("especificacoes") or {}
        te = _info_grid([
            ("Comprimento", esp.get("comprimento")), ("Boca", esp.get("boca")),
            ("Calado", esp.get("calado")), ("Casco", esp.get("material_casco")),
            ("Passageiros", esp.get("passageiros")), ("Cabines", esp.get("cabines")),
            ("Tanque", esp.get("tanque")),
        ], cols=3)
        if te:
            story.append(sp(5))
            story.append(Paragraph(track("ESPECIFICAÇÕES TÉCNICAS"), S["label"]))
            story.append(sp(2))
            story.append(te)

        mot = dados.get("motorizacao_ficha") or {}
        tm = _info_grid([
            ("Modelo", mot.get("modelo")), ("Potência", mot.get("potencia")),
            ("Nº de motores", mot.get("quantidade")),
            ("Combustível", mot.get("combustivel")),
        ], cols=3)
        if tm:
            story.append(sp(5))
            story.append(Paragraph(track("MOTORIZAÇÃO"), S["label"]))
            story.append(sp(2))
            story.append(tm)
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

    # Comprovação Fiscal e Documental — os documentos selados, um a um.
    #
    # Sem esta seção, a capa afirmava um valor investido e o dossiê não exibia
    # um comprovante sequer: as notas fiscais estavam no cofre desde sempre
    # ("Nota Fiscal (NFS-e) — Pintura de Fundo" etc.) e nunca chegavam ao
    # documento. É o que separa "custou R$ 48 mil" de "custou R$ 48 mil, aqui
    # está a nota, e este é o hash que prova que ela não mudou".
    comprov = dados.get("comprovacao") or []
    if comprov:
        story.append(_section_title(f"{n:02d} — Comprovação Fiscal e Documental"))
        story.append(Paragraph(
            f"{len(comprov)} documento(s) selado(s) com hash SHA-256 no momento do "
            "envio. Notas fiscais, laudos, certificados e apólices que sustentam "
            "os valores e serviços declarados neste dossiê. O arquivo original "
            "permanece no cofre digital, acessível ao proprietário e à marina "
            "custodiante.", S["body"]))
        story.append(sp(4))
        story.append(_data_table(
            ["Categoria", "Documento", "Data", "Hash SHA-256"],
            [[c["categoria"], c["descricao"], c["data"], c["hash"]] for c in comprov],
            [30 * mm, 86 * mm, 22 * mm, 30 * mm],
        ))
        n += 1

    # Perfil de Manutenção — preventiva × corretiva.
    #
    # `natureza_manutencao` é campo obrigatório na ficha e nunca aparecia no
    # documento. É o dado de risco mais forte que a plataforma coleta: barco
    # com manutenção programada é outro risco (e outro preço de apólice) que
    # barco que só conserta depois da falha.
    perfil = dados.get("perfil_manutencao") or {}
    if perfil.get("total"):
        story.append(_section_title(f"{n:02d} — Perfil de Manutenção"))
        pct = perfil.get("pct_preventiva")
        story.append(Paragraph(
            f"<b>{pct}%</b> dos serviços classificados são de natureza "
            "<b>preditiva/preventiva</b> — executados por programação, não por "
            "falha. Manutenção programada é o indicador que seguradoras usam "
            "para precificar risco, e que compradores usam para estimar o que "
            "vão gastar.", S["body"]))
        story.append(sp(4))
        story.append(_data_table(
            ["Natureza", "Serviços", "Valor"],
            [["Preditiva / Preventiva (programada)", perfil.get("preventiva"),
              perfil.get("valor_preventiva_fmt") or "—"],
             ["Corretiva (reparo / falha)", perfil.get("corretiva"),
              perfil.get("valor_corretiva_fmt") or "—"]],
            [96 * mm, 34 * mm, 38 * mm],
        ))
        n += 1

    # Vencimentos & Conformidade.
    #
    # Cinco datas ficavam seladas no JSONB e nenhuma chegava ao documento. É a
    # resposta para "o que vou ter que renovar?" — pergunta que decide quem
    # paga o quê numa negociação — e o que a seguradora confere antes de
    # emitir apólice.
    venc = dados.get("vencimentos") or []
    if venc:
        story.append(_section_title(f"{n:02d} — Vencimentos & Conformidade"))
        alertas = [v for v in venc if v["situacao"] in ("vencido", "a_vencer")]
        if alertas:
            story.append(Paragraph(
                f"<b>{_pluralizar(len(alertas), 'item vencido', 'itens vencidos')}</b> "
                "ou a vencer nos próximos 90 dias. Datas conferidas contra os "
                "registros selados na data de emissão deste dossiê.", S["body"]))
        else:
            story.append(Paragraph(
                "Nenhum item vencido ou a vencer nos próximos 90 dias. Datas "
                "conferidas contra os registros selados.", S["body"]))
        # A tabela guarda UMA data por campo, a mais recente — correto para
        # reinspeção do mesmo objeto. Mas o mesmo campo serve seis extintores e
        # a habilitação de vários condutores: o que foi substituído E estava
        # vencido é dito aqui, para a omissão não passar por "em dia".
        _omitidos = sum(v.get("omitidos_vencidos") or 0 for v in venc)
        if _omitidos:
            story.append(_alert(
                "warn", "Leituras vencidas não listadas:",
                f"{_pluralizar(_omitidos, 'outra leitura vencida foi substituída', 'outras leituras vencidas foram substituídas')} "
                "por uma posterior no mesmo campo. Um mesmo campo cobre vários "
                "itens (extintores, habilitação de condutores diferentes): a "
                "tabela mostra a data mais recente de cada um."))
        story.append(sp(4))
        story.append(_data_table(
            ["Item", "Vence em", "Prazo", "Situação"],
            [[v["item"], v["vence_em"],
              (_pluralizar(v["dias"], "dia", "dias") if v["dias"] >= 0
               else "vencido há " + _pluralizar(abs(v["dias"]), "dia", "dias")),
              {"vencido": "VENCIDO", "a_vencer": "A VENCER",
               "em_dia": "Em dia"}[v["situacao"]]]
             for v in venc],
            [66 * mm, 30 * mm, 40 * mm, 32 * mm],
        ))
        n += 1

    story.append(PageBreak())

    # ── Seções técnicas: uma página cada, fichas em cartão ──
    secoes_tecnicas = dados.get("secoes_tecnicas")
    if secoes_tecnicas is None:
        secoes_tecnicas = [{"titulo": "Histórico de Manutenção", "categoria": "manutencao",
                            "fichas": dados.get("manutencao") or []}]
    # `documentacao` NÃO entra aqui de saída.
    #
    # A seção "Documentação Legal e Fiscal" imprime apenas os itens de
    # `checklist` (dossie_data: `documentacao.extend(r.get("checklist"))`) —
    # nunca o título, os dados, a observação ou as evidências do registro. Com
    # "documentacao" nesta lista, o laço de "Demais categorias" também pulava
    # esses registros, e um registro de documentação SEM checklist marcado
    # desaparecia por inteiro do corpo do dossiê — continuando a contar no tile
    # "Registros selados" da capa. No Ferretti 780 a capa prometia 13 e o corpo
    # detalhava 12: o que faltava era "Renovação do Título de Inscrição",
    # justamente um documento da Capitania.
    #
    # Agora só é considerado tratado o registro que de fato contribuiu com
    # checklist; o resto cai no fallback e aparece.
    categorias_tratadas = {"proprietarios"}

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
            # A contagem por categoria vem ANTES das imagens: resumo primeiro,
            # detalhe depois. Estava no fim da seção, atrás de uma grade de
            # molduras vazias; tirada a grade, ela sobrava sozinha numa página
            # inteira só para si.
            story.append(sp(4))
            story.append(_data_table(["Categoria", "Imagens"],
                                     [[c.get("label"), c.get("total")] for c in cats],
                                     [130 * mm, 46 * mm]))

        # As imagens em si. Antes esta seção terminava na tabela de contagem
        # acima: o dossiê dizia "8 imagens seladas e geolocalizadas" e não
        # mostrava nenhuma. Num produto que vende "até 430 imagens datadas e
        # geolocalizadas", falar delas sem mostrá-las esvazia o argumento.
        imagens = foto.get("fotos") or []
        if imagens:
            story.append(sp(6))
            story.append(Paragraph(track("IMAGENS SELADAS"), S["label"]))
            story.append(sp(3))
            for bloco in _galeria_de_imagens(imagens):
                story.append(bloco)

        n += 1
        story.append(PageBreak())

    # ── Demais categorias não mapeadas (fallback) ──
    outras: dict = {}
    for r in (dados.get("registros") or []):
        c = r.get("categoria")
        if c in categorias_tratadas:
            continue
        # Documentação com checklist já saiu na seção 03; sem checklist, não
        # saiu em lugar nenhum — e é esse que precisa aparecer aqui.
        if c == "documentacao" and (r.get("checklist") or []):
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
        d = dd.get("data") or dd.get("data_servico")
        # As duas espécies de data NÃO podem dividir a coluna sem aviso.
        #
        # Quando a ficha não traz a data do serviço, o único carimbo que existe
        # é o do cadastro. Antes as duas saíam iguais, e no dossiê do Ferretti
        # 780 os treze marcos apareceram todos em "08/2026" — uma cronologia
        # sugerindo que revisão de 500 h, docagem anual, laudo estrutural e
        # apólice aconteceram no mesmo mês. Num documento cujo produto É o
        # histórico, esse é o gráfico que o comprador olha primeiro.
        de_cadastro = not d
        if de_cadastro:
            d = str(reg.get("created_at") or "")[:10]
        if not d:
            continue
        # ISO (2024-03-12) -> 03/2024
        partes = str(d)[:10].split("-")
        rotulo = f"{partes[1]}/{partes[0]}" if len(partes) == 3 else str(d)[:10]
        st = {"atencao": "crit", "pendente": "warn"}.get(reg.get("status"), "ok")
        titulo = reg.get("titulo") or "Registro"
        if de_cadastro:
            titulo += "  <font size=6 color='#7a8595'>(data de cadastro)</font>"
        eventos.append((str(d)[:10], rotulo, titulo, st, de_cadastro))
    eventos.sort(key=lambda e: e[0])
    if eventos:
        story.append(_section_title(f"{n:02d} — Linha do Tempo da Custódia"))
        story.append(Paragraph(
            "Cronologia dos eventos selados. Cada marco corresponde a um registro imutável "
            "com data, autoria e hash.", S["body"]))
        story.append(sp(4))
        _sem_data_de_servico = sum(1 for e in eventos if e[4])
        if _sem_data_de_servico:
            story.append(_alert(
                "na", "Datas de execução ausentes:",
                f"{_pluralizar(_sem_data_de_servico, 'marco usa', 'marcos usam')} a data em "
                "que o registro foi cadastrado, porque a ficha não trouxe a data do serviço. "
                "Estão assinalados na lista. Data de cadastro não é data de execução."))
            story.append(sp(3))
        story.append(_timeline([(rot, tit, st) for _, rot, tit, st, _c in eventos]))
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

    # ── Como ler o índice + termo + verificação de autenticidade ──
    # Metodologia antes do termo: o termo garante que o número é íntegro; esta
    # seção diz o que o número quer dizer. Sem ela o termo sela um dado mudo.
    if dados.get("prontidao") is not None:
        story.extend(_como_ler_indice())
        story.append(sp(6))

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

    # A assinatura impede enumeração: o protocolo é previsível, então sem `s`
    # a verificação não responde. Só confere quem tem este PDF em mãos.
    from app.api.v1.verificacao import assinar
    _s = assinar(protocolo, emitido)
    verify_url = (
        f"https://yachtsatlas.online/verificar/{protocolo}"
        f"?s={_s}&e={emitido.replace('/', '-')}"
    )
    story.append(_section_title("Verificação de Autenticidade"))
    try:
        qr_img = _qr(verify_url, 40)
    except Exception:
        qr_img = Paragraph(f"Verificar em: {verify_url}", S["small"])
    bloco = Table([[
        qr_img,
        [Paragraph("COMO VERIFICAR ESTE DOCUMENTO", S["h2"]),
         Spacer(1, 5),
         Paragraph("1. Aponte a câmera para o QR ao lado — ele já leva os três "
                   "dados abaixo.<br/>"
                   "2. Sem câmera: acesse o endereço e informe protocolo, "
                   "código e data de emissão.<br/>"
                   "3. A plataforma recalcula os hashes e confirma a "
                   "autenticidade e a integridade da cadeia de custódia.",
                   S["body"]),
         Spacer(1, 6),
         Paragraph(track("ENDEREÇO"), S["label"]),
         Paragraph("yachtsatlas.online/verificar",
                   ParagraphStyle("vu", fontName="Courier", fontSize=7.5,
                                  textColor=GOLD_LIGHT, leading=11)),
         Spacer(1, 5),
         # Os TRÊS dados que a API exige, juntos e no mesmo lugar.
         # Antes o card pedia "informe o protocolo e o código" e mostrava
         # só o código: o protocolo ficava noutro bloco da página e a data
         # de emissão não era sequer mencionada — embora seja obrigatória
         # (`e` em verificacao.py). Quem seguisse a instrução impressa não
         # conseguia verificar de jeito nenhum.
         _credenciais_verificacao(protocolo, _s.upper(), emitido),
         Spacer(1, 4),
         Paragraph("Os três juntos são exclusivos deste documento. Sem eles, a "
                   "consulta não retorna dados — nem o conteúdo do dossiê é "
                   "exposto publicamente.", S["small"]),
         Spacer(1, 3),
         # Avisar que o arquivo pode ser conferido é, por si só, o que
         # desestimula a adulteração: ninguém edita um documento sabendo que a
         # cópia pode ser confrontada com a original em dois segundos.
         #
         # Uma linha só, em corpo pequeno e dentro do quadro que já existe. O
         # dossiê é o produto — não pode virar folheto do serviço de
         # verificação.
         Paragraph("A verificação também informa a <b>impressão digital "
                   "(SHA-256)</b> deste arquivo. Documento alterado após a "
                   "emissão não confere com a impressão registrada.",
                   S["small"]),
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
