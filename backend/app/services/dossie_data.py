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
}

MAX_FOTOS = 430  # capacidade fotográfica por embarcação (espelha o front)


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
SAUDE_CATEGORIAS: list[tuple[str, str]] = [
    ("documentacao", "Documentação"), ("manutencao", "Manutenção"),
    ("motor", "Motor"), ("eletrica", "Elétrica"),
    ("seguranca", "Segurança"), ("pintura", "Pintura"),
    ("interior", "Interior"), ("dossie", "Dossiê"),
]


def _saude_por_categoria(registros: list[dict]) -> list[tuple[str, str]]:
    """Status por categoria, com a MESMA semântica do painel.

    Sem registro na categoria => 'na' (não avaliado). Nunca inventa 'ok'.
    """
    out = []
    for cat, label in SAUDE_CATEGORIAS:
        regs = _por_categoria(registros, cat)
        if not regs:
            out.append((label, "na"))
            continue
        status = {r.get("status") for r in regs}
        if "atencao" in status:
            st = "crit" if any(
                (r.get("dados") or {}).get("epirb_anatel", "").startswith("Pend")
                for r in regs
            ) else "warn"
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
    def _valor(r):
        d = r.get("dados") or {}
        return _num(d.get("valor")) or _num(d.get("custo"))

    investido = sum(v for v in (_valor(r) for r in registros) if v is not None)
    horimetros = [
        v for v in (_num((r.get("dados") or {}).get("horimetro")) for r in registros)
        if v is not None
    ]
    datas = sorted(r.get("created_at") for r in registros if r.get("created_at"))
    meses = None
    if datas:
        from datetime import datetime, timezone as _tz
        try:
            ini = datetime.fromisoformat(str(datas[0]).replace("Z", "+00:00"))
            delta = datetime.now(_tz.utc) - ini
            meses = max(1, round(delta.days / 30.44))
        except (ValueError, TypeError):
            meses = None

    com_hash = sum(1 for r in registros if r.get("hash_sha256"))
    pendencias = sum(1 for r in registros if r.get("status") in ("pendente", "atencao"))

    return {
        "investido": _brl(investido) if investido > 0 else None,
        "registros": len(registros) or None,
        "imagens": len(documentos) or None,
        "meses_custodia": meses,
        "horimetro": f"{max(horimetros):.0f} h" if horimetros else None,
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
    """Sumariza a galeria fotográfica selada por categoria (até MAX_FOTOS)."""
    por_cat: dict[str, int] = {}
    total = 0
    com_geo = 0
    for doc in documentos:
        if doc.get("tipo") != "foto":
            continue
        # Vitrine = fotos de apresentação (interior/exterior), separadas do pool de 430
        if doc.get("categoria") == "vitrine":
            continue
        total += 1
        if doc.get("latitude") is not None and doc.get("longitude") is not None:
            com_geo += 1
        cat = str(doc.get("categoria") or "fotos").replace("galeria_", "") or "fotos"
        por_cat[cat] = por_cat.get(cat, 0) + 1
    categorias = [
        {"chave": k, "label": GALERIA_LABELS.get(k, k.replace("_", " ").title()), "total": v}
        for k, v in sorted(por_cat.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return {"total": total, "capacidade": MAX_FOTOS, "categorias": categorias, "com_geo": com_geo}


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
        "registro": ativo.get("rgp") or ativo.get("nome_reg"),
        "vin": ativo.get("vin"),
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
    saude = _saude_por_categoria(registros)

    return {
        "ativo_id": ativo_id,
        "comprimento_pes": comprimento,
        "classificacao": (ativo.get("classificacao") or "").upper() or None,
        "custodiante": custodiante,
        "resumo": _resumo_executivo(registros, documentos),
        "saude": saude,
        "prontidao": _prontidao(saude),
        "identificacao": identificacao,
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
