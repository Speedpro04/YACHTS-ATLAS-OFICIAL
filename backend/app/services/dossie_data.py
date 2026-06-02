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


def _por_categoria(registros: list[dict], categoria: str) -> list[dict]:
    return [r for r in registros if r.get("categoria") == categoria]


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

    # 04 — Manutenção (registros categoria=manutencao)
    manutencao = []
    for r in _por_categoria(registros, "manutencao"):
        d = r.get("dados") or {}
        manutencao.append({
            "data": d.get("data"),
            "servico": d.get("servico") or r.get("titulo"),
            "resp": d.get("responsavel"),
            "status": "OK" if r.get("status") in ("registrado", "concluido") else (r.get("status") or "—"),
        })

    return {
        "ativo_id": ativo_id,
        "comprimento_pes": comprimento,
        "identificacao": identificacao,
        "proprietarios": proprietarios,
        "documentacao": documentacao,
        "manutencao": manutencao,
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
