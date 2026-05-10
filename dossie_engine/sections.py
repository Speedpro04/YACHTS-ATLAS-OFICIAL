"""
ATLAS YACHTS — Seções do Dossiê (com QR Code + Selo de Auditoria)
"""
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from core import *


# ─── CAPA ─────────────────────────────────────────────────
def build_cover(tier_name, tier_subtitle, price, vessel_size, dossie_num, vessel_name):
    story = [spacer(30)]
    story.append(Paragraph('ATLAS YACHTS', ParagraphStyle('brand',
        fontName='Helvetica-Bold', fontSize=20, textColor=GOLD, letterSpacing=5, leading=26)))
    story.append(spacer(2))
    story.append(Paragraph('CUSTÓDIA DIGITAL DE ATIVOS NÁUTICOS', S['eyebrow']))
    story.append(spacer(16))
    story.append(GoldLine())
    story.append(spacer(8))
    story.append(Paragraph(f'DOSSIÊ {tier_name.upper()}', ParagraphStyle('tier',
        fontName='Helvetica-Bold', fontSize=8, textColor=GOLD_DIM, letterSpacing=3, leading=11)))
    story.append(spacer(3))
    story.append(Paragraph(vessel_name, ParagraphStyle('vname',
        fontName='Helvetica-Bold', fontSize=32, textColor=WHITE, leading=36)))
    story.append(spacer(2))
    story.append(Paragraph(tier_subtitle, S['body']))
    story.append(spacer(12))
    story.append(GoldLine(opacity=0.3))
    story.append(spacer(8))
    meta = [
        ['Nº DO DOSSIÊ', 'TIER', 'PORTE', 'VALOR'],
        [dossie_num, tier_name, vessel_size, price],
    ]
    t = Table(meta, colWidths=[42*mm, 32*mm, 42*mm, 32*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica'), ('FONTSIZE', (0,0), (-1,0), 6),
        ('TEXTCOLOR', (0,0), (-1,0), GOLD_DIM),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Bold'), ('FONTSIZE', (0,1), (-1,1), 10),
        ('TEXTCOLOR', (0,1), (-1,1), WHITE),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('LINEBELOW', (0,0), (-1,0), 0.3, BORDER),
    ]))
    story.append(t)
    story.append(spacer(80))
    story.append(Paragraph('DOCUMENTO CONFIDENCIAL — USO RESTRITO', S['eyebrow']))
    story.append(Paragraph(
        'Este dossiê é emitido exclusivamente pela plataforma Atlas Yachts e destina-se '
        'à consulta por partes autorizadas. A reprodução ou distribuição não autorizada '
        'é expressamente proibida.', S['small']))
    return story


# ─── SEÇÕES COMUNS ────────────────────────────────────────
def secao_identificacao(dados):
    story = [section_title('01 — Identificação da Embarcação')]
    story.append(info_table([
        ('Nome da Embarcação', dados['nome']), ('Tipo / Categoria', dados['tipo']),
        ('Fabricante', dados['fabricante']), ('Modelo', dados['modelo']),
        ('Ano de Fabricação', dados['ano']), ('Comprimento (pés)', dados['comprimento']),
        ('Número de Registro', dados['registro']), ('Bandeira', dados['bandeira']),
    ]))
    return story

def secao_proprietarios(historico):
    story = [section_title('02 — Histórico de Proprietários')]
    rows = [['ORDEM', 'PROPRIETÁRIO', 'PERÍODO', 'TRANSFERÊNCIA']]
    for h in historico:
        rows.append([h['ordem'], h['nome'], h['periodo'], h['tipo']])
    t = Table(rows, colWidths=[15*mm, 55*mm, 45*mm, 33*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 7),
        ('TEXTCOLOR', (0,0), (-1,0), GOLD),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,1), (-1,-1), 8.5),
        ('TEXTCOLOR', (0,1), (-1,-1), WHITE_DIM),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [NEAR_BLACK, DARK_SURFACE]),
        ('LINEBELOW', (0,0), (-1,0), 0.3, GOLD_DIM),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    return story

def secao_documentacao(docs):
    story = [section_title('03 — Documentação Legal e Fiscal')]
    story.append(checklist_table(docs))
    return story

def secao_manutencao(registros):
    story = [section_title('04 — Histórico de Manutenção')]
    rows = [['DATA', 'SERVIÇO REALIZADO', 'RESPONSÁVEL', 'STATUS']]
    for r in registros:
        rows.append([r['data'], r['servico'], r['resp'], r['status']])
    t = Table(rows, colWidths=[22*mm, 80*mm, 38*mm, 18*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 7),
        ('TEXTCOLOR', (0,0), (-1,0), GOLD),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,1), (-1,-1), 8),
        ('TEXTCOLOR', (0,1), (-1,-1), WHITE_DIM),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [NEAR_BLACK, DARK_SURFACE]),
        ('LINEBELOW', (0,0), (-1,0), 0.3, GOLD_DIM),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    return story


# ─── FOTOS COM SELO DE AUDITORIA (MELHORADO) ─────────────
def secao_fotos():
    story = [section_title('05 — Registro Fotográfico Certificado')]
    placeholders = [
        ['Vista Lateral (Bombordo)', 'Vista Lateral (Boreste)'],
        ['Proa', 'Popa'],
        ['Cabine / Interior', 'Casa de Máquinas'],
    ]
    for pair in placeholders:
        row_cells = []
        for label in pair:
            seal = Paragraph(
                '✓ AUDITADO ATLAS  |  GEOLOCALIZAÇÃO CONFIRMADA',
                ParagraphStyle('seal', fontName='Helvetica-Bold', fontSize=5.5,
                    textColor=GOLD, leading=8, letterSpacing=1))
            cell = Table(
                [[seal], [Paragraph(label, S['label'])]],
                colWidths=[73*mm], rowHeights=[7*mm, 38*mm])
            cell.setStyle(TableStyle([
                ('BOX', (0,0), (-1,-1), 0.4, GOLD),
                ('LINEBELOW', (0,0), (-1,0), 0.3, GOLD_DIM),
                ('BACKGROUND', (0,0), (-1,0), GOLD_DIM),
                ('BACKGROUND', (0,1), (-1,-1), DARK_SURFACE),
                ('VALIGN', (0,0), (-1,-1), 'BOTTOM'),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            row_cells.append(cell)
        row = Table([row_cells], colWidths=[76*mm, 76*mm])
        row.setStyle(TableStyle([
            ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(row)
    story.append(Paragraph(
        'Imagens vinculadas ao cofre digital. Hash SHA-256 registrado no momento do upload.',
        S['small']))
    return story


# ─── SEÇÕES EXECUTIVE+ ───────────────────────────────────
def secao_inspecao_tecnica():
    story = [section_title('06 — Inspeção Técnica Certificada')]
    story.append(field_row('Data da Inspeção', '14/03/2025'))
    story.append(field_row('Inspetor Responsável', 'Eng. Ricardo Alves — CREA 12345-SP'))
    story.append(field_row('Metodologia', 'Inspeção visual + ensaio não destrutivo (ultrassom)'))
    story.append(spacer(4))
    story.append(Paragraph('RESULTADO POR SISTEMA', S['section_header']))
    story.append(GoldLine(opacity=0.3))
    story.append(spacer(3))
    itens = [
        ('Casco e Estrutura', True, 'Sem deformações ou pontos de corrosão ativos.'),
        ('Motorização', True, 'Motor em condições normais de operação.'),
        ('Sistema Elétrico', True, 'Fiação e painel revisados. Sem curtos identificados.'),
        ('Sistema Hidráulico', False, 'Mangueira de direção com desgaste — substituição recomendada.'),
        ('Equipamentos de Segurança', True, 'Coletes, sinalizadores e balsa dentro da validade.'),
        ('Navegação e Eletrônica', True, 'GPS, VHF e sonar funcionando corretamente.'),
    ]
    rows = [['SISTEMA', 'STATUS', 'OBSERVAÇÃO']]
    for sistema, ok, obs in itens:
        st = 'APROVADO' if ok else 'ATENÇÃO'
        clr = EMERALD if ok else RUBY
        rows.append([
            Paragraph(sistema, S['body_white']),
            Paragraph(st, ParagraphStyle('st', fontName='Helvetica-Bold', fontSize=7.5, textColor=clr, leading=11)),
            Paragraph(obs, S['small']),
        ])
    t = Table(rows, colWidths=[40*mm, 22*mm, 86*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 7),
        ('TEXTCOLOR', (0,0), (-1,0), GOLD),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [NEAR_BLACK, DARK_SURFACE]),
        ('LINEBELOW', (0,0), (-1,0), 0.3, GOLD_DIM),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t)
    return story

def secao_sinistros():
    story = [section_title('07 — Histórico de Sinistros e Reparos')]
    rows = [['DATA', 'EVENTO', 'REPARO REALIZADO', 'VALOR (USD)']]
    for s in [('Jun/2021','Colisão menor em marina','Reparo fibra proa — aprovado laudo','USD 1.800'),
              ('Nov/2023','Dano por mau tempo','Troca toldo e antenas','USD 3.200')]:
        rows.append(list(s))
    t = Table(rows, colWidths=[20*mm, 52*mm, 62*mm, 24*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 7),
        ('TEXTCOLOR', (0,0), (-1,0), GOLD),
        ('FONTNAME', (0,1), (-1,-1), 'Helvetica'), ('FONTSIZE', (0,1), (-1,-1), 8),
        ('TEXTCOLOR', (0,1), (-1,-1), WHITE_DIM),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [NEAR_BLACK, DARK_SURFACE]),
        ('LINEBELOW', (0,0), (-1,0), 0.3, GOLD_DIM),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(spacer(3))
    story.append(Paragraph(
        'Todos os reparos foram realizados por estaleiros certificados e documentados '
        'com notas fiscais e laudos técnicos arquivados no cofre digital.', S['small']))
    return story

def secao_valuation():
    story = [section_title('08 — Avaliação de Mercado')]
    story.append(info_table([
        ('Valor de Mercado Estimado', 'USD 185.000'), ('Data da Avaliação', 'Março 2025'),
        ('Metodologia', 'Comparativo de mercado + depreciação técnica'),
        ('Fonte de Referência', 'YachtWorld Index + BUC'),
    ]))
    story.append(spacer(4))
    story.append(Paragraph(
        'A avaliação considera estado de conservação, histórico de manutenção, '
        'equipamentos embarcados e comparativo com vendas recentes.', S['body']))
    return story

def secao_relatorio_seguradora():
    story = [section_title('09 — Relatório para Seguradora')]
    story.append(Paragraph(
        'Este relatório consolida as informações técnicas necessárias para contratação '
        'ou renovação de apólice de seguro marítimo.', S['body']))
    story.append(spacer(4))
    story.append(info_table([
        ('Valor Segurado Recomendado', 'USD 185.000'), ('Classe de Risco', 'Baixo'),
        ('Uso Declarado', 'Lazer — Costeiro'), ('Local de Atracação', 'Marina Paraty — RJ'),
        ('Equipamentos de Segurança', 'Completos e dentro da validade'),
        ('Histórico de Sinistros', '2 ocorrências menores (2021 e 2023)'),
    ]))
    return story


# ─── SEÇÕES SUPERYACHT+ ──────────────────────────────────
def secao_compliance_imo():
    story = [section_title('10 — Compliance Internacional (IMO)')]
    story.append(info_table([
        ('Número IMO', 'IMO 9876543'), ('Bandeira de Registro', 'Brasil (Marinha do Brasil)'),
        ('Classe de Certificação', 'RINA — Bureau Veritas'),
        ('Certificado de Arqueação', 'ARQUEA-2024-00312'),
        ('Validade do Certificado', 'Dezembro 2026'), ('Conformidade SOLAS', 'Aprovado'),
    ]))
    story.append(spacer(4))
    story.append(checklist_table([
        'ISM Code — International Safety Management',
        'ISPS Code — International Ship and Port Facility Security',
        'MARPOL — Prevenção de Poluição Marítima',
        'MLC 2006 — Maritime Labour Convention',
        'Certificado de Rádio (ITU)',
    ]))
    return story

def secao_auditoria_estrutural():
    story = [section_title('11 — Auditoria Estrutural do Casco')]
    story.append(field_row('Método de Inspeção', 'Ensaio Ultrassônico (UT) — ASNT NDT Level II'))
    story.append(field_row('Pontos Inspecionados', '48 pontos em 6 zonas estruturais'))
    story.append(field_row('Data da Auditoria', 'Fevereiro 2025'))
    story.append(spacer(4))
    zonas = [('Zona 1 — Proa','98%'),('Zona 2 — Amidships BB','100%'),
             ('Zona 3 — Amidships BE','97%'),('Zona 4 — Popa','99%'),
             ('Zona 5 — Fundo Central','95%'),('Zona 6 — Casa de Máquinas','93%')]
    rows = [['ZONA ESTRUTURAL', 'INTEGRIDADE', 'STATUS']]
    for zona, pct in zonas:
        rows.append([Paragraph(zona, S['body_white']), Paragraph(pct, S['body_white']),
            Paragraph('APROVADO', ParagraphStyle('ok', fontName='Helvetica-Bold', fontSize=7.5, textColor=EMERALD, leading=11))])
    t = Table(rows, colWidths=[70*mm, 40*mm, 38*mm])
    t.setStyle(TableStyle([
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 7),
        ('TEXTCOLOR', (0,0), (-1,0), GOLD),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [NEAR_BLACK, DARK_SURFACE]),
        ('LINEBELOW', (0,0), (-1,0), 0.3, GOLD_DIM),
        ('TOPPADDING', (0,0), (-1,-1), 5), ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t)
    return story

def secao_due_diligence():
    story = [section_title('12 — Suporte à Due Diligence')]
    story.append(Paragraph(
        'Indicadores críticos para análise por fundos, gestores de patrimônio e seguradoras.', S['body']))
    story.append(spacer(6))
    kpis = [('Índice de Integridade Estrutural','96.7 / 100'),
            ('Histórico de Sinistros (10 anos)','2 ocorrências menores'),
            ('Regularidade Documental','Completa'),
            ('Compliance Internacional','Aprovado — RINA / Bureau Veritas'),
            ('Pendências Judiciais','Nenhuma registrada'),
            ('Dívidas e Gravames','Livre e desembaraçado')]
    rows = []
    for label, value in kpis:
        rows.append([Paragraph(label, S['body_white']), Paragraph(value, S['body']),
            Paragraph('✓', ParagraphStyle('ck', fontName='Helvetica-Bold', fontSize=10, textColor=EMERALD, leading=13))])
    t = Table(rows, colWidths=[70*mm, 62*mm, 16*mm])
    t.setStyle(TableStyle([
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [NEAR_BLACK, DARK_SURFACE]),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 6), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOX', (0,0), (-1,-1), 0.3, BORDER),
    ]))
    story.append(t)
    return story

def secao_acesso_digital(tier):
    n = '10' if tier == 'compact' else '13'
    story = [section_title(f'{n} — Acesso ao Cofre Digital')]
    story.append(Paragraph('Este dossiê está vinculado ao cofre digital Atlas Yachts.', S['body']))
    story.append(spacer(4))
    aid = '142' if tier == 'compact' else '218' if tier == 'executive' else '089'
    story.append(info_table([
        ('URL de Acesso', 'app.yachtsatlas.com'), ('ID do Ativo', f'YA-2025-00{aid}'),
        ('Nível de Acesso', 'Proprietário' if tier == 'compact' else 'Somente Leitura (Convidado)'),
        ('Autenticação', '2FA obrigatório'),
    ]))
    if tier != 'compact':
        story.append(spacer(4))
        story.append(Paragraph('PERMISSÕES DISPONÍVEIS', S['section_header']))
        story.append(GoldLine(opacity=0.3))
        story.append(spacer(3))
        perms = ['Visualizar todos os documentos', 'Download do dossiê em PDF', 'Compartilhar link temporário']
        if tier == 'superyacht':
            perms += ['Acesso via API (token privado)', 'Convidar múltiplos usuários']
        story.append(checklist_table(perms))
    return story


# ─── ASSINATURA COM QR CODE (MELHORADO) ──────────────────
def secao_assinatura(dossie_id='YA-2025-00000'):
    verify_url = f'https://app.yachtsatlas.com/verify/{dossie_id}'
    story = [section_title('— Certificação e Assinatura Digital')]
    story.append(Paragraph(
        'Este documento foi gerado e certificado pela plataforma Atlas Yachts. '
        'A integridade é garantida por hash SHA-256 registrado no momento da emissão.', S['body']))
    story.append(spacer(8))
    rows = [
        [Paragraph('EMITIDO POR', S['label']), Paragraph('DATA DE EMISSÃO', S['label']), Paragraph('HASH DO DOCUMENTO', S['label'])],
        [Paragraph('Atlas Yachts Platform', S['value']), Paragraph('10/05/2025', S['value']),
         Paragraph('a3f7c2...9d41be', ParagraphStyle('hash', fontName='Helvetica', fontSize=8, textColor=GOLD_DIM, leading=11))],
    ]
    t = Table(rows, colWidths=[50*mm, 40*mm, 58*mm])
    t.setStyle(TableStyle([
        ('LINEABOVE', (0,0), (-1,0), 0.3, GOLD_DIM),
        ('LINEBELOW', (0,-1), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 0), ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(t)
    story.append(spacer(10))

    # QR Code de Autenticidade
    try:
        qr_img = make_qr_image(verify_url, size_mm=30)
        qr_label = Paragraph(
            f'ESCANEIE PARA VERIFICAR AUTENTICIDADE<br/>{verify_url}',
            ParagraphStyle('qr_l', fontName='Helvetica', fontSize=6.5, textColor=GOLD_DIM, leading=10, alignment=TA_CENTER))
        qr_t = Table([[qr_img], [qr_label]], colWidths=[35*mm])
        qr_t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('TOPPADDING', (0,0), (-1,-1), 4)]))
        outer = Table([[qr_t]], colWidths=[148*mm])
        outer.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(outer)
    except Exception:
        story.append(Paragraph(f'Verificar em: {verify_url}', S['small']))

    story.append(spacer(10))
    story.append(Paragraph(
        'ATLAS YACHTS — Plataforma de Custódia Digital de Ativos Náuticos\nyachtsatlas.com | contato@yachtsatlas.com',
        ParagraphStyle('fc', fontName='Helvetica', fontSize=7, textColor=GOLD_DIM, leading=11, alignment=TA_CENTER)))
    return story
