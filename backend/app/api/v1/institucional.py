"""
Yachts Atlas — Material institucional (vídeo de boas-vindas)

O vídeo que a Marina vê depois de assinar não é documento de cliente, mas
também não é público: ele mostra telas do sistema por dentro, e quem paga é
quem deve ver. Por isso mora no mesmo balde privado (`media`), fora de
`ativos/`, e sai daqui assinado — nunca por URL pública.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.security import get_current_user_id
from app.services.s3_service import get_s3_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Uma hora é bem mais que os 4 minutos do vídeo, e curto o suficiente para que
# um link copiado da aba de rede não vire distribuição.
VALIDADE_SEGUNDOS = 3600

VIDEO_BOAS_VINDAS = "institucional/boas-vindas/video-boas-vindas-marina.mp4"


@router.get("/boas-vindas")
async def video_boas_vindas(user_id: str = Depends(get_current_user_id)):
    """Link assinado do vídeo de boas-vindas da Marina.

    Sem `ativo_id` e sem autorização por embarcação de propósito: o material é
    o mesmo para toda Marina assinante, e a única pergunta que importa é se
    quem pede está autenticado.
    """
    try:
        url = get_s3_service().get_presigned_url(VIDEO_BOAS_VINDAS, VALIDADE_SEGUNDOS)
    except Exception as e:  # noqa: BLE001
        # Falhar com nome: sem isto, a tela mostraria um player mudo e ninguém
        # saberia se o vídeo sumiu do balde ou se a assinatura quebrou.
        logger.error("Falha ao assinar o video de boas-vindas: %s", e)
        raise HTTPException(status_code=503, detail="Vídeo indisponível no momento")

    return {"url": url, "validade_segundos": VALIDADE_SEGUNDOS}
