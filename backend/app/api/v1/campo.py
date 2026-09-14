"""
Yachts Atlas — códigos do app de campo.

A Marina gera, entrega ao colaborador e revoga quando quiser. O código não abre
o painel: serve só para enviar pré-dado. A razão de existir e o desenho do
fail-closed estão em `app/core/campo.py`.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.campo import criar_codigo, token_do_codigo
from app.core.security import get_current_user
from app.core.supabase import get_supabase_admin

router = APIRouter()
logger = logging.getLogger(__name__)


class EntrarBody(BaseModel):
    codigo: str


class NovoCodigoBody(BaseModel):
    apelido: str = "Aparelho de campo"


@router.post("/entrar")
async def entrar(body: EntrarBody):
    """Troca o código pelo token de campo. Rota pública, como todo login."""
    codigo = (body.codigo or "").strip()
    if not codigo:
        raise HTTPException(status_code=400, detail="Informe o código.")
    return token_do_codigo(codigo)


@router.post("/codigos")
async def novo_codigo(body: NovoCodigoBody, token: dict = Depends(get_current_user)):
    """Gera um código para esta Marina e o devolve UMA vez.

    Quem cria é a conta da Marina, autenticada normalmente — o código de campo
    não pode gerar outro código, senão o colaborador se multiplicaria sozinho.
    Isso sai de graça do fail-closed: esta rota usa `get_current_user`, que
    recusa token de campo.
    """
    usuario_id = token.get("sub")
    if not usuario_id or usuario_id == "maintenance-admin":
        raise HTTPException(status_code=400, detail="Entre com a conta da Marina para gerar o código.")

    codigo = criar_codigo(usuario_id, body.apelido, usuario_id)
    return {
        "codigo": codigo,
        "apelido": body.apelido,
        "aviso": "Anote agora: este código não é exibido de novo.",
    }


@router.get("/codigos")
async def listar_codigos(token: dict = Depends(get_current_user)):
    """Os aparelhos desta Marina. Sem o código — ele não existe mais em claro."""
    usuario_id = token.get("sub")
    supabase = get_supabase_admin()
    linhas = (
        supabase.table("codigos_campo")
        .select("id, apelido, criado_em, revogado_em, ultimo_uso_em")
        .eq("usuario_id", usuario_id).order("criado_em", desc=True).execute().data
        or []
    )
    return {"codigos": linhas}


@router.post("/codigos/{codigo_id}/revogar")
async def revogar(codigo_id: str, token: dict = Depends(get_current_user)):
    """Corta o acesso daquele aparelho. Vale na requisição seguinte.

    A linha não é apagada: o pré-dado que aquele aparelho mandou continua
    rastreável até ele. Revogar é tirar o acesso, não reescrever a história.
    """
    usuario_id = token.get("sub")
    supabase = get_supabase_admin()

    linha = (
        supabase.table("codigos_campo").select("id, usuario_id")
        .eq("id", codigo_id).limit(1).execute().data
        or []
    )
    if not linha or str(linha[0].get("usuario_id")) != str(usuario_id):
        raise HTTPException(status_code=404, detail="Código não encontrado")

    supabase.table("codigos_campo").update({
        "revogado_em": datetime.now(timezone.utc).isoformat(),
        "revogado_por": usuario_id,
    }).eq("id", codigo_id).execute()
    return {"id": codigo_id, "revogado": True}
