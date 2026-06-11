"""
Cron Job para verificação diária de vencimentos
Executado diariamente para verificar alertas de vencimento
"""

import sys
from datetime import datetime
from app.services.alert_service import process_alerts
from app.core.supabase import get_supabase_admin

def main():
    """
    Executa a verificação de vencimentos e envia alertas.
    """
    print(f"[{datetime.now()}] Iniciando verificação de vencimentos...")

    try:
        # Busca todos os registros com data de vencimento
        response = get_supabase_admin().from_('registros').select('*').execute()
        registros = response.data if response.data else []

        if not registros:
            print(f"[{datetime.now()}] Nenhum registro encontrado.")
            return

        # Processa alertas
        resultados = process_alerts(registros)

        print(f"[{datetime.now()}] Verificação concluída!")
        print(f"  - Total de registros: {resultados['total_registros']}")
        print(f"  - Alertas enviados: {resultados['alertas_enviados']}")
        print(f"  - Erros: {resultados['erros']}")

    except Exception as e:
        print(f"[{datetime.now()}] Erro na verificação: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
