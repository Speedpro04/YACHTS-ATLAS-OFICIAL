"""
Yachts Atlas — Serviço de E-mail (SMTP)

Envio transacional via SMTP (Gmail por padrão: smtp.gmail.com:465).
Remetente: yachtsatlas@gmail.com (EMAIL_SENDER).

Regra de ouro: e-mail é best-effort — NUNCA derruba o fluxo principal.
Se o SMTP falhar ou não estiver configurado, apenas registra e segue.

Configuração (variáveis de ambiente):
  EMAIL_SENDER     -> yachtsatlas@gmail.com
  EMAIL_PASSWORD   -> SENHA DE APP do Gmail (não a senha da conta; exige 2FA)
  EMAIL_SMTP_HOST  -> smtp.gmail.com (default)
  EMAIL_SMTP_PORT  -> 465 (default, SSL)
"""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from app.core.config import settings

logger = logging.getLogger(__name__)

REMETENTE_NOME = "Yachts Atlas"


def send_email(
    to_email: str,
    subject: str,
    html: str,
    text: str | None = None,
    remetente: str | None = None,
) -> bool:
    """
    Envia um e-mail HTML. Best-effort: retorna False em vez de levantar erro.

    `remetente` permite assinar como um alias do domínio — cobranca@ ou
    suporte@ — sem deixar de autenticar na caixa real. Alias nao tem senha
    propria: quem faz login continua sendo EMAIL_SENDER, e so o cabecalho
    From muda. Ausente, assina com a propria caixa.
    """
    if not settings.EMAIL_SENDER or not settings.EMAIL_PASSWORD:
        logger.info("E-mail não configurado (EMAIL_SENDER/EMAIL_PASSWORD) — pulando envio.")
        return False
    if not to_email:
        logger.info("E-mail sem destinatário — pulando envio.")
        return False

    try:
        msg = EmailMessage()
        msg["From"] = formataddr((REMETENTE_NOME, remetente or settings.EMAIL_SENDER))
        # Resposta da marina volta para a caixa real, mesmo quando o From e um
        # alias — e no alias que ela clica em "responder".
        msg["Reply-To"] = settings.EMAIL_SENDER
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.set_content(text or "Bem-vindo à Yachts Atlas. Acesse: " + settings.FRONTEND_URL)
        msg.add_alternative(html, subtype="html")

        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.EMAIL_SMTP_HOST, settings.EMAIL_SMTP_PORT, context=ctx, timeout=20) as server:
            server.login(settings.EMAIL_SENDER, settings.EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info("E-mail enviado para %s (%s)", to_email, subject)
        return True
    except Exception as exc:  # noqa: BLE001 — e-mail nunca derruba o fluxo
        logger.error("Falha ao enviar e-mail para %s: %s", to_email, exc)
        return False


# O e-mail é NEUTRO quanto à oferta, de propósito: um texto só serve o
# Lançamento e a Oficial.
#
# Chegou a descrever a oferta contratada — preço, prazo travado, meses de
# dossiê. O problema é que ele teria de ADIVINHAR qual das duas foi vendida:
# o metadata `programa` vem vazio nos Payment Links, então sobrava o valor
# pago como pista. Inferência que erra aqui não deixa o texto vago, deixa o
# texto ERRADO — uma fundadora lida como oficial receberia "dossiê 12 meses"
# tendo comprado 18, por escrito, no primeiro contato depois do cartão.
#
# Não afirmar é melhor que afirmar errado. O contrato vive no cadastro e no
# painel, que sabem a resposta; o e-mail confirma o pagamento e entrega o
# acesso, que é o que ele tem como saber sozinho.


def _welcome_html(nome: str | None) -> str:
    """Template premium de boas-vindas (table-based, inline CSS, à prova de cliente)."""
    saudacao = f"Olá, {nome}" if nome else "Olá"
    url = settings.FRONTEND_URL
    logo = f"{url.rstrip('/')}/logo-transparent.png"
    navy = "#010c20"
    navy2 = "#021431"
    gold = "#c5a059"
    cream = "#E5D5B7"

    beneficios = [
        ("Frota sob custódia", "Todos os seus ativos organizados e blindados em um cofre digital."),
        ("Conformidade com as normas", "Dossiês construídos sobre NORMAM, ABNT e ISO — com a Capitã Solara para tirar dúvidas."),
        ("Integridade imutável", "Cada registro selado com assinatura SHA-256. À prova de fraude."),
    ]
    linhas_beneficios = ""
    for titulo, desc in beneficios:
        linhas_beneficios += f"""
        <tr>
          <td style="padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.06);">
            <span style="display:inline-block;width:8px;height:8px;background:{gold};border-radius:50%;margin-right:12px;"></span>
            <span style="color:#ffffff;font-size:15px;font-weight:600;">{titulo}</span>
            <div style="color:rgba(255,255,255,0.45);font-size:13px;margin:4px 0 0 20px;line-height:1.5;">{desc}</div>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:{navy};font-family:Arial,Helvetica,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{navy};padding:32px 16px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:{navy2};border:1px solid rgba(197,160,89,0.25);border-radius:8px;overflow:hidden;">

        <!-- Header -->
        <tr><td align="center" style="padding:40px 40px 24px 40px;background:linear-gradient(180deg,#021a3d 0%,{navy2} 100%);">
          <img src="{logo}" alt="Yachts Atlas" width="170" style="display:block;max-width:170px;height:auto;margin-bottom:8px;">
        </td></tr>

        <!-- Hero -->
        <tr><td style="padding:8px 40px 0 40px;">
          <p style="color:{gold};font-size:11px;letter-spacing:3px;text-transform:uppercase;font-weight:bold;margin:0 0 12px 0;">Acesso Liberado</p>
          <h1 style="color:#ffffff;font-size:30px;line-height:1.2;margin:0 0 16px 0;font-weight:bold;">
            {saudacao}, bem-vindo à <span style="color:{gold};font-style:italic;">Atlas.</span>
          </h1>
          <p style="color:rgba(255,255,255,0.55);font-size:15px;line-height:1.7;margin:0 0 28px 0;">
            Seu pagamento foi confirmado e o seu acesso está <strong style="color:#ffffff;">liberado</strong>.
            A partir de agora, a gestão da sua frota entra na era da custódia digital imutável.
            É uma honra ter você na rede.
          </p>
        </td></tr>

        <!-- Benefícios -->
        <tr><td style="padding:0 40px;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{linhas_beneficios}</table>
        </td></tr>

        <!-- CTA -->
        <tr><td align="center" style="padding:32px 40px 8px 40px;">
          <a href="{url}/login" style="display:inline-block;background:{gold};color:{navy};text-decoration:none;padding:16px 40px;border-radius:4px;font-size:12px;font-weight:bold;letter-spacing:2px;text-transform:uppercase;">
            Acessar o Sistema &rarr;
          </a>
        </td></tr>

        <!-- Nota -->
        <tr><td style="padding:24px 40px 8px 40px;">
          <p style="color:rgba(255,255,255,0.35);font-size:12px;line-height:1.6;margin:0;border-top:1px solid rgba(255,255,255,0.06);padding-top:20px;">
            Guarde este e-mail: ele confirma seu pagamento e o seu acesso.
            Em caso de dúvida sobre a cobrança ou a entrada no sistema, basta responder aqui.
          </p>
        </td></tr>

        <!-- Footer -->
        <tr><td align="center" style="padding:24px 40px 36px 40px;">
          <p style="color:rgba(255,255,255,0.25);font-size:10px;letter-spacing:2px;text-transform:uppercase;margin:0;">
            Yachts Atlas &middot; Custódia Digital de Ativos Náuticos
          </p>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def send_welcome_email(to_email: str, nome: str | None = None) -> bool:
    """
    E-mail de boas-vindas — disparado na liberação do acesso (pós-pagamento).

    Um texto só, neutro quanto à oferta: serve o Lançamento e a Oficial sem
    precisar adivinhar qual das duas foi vendida. Ver a nota acima de
    `_welcome_html`.
    """
    texto = (
        f"{'Olá, ' + nome if nome else 'Olá'}! Seu pagamento foi confirmado e seu acesso ao "
        f"Yachts Atlas está liberado. Acesse: {settings.FRONTEND_URL}/login\n\n"
        "Guarde este e-mail: ele confirma seu pagamento e o seu acesso.\n"
        "Yachts Atlas — Custódia Digital de Ativos Náuticos."
    )
    return send_email(
        to_email=to_email,
        subject="Bem-vindo à Yachts Atlas — seu acesso está liberado ⚓",
        html=_welcome_html(nome),
        text=texto,
    )
