"""
Yachts Atlas — Índice de Saúde do Ativo (Asset Score)

Calcula, a partir dos dados REAIS do cofre (registros + documentos), uma nota
0–100 que sobe conforme o dono/marina alimenta manutenção, laudos e documentos.
A nota vira argumento de venda (para o broker) e selo de confiança (para a
seguradora). Também devolve um mapa de saúde por categoria que alimenta o
painel visual (AssetHealthDashboard).

Pesos (transparentes, fáceis de ajustar):
  50%  abrangência — quantas das 10 categorias-núcleo têm ao menos 1 registro
  25%  profundidade de manutenção — volume de registros de motor/mecânica/serviços
  15%  documentos — volume e verificação de integridade (SHA-256)
  10%  integridade estrutural — existência de laudo de casco/estrutura
"""
from typing import Any, Optional

from app.core.supabase import get_supabase_admin


# Categorias-núcleo (espelham registros_checklists.CategoriaChecklist)
CORE_CATEGORIAS = [
    "documentacao_legal",
    "motor_propulsao",
    "manutencao_mecanica",
    "eletrica_eletronica",
    "seguranca_salvatagem",
    "integridade_estrutural",
    "pintura_acabamento",
    "rastreabilidade_servicos",
    "interior_acomodacoes",
    "navegabilidade",
]

# Mapeia categoria do registro -> "balde" de saúde do painel visual
CAT_TO_HEALTH = {
    "documentacao_legal": "documentacao",
    "navegabilidade": "documentacao",
    "motor_propulsao": "motor",
    "manutencao_mecanica": "manutencao",
    "rastreabilidade_servicos": "manutencao",
    "integridade_estrutural": "manutencao",
    "eletrica_eletronica": "eletrica",
    "seguranca_salvatagem": "seguranca",
    "pintura_acabamento": "pintura",
    "interior_acomodacoes": "interior",
}

HEALTH_BUCKETS = ["documentacao", "manutencao", "motor", "eletrica",
                  "seguranca", "pintura", "interior", "dossie"]

STATUS_OK = {"registrado", "concluido"}
STATUS_ALERTA = {"atencao", "pendente"}


def _classificar(score: int) -> str:
    if score >= 80:
        return "gold"
    if score >= 50:
        return "silver"
    return "bronze"


def _health_map(registros: list[dict], score: int, docs_verificados: int) -> dict[str, str]:
    """Status (ok/warning/critical/na/info) por categoria do painel."""
    por_balde: dict[str, list[str]] = {b: [] for b in HEALTH_BUCKETS}
    for r in registros:
        balde = CAT_TO_HEALTH.get(r.get("categoria"))
        if balde:
            por_balde[balde].append(r.get("status") or "registrado")

    health: dict[str, str] = {}
    for balde in HEALTH_BUCKETS:
        if balde == "dossie":
            health[balde] = "ok" if (score >= 60 and docs_verificados > 0) else "info"
            continue
        status_list = por_balde[balde]
        if not status_list:
            health[balde] = "na"
        elif any(s in STATUS_ALERTA for s in status_list):
            health[balde] = "warning"
        elif all(s in STATUS_OK for s in status_list):
            health[balde] = "ok"
        else:
            health[balde] = "warning"
    return health


def calcular_saude_ativo(ativo_id: str, persistir: bool = True) -> dict[str, Any]:
    """Calcula o Asset Score do ativo a partir do banco real."""
    supabase = get_supabase_admin()

    registros = (
        supabase.table("registros").select("categoria, status").eq("ativo_id", ativo_id).execute().data
        or []
    )
    documentos = (
        supabase.table("documentos").select("status").eq("ativo_id", ativo_id).execute().data
        or []
    )

    cats_presentes = {r.get("categoria") for r in registros if r.get("categoria")}

    # 50% — abrangência
    abrangencia = len([c for c in CORE_CATEGORIAS if c in cats_presentes]) / len(CORE_CATEGORIAS)

    # 25% — profundidade de manutenção (registros de motor/mecânica/serviços)
    manut_cats = {"motor_propulsao", "manutencao_mecanica", "rastreabilidade_servicos"}
    manut_count = len([r for r in registros if r.get("categoria") in manut_cats])
    profundidade = min(1.0, manut_count / 6.0)

    # 15% — documentos (volume * taxa de verificação de integridade)
    total_docs = len(documentos)
    verificados = len([d for d in documentos if d.get("status") in ("verified", "verificado")])
    volume_docs = min(1.0, total_docs / 8.0)
    taxa_verif = (verificados / total_docs) if total_docs else 0.0
    docs_score = volume_docs * (0.5 + 0.5 * taxa_verif)  # volume conta mesmo sem verificação

    # 10% — integridade estrutural (laudo de casco/estrutura presente)
    estrutural = 1.0 if "integridade_estrutural" in cats_presentes else 0.0

    score_frac = (
        0.50 * abrangencia
        + 0.25 * profundidade
        + 0.15 * docs_score
        + 0.10 * estrutural
    )
    score = int(round(score_frac * 100))
    classificacao = _classificar(score)

    resultado = {
        "progresso": score,            # compat com o campo/endpoint existente
        "classificacao": classificacao,
        "score": score,
        "health": _health_map(registros, score, verificados),
        "resumo": {
            "categorias_presentes": len(cats_presentes),
            "categorias_total": len(CORE_CATEGORIAS),
            "registros_total": len(registros),
            "documentos_total": total_docs,
            "documentos_verificados": verificados,
        },
        "componentes": {
            "abrangencia": round(abrangencia, 3),
            "profundidade_manutencao": round(profundidade, 3),
            "documentos": round(docs_score, 3),
            "integridade_estrutural": round(estrutural, 3),
        },
    }

    # Persiste de volta no ativo para refletir nas listagens (best-effort).
    if persistir:
        try:
            supabase.table("ativos").update({
                "progresso": score,
                "classificacao": classificacao,
            }).eq("id", ativo_id).execute()
        except Exception:
            pass

    return resultado
