"""
Yachts Atlas — Classificação de fotos por visão (semi-automática).

Sugere a categoria da galeria de uma foto da embarcação. A sugestão é só um
ponto de partida: o usuário confirma/corrige na interface. Degrada com
segurança para 'outros' se a OpenAI não estiver configurada ou falhar.

Usa o mesmo modelo do projeto (settings.OPENAI_CHAT_MODEL, ex.: gpt-5-mini),
que é de raciocínio — por isso `max_completion_tokens` (não `max_tokens`) e
sem `temperature`.
"""
import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Chaves válidas (espelha GALERIA_CATS no frontend)
CATEGORIAS = {
    "casco_exterior", "motor", "pintura", "interior",
    "eletronica", "notas_fiscais", "antes_depois", "outros",
}

_client: Optional[Any] = None
_init_tried = False

_PROMPT = (
    "Você classifica UMA foto ligada a uma embarcação (iate/lancha) para um dossiê. "
    "Escolha a MELHOR categoria entre estas chaves exatas:\n"
    "- casco_exterior: casco, deck/convés, vista externa do barco\n"
    "- motor: motor, propulsão, casa de máquinas\n"
    "- pintura: pintura, gelcoat, antifouling, acabamento de superfície\n"
    "- interior: cabines, salão, cozinha, acomodações internas\n"
    "- eletronica: navegação, painéis, eletrônica, instrumentos\n"
    "- notas_fiscais: nota fiscal, recibo, documento com texto\n"
    "- antes_depois: comparação antes/depois de um serviço\n"
    "- outros: quando nenhuma acima se aplica\n"
    "Responda APENAS a chave (uma palavra), sem nenhum outro texto."
)


def _get_client() -> Optional[Any]:
    global _client, _init_tried
    if _init_tried:
        return _client
    _init_tried = True
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY ausente — classificação de foto indisponível.")
        return None
    try:
        from openai import OpenAI
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha ao iniciar OpenAI (visão): %s", exc)
        _client = None
    return _client


def classificar_foto(url: str) -> str:
    """Sugere a categoria da galeria para a foto na URL. Default seguro: 'outros'."""
    client = _get_client()
    if client is None or not url:
        return "outros"
    try:
        resp = client.chat.completions.create(
            model=settings.OPENAI_CHAT_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": _PROMPT},
                    {"type": "image_url", "image_url": {"url": url}},
                ],
            }],
            # Modelo de raciocínio: budget inclui "pensamento" -> folga generosa.
            max_completion_tokens=2000,
        )
        raw = (resp.choices[0].message.content or "").strip().lower()
        token = raw.split()[0].strip(".,:;\"'") if raw else "outros"
        return token if token in CATEGORIAS else "outros"
    except Exception as exc:  # noqa: BLE001
        logger.error("Falha ao classificar foto: %s", exc)
        return "outros"
