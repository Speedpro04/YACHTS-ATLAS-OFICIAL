"""
Endpoints para gestão de alertas de vencimento
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict
from datetime import datetime
from app.services.alert_service import process_alerts, check_vencimentos, ALERT_EMAIL
from app.core.supabase import supabase

router = APIRouter()


@router.get("/alertas/configurar")
async def configurar_alertas():
    """
    Configura os alertas de vencimento.
    Retorna a configuração atual dos alertas.
    """
    return {
        "email_destino": ALERT_EMAIL,
        "periodos": [-5, -2, 0, 2, 5, 7, 10],
        "descricao": {
            "-5": "5 dias antes do vencimento",
            "-2": "2 dias antes do vencimento",
            "0": "No dia do vencimento",
            "2": "2 dias após o vencimento",
            "5": "5 dias após o vencimento",
            "7": "7 dias após o vencimento",
            "10": "10 dias após o vencimento"
        }
    }


@router.get("/alertas/verificar")
async def verificar_vencimentos():
    """
    Verifica todos os registros e retorna aqueles que estão nos períodos de alerta.
    """
    try:
        # Busca todos os registros com data de vencimento
        response = supabase.from_('registros').select('*').execute()
        registros = response.data if response.data else []

        alertas = check_vencimentos(registros)

        return {
            "total_registros": len(registros),
            "alertas_encontrados": len(alertas),
            "alertas": [
                {
                    "registro_id": alerta['registro'].get('id'),
                    "titulo": alerta['registro'].get('titulo'),
                    "dias_vencimento": alerta['dias_vencimento'],
                    "tipo": alerta['tipo']
                }
                for alerta in alertas
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alertas/enviar")
async def enviar_alertas(background_tasks: BackgroundTasks):
    """
    Envia todos os alertas de vencimento pendentes.
    Pode ser executado em background.
    """
    try:
        # Busca todos os registros
        response = supabase.from_('registros').select('*').execute()
        registros = response.data if response.data else []

        resultados = process_alerts(registros)

        return {
            "status": "sucesso",
            "resumo": resultados
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alertas/testar")
async def testar_envio_email():
    """
    Envia um email de teste para o email configurado.
    """
    from app.services.alert_service import send_email_alert

    assunto = "Teste de Alerta - Yachts Atlas"
    corpo = """
    🚢 YACHTS ATLAS - TESTE DE ALERTA

    Este é um email de teste do sistema de alertas.

    Se você recebeu este email, o sistema de alertas está funcionando corretamente.

    ---
    Yachts Atlas - Sistema de Custódia Digital
    """

    sucesso = send_email_alert(ALERT_EMAIL, assunto, corpo)

    if sucesso:
        return {"status": "sucesso", "mensagem": "Email de teste enviado com sucesso!"}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar email de teste")
