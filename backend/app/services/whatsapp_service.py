"""
Yachts Atlas — Envio de WhatsApp.

Quem chama daqui pede `enviar_whatsapp(telefone, texto)` e não sabe — nem
precisa saber — quem entrega. O provedor vem de `WHATSAPP_PROVIDER`, e trocar
Evolution por Z-API ou pela Cloud API da Meta é escrever outra função `_envia_*`
e acrescentar uma linha no despacho. Nada do resto do sistema muda.

Hoje: Evolution API v2, o mesmo cliente que o ATLAS-SHOP já usa
(`POST /message/sendText/{instance}`, autenticação no header `apikey`).

Best-effort por definição: falhar em avisar não pode derrubar o webhook de um
pagamento nem travar a rotina de cobrança. Devolve False e registra no log.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# Tamanho de um número brasileiro com DDD, sem DDI: 11 dígitos (celular) ou 10
# (fixo). Acima disso o DDI já veio junto e não deve ser acrescentado de novo.
_MAX_SEM_DDI = 11


def normalizar_telefone(telefone: Optional[str]) -> Optional[str]:
    """
    Deixa o número no formato que a Evolution espera: só dígitos, com DDI.

    A marina digita do jeito que quiser — `(48) 99123-4567`, `+55 48 99123
    4567`, `48991234567`. Sem normalizar, a mensagem simplesmente não sai, e o
    erro é mudo: a API aceita a chamada e não entrega nada.
    """
    if not telefone:
        return None

    digitos = re.sub(r"\D", "", telefone)
    if not digitos:
        return None

    # Zero à esquerda de DDD ("048 99123-4567") não existe em número internacional.
    digitos = digitos.lstrip("0")

    if len(digitos) <= _MAX_SEM_DDI:
        digitos = f"{settings.DDI_PADRAO}{digitos}"

    # Curto demais para ser telefone de verdade: melhor não enviar do que
    # entregar na caixa de outra pessoa.
    return digitos if len(digitos) >= 12 else None


def _envia_evolution(telefone: str, texto: str, instancia: str, apikey: str) -> bool:
    """
    Envia por `POST /message/sendText/{instance}`.

    O corpo mudou entre as versões da Evolution: a v2 espera `text` na raiz,
    a v1 esperava `textMessage.text`. Algumas builds aceitam os dois, outras
    não — e a que não aceita responde 400 sem que nada mais aconteça. Como
    esse canal carrega cobrança, tentamos o formato novo e caímos no antigo
    se ele for recusado, em vez de descobrir o problema pelo silêncio.
    """
    if not (settings.EVOLUTION_BASE_URL and apikey and instancia):
        logger.warning("Evolution sem configuração completa — WhatsApp não enviado")
        return False

    url = (
        f"{settings.EVOLUTION_BASE_URL.rstrip('/')}"
        f"/message/sendText/{instancia}"
    )
    headers = {"apikey": apikey, "Content-Type": "application/json"}
    formatos = (
        ("v2", {"number": telefone, "text": texto}),
        ("v1", {"number": telefone, "textMessage": {"text": texto}}),
    )

    ultimo_erro = None
    with httpx.Client(timeout=_TIMEOUT) as client:
        for versao, corpo in formatos:
            try:
                resposta = client.post(url, json=corpo, headers=headers)
                resposta.raise_for_status()
                logger.info(f"WhatsApp enviado para {telefone} (formato {versao})")
                return True
            except httpx.HTTPStatusError as e:
                ultimo_erro = e
                # 400/422 = corpo recusado, vale tentar o outro formato.
                # 401 (chave errada) ou 404 (instância errada) não melhoram
                # com outro corpo — parar aqui evita mascarar o erro real.
                if e.response.status_code not in (400, 422):
                    break
            except httpx.HTTPError as e:
                ultimo_erro = e
                break

    logger.error(f"Evolution falhou ao enviar para {telefone}: {ultimo_erro}")
    return False


_PROVEDORES = {
    "evolution": _envia_evolution,
}


def whatsapp_ativo() -> bool:
    """Se há canal configurado. Útil para o log dizer o que não foi enviado."""
    return settings.WHATSAPP_PROVIDER in _PROVEDORES


def prospeccao_ativa() -> bool:
    """Se a instância separada de prospecção está pronta para disparar."""
    return whatsapp_ativo() and bool(settings.EVOLUTION_INSTANCE_PROSPECCAO)


def enviar_whatsapp(
    telefone: Optional[str], texto: str, *, prospeccao: bool = False
) -> bool:
    """Envia uma mensagem. Devolve False (sem levantar) quando não dá.

    `prospeccao=True` manda pela instância de vendas
    (`EVOLUTION_INSTANCE_PROSPECCAO`), nunca pela transacional. Sem essa
    variável configurada, a prospecção **não sai** — e é de propósito: cair no
    número transacional é o único jeito de um disparo de vendas derrubar o
    login do armador e a régua de cobrança junto.

    Quem chama sem o parâmetro continua no comportamento de sempre.
    """
    provedor = _PROVEDORES.get(settings.WHATSAPP_PROVIDER)
    if not provedor:
        if settings.WHATSAPP_PROVIDER:
            logger.warning(f"WHATSAPP_PROVIDER desconhecido: {settings.WHATSAPP_PROVIDER}")
        return False

    if prospeccao:
        instancia = settings.EVOLUTION_INSTANCE_PROSPECCAO
        apikey = settings.EVOLUTION_API_KEY_PROSPECCAO
        if not instancia:
            logger.warning(
                "Prospecção pedida sem EVOLUTION_INSTANCE_PROSPECCAO configurada — "
                "não enviado (não usamos a instância transacional para isto)"
            )
            return False
    else:
        instancia = settings.EVOLUTION_INSTANCE
        apikey = settings.EVOLUTION_API_KEY

    numero = normalizar_telefone(telefone)
    if not numero:
        logger.warning(f"Telefone inutilizável para WhatsApp: {telefone!r}")
        return False

    return provedor(numero, texto, instancia, apikey)


if __name__ == "__main__":
    # Teste de fumaça da configuração, para não descobrir que o canal está
    # errado no dia em que uma marina de verdade precisar ser avisada:
    #     python -m app.services.whatsapp_service 48991234567
    import sys

    destino = sys.argv[1] if len(sys.argv) > 1 else None
    if not destino:
        print("uso: python -m app.services.whatsapp_service <telefone> [mensagem]")
        raise SystemExit(2)

    mensagem = sys.argv[2] if len(sys.argv) > 2 else (
        "Teste do canal de avisos do Yachts Atlas. Se você recebeu isto, "
        "está tudo certo."
    )

    print(f"provedor : {settings.WHATSAPP_PROVIDER or '(nenhum)'}")
    print(f"instancia: {settings.EVOLUTION_INSTANCE or '(nao configurada)'}")
    print(f"numero   : {normalizar_telefone(destino) or '(invalido)'}")
    print("enviado  :", enviar_whatsapp(destino, mensagem))
