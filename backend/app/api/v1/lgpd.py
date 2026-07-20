"""
Yachts Atlas — LGPD: direitos do titular (Art. 18).

Contexto que justifica este módulo existir:

  `registros` é append-only. UPDATE e DELETE são recusados pelo banco, mesmo
  para service_role — é o que sustenta a promessa de custódia. Mas o diário de
  bordo guarda nome do condutor, habilitação e número do CHA: dado pessoal de
  gente identificável. Quando o titular exerce o direito de eliminação,
  "é imutável, não posso" não se sustenta perante a ANPD.

  A saída não é afrouxar a imutabilidade. É abrir UMA porta estreita, auditada
  e autovalidada: `public.fn_lgpd_redigir()`. Ela só apaga campos de uma lista
  fechada, exige vínculo com a solicitação do titular, preserva o hash original
  e marca o registro. O conteúdo técnico continua intocável — a própria trigger
  recusa qualquer tentativa de usar esse caminho para outra coisa.

  E o dossiê DECLARA a redação. Apagar em silêncio seria adulterar o histórico,
  que é o oposto do que o produto promete.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from app.core.supabase import get_supabase_admin
from app.core.security import get_current_user_id

router = APIRouter()


def _exige_admin(supabase, user_id: str) -> None:
    """Redação de dado pessoal é ato administrativo — não é do dono do ativo."""
    if user_id == "maintenance-admin":
        return
    prof = supabase.table("profiles").select("user_role").eq("id", user_id).execute()
    papel = prof.data[0].get("user_role") if prof.data else None
    if papel != "admin":
        raise HTTPException(
            status_code=403,
            detail="Somente a administração da plataforma pode atender solicitações LGPD.",
        )


class SolicitacaoCreate(BaseModel):
    tipo: str = Field(default="eliminacao",
                      pattern="^(eliminacao|acesso|correcao|portabilidade)$")
    titular_nome: Optional[str] = None
    titular_contato: Optional[str] = None
    descricao: str = Field(min_length=10)


class RedacaoCreate(BaseModel):
    registro_id: str
    solicitacao_id: str
    # None = todos os campos pessoais presentes no registro
    campos: Optional[list[str]] = None


@router.post("/solicitacoes")
async def abrir_solicitacao(
    data: SolicitacaoCreate, user_id: str = Depends(get_current_user_id)
):
    """Registra um pedido do titular. É a trilha que a ANPD pode exigir."""
    supabase = get_supabase_admin()
    _exige_admin(supabase, user_id)
    r = supabase.table("lgpd_solicitacoes").insert(data.model_dump()).execute()
    return r.data[0] if r.data else {}


@router.get("/solicitacoes")
async def listar_solicitacoes(user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()
    _exige_admin(supabase, user_id)
    r = (supabase.table("lgpd_solicitacoes").select("*")
         .order("solicitado_em", desc=True).execute())
    return r.data or []


@router.get("/dados-pessoais/{ativo_id}")
async def mapear_dados_pessoais(
    ativo_id: str, user_id: str = Depends(get_current_user_id)
):
    """Onde há dado pessoal neste ativo — atende o direito de ACESSO (Art. 18, II)
    e mostra ao operador o que seria afetado antes de redigir."""
    supabase = get_supabase_admin()
    _exige_admin(supabase, user_id)

    campos = supabase.rpc("fn_lgpd_campos_pessoais").execute().data or []
    regs = (supabase.table("registros")
            .select("id, categoria, titulo, dados, redigido_em, redigido_campos")
            .eq("ativo_id", ativo_id).execute().data or [])

    achados = []
    for r in regs:
        d = r.get("dados") or {}
        presentes = {k: d[k] for k in campos if k in d and d[k]}
        if presentes:
            achados.append({
                "registro_id": r["id"],
                "categoria": r.get("categoria"),
                "titulo": r.get("titulo"),
                "campos": presentes,
                "ja_redigido": bool(r.get("redigido_em")),
                "redigido_campos": r.get("redigido_campos") or [],
            })
    return {"ativo_id": ativo_id, "registros_com_dado_pessoal": len(achados),
            "campos_monitorados": campos, "detalhe": achados}


@router.post("/redigir")
async def redigir(data: RedacaoCreate, user_id: str = Depends(get_current_user_id)):
    """Executa a eliminação de dado pessoal num registro selado.

    IRREVERSÍVEL: o dado é substituído por um marcador e não há como recuperar.
    O hash é recalculado e o original preservado em `hash_pre_redacao`, para a
    divergência ficar documentada em vez de parecer adulteração.
    """
    supabase = get_supabase_admin()
    _exige_admin(supabase, user_id)
    try:
        r = supabase.rpc("fn_lgpd_redigir", {
            "p_registro_id": data.registro_id,
            "p_solicitacao": data.solicitacao_id,
            "p_campos": data.campos,
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    resultado = (r.data or [{}])[0]
    supabase.table("lgpd_solicitacoes").update({
        "status": "atendida",
        "atendido_em": "now()",
    }).eq("id", data.solicitacao_id).execute()

    return {
        "message": "Dado pessoal removido. O registro técnico permanece íntegro.",
        **resultado,
    }
