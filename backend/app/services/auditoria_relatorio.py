"""
Yachts Atlas — Relatório de Auditoria (Polars)

Transforma `audit_logs` em respostas para as perguntas que um auditor de
SOC 2 / ISO 27001 / SUSEP faz. O dado sempre esteve lá — 184 linhas em
30/08/2026, com ação, autor, IP, horário, severidade e resultado — mas não
havia como perguntar nada a ele: `audit_service` só sabia listar os eventos
de UM usuário, em ordem cronológica.

Auditoria não se responde com lista cronológica. Ela pergunta:

    "Quantas tentativas de acesso falharam no trimestre, e de quais IPs?"
    "Quem acessou documentos nos últimos 90 dias?"
    "Houve pico de erro em algum dia? O que aconteceu ali?"
    "Me exporte a trilha do período."

POR QUE POLARS AQUI, E NÃO NO RESTO DO SISTEMA
----------------------------------------------
Medido em 30/08/2026: o sistema tem 188 registros, 96 documentos e 14
ativos. Nessa escala Polars ATRAPALHA — construir um DataFrame custa mais
que iterar a lista, e é por isso que `dossie_data` e `asset_score_service`
continuam em Python puro. Não é descuido; é a escolha certa para o volume.

`audit_logs` é a exceção, por três motivos:

  1. É a única tabela que cresce SEM PARAR. É append-only por design e não
     apaga nunca — a SUSEP fala em reter de 5 a 10 anos. Vinte marinas em
     um ano colocam isso na casa das dezenas de milhares de linhas.
  2. As perguntas são agregação pura — group by, contagem, série por dia,
     distinct de IP. É exatamente onde Polars ganha de laço Python.
  3. A saída precisa virar arquivo para o auditor. Polars escreve CSV e
     Parquet nativamente, sem dependência nova.

O relatório NÃO julga: ele conta. Marcar "suspeito" no lugar do auditor é
inventar conclusão — a função aponta o que se destaca e deixa a leitura
para quem tem contexto. As 14 assinaturas inválidas de agosto/2026, por
exemplo, foram PDFs de teste gerados com o segredo de desenvolvimento; um
relatório que gritasse "ataque" teria custado uma investigação inútil.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app.core.supabase import get_supabase_admin

logger = logging.getLogger(__name__)

# Uma leitura de auditoria não deve conseguir derrubar a aplicação puxando
# a tabela inteira para a memória. Acima disto, o relatório reporta que
# truncou — silêncio aqui viraria "não houve mais nada no período", que é
# uma afirmação falsa sobre um documento de auditoria.
LIMITE_LINHAS = 50_000

# `severity` e `success` são independentes no schema: existe evento com
# success=false e severity='warning' (login recusado) e evento crítico que
# tecnicamente "teve sucesso". Auditoria olha os dois.
SEVERIDADES_ALERTA = ("critical", "error")


def _polars():
    """Importa Polars sob demanda.

    O relatório é uma rota administrativa, chamada raramente. Importar no
    topo do módulo somaria ~0,3 s ao boot de TODA a aplicação, inclusive dos
    caminhos que nunca vão gerar relatório nenhum.
    """
    import polars as pl
    return pl


def carregar(dias: int = 90, ate: Optional[datetime] = None):
    """Puxa a janela de auditoria como DataFrame Polars.

    Devolve DataFrame vazio (com o schema certo) quando não há nada no
    período — nunca None. Quem consome não deveria precisar distinguir
    "sem dados" de "falhou".
    """
    pl = _polars()
    fim = ate or datetime.now(timezone.utc)
    inicio = fim - timedelta(days=dias)

    colunas = ["id", "action", "user_id", "ip_address", "timestamp",
               "severity", "success", "error_message"]
    vazio = pl.DataFrame(schema={c: pl.Utf8 for c in colunas})

    try:
        resp = (get_supabase_admin().table("audit_logs")
                .select(",".join(colunas))
                .gte("timestamp", inicio.isoformat())
                .lte("timestamp", fim.isoformat())
                .order("timestamp", desc=True)
                .limit(LIMITE_LINHAS)
                .execute())
    except Exception as e:                                    # noqa: BLE001
        logger.error("Auditoria: leitura de audit_logs falhou: %s", e)
        return vazio

    linhas = resp.data or []
    if not linhas:
        return vazio

    df = pl.DataFrame(linhas, infer_schema_length=None)
    # time_zone explicito: o Postgres devolve ISO COM offset, e a partir do
    # Polars 1.x converter sem declarar fuso e erro -- antes era aceito em
    # silencio e produzia horario deslocado, que num relatorio de auditoria
    # significa evento atribuido ao dia errado.
    return df.with_columns(
        pl.col("timestamp").str.to_datetime(time_zone="UTC", strict=False).alias("quando")
    ).with_columns(
        pl.col("quando").dt.date().alias("dia")
    )


def relatorio(dias: int = 90, ate: Optional[datetime] = None) -> dict[str, Any]:
    """O relatório que o auditor pede, em um dicionário serializável.

    Cada bloco responde a UMA pergunta de auditoria, e o nome da chave é a
    pergunta. Números soltos sem a pergunta ao lado foi o defeito que este
    projeto passou o mês inteiro corrigindo no dossiê.
    """
    pl = _polars()
    df = carregar(dias=dias, ate=ate)
    total = df.height

    base = {
        "janela_dias": dias,
        "gerado_em": (ate or datetime.now(timezone.utc)).isoformat(),
        "eventos": total,
        "truncado": total >= LIMITE_LINHAS,
    }
    if total == 0:
        return {**base, "sem_dados": True}

    falhas = df.filter(~pl.col("success").fill_null(True))
    alerta = df.filter(pl.col("severity").is_in(SEVERIDADES_ALERTA))

    def _tabela(frame, por: list[str], nome: str = "n"):
        if frame.height == 0:
            return []
        return (frame.group_by(por)
                     .agg(pl.len().alias(nome))
                     .sort(nome, descending=True)
                     .to_dicts())

    return {
        **base,
        # "O que aconteceu no período?"
        "por_acao": _tabela(df, ["action"]),
        # "Quantos eventos de risco?" — severidade e falha são independentes
        "por_severidade": _tabela(df, ["severity"]),
        "falhas": falhas.height,
        "eventos_de_alerta": alerta.height,
        # "O que falhou, e quantas vezes?" — a mensagem é o que dá o contexto
        "falhas_por_motivo": _tabela(falhas, ["error_message"]),
        # "Houve pico em algum dia?" — série temporal só das falhas
        "falhas_por_dia": (
            falhas.group_by("dia").agg(pl.len().alias("n")).sort("dia").to_dicts()
            if falhas.height else []
        ),
        # "De quais origens?" — IP distinto é o sinal que auditoria persegue
        "ips_distintos": df.get_column("ip_address").n_unique(),
        "ips_com_falha": _tabela(falhas, ["ip_address"]),
        # "Quem esteve ativo?"
        "usuarios_distintos": df.get_column("user_id").n_unique(),
        "por_usuario": _tabela(df, ["user_id"])[:20],
        "primeiro_evento": str(df.get_column("quando").min()),
        "ultimo_evento": str(df.get_column("quando").max()),
    }


def exportar(caminho: str, dias: int = 90, formato: str = "csv") -> dict[str, Any]:
    """Grava a trilha do período em arquivo, para o auditor levar.

    CSV abre em qualquer lugar e é o que costuma ser pedido; Parquet
    preserva tipos e comprime, e serve para retenção longa — a SUSEP fala em
    5 a 10 anos, e CSV de milhões de linhas guardado por uma década é
    desperdício de armazenamento e de tempo de leitura.
    """
    df = carregar(dias=dias)
    if df.height == 0:
        return {"ok": False, "motivo": "sem eventos no período", "linhas": 0}

    fmt = formato.lower()
    if fmt == "csv":
        df.write_csv(caminho)
    elif fmt == "parquet":
        df.write_parquet(caminho)
    else:
        raise ValueError(f"formato não suportado: {formato} (use csv ou parquet)")

    return {"ok": True, "arquivo": caminho, "formato": fmt,
            "linhas": df.height, "truncado": df.height >= LIMITE_LINHAS}
