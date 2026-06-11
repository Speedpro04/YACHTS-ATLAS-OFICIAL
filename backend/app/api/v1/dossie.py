"""
Yachts Atlas — Dossiê (montagem de dados reais a partir do banco)
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from app.core.config import settings
from app.core.security import get_current_user
from app.core.supabase import get_supabase_admin
from app.core.authz import get_ativo_autorizado
from app.services.dossie_data import montar_dados_dossie
from app.services.dossie_pdf import gerar_pdf_dossie

router = APIRouter()


def _assert_acesso_ativo(ativo_id: str, user: dict) -> None:
    """Só o dono/marina do ativo (ou admin da plataforma) acessa o dossiê."""
    get_ativo_autorizado(ativo_id, str(user["sub"]))


def _assert_dossie_pago(ativo_id: str) -> None:
    """Exige pagamento do dossiê quando DOSSIER_REQUIRE_PAYMENT=true."""
    if not settings.DOSSIER_REQUIRE_PAYMENT:
        return
    supabase = get_supabase_admin()
    res = (
        supabase.table("payments")
        .select("id")
        .eq("ativo_id", ativo_id)
        .eq("payment_type", "dossier")
        .eq("status", "completed")
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=402, detail="Dossiê ainda não foi adquirido para este ativo")


@router.get("/{ativo_id}/dados")
async def dados_dossie(ativo_id: str, user: dict = Depends(get_current_user)):
    """
    Retorna o pacote de dados do dossiê montado a partir do banco real
    (ativos + registros + documentos). É a fonte que o gerador de PDF consome.
    """
    _assert_acesso_ativo(ativo_id, user)
    try:
        return montar_dados_dossie(ativo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ativo_id}/pdf")
async def pdf_dossie(ativo_id: str, user: dict = Depends(get_current_user)):
    """Gera o PDF do dossiê a partir dos dados reais do banco (só seções com dado)."""
    _assert_acesso_ativo(ativo_id, user)
    _assert_dossie_pago(ativo_id)
    try:
        dados = montar_dados_dossie(ativo_id)
        pdf = gerar_pdf_dossie(dados)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="dossie_{ativo_id}.pdf"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
