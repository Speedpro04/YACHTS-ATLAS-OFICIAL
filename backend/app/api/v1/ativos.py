"""
Yachts Atlas — Ativos Endpoints
Alinhado ao schema REAL do banco (legado): ativos.usuario_id + ativos.comprimento.
Usa a chave de serviço (o backend já autentica o usuário via get_current_user_id).
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.models import AtivoCreate
from app.core.supabase import get_supabase_admin
from app.core.security import get_current_user_id
from datetime import datetime, timezone
import uuid

router = APIRouter()


def _role(supabase, user_id: str) -> str | None:
    if user_id == "maintenance-admin":
        return "admin"
    prof = supabase.table("profiles").select("user_role").eq("id", user_id).execute()
    return prof.data[0].get("user_role") if prof.data else None


def _enrich(ativo: dict) -> dict:
    """Compat com o frontend: expõe comprimento_pes a partir de comprimento."""
    if ativo is not None and "comprimento_pes" not in ativo:
        ativo["comprimento_pes"] = ativo.get("comprimento")
    return ativo


def _anexar_total_fotos(supabase, ativos: list[dict]) -> None:
    """Conta as fotos (tipo='foto') de cada ativo em UMA única consulta (sem N+1)
    e injeta `total_fotos` em cada item. Falha de forma silenciosa => 0."""
    ids = [a["id"] for a in ativos if a.get("id")]
    contagem: dict[str, int] = {}
    if ids:
        try:
            # Exclui a vitrine (fotos de apresentação, separadas do pool de 400)
            res = (
                supabase.table("documentos")
                .select("ativo_id")
                .in_("ativo_id", ids)
                .eq("tipo", "foto")
                .neq("categoria", "vitrine")
                .execute()
            )
            for row in (res.data or []):
                aid = row.get("ativo_id")
                if aid:
                    contagem[aid] = contagem.get(aid, 0) + 1
        except Exception:
            pass
    for a in ativos:
        a["total_fotos"] = contagem.get(a.get("id"), 0)


@router.get("")
async def list_ativos(
    incluir_arquivados: bool = False,
    user_id: str = Depends(get_current_user_id),
):
    """Lista os ativos em operação.

    Arquivado sai da lista por padrão — mas continua no banco com todo o
    histórico selado, e volta com `?incluir_arquivados=true`. Arquivar é o
    substituto da exclusão: registro selado não pode ser apagado.
    """
    supabase = get_supabase_admin()
    role = _role(supabase, user_id)
    q = supabase.table("ativos").select("*")
    if role != "admin":
        q = q.eq("usuario_id", user_id)
    if not incluir_arquivados:
        q = q.is_("arquivado_em", "null")
    response = q.order("created_at", desc=True).execute()
    ativos = [_enrich(a) for a in (response.data or [])]
    _anexar_total_fotos(supabase, ativos)
    return ativos


@router.post("")
async def create_ativo(ativo: AtivoCreate, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()

    tipo = ativo.tipo.value if hasattr(ativo.tipo, "value") else ativo.tipo
    ativo_id = f"YA-{str(tipo).upper()}-{ativo.ano_fabricacao}-{str(uuid.uuid4())[:4].upper()}"

    # Dono do ativo = usuário logado (ou owner_id explícito, se enviado).
    owner = str(ativo.owner_id) if getattr(ativo, "owner_id", None) else user_id
    if owner == "maintenance-admin":
        owner = None

    data = {
        "id": ativo_id,
        "usuario_id": owner,
        "tipo": tipo,
        "marca": ativo.marca,
        "modelo": ativo.modelo,
        "ano_fabricacao": ativo.ano_fabricacao,
        "classificacao": "bronze",
        "progresso": 0,
        "status": "ativo",
    }

    # Coluna real é 'comprimento'. Aceita comprimento_pes (front) ou metros.
    comp = getattr(ativo, "comprimento_pes", None) or getattr(ativo, "comprimento_metres", None)
    if comp:
        data["comprimento"] = comp

    # Campos técnicos opcionais que existem no schema real
    for attr, col in [
        ("largura", "largura"),
        ("calado", "calado"),
        ("capacidade_passageiros", "capacidade_passageiros"),
    ]:
        v = getattr(ativo, attr, None)
        if v:
            data[col] = v
    mat = getattr(ativo, "material_casco", None)
    if mat:
        data["material_casco"] = mat.value if hasattr(mat, "value") else mat

    try:
        response = supabase.table("ativos").insert(data).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao cadastrar embarcação: {e}")

    if response.data:
        return _enrich(response.data[0])
    raise HTTPException(status_code=400, detail="Falha ao cadastrar embarcação")


@router.get("/{ativo_id}")
async def get_ativo(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()
    response = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    role = _role(supabase, user_id)
    if role != "admin" and str(ativo.get("usuario_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized for this asset")
    ativo = _enrich(ativo)
    _anexar_total_fotos(supabase, [ativo])
    return ativo


@router.delete("/{ativo_id}")
async def arquivar_ativo(
    ativo_id: str,
    motivo: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """Arquiva o ativo. NÃO exclui.

    Um ativo com registros selados não pode ser apagado: a cadeia de custódia
    é o produto. Arquivar tira o ativo da operação e preserva o histórico.
    """
    supabase = get_supabase_admin()
    response = supabase.table("ativos").select("id, usuario_id, arquivado_em").eq("id", ativo_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    role = _role(supabase, user_id)
    if role != "admin" and str(ativo.get("usuario_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to archive this asset")
    if ativo.get("arquivado_em"):
        raise HTTPException(status_code=409, detail="Ativo já está arquivado")

    # arquivado_por é uuid; o acesso de manutenção usa o literal "maintenance-admin"
    try:
        arquivado_por = str(uuid.UUID(str(user_id)))
    except (ValueError, AttributeError, TypeError):
        arquivado_por = None
        motivo = f"[{user_id}] {motivo or 'arquivado via acesso de manutenção'}"

    supabase.table("ativos").update({
        "arquivado_em": datetime.now(timezone.utc).isoformat(),
        "arquivado_por": arquivado_por,
        "arquivado_motivo": motivo,
    }).eq("id", ativo_id).execute()

    return {
        "message": "Ativo arquivado",
        "ativo_id": ativo_id,
        "historico_preservado": True,
    }


@router.get("/{ativo_id}/progresso")
async def get_progresso(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()
    response = supabase.table("ativos").select("progresso, classificacao, usuario_id").eq("id", ativo_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    role = _role(supabase, user_id)
    if role != "admin" and str(ativo.get("usuario_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this asset progress")
    try:
        from app.services.asset_score_service import calcular_saude_ativo
        return calcular_saude_ativo(ativo_id)
    except Exception:
        return {"progresso": ativo["progresso"], "classificacao": ativo["classificacao"]}
