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
    ("motor", "Motorização & Propulsão"),
    ("velame", "Mastro, Rigging & Velame"),
    ("eletrica", "Sistema Elétrico & Eletrônica de Navegação"),
    ("seguranca", "Segurança & Salvatagem"),
    ("pintura", "Casco, Pintura & Acabamento"),
    ("interior", "Interior & Acomodações"),
    ("seguro", "Seguro & Cobertura"),
]

# Rótulos náuticos da galeria fotográfica (espelha GALERIA_CATS no front).
GALERIA_LABELS: dict[str, str] = {
    "casco_exterior": "Casco / Exterior",
    "motor": "Motor / Propulsão",
    "pintura": "Pintura",
    "interior": "Interior",
    "eletronica": "Eletrônica / Navegação",
    "notas_fiscais": "Notas Fiscais",
    "antes_depois": "Antes e Depois",
    "outros": "Outros",
    "fotos": "Registro Geral",
}

MAX_FOTOS = 400  # capacidade fotográfica por embarcação (espelha o front)


def _por_categoria(registros: list[dict], categoria: str) -> list[dict]:
    return [r for r in registros if r.get("categoria") == categoria]


def _ficha_rica(r: dict) -> dict[str, Any]:
    """Extrai a ficha de serviço completa (logbook) de um registro — mesma
    estrutura para TODAS as categorias técnicas (alinhado ao painel)."""
    d = r.get("dados") or {}
    evidencias = d.get("evidencias") or []
    return {
        "data": d.get("data"),
        "servico": d.get("servico") or r.get("titulo"),
        "tipo": d.get("tipo"),
        "resp": d.get("responsavel"),
        "prestador": d.get("prestador"),
        "cnpj": d.get("cnpj"),
        "local": d.get("local"),
        "horimetro": d.get("horimetro"),
        "horas_trabalhadas": d.get("horas_trabalhadas"),
        "proxima_revisao": d.get("proxima_revisao"),
        "valor": d.get("valor"),
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
    }


def _resumo_fotografico(documentos: list[dict]) -> dict[str, Any]:
    """Sumariza a galeria fotográfica selada por categoria (até MAX_FOTOS)."""
    por_cat: dict[str, int] = {}
    total = 0
    com_geo = 0
    for doc in documentos:
        if doc.get("tipo") != "foto":
            continue
        # Vitrine = fotos de apresentação (interior/exterior), separadas do pool de 400
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

    registros = (
        supabase.table("registros").select("*").eq("ativo_id", ativo_id).order("created_at").execute().data
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
        "comprimento": f"{comprimento} pés" if comprimento else None,
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

    return {
        "ativo_id": ativo_id,
        "comprimento_pes": comprimento,
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
