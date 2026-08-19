"""
Cron Job — Régua de cobrança da inadimplência.

Roda 1x/dia e manda, para cada marina em atraso, o aviso do marco vencido
(dias 0, 7, 15, 19 e 20 desde a primeira cobrança recusada). Ver
app/services/cobranca_service.py para a regra.

Só avisa. O corte do acesso é calculado na leitura pelo porteiro
(app/core/acesso.py), então esta rotina pode falhar, atrasar ou ficar dias sem
rodar sem que ninguém seja cortado por engano nem deixe de ser cortado.

Rodar como script, fora da aplicação — mesmo padrão do
cron_vagas_fundadoras.py, sem HTTP e sem autenticação no meio:

    python -m app.services.cron_cobranca
"""

import sys
from datetime import datetime

from app.services.cobranca_service import processar_inadimplentes
from app.services.notify_service import notificar_fundador


def main() -> None:
    print(f"[{datetime.now()}] Verificando marinas em atraso...")

    try:
        resumo = processar_inadimplentes()
    except Exception as e:
        print(f"[{datetime.now()}] Erro ao processar a régua de cobrança: {e}")
        sys.exit(1)

    print(
        f"[{datetime.now()}] Concluído. "
        f"Em atraso: {resumo['em_atraso']} | "
        f"Avisos enviados: {resumo['avisos_enviados']} | "
        f"Cortadas: {resumo['cortadas']} | "
        f"Erros: {resumo['erros']}"
    )

    # Silêncio total é o estado normal — a maioria dos dias não tem ninguém
    # devendo. Só interrompe o fundador quando há o que decidir.
    if resumo["em_atraso"]:
        notificar_fundador(
            "Cobrança — marinas em atraso",
            f"Em atraso: {resumo['em_atraso']}\n"
            f"Com acesso suspenso: {resumo['cortadas']}\n"
            f"Avisos enviados hoje: {resumo['avisos_enviados']}",
        )


if __name__ == "__main__":
    main()
