"""
Os números do DOSSIÊ-ATLAS têm que dizer o que medem.

Todos estes testes nasceram de defeitos REAIS encontrados em 28/08/2026 no
dossiê emitido do Ferretti 780 (protocolo YA-IATE-2020-ECDD) e no código que o
gerou. O padrão se repete há meses neste projeto e tem um nome:

    um campo CERTO no banco que o leitor entende como OUTRA COISA.

O documento é selado por SHA-256 e traz QR de verificação — ele AFIRMA
integridade. Um número que promete mais do que mediu não é detalhe de layout:
é o selo garantindo uma afirmação falsa.
"""
import io
import re
from pathlib import Path

import pytest

from app.services.dossie_data import (
    _prontidao,
    _resumo_executivo,
    _saude_por_categoria,
)

RAIZ = Path(__file__).resolve().parents[2]
FRONT = RAIZ / "frontend" / "src"


def _reg(categoria, status="concluido", dados=None, created_at="2026-08-01T10:00:00+00:00",
         situacao="vigente"):
    return {
        "categoria": categoria,
        "status": status,
        "dados": dados or {},
        "created_at": created_at,
        "situacao": situacao,
        "hash_sha256": "a" * 64,
    }


# ─────────────────────────────────────────────────────────────────────────────
# O PIOR DE TODOS: "Crítico (Avaria Estrutural)" chegava como CONFORME
#
# `STATUS_ENUM` no FichaServicoForm mapeava três textos exatos — 'Concluído',
# 'Pendente', 'Atenção' — e tudo o mais caía em `|| 'registrado'`. Mas as
# fichas oferecem SETE conjuntos de rótulos, e seis não usam nenhuma dessas
# três palavras sozinhas. Resultado: o operador marcava AVARIA ESTRUTURAL no
# casco e o dossiê imprimia CASCO · CONFORME, peso 100.
#
# Pior ainda: o agravamento criado em REV-06 (casco e sinistro em atenção
# valem 0, não 50) nunca chegou a disparar, porque o status jamais chegava
# como 'atencao' vindo desses formulários. A trava existia e estava desligada
# na origem.
#
# Não há runner de teste no frontend, então este teste lê os DOIS arquivos
# como texto e confere que todo rótulo oferecido cai numa regra conhecida.
# Rótulo novo sem regra quebra aqui, que é o único lugar onde ainda dá tempo.
# ─────────────────────────────────────────────────────────────────────────────

def _rotulos_de_status_do_formulario() -> set[str]:
    fonte = (FRONT / "config" / "servicosCategorias.ts").read_text(encoding="utf-8")
    rotulos: set[str] = set()
    for bloco in re.finditer(r"key:\s*'status'.*?options:\s*\[(.*?)\]", fonte, re.S):
        for m in re.finditer(r"'([^']+)'", bloco.group(1)):
            rotulos.add(m.group(1))
    return rotulos


def _regra_do_formulario() -> str:
    return (FRONT / "components" / "FichaServicoForm.tsx").read_text(encoding="utf-8")


def _status_esperado(rotulo: str) -> str:
    """Espelha `statusDoRotulo` do FichaServicoForm.tsx."""
    s = rotulo.strip().lower()
    if rotulo in ("Concluído", "Pendente", "Atenção"):
        return {"Concluído": "concluido", "Pendente": "pendente", "Atenção": "atencao"}[rotulo]
    if "sem ressalva" in s:
        return "concluido"
    if "ressalva" in s or "pendencia" in s or "pendência" in s:
        return "atencao"
    if s.startswith(("nao ", "não ")):
        return "atencao"
    if s.startswith(("crítico", "critico", "vencida", "vencido", "atenção", "atencao")):
        return "atencao"
    if s.startswith("pendente"):
        return "pendente"
    if s.startswith(("concluído", "concluido", "excelente", "bom", "operacional",
                     "regular", "vigente")):
        return "concluido"
    return "registrado"


def test_todo_rotulo_de_status_tem_regra():
    """Nenhum rótulo do formulário pode cair no fallback silencioso.

    'registrado' não é 'atencao' nem 'pendente', então em
    `_saude_por_categoria` ele cai no `else: st = "ok"` — vira CONFORME,
    peso 100. Um rótulo sem regra é uma avaria que some.
    """
    sem_regra = {r for r in _rotulos_de_status_do_formulario()
                 if _status_esperado(r) == "registrado"}
    assert not sem_regra, (
        "Rótulo de status sem regra em statusDoRotulo (viraria CONFORME "
        f"silenciosamente): {sorted(sem_regra)}"
    )


def test_rotulos_graves_viram_alerta():
    """Avaria, apólice vencida e sistema crítico não podem virar notícia boa."""
    for rotulo in ("Crítico (Avaria Estrutural)", "Crítico (Sem proteção/craca)",
                   "Atenção (Recomenda-se Reparo)", "Vencida", "Crítico"):
        assert _status_esperado(rotulo) == "atencao", rotulo


def test_sinistro_nao_reparado_nao_sai_conforme():
    """Achado POR ESTE ARQUIVO, enquanto era escrito: a ficha de sinistro tem
    o próprio conjunto de rótulos, e nenhum deles usa as palavras das outras
    fichas. 'Nao reparado' caía no fallback e saía CONFORME — na categoria que
    o dossiê trata como fato grave, que vale zero."""
    assert _status_esperado("Nao reparado") == "atencao"
    assert _status_esperado("Reparo parcial - pendencias em aberto") == "atencao"
    assert _status_esperado("Reparado com ressalva tecnica") == "atencao"
    # ... e o sufixo que INVERTE o sentido da mesma palavra:
    assert _status_esperado("Totalmente reparado - sem ressalva") == "concluido"


def test_a_regra_ainda_e_por_prefixo():
    """Se voltar a ser igualdade exata, o defeito volta inteiro."""
    regra = _regra_do_formulario()
    assert "statusDoRotulo" in regra, "a função de normalização sumiu"
    assert "startsWith" in regra, "a leitura voltou a ser por igualdade exata"


def test_casco_com_avaria_nao_sai_conforme():
    """Ponta a ponta no backend: status 'atencao' em casco vale ZERO."""
    saude = dict(_saude_por_categoria([_reg("casco", status="atencao")], "iate"))
    assert saude["Casco"] == "crit"
    assert _prontidao([("Casco", "crit")]) == 0


def test_sinistro_aberto_vale_zero():
    saude = dict(_saude_por_categoria([_reg("sinistros", status="atencao")], "iate"))
    assert saude["Sinistros"] == "crit"


# ─────────────────────────────────────────────────────────────────────────────
# Retificação: o dossiê PUBLICA a regra, então ela tem que ser verdade
# ─────────────────────────────────────────────────────────────────────────────

def test_registro_retificado_sai_da_saude():
    """A seção "Como Ler Cobertura e Conformidade" afirma que registro
    retificado sai das métricas. `vw_registros_situacao` devolve o original E
    a correção; sem filtro, um problema já corrigido puxava a categoria para
    ATENÇÃO para sempre."""
    registros = [
        _reg("motor", status="atencao", situacao="retificado"),
        _reg("motor", status="concluido", situacao="retificador"),
    ]
    assert dict(_saude_por_categoria(registros, "iate"))["Motor"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Os tiles da capa
# ─────────────────────────────────────────────────────────────────────────────

def test_documentos_selados_nao_conta_fotos():
    """No Ferretti a capa dizia 28, a pág. 4 listava 10 e a pág. 14 falava em
    18 imagens: 10 + 18 = 28. O tile somava duas espécies com o nome de uma."""
    documentos = [{"tipo": "documento"}] * 10 + [{"tipo": "foto"}] * 18
    resumo = _resumo_executivo([_reg("manutencao")], documentos)
    assert resumo["documentos"] == 10


def test_investido_nao_soma_prejuizo_estimado():
    """Em casco e sinistros o campo `valor` é dano ESTIMADO, não gasto:
    "Estimativa de custo de reparo estrutural" e "Estimativa inicial de
    prejuízo". Um barco que bateu imprimia o prejuízo como benfeitoria."""
    registros = [
        _reg("manutencao", dados={"valor": "10000"}),
        _reg("casco", dados={"valor": "300000"}),       # estimativa de reparo
        _reg("sinistros", dados={"valor": "250000"}),   # prejuízo estimado
        _reg("seguro", dados={"valor": "2400000"}),     # apólice
    ]
    resumo = _resumo_executivo(registros, [])
    # _brl abrevia: "R$ 10,0 mil". O que importa é a ORDEM DE GRANDEZA —
    # com casco e sinistros dentro, este número passaria de meio milhão.
    assert resumo["investido"] == "R$ 10,0 mil", resumo["investido"]


def test_horimetro_e_a_leitura_mais_recente():
    """Era `max()` de todas as máquinas. O Ferretti tem quatro leituras
    (1.480, 1.476, 1.120, 1.095): o tile escolhia a maior e a chamava de "o"
    horímetro. max() é o MAIOR, não o mais recente — um zero a mais digitado
    virava o horímetro do barco para sempre."""
    registros = [
        _reg("motor", dados={"horimetro": "1480"}, created_at="2026-01-01T00:00:00+00:00"),
        _reg("motor", dados={"horimetro": "1120"}, created_at="2026-08-01T00:00:00+00:00"),
    ]
    resumo = _resumo_executivo(registros, [])
    assert resumo["horimetro"] == "1120 h"
    assert resumo["horimetro_leituras"] == 2


def test_custo_mensal_exige_periodo_de_servico():
    """Dividia o gasto pelo tempo de CADASTRO. A marina sobe anos de histórico
    na primeira semana e o dossiê anunciava a década como mensalidade."""
    sem_data = [_reg("manutencao", dados={"valor": "12000"})]
    assert _resumo_executivo(sem_data, [])["custo_mensal"] is None

    com_periodo = [
        _reg("manutencao", dados={"valor": "12000", "data": "2025-08-01"}),
        _reg("manutencao", dados={"valor": "0", "data": "2026-08-01"}),
    ]
    assert _resumo_executivo(com_periodo, [])["custo_mensal"] is not None


# ─────────────────────────────────────────────────────────────────────────────
# O documento como artefato: selo, fonte e texto extraível
# ─────────────────────────────────────────────────────────────────────────────

def _dados_minimos(nome="Vento Sul", proprietarios=None):
    return {
        "ativo_id": "YA-TESTE-2026-0001",
        "identificacao": {"nome": nome, "tipo": "iate", "ano": "2019"},
        "proprietarios": proprietarios or [],
        "resumo": {}, "registros": [], "documentos": [],
        "secoes_tecnicas": [], "fotografico": {"total": 0, "fotos": []},
        "saude": [("Manutenção", "ok"), ("Motor", "na")],
        "prontidao": 100, "prontidao_avaliados": 1, "prontidao_total": 2,
    }


def _texto_do_pdf(dados) -> str:
    fitz = pytest.importorskip("fitz", reason="PyMuPDF não instalado")
    from app.services.dossie_pdf import gerar_pdf_dossie
    doc = fitz.open(stream=gerar_pdf_dossie(dados), filetype="pdf")
    return "".join(p.get_text() for p in doc)


def test_nome_fora_do_latin1_sai_integro():
    """As fontes base-14 do PDF só conhecem Latin-1 e o ReportLab troca o que
    não conhece por um QUADRADO PRETO, sem erro e sem log: "Dvořák" virava
    "Dvo■ák". Num documento selado por SHA-256, que afirma integridade, o selo
    carimbava o nome errado do proprietário."""
    texto = _texto_do_pdf(_dados_minimos(nome="Yıldız Şafak"))
    assert "Yıldız Şafak" in texto


def test_protocolo_e_cnpj_sao_copiaveis():
    """O letter-spacing do cabeçalho quebrava a extração: saía
    "P r o t o c o l o  Y A - I A T E", que lido corrido vira "YA HATE" — foi
    assim que um revisor externo relatou "protocolo corrompido" e "CNPJ
    divergente" num PDF que estava impresso corretamente.

    Quem depende disto: o comprador que COPIA o protocolo para colar na página
    de verificação, o Ctrl+F, o leitor de tela e qualquer sistema que processe
    o arquivo."""
    texto = _texto_do_pdf(_dados_minimos())
    assert "Protocolo YA-TESTE-2026-0001" in texto
    assert "CNPJ 26.998.571/0001-50" in texto


def test_cnpj_tem_um_valor_so_no_projeto():
    """O relatório externo apontou dois CNPJs divergentes. Não havia — mas a
    string está repetida em sete arquivos, e é assim que a divergência nasce."""
    achados = set()
    for pasta in (RAIZ / "backend" / "app", FRONT):
        for arq in list(pasta.rglob("*.py")) + list(pasta.rglob("*.tsx")):
            achados |= set(re.findall(r"26\.998\.571/\d{4}-\d{2}", arq.read_text(encoding="utf-8")))
    assert achados == {"26.998.571/0001-50"}, f"CNPJ divergente no código: {achados}"


def test_conformidade_nao_tem_barra():
    """A barra cheia de ponta a ponta afirmava "completo" antes de a legenda
    ser lida — forma vence cor. Deixá-la fina e dourada não bastou."""
    fonte = (RAIZ / "backend" / "app" / "services" / "dossie_pdf.py").read_text(encoding="utf-8")
    assert "_conformidade_texto" in fonte
    assert fonte.count("GaugeBar(") == 2, (
        "GaugeBar deve ter só a definição da classe e UM uso (cobertura). "
        "A conformidade não volta a ser barra."
    )


def test_criterio_publicado_nao_rouba_o_nome_do_selo():
    """A seção explica Cobertura e Conformidade; o selo da capa é o Índice de
    Custódia e vem de OUTRA fórmula. Com o nome antigo, quem contestasse o
    selo recebia a explicação do indicador errado."""
    texto = _texto_do_pdf(_dados_minimos())
    assert "Como Ler Cobertura e Conformidade" in texto
    assert "Não confundir com o selo" in texto


def test_foto_nunca_e_recortada_para_caber():
    """A grade uniformiza a altura das celas, mas por letterbox — nunca por
    corte. Num dossiê de custódia a foto é evidência: recortar para preencher
    pode recortar justamente a avaria que ela registra."""
    Image = pytest.importorskip("PIL.Image", reason="Pillow não instalado")
    from app.services.dossie_pdf import _encaixar

    for largura, altura in ((600, 800), (1200, 400), (500, 500), (300, 900)):
        saida = _encaixar(Image.new("RGB", (largura, altura)), Image.new)
        assert saida.size[0] >= largura and saida.size[1] >= altura, "cortou a evidência"
        assert abs(saida.size[0] / saida.size[1] - 4 / 3) < 0.01


# ─────────────────────────────────────────────────────────────────────────────
# Omissão: o que o documento deixa de dizer também é afirmação
# ─────────────────────────────────────────────────────────────────────────────

def test_vencimento_vencido_nao_some_em_silencio():
    """A dedup guarda uma data por CAMPO e escolhia a mais distante. Mas o
    mesmo campo serve seis extintores e a habilitação de vários condutores: se
    três navegaram e dois estavam com a CHA vencida, saía UMA linha, "Em dia",
    com a validade do único regular. O viés era sempre para o lado favorável."""
    from app.services.dossie_data import _vencimentos

    registros = [
        _reg("operacao", dados={"cha_validade": "2020-01-01"}),   # vencida
        _reg("operacao", dados={"cha_validade": "2019-01-01"}),   # vencida
        _reg("operacao", dados={"cha_validade": "2030-01-01"}),   # em dia
    ]
    itens = _vencimentos(registros)
    assert len(itens) == 1, "a dedup por campo continua valendo"
    assert itens[0]["situacao"] == "em_dia"
    assert itens[0]["omitidos_vencidos"] == 2, (
        "as duas habilitações vencidas sumiram sem deixar rastro"
    )


def test_plural_de_um_dia():
    """"1 MESES" já saiu num dossiê real. "1 dias" estava na mesma tabela."""
    from app.services.dossie_pdf import _pluralizar

    assert _pluralizar(1, "dia", "dias") == "1 dia"
    assert _pluralizar(2, "dia", "dias") == "2 dias"
    assert _pluralizar(0, "dia", "dias") == "0 dias"


def test_selo_da_foto_nao_promete_data_de_captura():
    """A data era `uploaded_at`, impressa ao lado de GEO e do hash. Lado a
    lado, as três se leem como propriedades da FOTO. GEO foi corrigido em
    26/08 e passou a sair do EXIF; a data não. Uma foto de 2019 enviada hoje
    saía "2026-08-26"."""
    fonte = (RAIZ / "backend" / "app" / "services" / "dossie_pdf.py").read_text(encoding="utf-8")
    assert "SELADO EM" in fonte, "o selo voltou a imprimir a data nua"


def test_linha_do_tempo_assinala_data_de_cadastro():
    """No Ferretti os 13 marcos saíram todos em "08/2026": nenhum registro
    tinha data de serviço e todos caíram no fallback do `created_at`, sem
    aviso. Uma cronologia dizendo que revisão, docagem e apólice aconteceram
    no mesmo mês, num documento cujo produto É o histórico."""
    dados = _dados_minimos()
    dados["registros"] = [
        _reg("manutencao", dados={"data": "2024-03-12"}),
        _reg("motor"),  # sem data de serviço -> cai no created_at
    ]
    texto = _texto_do_pdf(dados)
    assert "data de cadastro" in texto
    assert "Datas de execução ausentes" in texto


def test_registro_de_documentacao_sem_checklist_aparece():
    """A capa prometia 13 registros e o corpo detalhava 12. A seção 03 imprime
    só os itens de `checklist`, e "documentacao" estava em `categorias_tratadas`
    de saída — então o registro sem checklist não saía nem lá nem no fallback.
    Sumia inteiro, continuando a contar no tile da capa."""
    dados = _dados_minimos()
    dados["registros"] = [
        {**_reg("documentacao"), "titulo": "Renovação do Título de Inscrição",
         "checklist": []},
    ]
    assert "Renovação do Título de Inscrição" in _texto_do_pdf(dados)
