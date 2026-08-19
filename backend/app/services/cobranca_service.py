"""
Yachts Atlas — Régua de cobrança da inadimplência.

Do primeiro cartão recusado até o corte são 20 dias, e a marina é avisada em
cinco momentos. Cada aviso sai por e-mail e por WhatsApp.

O que já foi enviado fica registrado no `user_metadata`, em `avisos_cobranca`.
Sem esse registro a régua tem os dois defeitos clássicos:

  • rodar duas vezes no mesmo dia manda o mesmo aviso duas vezes ao cliente;
  • ficar um dia sem rodar perde aquele aviso para sempre, porque a janela
    "faltam exatamente 7 dias" passou e não volta.

Com ele, o envio é do marco vencido mais recente que ainda não saiu: repetir a
execução não duplica nada, e uma falha de um dia é recuperada no dia seguinte.

Quem corta o acesso NÃO é este módulo — é o porteiro (app/core/acesso.py), que
calcula os 20 dias na leitura. Aqui só se avisa. Assim, se esta rotina parar de
rodar, ninguém deixa de ser cortado nem é cortado sem dever: o corte não
depende de cron nenhum estar de pé.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Dias desde a primeira recusa em que a marina é avisada. O último coincide com
# o corte: é o aviso de que o acesso já está suspenso.
MARCOS_DE_AVISO: tuple[int, ...] = (0, 7, 15, 19, 20)

CHAVE_AVISOS = "avisos_cobranca"


def _dias_de_atraso(metadata: dict) -> Optional[int]:
    from app.core.acesso import _dias_desde
    return _dias_desde(metadata.get("inadimplente_desde"))


def marco_devido(dias: Optional[int], ja_enviados: Any) -> Optional[int]:
    """
    Qual aviso mandar agora: o marco vencido mais recente que ainda não saiu.

    Devolve None quando não há nada a enviar. Pular direto para o mais recente
    é proposital — se a rotina ficou três dias parada, a marina recebe o aviso
    de hoje, e não três atrasados de uma vez.
    """
    if dias is None or dias < 0:
        return None
    enviados = set(ja_enviados) if isinstance(ja_enviados, (list, tuple, set)) else set()
    vencidos = [m for m in MARCOS_DE_AVISO if m <= dias and m not in enviados]
    return max(vencidos) if vencidos else None


def _textos(marco: int, nome: Optional[str], link: Optional[str]) -> tuple[str, str]:
    """Assunto e corpo do aviso. Mesmo texto no e-mail e no WhatsApp."""
    tratamento = f"Olá, {nome}" if nome else "Olá"
    faltam = settings.DIAS_ATE_CORTE_INADIMPLENCIA - marco
    onde_pagar = f"\n\nPague por aqui: {link}" if link else ""

    if marco == 0:
        return (
            "Não conseguimos processar seu pagamento",
            f"{tratamento}. A cobrança da sua assinatura do Programa Atlas não "
            f"foi aprovada. Isso costuma ser cartão vencido ou limite.\n\n"
            f"Você tem {faltam} dias para regularizar sem perder o acesso ao "
            f"sistema.{onde_pagar}",
        )

    if marco >= settings.DIAS_ATE_CORTE_INADIMPLENCIA:
        return (
            "Seu acesso ao Programa Atlas foi suspenso",
            f"{tratamento}. Como a fatura segue em aberto há "
            f"{settings.DIAS_ATE_CORTE_INADIMPLENCIA} dias, o acesso ao sistema "
            f"foi suspenso.\n\nSeus dados e registros continuam guardados. "
            f"Assim que o pagamento for confirmado, o acesso volta "
            f"automaticamente.{onde_pagar}",
        )

    if faltam <= 1:
        return (
            "Seu acesso será suspenso amanhã",
            f"{tratamento}. A fatura da sua assinatura continua em aberto e o "
            f"acesso ao sistema será suspenso amanhã.\n\nDá tempo de "
            f"resolver.{onde_pagar}",
        )

    return (
        f"Fatura em aberto — {faltam} dias para regularizar",
        f"{tratamento}. A fatura da sua assinatura do Programa Atlas ainda está "
        f"em aberto.\n\nFaltam {faltam} dias para o acesso ao sistema ser "
        f"suspenso.{onde_pagar}",
    )


def _html(corpo: str) -> str:
    paragrafos = "".join(
        f'<p style="margin:0 0 16px;line-height:1.6">{linha}</p>'
        for linha in corpo.split("\n\n")
    )
    return (
        '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;'
        'color:#1a1a1a;max-width:560px">'
        f"{paragrafos}"
        '<p style="margin:32px 0 0;font-size:12px;color:#888">Yachts Atlas</p>'
        "</div>"
    )


def avisar(user_id: str, metadata: dict, marco: int) -> bool:
    """
    Manda um aviso e registra que ele saiu.

    O registro é gravado mesmo se e-mail e WhatsApp falharem. É de propósito:
    insistir todo dia no mesmo marco por causa de um endereço inválido vira
    perseguição a quem talvez nem esteja recebendo. O corte continua valendo
    do mesmo jeito, e a falha fica no log.
    """
    email = metadata.get("email")
    assunto, corpo = _textos(
        marco,
        metadata.get("nome") or metadata.get("marina"),
        metadata.get("fatura_url"),
    )

    if email:
        try:
            from app.services.email_service import send_email
            send_email(email, assunto, _html(corpo), corpo)
        except Exception as e:
            logger.error(f"Falha no e-mail de cobrança (marco {marco}) para {email}: {e}")

    try:
        from app.services.whatsapp_service import enviar_whatsapp
        enviar_whatsapp(metadata.get("telefone"), f"*{assunto}*\n\n{corpo}")
    except Exception as e:
        logger.error(f"Falha no WhatsApp de cobrança (marco {marco}): {e}")

    try:
        from app.services.stripe_service import StripeService
        enviados = metadata.get(CHAVE_AVISOS)
        enviados = list(enviados) if isinstance(enviados, (list, tuple)) else []
        StripeService._atualizar_metadata(
            user_id, {CHAVE_AVISOS: sorted(set(enviados + [marco]))}
        )
    except Exception as e:
        logger.error(f"Falha ao registrar o aviso {marco} de {user_id}: {e}")
        return False

    logger.info(f"Aviso de cobrança do dia {marco} enviado para {user_id}")
    return True


def avisar_primeira_recusa(user_id: str) -> None:
    """
    Dispara o aviso do dia 0 na hora da recusa, direto do webhook.

    Os outros marcos são do cron diário, mas este não pode esperar até a
    próxima madrugada: quanto antes a marina souber, mais barato é resolver.
    Se o dia 0 já foi registrado, não repete — a Stripe tenta várias vezes.
    """
    try:
        from app.core.supabase import get_supabase_admin
        atual = get_supabase_admin().auth.admin.get_user_by_id(user_id)
        usuario = getattr(atual, "user", None) or atual
        metadata = dict(getattr(usuario, "user_metadata", None) or {})
        metadata.setdefault("email", getattr(usuario, "email", None))
    except Exception as e:
        logger.error(f"Falha ao ler o cadastro de {user_id} para avisar da recusa: {e}")
        return

    if marco_devido(_dias_de_atraso(metadata), metadata.get(CHAVE_AVISOS)) == 0:
        avisar(user_id, metadata, 0)


def _todos_os_usuarios() -> list:
    """Percorre o Auth em páginas. São dezenas de contas, não milhões."""
    from app.core.supabase import get_supabase_admin
    admin = get_supabase_admin().auth.admin

    usuarios: list = []
    pagina = 1
    while True:
        try:
            lote = admin.list_users(page=pagina, per_page=200)
        except TypeError:
            # supabase-py antigo não aceita paginação; devolve tudo de uma vez.
            lote = admin.list_users()
            usuarios.extend(getattr(lote, "users", None) or lote or [])
            break
        lote = getattr(lote, "users", None) or lote or []
        if not lote:
            break
        usuarios.extend(lote)
        if len(lote) < 200:
            break
        pagina += 1
    return usuarios


def processar_inadimplentes() -> dict:
    """Varre as contas em atraso e manda o aviso devido de cada uma."""
    resumo = {"em_atraso": 0, "avisos_enviados": 0, "cortadas": 0, "erros": 0}

    for usuario in _todos_os_usuarios():
        metadata = dict(getattr(usuario, "user_metadata", None) or {})
        if not metadata.get("inadimplente_desde"):
            continue

        resumo["em_atraso"] += 1
        dias = _dias_de_atraso(metadata)
        if dias is not None and dias >= settings.DIAS_ATE_CORTE_INADIMPLENCIA:
            resumo["cortadas"] += 1

        marco = marco_devido(dias, metadata.get(CHAVE_AVISOS))
        if marco is None:
            continue

        metadata.setdefault("email", getattr(usuario, "email", None))
        if avisar(getattr(usuario, "id", None), metadata, marco):
            resumo["avisos_enviados"] += 1
        else:
            resumo["erros"] += 1

    return resumo
