"""
Yachts Atlas — Relatório de Auditoria

As perguntas que um auditor de SOC 2 / ISO 27001 / SUSEP faz sobre a trilha
de `audit_logs`, respondidas por HTTP. A agregação mora em
`services/auditoria_relatorio.py` (Polars) — aqui só entram autorização,
validação de entrada e a forma da resposta.

ADMIN DA PLATAFORMA, NUNCA A MARINA
-----------------------------------
Toda rota exige `require_platform_admin`. A trilha registra IP, user-agent e
o que cada conta acessou: entregá-la a uma marina seria vazar o
comportamento das outras. Auditor externo recebe o ARQUIVO exportado, por
fora, com escopo combinado — não uma credencial no sistema.

O DOWNLOAD NÃO GRAVA NADA EM DISCO
----------------------------------
A exportação sai como streaming direto para o cliente. Arquivo de auditoria
esquecido no disco do container é dado pessoal (IP, autoria, horário)
sobrando em lugar que ninguém audita, e o container é efêmero: some no
próximo deploy, e some sem registro.
"""
from datetime import datetime, timezone
from io import BytesIO, StringIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.security import require_platform_admin
from app.services import auditoria_relatorio

router = APIRouter()

# Uma janela de auditoria vai de um trimestre (o padrão de quem pergunta) a
# dez anos (o teto de retenção que a SUSEP menciona). Acima disso é engano
# de digitação, e vale recusar em vez de varrer a tabela inteira.
JANELA_MIN, JANELA_MAX = 1, 3660


@router.get("/relatorio")
async def relatorio(
    dias: int = Query(90, ge=JANELA_MIN, le=JANELA_MAX,
                      description="Janela em dias. 90 = um trimestre."),
    _admin: dict = Depends(require_platform_admin),
):
    """Resumo da trilha no período.

    Cada bloco responde a UMA pergunta de auditoria, e a chave é a pergunta:
    o que aconteceu (`por_acao`), o que falhou e por quê
    (`falhas_por_motivo`), houve pico em algum dia (`falhas_por_dia`), de
    quais origens (`ips_com_falha`) e quem esteve ativo (`por_usuario`).

    `truncado: true` significa que a janela bateu no teto de linhas e há
    eventos que NÃO entraram na conta. Num relatório de auditoria isso
    precisa aparecer: número parcial apresentado como total é o defeito que
    este projeto passou o mês corrigindo no dossiê.
    """
    try:
        return auditoria_relatorio.relatorio(dias=dias)
    except Exception as e:                                    # noqa: BLE001
        raise HTTPException(status_code=500,
                            detail=f"Falha ao gerar relatório de auditoria: {e}")


@router.get("/exportar")
async def exportar(
    dias: int = Query(90, ge=JANELA_MIN, le=JANELA_MAX),
    formato: str = Query("csv", pattern="^(csv|parquet)$",
                         description="csv abre em qualquer lugar; parquet "
                                     "preserva tipo e comprime, para retenção longa"),
    _admin: dict = Depends(require_platform_admin),
):
    """Baixa a trilha do período como arquivo, para o auditor levar.

    Sai em streaming, sem passar por disco — ver o cabeçalho do módulo.
    """
    try:
        df = auditoria_relatorio.carregar(dias=dias)
    except Exception as e:                                    # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"Falha ao ler a trilha: {e}")

    if df.height == 0:
        raise HTTPException(status_code=404,
                            detail=f"Nenhum evento de auditoria nos últimos {dias} dias.")

    carimbo = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    nome = f"auditoria-yachts-atlas-{dias}d-{carimbo}.{formato}"

    if formato == "csv":
        buf = StringIO()
        df.write_csv(buf)
        conteudo, midia = buf.getvalue().encode("utf-8"), "text/csv; charset=utf-8"
    else:
        buf = BytesIO()
        df.write_parquet(buf)
        conteudo, midia = buf.getvalue(), "application/vnd.apache.parquet"

    return StreamingResponse(
        BytesIO(conteudo),
        media_type=midia,
        headers={
            "Content-Disposition": f'attachment; filename="{nome}"',
            # O auditor precisa saber se levou a trilha inteira ou uma fatia.
            "X-Auditoria-Linhas": str(df.height),
            "X-Auditoria-Truncado": str(df.height >= auditoria_relatorio.LIMITE_LINHAS).lower(),
            "X-Auditoria-Janela-Dias": str(dias),
        },
    )
