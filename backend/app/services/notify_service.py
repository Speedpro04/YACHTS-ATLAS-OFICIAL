"""
Yachts Atlas — Avisos operacionais para o fundador.

É por aqui que o sistema chama a atenção de um humano: pagamento recusado,
alguém pagou preço de fundadora sem vaga para honrar, resumo diário da
cobrança, novo pedido de dossiê.

Dois canais, e só dois: **WhatsApp e e-mail**. Envia pelos que estiverem
configurados — não é redundância à toa: o aviso de que uma marina parou de
pagar não pode depender de um único canal estar de pé naquele dia.

Best-effort por definição. Falhar em avisar nunca pode derrubar o fluxo que
gerou o aviso — o pagamento já aconteceu, o pedido já entrou.

Configuração:
    ALERTA_WHATSAPP  -> seu número, com ou sem DDI (ex.: 48991234567)
    ALERTA_EMAIL     -> seu e-mail; se vazio, cai no EMAIL_SENDER
"""
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def _destino_email() -> str | None:
    return settings.ALERTA_EMAIL or settings.EMAIL_SENDER or None


def notificar_fundador(titulo: str, corpo: str) -> bool:
    """
    Manda um aviso pelos canais configurados. True se ao menos um saiu.

    `titulo` e `corpo` vêm em texto puro: cada canal aplica a formatação dele
    (negrito com asteriscos no WhatsApp, HTML no e-mail). Foi o que permitiu
    trocar de canal sem reescrever mensagem nenhuma.
    """
    entregou = False

    if settings.ALERTA_WHATSAPP:
        try:
            from app.services.whatsapp_service import enviar_whatsapp
            # Sai pela instância de MARINAS, não pela transacional. A
            # transacional entrega o código de acesso do armador, que é
            # autenticação: quanto menos tráfego passar por ela, menor a chance
            # de o login cair junto com outra coisa. Aviso ao fundador é
            # operação, não autenticação — não precisa desse número.
            #
            # E o destino (ALERTA_WHATSAPP) é um número de FORA das instâncias.
            # Enquanto era o próprio número da transacional, o aviso chegava no
            # chat "mensagem para você mesmo" e saía pelo canal que ele deveria
            # vigiar — foi assim que a queda do WhatsApp passou despercebida.
            entregou = enviar_whatsapp(
                settings.ALERTA_WHATSAPP, f"*{titulo}*\n\n{corpo}",
                prospeccao=True,
            ) or entregou
        except Exception as e:
            logger.error(f"Falha ao avisar o fundador por WhatsApp: {e}")
    else:
        # O silêncio mais caro do sistema morava exatamente aqui. Sem esta
        # linha, `ALERTA_WHATSAPP` vazio pulava o canal sem deixar rastro: no
        # log de produção o aviso que nunca foi tentado ficava idêntico ao
        # aviso que saiu — nenhuma linha nos dois casos. O e-mail continuava
        # chegando, o que reforçava a impressão de que estava tudo certo.
        logger.warning(
            f"ALERTA_WHATSAPP vazio — aviso NAO sai por WhatsApp: {titulo}"
        )

    destino = _destino_email()
    if destino:
        try:
            from app.services.email_service import send_email
            html = (
                '<div style="font-family:Arial,Helvetica,sans-serif;font-size:15px;'
                f'color:#1a1a1a"><p><strong>{titulo}</strong></p>'
                + "".join(f"<p>{linha}</p>" for linha in corpo.split("\n") if linha.strip())
                + "</div>"
            )
            entregou = bool(send_email(destino, titulo, html, corpo)) or entregou
        except Exception as e:
            logger.error(f"Falha ao avisar o fundador por e-mail: {e}")

    if not entregou:
        # O aviso morreu aqui. Fica no log com o texto inteiro para não se
        # perder de vez — é a última rede antes do silêncio total.
        logger.warning(f"Aviso do fundador não entregue por nenhum canal: {titulo} | {corpo}")

    return entregou
