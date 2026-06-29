"""
Cron Job — Programa das 3 Vagas Fundadoras

Executado diariamente. Verifica as contas piloto cujo período gratuito de
6 meses (contado a partir do cadastro da marina) chegou ao fim e:

  • inicia a cobrança (billing_status -> 'past_due')
  • trava o acesso na camada de aplicação (access_status -> 'blocked')

A regra de negócio roda de forma atômica dentro do Postgres, na função
public.processar_vencimentos_piloto(). Aqui apenas disparamos a função,
registramos o resultado e avisamos o fundador no Telegram.

Agende este script para rodar 1x/dia (cron do servidor, Render, etc.):
    python -m app.services.cron_vagas_fundadoras
"""

import sys
from datetime import datetime

from app.core.supabase import get_supabase_admin
from app.services.notify_service import send_telegram


def main() -> None:
    print(f"[{datetime.now()}] Verificando vencimentos das vagas fundadoras...")

    try:
        resp = get_supabase_admin().rpc("processar_vencimentos_piloto").execute()
        resultado = resp.data or {}
        vencidas = resultado.get("vencidas", []) if isinstance(resultado, dict) else []
        total = resultado.get("total_vencidas", len(vencidas)) if isinstance(resultado, dict) else len(vencidas)

        print(f"[{datetime.now()}] Concluído. Marinas vencidas nesta execução: {total}")

        if vencidas:
            linhas = "\n".join(
                f"• Vaga {v.get('slot_number')}: {v.get('marina_name') or v.get('email')} "
                f"(prazo: {str(v.get('billing_starts_at'))[:10]})"
                for v in vencidas
            )
            send_telegram(
                "<b>Vagas Fundadoras — período gratuito encerrado</b>\n"
                f"{total} marina(s) entraram em cobrança (USD 250/mês) e tiveram o "
                f"acesso travado até regularização:\n{linhas}"
            )

    except Exception as e:
        print(f"[{datetime.now()}] Erro ao processar vencimentos das vagas fundadoras: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
