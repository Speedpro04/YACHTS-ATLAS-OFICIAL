"""
Envio de e-mail da plataforma.

Este módulo já foi um "sistema de alertas de vencimento": tinha uma tabela de
períodos (-5, -2, 0, 2, 5, 7, 10 dias), um varredor de registros e um
disparador. Nada disso foi removido por estar obsoleto — foi removido por
estar **errado de um jeito que só apareceria em produção**:

- o varredor lia `registros` sem filtro de marina, e mandava tudo para um
  endereço fixo (`yachtsatlas@gmail.com`). Vencimento de barco da marina A
  chegava numa caixa que não é da marina A;
- os quatro endpoints que o expunham estavam registrados com prefixo duplo
  (`/api/v1/alertas/alertas/...`), o que é a prova de que ninguém nunca os
  chamou;
- exigiam token de admin de plataforma, então nenhum agendador externo
  alcançava — e nenhum agendador foi configurado.

Alerta de vencimento continua sendo boa ideia; o que não serve é esta versão.
Quando voltar, cada marina recebe o alerta do próprio ativo, no padrão do
`cron_cobranca`, que já resolve idempotência e janela de disparo.

Removido em 31/08/2026. O que sobrou é o que a plataforma realmente usa hoje:
mandar um e-mail para um destinatário específico — a liberação do dossiê e o
aviso de solicitação, ambos em `api/v1/dossie.py`.
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_email_alert(
    to_email: str,
    subject: str,
    body: str,
    is_html: bool = False
) -> bool:
    """
    Envia email de alerta.

    Args:
        to_email: Email do destinatário
        subject: Assunto do email
        body: Corpo do email
        is_html: Se o corpo é HTML

    Returns:
        True se enviado com sucesso, False caso contrário
    """
    try:
        # Configurações SMTP (exemplo com Gmail)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = settings.EMAIL_SENDER or "yachtsatlas@gmail.com"
        sender_password = settings.EMAIL_PASSWORD or ""

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Yachts Atlas - {subject}"

        if is_html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

        # Envia o email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False

