"""
Yachts Atlas — Montagem dos dados do Dossiê a partir do banco real.
Ponte entre o que a marina preenche (tabela `registros`, alinhada às
categorias) e a estrutura que o gerador de PDF (dossie_engine) consome.

Princípios:
 - Dossiê ÚNICO; as seções aparecem conforme o porte / dados existentes.
 - "Nenhuma seção vazia": seções sem dado não entram (ver `secoes_aplicaveis`).
 - Custódia: o conteúdo vem de `registros` (dados JSONB) e `documentos`.
"""
from typing import Any, Optional
from app.core.pii import mascarar_documento
from app.core.supabase import get_supabase_admin


# Porte mínimo (pés) em que cada seção do dossiê passa a ser relevante.
# Espelha frontend/src/config/dossieCategorias.ts (porteMinimoPes).
PORTE_MINIMO = {
    "identificacao": 0,
    "proprietarios": 0,
    "documentacao": 0,
    "especificacoes": 0,
    "motorizacao": 0,
    "sistemas_auxiliares": 40,
    "manutencao": 0,
    "operacao": 0,
    "inspecao_tecnica": 46,
    "auditoria_casco": 46,
    "sinistros": 0,
    "fotografico": 0,
    "tripulacao": 80,
    "tenders_toys": 80,
    "areas": 80,
    "avaliacao_mercado": 46,
    "relatorio_seguradora": 46,
    "compliance_imo": 80,
}


# Categorias técnicas do PAINEL (servicosCategorias.ts) → título náutico no dossiê.
# Todas usam a MESMA ficha rica (logbook). Ordem = ordem das seções no PDF.
CATEGORIAS_TECNICAS: list[tuple[str, str]] = [
    ("manutencao", "Histórico de Manutenção"),
    ("operacao", "Diário de Bordo — Operações & Idas ao Mar"),
    ("motor", "Motorização & Propulsão"),
    ("velame", "Mastro, Rigging & Velame"),
    ("casco", "Casco & Integridade Estrutural"),
    ("drenagem", "Drenagem, Porão & Esgotamento"),
    ("eletrica", "Sistema Elétrico & Eletrônica de Navegação"),
    ("seguranca", "Segurança & Salvatagem"),
    ("pintura", "Pintura & Acabamento"),
    ("interior", "Interior & Acomodações"),
    ("seguro", "Seguro & Cobertura"),
]

# Rótulos náuticos da galeria fotográfica (espelha GALERIA_CATS no front).
GALERIA_LABELS: dict[str, str] = {
    "embarcacao": "Fotos da Embarcação",
    "casco_exterior": "Integridade do Casco",
    "motor": "Motor / Propulsão",
    "pintura": "Pintura",
    "interior": "Interior",
    "eletronica": "Eletrônica / Navegação",
    "notas_fiscais": "Notas Fiscais",
    "antes_depois": "Antes e Depois",
    "outros": "Outros",
    "fotos": "Registro Geral",
    "seguranca": "Segurança & Salvatagem",
}

MAX_FOTOS = 460  # capacidade fotográfica por embarcação (espelha COBERTURA_CATS do front)


# O mascaramento vive em `core.pii`, fonte unica: a MESMA funcao roda na
# gravacao (api/v1/ativos.py) e aqui. Duas implementacoes do mesmo
# mascaramento divergiriam, e a que ficasse errada seria justamente a que
# ninguem estivesse olhando.
#
# Desde 31/08/2026 o documento chega mascarado do proprio banco -- o completo
# nao e mais gravado (ver core/pii.py). Este passo permanece por dois
# motivos: as linhas antigas ate o backfill, e a garantia de que um caminho
# de escrita novo que esqueca de mascarar nao vaze pelo dossie.
_mascarar_documento = mascarar_documento


# Rótulo náutico de cada campo de validade que a ficha coleta. Chave = campo
# no JSONB do registro; valor = como o comprador e a seguradora chamam a coisa.
CAMPOS_DE_VALIDADE: dict[str, str] = {
    "extintor_validade": "Extintores",
    "pirotecnicos_validade": "Sinais pirotécnicos",
    "coletes_validade": "Coletes salva-vidas",
    "epirb_validade_bateria": "EPIRB — bateria",
    "cha_validade": "Habilitação do condutor (CHA)",
    "balsa_validade": "Balsa salva-vidas",
    "radiobaliza_validade": "Radiobaliza",
}


def _valor_registro(r: dict) -> Optional[float]:
    """Valor monetário de um registro, venha em `valor` ou `custo`."""
    d = r.get("dados") or {}
    return _num(d.get("valor")) or _num(d.get("custo"))


def _vencimentos(registros: list[dict]) -> list[dict[str, Any]]:
    """O que vence, quando, e em quantos dias.

    Fica no JSONB do registro e nunca chegava ao dossiê. É o que responde
    "o que vou ter que renovar?" — pergunta que decide quem paga o quê numa
    negociação — e o que a seguradora exige conferir antes de emitir apólice.

    Mantém só a data MAIS RECENTE de cada item: o extintor inspecionado duas
    vezes tem duas datas, e a que vale é a última. Mostrar as duas faria o
    dossiê parecer contraditório.

    MAS a chave é o CAMPO, e o mesmo campo carrega objetos e pessoas
    diferentes: `extintor_validade` num barco com seis extintores, e
    principalmente `cha_validade`, preenchido no Diário de Bordo uma vez por
    viagem, por condutor diferente. Guardando sempre a data mais distante, o
    viés é SEMPRE para o lado favorável: se três condutores navegaram e dois
    estavam com a habilitação vencida, a tabela imprimia uma única linha,
    "Em dia", com a validade do único regular.

    Descartar em silêncio o que está vencido é omissão num documento que
    circula numa negociação. A escolha continua sendo a mais recente — que é
    o certo para reinspeção do mesmo objeto — mas o que foi descartado E
    estava vencido passa a ser contado e dito na seção.
    """
    from datetime import date, datetime

    achados: dict[str, dict] = {}
    # `date.today()` é usado dentro do laço para saber se o que está sendo
    # substituído já tinha vencido.
    for r in registros:
        d = r.get("dados") or {}
        for campo, rotulo in CAMPOS_DE_VALIDADE.items():
            bruto = str(d.get(campo) or "").strip()
            if not bruto:
                continue
            try:
                venc = datetime.fromisoformat(bruto[:10]).date()
            except ValueError:
                continue
            anterior = achados.get(campo)
            if anterior is None or venc > anterior["_data"]:
                # O que sai de cena ainda conta, se estava vencido.
                omitidos = anterior["_omitidos_vencidos"] if anterior else 0
                if anterior is not None and anterior["_data"] < date.today():
                    omitidos += 1
                achados[campo] = {
                    "item": rotulo,
                    "vence_em": "/".join(reversed(bruto[:10].split("-"))),
                    "_data": venc,
                    "origem": r.get("titulo") or None,
                    "_omitidos_vencidos": omitidos,
                }
            elif venc < date.today():
                anterior["_omitidos_vencidos"] += 1

    hoje = date.today()
    saida = []
    for v in achados.values():
        dias = (v["_data"] - hoje).days
        v.pop("_data")
        v["dias"] = dias
        v["omitidos_vencidos"] = v.pop("_omitidos_vencidos", 0)
        # Três faixas, e o limiar de 90 dias não é arbitrário: é o prazo em que
        # ainda dá para renovar sem correria, e o que uma seguradora considera
        # "a vencer" numa renovação de apólice.
        v["situacao"] = ("vencido" if dias < 0 else
                         "a_vencer" if dias <= 90 else "em_dia")
        saida.append(v)
    saida.sort(key=lambda x: x["dias"])
    return saida


def _por_categoria(registros: list[dict], categoria: str) -> list[dict]:
    return [r for r in registros if r.get("categoria") == categoria]


def _num(v: Any) -> Optional[float]:
    """Converte valor em pt-BR ('18.500,00') ou en ('18500.00') para float."""
    if v in (None, "", "None"):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    for lixo in ("R$", "r$", " ", "h", "H"):
        s = s.replace(lixo, "")
    if "," in s and "." in s:          # 18.500,00 -> 18500.00
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:                      # 380,00 -> 380.00
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _brl(v: float) -> str:
    """Formata em Real, abreviando a partir de mil para caber no tile."""
    if v >= 1_000_000:
        return f"R$ {v / 1_000_000:.1f} mi".replace(".", ",")
    if v >= 1_000:
        return f"R$ {v / 1_000:.1f} mil".replace(".", ",")
    return f"R$ {v:,.0f}".replace(",", ".")


# Espelha as 8 categorias do AssetHealthDashboard (painel técnico).
# Categorias que entram no Índice de Segurança.
#
# Precisa espelhar CATEGORIAS_TECNICAS + sinistros. A lista anterior deixava de
# fora justamente onde o problema mora — casco, operação e sinistros — e por
# isso o dossiê do Marlin Sea saiu "GOLD · 100%" num barco que bateu em objeto
# submerso, furou a proa a bombordo e voltou do mar avariado. Os dois registros
# em atenção estavam em `operacao` e `sinistros`; nenhuma das duas era contada.
#
# `documentacao` e `dossie` saíram: não são categorias de REGISTRO (documento
# vive em outra tabela), então davam "NÃO AVALIADO" para sempre — a linha que
# aparecia na capa ao lado de "29 documentos selados", parecendo defeito.
SAUDE_CATEGORIAS: list[tuple[str, str]] = [
    ("manutencao", "Manutenção"), ("operacao", "Operação"),
    ("motor", "Motor"), ("velame", "Velame & Rigging"),
    ("casco", "Casco"), ("drenagem", "Drenagem & Porão"),
    ("eletrica", "Elétrica"), ("seguranca", "Segurança"),
    ("pintura", "Pintura"), ("interior", "Interior"),
    ("seguro", "Seguro"), ("sinistros", "Sinistros"),
]

# Categorias em que "atenção" não é ressalva, é fato grave: sinistro aberto e
# retorno de mar com avaria valem 0, não 50. Um casco furado não é meio-termo.
SAUDE_CRITICAS: frozenset[str] = frozenset({"sinistros", "casco"})


# Categorias que NÃO se aplicam a cada tipo de embarcação.
#
# Espelha o que o painel já faz (`AtivoHub.categorias()`): veleiro troca motor
# por velame, e jet ski não tem interior nem pintura. O dossiê não olhava o
# tipo, e por isso um Fibrafort Focker — lancha a motor — saía com uma linha
# "VELAME & RIGGING · NÃO AVALIADO" no relatório entregue ao comprador.
#
# Não é só estética: categoria que nunca poderá ser preenchida entra na conta
# como buraco permanente e faz o barco parecer incompleto por algo que não
# existe nele.
NAO_SE_APLICA: dict[str, frozenset[str]] = {
    "veleiro": frozenset({"motor"}),                            # registra em velame
    "jetski": frozenset({"velame", "interior", "pintura"}),
}
# Barco a motor não tem velame — é o caso da maioria (iate, lancha, pesca).
_SEM_VELAME = frozenset({"velame"})


def categorias_do_tipo(tipo: Optional[str]) -> list[tuple[str, str]]:
    """As categorias de saúde que fazem sentido para este tipo de embarcação."""
    fora = NAO_SE_APLICA.get((tipo or "").strip().lower(), _SEM_VELAME)
    return [(c, l) for c, l in SAUDE_CATEGORIAS if c not in fora]


def _saude_por_categoria(registros: list[dict], tipo: Optional[str] = None) -> list[tuple[str, str]]:
    """Status por categoria, com a MESMA semântica do painel.

    Sem registro na categoria => 'na' (não avaliado). Nunca inventa 'ok'.
    Categoria que não se aplica ao tipo não aparece — ver `categorias_do_tipo`.
    """
    # Registro RETIFICADO sai da conta: quem vale é a correção que o
    # substituiu. `vw_registros_situacao` devolve os dois — o original e o
    # retificador — e sem este filtro um problema já corrigido continuava
    # puxando a categoria para ATENÇÃO para sempre. A seção "Como Ler Este
    # Índice", no PDF, publica esta regra; ela precisa ser verdade aqui.
    registros = [r for r in registros
                 if (r.get("situacao") or "vigente") != "retificado"]
    out = []
    for cat, label in categorias_do_tipo(tipo):
        regs = _por_categoria(registros, cat)
        if not regs:
            out.append((label, "na"))
            continue
        status = {r.get("status") for r in regs}
        if "atencao" in status:
            # Sinistro aberto e casco em atenção não são ressalva: são fato
            # grave, e valem 0. EPIRB com ANATEL pendente idem — sem ela o
            # sinal de socorro não é atendido.
            grave = cat in SAUDE_CRITICAS or any(
                (r.get("dados") or {}).get("epirb_anatel", "").startswith("Pend")
                for r in regs
            )
            st = "crit" if grave else "warn"
        elif "pendente" in status:
            st = "warn"
        else:
            st = "ok"
        out.append((label, st))
    return out


def _prontidao(saude: list[tuple[str, str]]) -> Optional[int]:
    """Índice de segurança — mesma fórmula do painel (ok=100, warn=50, crit=0).

    Categorias sem dado saem da média, como no painel. Retorna None se não há
    nada avaliado: melhor não exibir indicador do que exibir um inventado.
    """
    pontos, total = 0, 0
    for _, st in saude:
        if st == "na":
            continue
        total += 1
        pontos += 100 if st == "ok" else (50 if st == "warn" else 0)
    return round(pontos / total) if total else None


def _resumo_executivo(registros: list[dict], documentos: list[dict]) -> dict[str, Any]:
    """KPIs do sumário — TODOS derivados do banco. Campo sem dado vira None
    e o tile correspondente não é renderizado."""
    # Seguro NÃO é investimento no ativo — é cobertura contratada.
    #
    # A apólice do Marlin Sea traz valor 2.400.000 no mesmo campo `valor` que
    # uma revisão de R$ 9.800. Somados, a capa anunciava "R$ 2,5 mi investido
    # no ativo" quando o gasto real em manutenção e reparo era R$ 89,3 mil —
    # inflado em 27 vezes. Um comprador que confere isso duvida do dossiê
    # inteiro, e com razão.
    #
    # A cobertura continua aparecendo, em tile próprio: ela é informação
    # valiosa, só não é dinheiro gasto no barco.
    #
    # CASCO e SINISTROS entram pelo mesmo motivo, descoberto em 28/08/2026: o
    # campo `valor` nessas duas fichas não é dinheiro gasto, é dano ESTIMADO —
    # "Estimativa de custo de reparo estrutural" (servicosCategorias.ts, casco)
    # e "Estimativa inicial de prejuízo" (sinistros). Um barco que bateu e teve
    # prejuízo estimado em R$ 300 mil imprimia na capa "Investido no ativo:
    # R$ 300,0 mil" — dinheiro que ninguém gastou, anunciado como benfeitoria.
    # É o mesmo defeito da apólice reaparecendo por outro campo, e a lição é
    # que excluir POR CATEGORIA não basta: o que decide é a natureza do valor.
    CATEGORIAS_NAO_INVESTIMENTO = {"seguro", "casco", "sinistros"}
    investido = sum(
        v for v in (
            _valor_registro(r) for r in registros
            if r.get("categoria") not in CATEGORIAS_NAO_INVESTIMENTO
        ) if v is not None
    )
    cobertura = sum(
        v for v in (
            _valor_registro(r) for r in registros if r.get("categoria") == "seguro"
        ) if v is not None
    )
    # Horímetro: a leitura mais RECENTE, não a maior.
    #
    # Era `max()` de todos os registros. Mas `horimetro` é preenchido em várias
    # fichas com sentidos diferentes — motor principal, motor de bombordo, de
    # boreste, geradores — e o Ferretti 780 tem quatro leituras distintas
    # (1.480 h, 1.476 h, 1.120 h, 1.095 h). O tile escolhia a maior de todas e
    # a chamava de "Horímetro atual", no singular, sem dizer de qual máquina.
    # Pior: `max()` é o MAIOR, não o mais recente — um dígito a mais digitado
    # uma vez ficava sendo o horímetro do barco para sempre.
    #
    # Agora vale a última leitura pela data do registro, e o rótulo diz que é
    # leitura de máquina, não um número único do barco.
    _com_hora = [
        (str(r.get("created_at") or ""), _num((r.get("dados") or {}).get("horimetro")))
        for r in registros
    ]
    horimetros = [v for _, v in _com_hora if v is not None]
    _ultima_hora = None
    for _dt, _v in sorted(_com_hora, key=lambda x: x[0]):
        if _v is not None:
            _ultima_hora = _v
    datas = sorted(r.get("created_at") for r in registros if r.get("created_at"))
    # Tempo em custódia — em DIAS enquanto não fecha um mês.
    #
    # Era `max(1, round(dias / 30.44))`, que transformava um dia em "1 mês".
    # Num documento cujo valor é justamente o tempo de histórico, arredondar
    # um dia para um mês é exagero que um comprador atento pega — e o rótulo
    # ainda saía "1 MESES", no plural.
    meses = dias = None
    if datas:
        from datetime import datetime, timezone as _tz
        try:
            ini = datetime.fromisoformat(str(datas[0]).replace("Z", "+00:00"))
            dias = max(0, (datetime.now(_tz.utc) - ini).days)
            meses = round(dias / 30.44)
        except (ValueError, TypeError):
            meses = dias = None

    # Valor e rótulo andam juntos: "12 · DIAS EM CUSTÓDIA" ou "3 · MESES DE
    # CUSTÓDIA". Sem isso o rótulo era fixo no plural e mentia no singular.
    if dias is None:
        custodia_valor = custodia_rotulo = None
    elif dias < 30:
        # O dia da entrada conta como o primeiro: "0 dias em custódia" está
        # certo pelo relógio e parece defeito na tela. Isto NÃO é o arredonda-
        # mento antigo — ali um dia virava um mês; aqui o dia é a menor unidade
        # honesta que existe.
        d = max(1, dias)
        custodia_valor = str(d)
        custodia_rotulo = "Dia em custódia" if d == 1 else "Dias em custódia"
    else:
        custodia_valor = str(meses)
        custodia_rotulo = "Mês de custódia" if meses == 1 else "Meses de custódia"

    # Este número conta quantos registros TÊM selo gravado — não recalcula
    # hash nenhum. O selo é escrito por trigger no INSERT
    # (fn_registro_hash), então a coluna nunca é nula e a conta dá 100%
    # sempre. Continuava útil como "todo registro está selado", mas o rótulo
    # "HASHES ÍNTEGROS" prometia uma conferência que a emissão não faz: não
    # há uma única chamada de hash no caminho montar_dados -> gerar_pdf.
    # Renomeado no PDF para "REGISTROS COM SELO". A conferência de verdade
    # é a do leitor, contra a impressão digital do PDF.
    # Intervalo REAL coberto pelos serviços — base do custo mensal.
    _datas_servico = sorted(
        d for d in (
            (r.get("dados") or {}).get("data") or (r.get("dados") or {}).get("data_servico")
            for r in registros
        ) if d
    )
    _meses_de_servico = None
    if len(_datas_servico) >= 2:
        from datetime import datetime as _dt2
        try:
            _a = _dt2.fromisoformat(str(_datas_servico[0])[:10])
            _b = _dt2.fromisoformat(str(_datas_servico[-1])[:10])
            _m = round((_b - _a).days / 30.44)
            _meses_de_servico = _m if _m >= 1 else None
        except (ValueError, TypeError):
            _meses_de_servico = None

    com_hash = sum(1 for r in registros if r.get("hash_sha256"))
    pendencias = sum(1 for r in registros if r.get("status") in ("pendente", "atencao"))

    return {
        "investido": _brl(investido) if investido > 0 else None,
        "cobertura": _brl(cobertura) if cobertura > 0 else None,
        # Custo de propriedade: a primeira conta que um comprador faz, e o
        # dado já estava todo aqui. Só de manutenção e reparo — seguro fora,
        # pelo mesmo motivo que ele saiu do "investido".
        # Custo por mês só faz sentido depois de fechar um mês. Antes disso a
        # conta dividia tudo por "1 mês" e anunciava o gasto inteiro como se
        # fosse mensalidade.
        # Custo médio / mês — só quando há período de SERVIÇO para dividir.
        #
        # Dividia `investido` por `meses`, que é a idade do CADASTRO (contada
        # do `created_at` do primeiro registro). No onboarding normal a marina
        # sobe anos de histórico na primeira semana: trinta dias depois o
        # dossiê imprimia o gasto acumulado de uma década como se fosse
        # mensalidade. Numerador de dez anos, denominador de um mês.
        #
        # Agora o denominador é o intervalo coberto pelas datas dos serviços.
        # Sem essas datas o tile não aparece — não há como afirmar o número.
        "custo_mensal": (_brl(investido / _meses_de_servico)
                         if investido > 0 and _meses_de_servico else None),
        "registros": len(registros) or None,
        # SÓ documentos — foto tem seção e contagem próprias.
        #
        # Era `len(documentos)`: a tabela inteira, fotos junto. No dossiê do
        # Ferretti 780 a capa anunciava "28 DOCUMENTOS SELADOS" enquanto a
        # página 4 listava 10 documentos e a página 14 falava em 18 imagens —
        # 10 + 18 = 28. Quem contasse os documentos listados concluiria que a
        # capa inflou o número em quase três vezes. E a chave ainda se chamava
        # `imagens` enquanto o rótulo impresso dizia "Documentos".
        "documentos": sum(1 for d in documentos if d.get("tipo") != "foto") or None,
        "meses_custodia": meses,
        "custodia_valor": custodia_valor,
        "custodia_rotulo": custodia_rotulo,
        "horimetro": f"{_ultima_hora:.0f} h" if _ultima_hora is not None else None,
        # Quantas máquinas têm leitura própria: com mais de uma, o rótulo do
        # tile deixa de prometer um horímetro único para a embarcação.
        "horimetro_leituras": len({round(v) for v in horimetros}) or None,
        "pendencias": pendencias,
        "integridade": (
            f"{round(com_hash / len(registros) * 100)}%" if registros else None
        ),
        # ISO -> DD/MM/AAAA
        "custodia_desde": (
            "/".join(reversed(str(datas[0])[:10].split("-"))) if datas else None
        ),
    }


def _ficha_rica(r: dict) -> dict[str, Any]:
    """Extrai a ficha de serviço completa (logbook) de um registro — mesma
    estrutura para TODAS as categorias técnicas (alinhado ao painel)."""
    d = r.get("dados") or {}
    evidencias = d.get("evidencias") or []
    return {
        # Dois formulários, dois nomes: a ficha técnica grava `data`
        # (servicosCategorias.ts) e o form rápido do painel grava `data_servico`
        # (AtivoHub.tsx). Ler só um zerava a data de tudo que vem do form rápido.
        "data": d.get("data") or d.get("data_servico"),
        "servico": d.get("servico") or r.get("titulo"),
        "tipo": d.get("tipo"),
        "resp": d.get("responsavel"),
        "prestador": d.get("prestador"),
        "cnpj": d.get("cnpj"),
        "local": d.get("local"),
        "horimetro": d.get("horimetro"),
        "horas_trabalhadas": d.get("horas_trabalhadas"),
        "proxima_revisao": d.get("proxima_revisao"),
        # Idem para dinheiro: ficha técnica grava `valor`, form rápido grava `custo`.
        "valor": d.get("valor") or d.get("custo"),
        "peca": d.get("peca_descricao"),
        "peca_serie": d.get("peca_serie"),
        "peca_part_number": d.get("peca_part_number"),
        "observacao": r.get("observacao"),
        "enviado_por": d.get("enviado_por"),
        "enviado_em": d.get("enviado_em"),
        "evidencias": [
            {"slot": e.get("slot"), "nome": e.get("nome"), "hash": e.get("hash"), "url": e.get("url")}
            for e in evidencias if isinstance(e, dict)
        ],
        "status": "OK" if r.get("status") in ("registrado", "concluido") else (r.get("status") or "—"),
        # Cadeia de retificação — o dossiê mostra o erro E a correção.
        "situacao": r.get("situacao") or "vigente",
        # Redação LGPD: o campo pessoal foi apagado por direito do titular.
        # O dossiê declara isso — omitir em silêncio seria adulterar o histórico.
        "redacao_lgpd": bool(r.get("tem_redacao_lgpd")),
        "redigido_campos": r.get("redigido_campos") or [],
        "redigido_em": r.get("redigido_em"),
        "retificado_motivo": r.get("retificado_motivo"),
        "retificado_em": r.get("retificado_em"),
        "motivo_retificacao": r.get("motivo_retificacao"),
        # Passthrough completo dos campos da ficha (ex.: Diário de Bordo: condutor,
        # habilitação, horímetros, reboque, avarias) para o dossiê não perder nada.
        "campos": d,
    }


def _resumo_fotografico(documentos: list[dict]) -> dict[str, Any]:
    """Sumariza a galeria fotográfica selada por categoria (até MAX_FOTOS).

    Devolve TAMBÉM a lista das fotos que serão impressas. Antes devolvia só
    contagem, e a seção "Registro Fotográfico Certificado" saía sem uma única
    imagem — o dossiê falava das fotos e não as mostrava, num produto cujo
    principal argumento de venda é "até 460 imagens datadas e geolocalizadas".
    """
    por_cat: dict[str, int] = {}
    total = 0
    com_geo = 0
    fotos: list[dict[str, Any]] = []
    for doc in documentos:
        if doc.get("tipo") != "foto":
            continue
        # Vitrine = fotos de apresentação (interior/exterior), separadas do pool de 460
        if doc.get("categoria") == "vitrine":
            continue
        total += 1
        if doc.get("latitude") is not None and doc.get("longitude") is not None:
            com_geo += 1
        cat = str(doc.get("categoria") or "fotos").replace("galeria_", "") or "fotos"
        por_cat[cat] = por_cat.get(cat, 0) + 1
        if doc.get("url_arquivo"):
            fotos.append({
                "url": doc["url_arquivo"],
                "categoria": cat,
                "label": GALERIA_LABELS.get(cat, cat.replace("_", " ").title()),
                "descricao": doc.get("descricao") or None,
                "geo": doc.get("latitude") is not None and doc.get("longitude") is not None,
                "data": str(doc.get("uploaded_at") or doc.get("created_at") or "")[:10],
                # Prefixo do hash: prova visual de que a imagem impressa é a
                # mesma que está selada, conferível contra o painel.
                "hash": (doc.get("hash_sha256") or "")[:12].upper() or None,
            })
    categorias = [
        {"chave": k, "label": GALERIA_LABELS.get(k, k.replace("_", " ").title()), "total": v}
        for k, v in sorted(por_cat.items(), key=lambda kv: kv[1], reverse=True)
    ]
    # `fotos` sai ordenada por categoria e data: no PDF elas aparecem
    # agrupadas, e não na ordem em que subiram — o leitor procura "o casco",
    # não "o que a marina mandou na terça".
    fotos.sort(key=lambda f: (f["label"], f["data"]))
    return {"total": total, "capacidade": MAX_FOTOS, "categorias": categorias,
            "com_geo": com_geo, "fotos": fotos}


def montar_dados_dossie(ativo_id: str) -> dict[str, Any]:
    """Monta o pacote de dados do dossiê de um ativo, a partir do banco real."""
    supabase = get_supabase_admin()

    ativo_res = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
    if not ativo_res.data:
        raise ValueError("Ativo não encontrado")
    ativo = ativo_res.data[0]

    # Lê a VIEW, não a tabela: traz a situação derivada (vigente / retificado /
    # retificador). Sem isso uma retificação entraria no dossiê como registro
    # comum e o original continuaria parecendo válido.
    registros = (
        supabase.table("vw_registros_situacao").select("*")
        .eq("ativo_id", ativo_id).order("created_at").execute().data
        or []
    )
    documentos = (
        supabase.table("documentos").select("*").eq("ativo_id", ativo_id).execute().data
        or []
    )

    # As fotos do dossie vinham pela URL publica gravada no banco. Com o balde
    # fechado elas sumiriam do PDF — exatamente o defeito que consertamos em
    # 22/08. Assinadas em lote: uma chamada, e nao uma por foto no meio da
    # montagem do documento.
    from app.services.s3_service import assinar_documentos
    documentos = assinar_documentos(documentos)

    comprimento = ativo.get("comprimento") or 0

    # 01 — Identificação (da tabela ativos)
    identificacao = {
        "nome": ativo.get("nome_reg") or f"{ativo.get('marca','')} {ativo.get('modelo','')}".strip(),
        "tipo": ativo.get("tipo"),
        "fabricante": ativo.get("marca"),
        "modelo": ativo.get("modelo"),
        "ano": ativo.get("ano_fabricacao"),
        # 32.0 -> "32 pés"; 32.5 -> "32,5 pés"
        "comprimento": (
            f"{float(comprimento):g} pés".replace(".", ",") if comprimento else None
        ),
        # Nº de inscrição na Capitania. SEM cair no nome da embarcação: o campo
        # se chama "Nº de Registro" e saía preenchido com "Netuno II (TESTE)",
        # repetindo o nome que já aparece na linha de cima. Num documento que
        # cita LESTA e NORMAM, campo legal com valor de outro tipo é pior que
        # campo vazio — e a linha some sozinha quando não há dado.
        "registro": ativo.get("rgp") or None,
        "vin": ativo.get("vin"),
    }

    # ── Perfil de manutenção: preventiva × corretiva ──────────────────
    #
    # `natureza_manutencao` é campo OBRIGATÓRIO na ficha e nunca chegava ao
    # dossiê. É o dado de risco mais forte que a plataforma coleta: barco com
    # manutenção programada é outro risco — e outro preço de apólice — que
    # barco que só conserta depois da falha. Seguradora precifica exatamente
    # isso, e comprador negocia com isso.
    perfil = {"preventiva": 0, "corretiva": 0,
              "valor_preventiva": 0.0, "valor_corretiva": 0.0}
    for r in registros:
        nat = str((r.get("dados") or {}).get("natureza_manutencao") or "")
        if not nat:
            continue
        chave = "corretiva" if "orretiva" in nat else "preventiva"
        perfil[chave] += 1
        v = _valor_registro(r)
        if v:
            perfil[f"valor_{chave}"] += v
    total_nat = perfil["preventiva"] + perfil["corretiva"]
    perfil["total"] = total_nat
    perfil["pct_preventiva"] = (
        round(perfil["preventiva"] / total_nat * 100) if total_nat else None
    )
    perfil["valor_preventiva_fmt"] = _brl(perfil["valor_preventiva"]) if perfil["valor_preventiva"] else None
    perfil["valor_corretiva_fmt"] = _brl(perfil["valor_corretiva"]) if perfil["valor_corretiva"] else None

    # ── Vencimentos: o que expira, e em quantos dias ──────────────────
    #
    # Cinco datas de validade ficavam seladas dentro do JSONB de registros e
    # nenhuma aparecia. No Marlin Sea o extintor vence em 38 dias — informação
    # que decide negociação (quem paga a renovação?) e que a seguradora exige
    # saber. Estava tudo lá, sem ninguém para ler.
    vencimentos = _vencimentos(registros)

    # Comprovação fiscal e documental.
    #
    # Os documentos selados existiam no banco e NUNCA apareciam no dossiê: a
    # seção "Documentação Legal e Fiscal" listava só itens de checklist em
    # texto. O resultado é que a capa afirmava um valor investido sem exibir um
    # comprovante sequer — e comprovante é exatamente o que separa "custou
    # R$ 48 mil" de "custou R$ 48 mil, aqui está a nota, com hash".
    comprovacao = []
    for d in documentos:
        if d.get("tipo") == "foto":
            continue
        cat = str(d.get("categoria") or "")
        comprovacao.append({
            "categoria": GALERIA_LABELS.get(cat, cat.replace("_", " ").title() or "—"),
            "descricao": (d.get("descricao") or d.get("nome_arquivo") or "—"),
            "data": str(d.get("uploaded_at") or d.get("created_at") or "")[:10],
            # Prefixo do hash: é o que torna a linha conferível contra o painel.
            # Sem ele a tabela seria uma lista de nomes de arquivo.
            "hash": (d.get("hash_sha256") or "")[:12].upper() or "—",
        })
    comprovacao.sort(key=lambda x: (x["categoria"], x["data"]))

    # Especificações e motorização — as duas seções que o código declarava em
    # PORTE_MINIMO e TITULOS_DOSSIE e nunca montava. Dez colunas existiam no
    # banco e nenhuma chegava ao documento: um dossiê de "conformidade
    # náutica" que não dizia a boca da embarcação.
    def _m(v, unidade):
        n = _num(v)
        return f"{n:g} {unidade}".replace(".", ",") if n else None

    especificacoes = {
        "comprimento": (f"{float(comprimento):g} pés".replace(".", ",")
                        if comprimento else None),
        "boca": _m(ativo.get("largura"), "m"),
        "calado": _m(ativo.get("calado"), "m"),
        "material_casco": ativo.get("material_casco"),
        "passageiros": (str(ativo.get("capacidade_passageiros"))
                        if ativo.get("capacidade_passageiros") else None),
        "cabines": (str(ativo.get("num_cabines"))
                    if ativo.get("num_cabines") else None),
        "tanque": _m(ativo.get("capacidade_tanque"), "L"),
    }

    # Potência: o banco guarda HP POR MOTOR (integer). Quem lê o dossiê quer
    # os dois números — o de cada motor e o total —, porque é o total que
    # define desempenho e é a unidade que a seguradora usa.
    pot = _num(ativo.get("potencia_motor"))
    qtd = ativo.get("num_motores")
    if pot and qtd and int(qtd) > 1:
        potencia = f"{int(qtd)} × {pot:g} HP ({pot * int(qtd):g} HP total)"
    elif pot:
        potencia = f"{pot:g} HP"
    else:
        potencia = None

    motorizacao = {
        "modelo": ativo.get("modelo_motor"),
        "potencia": potencia,
        "quantidade": (str(qtd) if qtd else None),
        "combustivel": ativo.get("tipo_combustivel"),
    }

    # Titular da custódia. NOME e DOCUMENTO apenas — e-mail e telefone ficam
    # de fora de propósito: eles são chave de acesso ao Portal, e o dossiê
    # circula entre corretor, comprador e seguradora. O comprador precisa
    # saber DE QUEM é o barco, não como ligar para o dono; o contato passa
    # pela marina, que é o modelo do negócio.
    titular = {
        "nome": (ativo.get("proprietario_nome") or "").strip() or None,
        "documento": _mascarar_documento(ativo.get("proprietario_documento")),
    }

    # 02 — Proprietários (registros categoria=proprietarios)
    proprietarios = []
    for i, r in enumerate(_por_categoria(registros, "proprietarios"), start=1):
        d = r.get("dados") or {}
        proprietarios.append({
            "ordem": f"{i}º",
            "nome": d.get("nome") or r.get("titulo"),
            "periodo": d.get("periodo"),
            "tipo": d.get("tipo"),
        })

    # 03 — Documentação (checklist marcado nos registros + documentos anexados)
    documentacao = []
    for r in _por_categoria(registros, "documentacao"):
        documentacao.extend(r.get("checklist") or [])
    documentacao = sorted(set(documentacao))

    # 04+ — Seções técnicas (TODAS com a mesma ficha rica do painel/logbook).
    # Cada categoria do painel com registro vira uma seção náutica do dossiê.
    secoes_tecnicas = []
    for cat, titulo in CATEGORIAS_TECNICAS:
        regs = _por_categoria(registros, cat)
        if not regs:
            continue
        secoes_tecnicas.append({
            "categoria": cat,
            "titulo": titulo,
            "fichas": [_ficha_rica(r) for r in regs],
        })

    # Compat: mantém a chave `manutencao` (consumida hoje no PDF/preview).
    manutencao = [_ficha_rica(r) for r in _por_categoria(registros, "manutencao")]

    # Resumo fotográfico (galeria selada por categoria, até MAX_FOTOS).
    fotografico = _resumo_fotografico(documentos)

    # Custodiante: ativo.usuario_id -> profiles (nome, empresa, contato).
    # Só entra no dossiê o que estiver preenchido — nada é inventado.
    custodiante = None
    dono_id = ativo.get("usuario_id")
    if dono_id:
        prof_res = (
            supabase.table("profiles")
            .select("nome, company_name, company_type, telefone, whatsapp, email, verified")
            .eq("id", dono_id).execute()
        )
        if prof_res.data:
            p = prof_res.data[0]
            contato = " · ".join(x for x in [
                p.get("telefone") or p.get("whatsapp"), p.get("email")
            ] if x)
            custodiante = {
                "empresa": p.get("company_name"),
                "responsavel": p.get("nome"),
                "contato": contato or None,
                "verificado": bool(p.get("verified")),
            }
            if not any(v for k, v in custodiante.items() if k != "verificado"):
                custodiante = None

    # Sumário executivo + saúde — tudo derivado dos registros reais.
    #
    # A saúde depende do TIPO: veleiro tem velame e não motor, jet ski não tem
    # interior nem pintura. Sem isso, uma lancha saía com "Velame & Rigging ·
    # NÃO AVALIADO" no relatório entregue ao comprador.
    saude = _saude_por_categoria(registros, ativo.get("tipo"))

    # O percentual vem acompanhado do denominador. "100%" com cinco sistemas
    # NÃO AVALIADOS é verdade pela fórmula e mentira para quem lê.
    avaliados = sum(1 for _, st in saude if st != "na")

    return {
        "ativo_id": ativo_id,
        "comprimento_pes": comprimento,
        "classificacao": (ativo.get("classificacao") or "").upper() or None,
        "custodiante": custodiante,
        "resumo": _resumo_executivo(registros, documentos),
        "saude": saude,
        "prontidao": _prontidao(saude),
        "prontidao_avaliados": avaliados,
        "prontidao_total": len(saude),
        "identificacao": identificacao,
        "titular": titular,
        "comprovacao": comprovacao,
        "perfil_manutencao": perfil,
        "vencimentos": vencimentos,
        "especificacoes": especificacoes,
        "motorizacao_ficha": motorizacao,
        "proprietarios": proprietarios,
        "documentacao": documentacao,
        "manutencao": manutencao,
        # NOVO: seções técnicas alinhadas ao painel (rico) + resumo de fotos
        "secoes_tecnicas": secoes_tecnicas,
        "fotografico": fotografico,
        # registros crus por categoria (para as demais seções do dossiê)
        "registros": registros,
        "documentos": documentos,
        "secoes": secoes_aplicaveis(comprimento, registros),
    }


def secoes_aplicaveis(comprimento_pes: float, registros: list[dict]) -> list[str]:
    """
    Seções que entram no dossiê: aplicáveis ao porte E (para as opcionais)
    que tenham ao menos um registro. Garante "nenhuma seção vazia".
    """
    cats_com_dado = {r.get("categoria") for r in registros}
    sempre = {"identificacao", "documentacao", "manutencao", "fotografico"}
    aplicaveis = []
    for cat, minimo in PORTE_MINIMO.items():
        if comprimento_pes < minimo:
            continue
        if cat in sempre or cat in cats_com_dado:
            aplicaveis.append(cat)
    return aplicaveis
