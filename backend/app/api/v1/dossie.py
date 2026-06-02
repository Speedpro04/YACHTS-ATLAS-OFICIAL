"""
Yachts Atlas — Dossiê (montagem de dados reais a partir do banco)
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from app.core.security import verify_token
from app.services.dossie_data import montar_dados_dossie
from app.services.dossie_pdf import gerar_pdf_dossie

router = APIRouter()


@router.get("/{ativo_id}/dados")
async def dados_dossie(ativo_id: str, token: dict = Depends(verify_token)):
    """
    Retorna o pacote de dados do dossiê montado a partir do banco real
    (ativos + registros + documentos). É a fonte que o gerador de PDF consome.
    """
    try:
        return montar_dados_dossie(ativo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ativo_id}/pdf")
async def pdf_dossie(ativo_id: str, token: dict = Depends(verify_token)):
    """Gera o PDF do dossiê a partir dos dados reais do banco (só seções com dado)."""
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
