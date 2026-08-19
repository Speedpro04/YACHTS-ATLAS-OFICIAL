"""
Yachts Atlas — Porteiro do acesso pago.

Duas regras de negócio moram aqui, e só aqui:

  1. Ninguém usa o Atlas antes do pagamento cair na Stripe.
  2. Vinte dias de inadimplência cortam o acesso; pagou, volta sozinho.

O estado vive no `user_metadata` do Supabase Auth, escrito pelo cadastro
(leads._criar_acesso_marina_paga) e pelo webhook da Stripe:

    pagamento           'pendente' | 'pago' | 'cancelado'
    inadimplente_desde  ISO-8601 da PRIMEIRA cobrança recusada; some ao pagar
    fatura_url          link da fatura em aberto, para a marina se regularizar

O corte dos 20 dias é calculado na LEITURA, não por rotina agendada. Duas
razões: não depende de um cron estar de pé um mês depois, e o religamento é
automático — o webhook apaga `inadimplente_desde` e o acesso volta já na
requisição seguinte, sem ninguém precisar rodar nada.

FAIL-OPEN de propósito. Só bloqueia quem está EXPLICITAMENTE marcado: conta
sem a chave `pagamento` — manutenção, admin, as marinas do piloto gratuito —
passa direto. Um defeito aqui tem que errar deixando entrar quem não devia,
nunca trancando do lado de fora quem paga. Muito menos o dono da plataforma.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings

# Valores de `pagamento` que impedem o uso do sistema. Qualquer outro valor —
# inclusive um que ainda não exista — libera: ver FAIL-OPEN acima.
PAGAMENTO_PENDENTE = "pendente"
PAGAMENTO_PAGO = "pago"
PAGAMENTO_CANCELADO = "cancelado"


@dataclass(frozen=True)
class Bloqueio:
    """Por que esta conta não pode entrar, em termos que a marina entende."""

    motivo: str          # chave estável, para o frontend decidir a tela
    mensagem: str        # texto exibido à marina
    dias_em_atraso: Optional[int] = None
    link_pagamento: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "motivo": self.motivo,
            "mensagem": self.mensagem,
            "dias_em_atraso": self.dias_em_atraso,
            "link_pagamento": self.link_pagamento,
        }


def _link_do_checkout(metadata: dict) -> str:
    """Link do preço que ESTA marina contratou — $200 se fundadora, senão $250."""
    if (metadata or {}).get("oferta") == "fundadora":
        return settings.STRIPE_LINK_MARINA_FUNDADORA
    return settings.STRIPE_LINK_MARINA_OFICIAL


def _dias_desde(iso: Any) -> Optional[int]:
    """
    Dias inteiros desde uma data ISO-8601.

    Devolve None se o valor não for uma data legível. O chamador trata isso
    como "não sei há quanto tempo" e libera: data corrompida no metadata não
    pode virar um bloqueio que ninguém consegue explicar nem desfazer.
    """
    if not isinstance(iso, str) or not iso.strip():
        return None
    try:
        quando = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except ValueError:
        return None
    if quando.tzinfo is None:
        quando = quando.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - quando).days


def avaliar_acesso(metadata: Optional[dict]) -> Optional[Bloqueio]:
    """
    Decide se a conta pode usar o sistema. `None` = liberado.

    Função pura: recebe o metadata e devolve a decisão, sem tocar em rede nem
    em banco. É o que torna essa regra testável de verdade — e o que permite
    aplicá-la tanto no login quanto em cada requisição sem custo nenhum, já
    que o metadata vem junto na validação do token.
    """
    meta = metadata or {}
    situacao = meta.get("pagamento")

    if situacao == PAGAMENTO_PENDENTE:
        return Bloqueio(
            motivo="pagamento_pendente",
            mensagem=(
                "Seu acesso é liberado assim que o pagamento for confirmado. "
                "Se você já pagou, aguarde alguns instantes e tente de novo."
            ),
            link_pagamento=_link_do_checkout(meta),
        )

    if situacao == PAGAMENTO_CANCELADO:
        return Bloqueio(
            motivo="assinatura_cancelada",
            mensagem=(
                "Sua assinatura do Programa Atlas foi encerrada. "
                "Para voltar a usar o sistema, faça uma nova assinatura."
            ),
            link_pagamento=_link_do_checkout(meta),
        )

    # Inadimplência só faz sentido para quem já pagou algum dia. Enquanto os
    # 20 dias não fecham, a marina continua usando normalmente — é o prazo que
    # ela tem para trocar o cartão sem perder o acesso.
    atraso = _dias_desde(meta.get("inadimplente_desde"))
    if atraso is not None and atraso >= settings.DIAS_ATE_CORTE_INADIMPLENCIA:
        return Bloqueio(
            motivo="inadimplente",
            mensagem=(
                f"Seu acesso está suspenso por {atraso} dias de pagamento em "
                "aberto. Assim que a fatura for paga, ele volta automaticamente."
            ),
            dias_em_atraso=atraso,
            link_pagamento=meta.get("fatura_url") or _link_do_checkout(meta),
        )

    return None
