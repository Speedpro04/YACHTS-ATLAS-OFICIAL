"""
ATLAS YACHTS — Gerador Principal de Dossiês
Execute: python generate.py
Saída: c:\\yachts-atlas\\dossie_engine\\output\\
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, PageBreak

from core import cover_canvas, dark_canvas
from sections import *

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ─── DADOS MOCK ──────────────────────────────────────────
DADOS_COMPACT = {
    'nome': 'AURORA III', 'tipo': 'Lancha Esportiva',
    'fabricante': 'Intermarine', 'modelo': 'Schaefer 400',
    'ano': '2018', 'comprimento': '40 pés',
    'registro': 'TG-12345-SP', 'bandeira': 'Brasil — Marinha do Brasil',
}
DADOS_EXECUTIVE = {
    'nome': 'CRISTAL DEL MAR', 'tipo': 'Iate de Luxo',
    'fabricante': 'Ferretti Group', 'modelo': 'Pershing 62',
    'ano': '2020', 'comprimento': '62 pés',
    'registro': 'TG-98765-RJ', 'bandeira': 'Brasil — Marinha do Brasil',
}
DADOS_SUPER = {
    'nome': 'IMPERADOR DO SUL', 'tipo': 'Superyacht',
    'fabricante': 'Azimut-Benetti', 'modelo': 'Azimut 105',
    'ano': '2019', 'comprimento': '105 pés',
    'registro': 'TG-55501-SP', 'bandeira': 'Brasil — Bandeira Internacional (Cayman)',
}

PROPRIETARIOS = [
    {'ordem': '1º', 'nome': 'Carlos Eduardo Menezes', 'periodo': '2018 – 2021', 'tipo': 'Proprietário Original'},
    {'ordem': '2º', 'nome': 'Náutica Horizonte Ltda.', 'periodo': '2021 – 2023', 'tipo': 'Compra e Venda'},
    {'ordem': '3º', 'nome': 'Roberto Albuquerque', 'periodo': '2023 – atual', 'tipo': 'Compra e Venda'},
]
DOCUMENTOS = [
    'Certificado de Registro de Embarcação (CPAM)',
    'Certificado de Segurança da Embarcação (CSE)',
    'Seguro Obrigatório DPEM vigente',
    'Habilitação do proprietário (Arrais Amador)',
    'Comprovante de IPVA náutico quitado',
    'Nota fiscal de aquisição',
]
MANUTENCAO = [
    {'data': 'Mar/2023', 'servico': 'Revisão geral motor — 500h', 'resp': 'Oficina Marítima SP', 'status': 'OK'},
    {'data': 'Jul/2023', 'servico': 'Troca impulsores e zincos', 'resp': 'Marina Santos', 'status': 'OK'},
    {'data': 'Jan/2024', 'servico': 'Pintura fundo antivegetativo', 'resp': 'Estaleiro Guarujá', 'status': 'OK'},
    {'data': 'Abr/2024', 'servico': 'Revisão sistemas elétricos', 'resp': 'Elétrica Náutica RJ', 'status': 'OK'},
    {'data': 'Out/2024', 'servico': 'Substituição coxim motor BB', 'resp': 'Volvo Penta SP', 'status': 'OK'},
]

def make_doc(filename):
    return SimpleDocTemplate(
        os.path.join(OUTPUT_DIR, filename), pagesize=A4,
        leftMargin=20*mm, rightMargin=14*mm, topMargin=16*mm, bottomMargin=18*mm)

# ─── COMPACT ─────────────────────────────────────────────
def gerar_compact():
    doc = make_doc('dossie_compact_aurora_iii.pdf')
    story = build_cover('Compact', 'Lanchas esportivas & day cruisers',
        'US$ 200', 'Até 45 pés', 'YA-2025-00142', 'AURORA III')
    story.append(PageBreak())
    story += secao_identificacao(DADOS_COMPACT)
    story += secao_proprietarios(PROPRIETARIOS)
    story.append(PageBreak())
    story += secao_documentacao(DOCUMENTOS)
    story += secao_manutencao(MANUTENCAO)
    story.append(PageBreak())
    story += secao_fotos()
    story.append(PageBreak())
    story += secao_acesso_digital('compact')
    story += secao_assinatura('YA-2025-00142')
    doc.build(story, onFirstPage=cover_canvas, onLaterPages=dark_canvas)
    print('[OK] Compact gerado')

# ─── EXECUTIVE ───────────────────────────────────────────
def gerar_executive():
    doc = make_doc('dossie_executive_cristal_del_mar.pdf')
    story = build_cover('Executive', 'Iates de luxo & uso misto',
        'US$ 400', '46 a 79 pés', 'YA-2025-00218', 'CRISTAL DEL MAR')
    story.append(PageBreak())
    story += secao_identificacao(DADOS_EXECUTIVE)
    story += secao_proprietarios(PROPRIETARIOS)
    story.append(PageBreak())
    story += secao_documentacao(DOCUMENTOS)
    story += secao_manutencao(MANUTENCAO)
    story.append(PageBreak())
    story += secao_fotos()
    story.append(PageBreak())
    story += secao_inspecao_tecnica()
    story.append(PageBreak())
    story += secao_sinistros()
    story += secao_valuation()
    story.append(PageBreak())
    story += secao_relatorio_seguradora()
    story += secao_acesso_digital('executive')
    story += secao_assinatura('YA-2025-00218')
    doc.build(story, onFirstPage=cover_canvas, onLaterPages=dark_canvas)
    print('[OK] Executive gerado')

# ─── SUPERYACHT ──────────────────────────────────────────
def gerar_superyacht():
    doc = make_doc('dossie_superyacht_imperador_do_sul.pdf')
    story = build_cover('Superyacht', 'Superyachts & ativos de legado',
        'US$ 600', '80+ pés', 'YA-2025-00089', 'IMPERADOR DO SUL')
    story.append(PageBreak())
    story += secao_identificacao(DADOS_SUPER)
    story += secao_proprietarios(PROPRIETARIOS)
    story.append(PageBreak())
    story += secao_documentacao(DOCUMENTOS)
    story += secao_manutencao(MANUTENCAO)
    story.append(PageBreak())
    story += secao_fotos()
    story.append(PageBreak())
    story += secao_inspecao_tecnica()
    story.append(PageBreak())
    story += secao_sinistros()
    story += secao_valuation()
    story.append(PageBreak())
    story += secao_relatorio_seguradora()
    story.append(PageBreak())
    story += secao_compliance_imo()
    story.append(PageBreak())
    story += secao_auditoria_estrutural()
    story.append(PageBreak())
    story += secao_due_diligence()
    story += secao_acesso_digital('superyacht')
    story += secao_assinatura('YA-2025-00089')
    doc.build(story, onFirstPage=cover_canvas, onLaterPages=dark_canvas)
    print('[OK] Superyacht gerado')

if __name__ == '__main__':
    gerar_compact()
    gerar_executive()
    gerar_superyacht()
    print(f'\n[OK] Todos os 3 dossies gerados em: {OUTPUT_DIR}')
