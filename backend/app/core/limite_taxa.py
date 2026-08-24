"""
Yachts Atlas — Limite de taxa para endpoints públicos.

O sistema tem sete rotas que aceitam POST sem autenticação nenhuma: os
formulários de indicação, de parceiro, de cadastro público de marina, o pedido
de dossiê, o pedido LGPD, o clique de parceiro — e, a mais séria, o formulário
que confere a SENHA-MESTRA e devolve o PDF de um cliente.

Até 24/08/2026 nenhuma delas tinha limite. O único limitador do código era o do
chatbot, e ele desistia sozinho:

    redis = get_redis()
    if redis is None:
        return True   # sem Redis, não bloqueia

Como produção nunca teve `REDIS_URL` (o boot registra "cache desativado"), o
efeito prático era **zero limite em todo o sistema**. Um robô podia tentar
senha-mestra indefinidamente, e entupir a caixa de indicações num fim de semana.

Aqui a decisão é o contrário: **sem Redis, limita na memória do processo.**
Redis, quando existir, só melhora — passa a valer entre contêineres. Um
limitador que se desliga quando a dependência opcional falta é um limitador que
não existe justamente no dia em que a dependência cai.

Uso:

    from app.core.limite_taxa import limite

    @router.post("/marina", dependencies=[Depends(limite("leads", 5, 60))])
    async def create_marina_lead(...):
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from typing import Deque, Dict

from fastapi import HTTPException, Request

from app.core.cache import get_client as get_redis

logger = logging.getLogger(__name__)

# Janela deslizante por chave, em memória. Cada valor é a fila de instantes das
# requisições ainda dentro da janela.
_memoria: Dict[str, Deque[float]] = {}
_trava = threading.Lock()

# Teto de chaves distintas guardadas. Sem isto, um atacante que varia o IP a
# cada requisição transforma o limitador em vazamento de memória — trocaria um
# problema por outro pior. Estourando o teto, as chaves mais antigas saem.
_MAX_CHAVES = 20_000


def _ip_do_pedido(request: Request) -> str:
    """IP real de quem pediu, respeitando o proxy da frente.

    A aplicação roda atrás de nginx: `request.client.host` seria sempre o IP
    interno do contêiner, e o limitador trataria o mundo inteiro como um
    visitante só — bloquearia todos ao primeiro abuso.
    """
    encaminhado = request.headers.get("x-forwarded-for", "")
    if encaminhado:
        return encaminhado.split(",")[0].strip()
    return (request.client.host if request.client else "desconhecido")


def _permitido_em_memoria(chave: str, maximo: int, janela: int) -> bool:
    agora = time.monotonic()
    corte = agora - janela
    with _trava:
        fila = _memoria.get(chave)
        if fila is None:
            if len(_memoria) >= _MAX_CHAVES:
                # Poda barata: remove as chaves cuja janela já venceu por
                # inteiro. Se ainda assim estiver cheio, descarta as mais antigas.
                vencidas = [k for k, v in _memoria.items() if not v or v[-1] < corte]
                for k in vencidas:
                    _memoria.pop(k, None)
                while len(_memoria) >= _MAX_CHAVES:
                    _memoria.pop(next(iter(_memoria)), None)
            fila = _memoria[chave] = deque()
        while fila and fila[0] < corte:
            fila.popleft()
        if len(fila) >= maximo:
            return False
        fila.append(agora)
        return True


def _permitido_no_redis(chave: str, maximo: int, janela: int) -> bool | None:
    """True/False pelo Redis; None quando o Redis não puder responder."""
    redis = get_redis()
    if redis is None:
        return None
    try:
        balde = f"rl:{chave}"
        quantas = redis.incr(balde)
        if quantas == 1:
            redis.expire(balde, janela)
        return quantas <= maximo
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Limite de taxa: Redis falhou ({e}) — usando memória")
        return None


def permitido(chave: str, maximo: int, janela: int) -> bool:
    """Se esta chave ainda cabe no limite. Redis quando dá, memória sempre."""
    resposta = _permitido_no_redis(chave, maximo, janela)
    if resposta is not None:
        return resposta
    return _permitido_em_memoria(chave, maximo, janela)


def limite(nome: str, maximo: int, janela: int = 60, *, por_rota: bool = False):
    """Dependência do FastAPI que barra excesso de requisições por IP.

    `nome` separa os baldes: estourar o formulário de indicação não pode
    bloquear o pedido de dossiê da mesma pessoa.

    `por_rota=True` acrescenta o caminho à chave — usado no formulário de senha,
    onde cada solicitação de dossiê tem o próprio balde e o atacante não pode
    diluir as tentativas trocando de link.

    Responde 429 com `Retry-After`, e registra em WARNING. O log importa: um
    limite que barra em silêncio esconde o ataque em vez de denunciá-lo.
    """
    def dependencia(request: Request) -> None:
        ip = _ip_do_pedido(request)
        chave = f"{nome}:{ip}"
        if por_rota:
            chave = f"{chave}:{request.url.path}"
        if not permitido(chave, maximo, janela):
            logger.warning(
                f"Limite de taxa estourado em '{nome}' por {ip} "
                f"({maximo} em {janela}s) — {request.url.path}"
            )
            raise HTTPException(
                status_code=429,
                detail="Muitas tentativas. Aguarde um instante e tente de novo.",
                headers={"Retry-After": str(janela)},
            )
    return dependencia
