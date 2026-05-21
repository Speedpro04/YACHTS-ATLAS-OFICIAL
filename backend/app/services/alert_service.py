"""
Sistema de Alertas de Vencimento - Yachts Atlas
Envia alertas de vencimento de documentos/registros nos seguintes períodos:
- 5 dias antes do vencimento
- 2 dias antes do vencimento
- No dia do vencimento
- 2 dias após o vencimento
- 5 dias após o vencimento
- 7 dias após o vencimento
- 10 dias após o vencimento
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

# Períodos de alerta (dias)
ALERT_PERIODS = [-5, -2, 0, 2, 5, 7, 10]

# Email de destino
ALERT_EMAIL = "yachtsatlas@gmail.com"


def get_alert_message(dias_vencimento: int, titulo: str, descricao: str) -> str:
    """Gera a mensagem do alerta baseada nos dias restantes/atrasados."""
    if dias_vencimento < 0:
        dias = abs(dias_vencimento)
        return f"""
        🚢 YACHTS ATLAS - ALERTA DE VENCIMENTO

        📋 Serviço: {titulo}

        ⏰ Vence em {dias} dia(s)

        📝 {descricao}

        ---
        Este é um alerta automático do sistema Yachts Atlas.
        """
    elif dias_vencimento == 0:
        return f"""
        🚢 YACHTS ATLAS - VENCE HOJE

        📋 Serviço: {titulo}

        ⚠️ Vence HOJE!

        📝 {descricao}

        ---
        Este é um alerta automático do sistema Yachts Atlas.
        """
    else:
        dias = dias_vencimento
        return f"""
        🚢 YACHTS ATLAS - VENCIDO

        📋 Serviço: {titulo}

        ❌ Vencido há {dias} dia(s)

        📝 {descricao}

        ---
        Este é um alerta automático do sistema Yachts Atlas.
        """


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


def check_vencimentos(registros: List[Dict]) -> List[Dict]:
    """
    Verifica quais registros estão nos períodos de alerta.

    Args:
        registros: Lista de registros com data de vencimento

    Returns:
        Lista de registros que precisam de alerta
    """
    alertas = []
    hoje = datetime.now().date()

    for registro in registros:
        data_vencimento = registro.get('data_vencimento')
        if not data_vencimento:
            continue

        vencimento = data_vencimento if isinstance(data_vencimento, datetime) else datetime.fromisoformat(data_vencimento).date()
        dias_restantes = (vencimento - hoje).days

        # Verifica se está em algum período de alerta
        if dias_restantes in ALERT_PERIODS:
            alertas.append({
                'registro': registro,
                'dias_vencimento': dias_restantes,
                'tipo': 'antes' if dias_restantes <= 0 else 'depois'
            })

    return alertas


def process_alerts(registros: List[Dict]) -> Dict:
    """
    Processa todos os alertas e envia emails.

    Args:
        registros: Lista de registros para verificar

    Returns:
        Dicionário com resumo do processamento
    """
    alertas = check_vencimentos(registros)
    resultados = {
        'total_registros': len(registros),
        'alertas_enviados': 0,
        'erros': 0,
        'detalhes': []
    }

    for alerta in alertas:
        registro = alerta['registro']
        dias = alerta['dias_vencimento']

        # Gera assunto e corpo do email
        if dias < 0:
            assunto = f"Vence em {abs(dias)} dia(s) - {registro.get('titulo', 'Serviço')}"
        elif dias == 0:
            assunto = f"Vence HOJE - {registro.get('titulo', 'Serviço')}"
        else:
            assunto = f"Vencido há {dias} dia(s) - {registro.get('titulo', 'Serviço')}"

        corpo = get_alert_message(dias, registro.get('titulo', ''), registro.get('descricao', ''))

        # Envia o email
        sucesso = send_email_alert(ALERT_EMAIL, assunto, corpo)

        if sucesso:
            resultados['alertas_enviados'] += 1
        else:
            resultados['erros'] += 1

        resultados['detalhes'].append({
            'registro_id': registro.get('id'),
            'titulo': registro.get('titulo'),
            'dias_vencimento': dias,
            'enviado': sucesso
        })

    return resultados
