"""
Yachts Atlas — Dossiê (montagem de dados reais a partir do banco)
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.security import verify_token
from app.services.dossie_data import montar_dados_dossie

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


# PRÓXIMO PASSO (rodar/testar no backend com python + reportlab):
#   @router.get("/{ativo_id}/pdf") -> usar montar_dados_dossie() para alimentar
#   o dossie_engine (sections.py) e devolver o PDF gerado a partir de dados reais.
#   Requer o dossie_engine importável no PYTHONPATH e reportlab instalado.
