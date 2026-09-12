"""
Yachts Atlas — de onde o dossiê pode ser emitido.

Decisão do fundador (12/09/2026): o Dossiê Atlas é gerado SOMENTE no computador.
Ele é um PDF — documento que se confere inteiro antes de sair, e não algo que se
despacha do celular no pier.

O que NÃO muda: ver, consultar e navegar seguem funcionando em celular e tablet,
inclusive a página de acesso que o comprador abre pelo link recebido. A trava é
sobre EMITIR, não sobre ler.

Isto é política de uso, não segurança: o `User-Agent` é um texto que o cliente
escreve, e quem chamar a API na mão pode mentir. Por isso a tentativa é
registrada — dissuasão com rastro vale mais do que uma barreira que finge ser
intransponível. A trava que a marina encontra de fato está no painel; esta aqui
existe para que o painel não seja a única.
"""
import logging
import re

from fastapi import HTTPException, Request

logger = logging.getLogger(__name__)

# A mesma frase que o painel mostra. Uma fonte por texto: se a tela diz uma coisa
# e o servidor outra, quem lê conclui que o sistema está quebrado.
MENSAGEM_SO_DESKTOP = (
    "Geração não autorizada em dispositivo mobile ou tablet. O Dossiê Atlas é "
    "emitido no computador — abra o painel em tela cheia para gerar."
)

# Aparelho de mão, do jeito que ele se apresenta. "Mobile" cobre a maioria dos
# navegadores de celular; os nomes próprios cobrem o resto.
_APARELHO_DE_MAO = re.compile(
    r"android|iphone|ipod|ipad|mobile|windows\s*phone|tablet|silk|kindle|playbook",
    re.IGNORECASE,
)


def e_aparelho_de_mao(user_agent: str) -> bool:
    """Se o `User-Agent` se apresenta como celular ou tablet."""
    return bool(_APARELHO_DE_MAO.search(user_agent or ""))


def exigir_desktop(request: Request) -> None:
    """Recusa a emissão fora do computador, e registra a tentativa.

    Usada como `Depends` nas duas rotas que EMITEM dossiê: o PDF do painel e a
    liberação de um pedido de terceiro.
    """
    user_agent = request.headers.get("user-agent", "")
    if not e_aparelho_de_mao(user_agent):
        return

    # Registrar não pode derrubar a recusa: falhar em auditar é ruim, mas deixar
    # passar a emissão por causa disso seria pior.
    try:
        from app.middleware.tracking import get_client_ip
        from app.services.audit_service import (
            audit_service,
            AuditAction,
            AuditSeverity,
        )

        audit_service.create_audit_log(
            action=AuditAction.UNAUTHORIZED_ACCESS,
            user_id="desconhecido",
            ip_address=get_client_ip(request),
            user_agent=user_agent,
            success=False,
            details={
                "motivo": "emissao_de_dossie_fora_do_desktop",
                "endpoint": str(request.url.path),
                "method": request.method,
            },
            severity=AuditSeverity.WARNING,
        )
    except Exception as e:  # pragma: no cover - degradação proposital
        logger.warning(f"Falha ao auditar emissão fora do desktop: {e}")

    raise HTTPException(status_code=409, detail=MENSAGEM_SO_DESKTOP)
