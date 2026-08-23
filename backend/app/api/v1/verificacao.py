"""
Yachts Atlas — Verificação pública de autenticidade do dossiê.

É o destino do QR Code impresso na última página de cada dossiê. Quem escaneia
é um comprador, corretor ou perito de seguradora — gente SEM conta na
plataforma. Por isso estes endpoints são públicos.

DUAS REGRAS DE SEGURANÇA QUE MOLDAM ESTE MÓDULO:

1. O protocolo é o `ativo_id` (ex.: YA-LANCHA-2017-0065) — formato previsível,
   portanto ENUMERÁVEL. Alguém pode varrer trocando os dígitos finais.
   Por isso o QR carrega uma assinatura (`s`) derivada do próprio documento:
   sem ela, a verificação não responde. Só verifica quem tem o PDF na mão.

2. Esta página NÃO expõe o conteúdo do dossiê — nem histórico, nem valores,
   nem dados do proprietário. Devolve apenas o mínimo para confirmar
   autenticidade: identificação da embarcação, contagem de registros selados
   e o veredito de integridade. Vazar a base seria o oposto do que o produto
   promete.
"""
import hashlib
import logging
import hmac
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import get_supabase_admin

router = APIRouter()

# Segredo da assinatura.
#
# Já caiu no SUPABASE_JWT_SECRET quando a variável dedicada faltava. Aquele
# valor está publicado no histórico do Git, então quem o tivesse forjava o
# código de verificação de qualquer dossiê. O encadeamento foi removido: ou a
# variável dedicada existe, ou fica o literal de dev — que nunca deve chegar a
# produção e por isso grita no log.
#
# ATENÇÃO: trocar este segredo invalida os QR de todos os dossiês já emitidos.
# Se um dia for necessário rotacionar, versione a assinatura em vez de trocar.
_SEGREDO = os.getenv("VERIFICACAO_SECRET") or "yachts-atlas-verificacao-dev"

if not os.getenv("VERIFICACAO_SECRET"):
    logging.getLogger(__name__).warning(
        "VERIFICACAO_SECRET nao configurado — assinatura do QR usando segredo "
        "de desenvolvimento. NAO usar assim em producao."
    )

TAM_ASSINATURA = 12


def _so_digitos(data: str) -> str:
    """19/07/2026 e 19-07-2026 devem gerar a MESMA assinatura.

    A URL do QR troca `/` por `-` (barra quebraria o caminho), então normalizar
    aqui evita que a assinatura dependa do separador.
    """
    return "".join(ch for ch in str(data or "") if ch.isdigit())


def assinar(protocolo: str, emitido: str) -> str:
    """Assinatura curta do documento, embutida no QR.

    Deriva de protocolo + data de emissão, então o link de um dossiê emitido
    hoje não valida um protocolo diferente. Curta de propósito: cabe no QR e
    não precisa resistir a ataque criptográfico — só a adivinhação casual.
    """
    msg = f"{protocolo}|{_so_digitos(emitido)}".encode()
    return hmac.new(_SEGREDO.encode(), msg, hashlib.sha256).hexdigest()[:TAM_ASSINATURA]


def _confere_assinatura(protocolo: str, emitido: str, s: str) -> bool:
    return hmac.compare_digest(assinar(protocolo, emitido), (s or "").lower())


@router.get("/documento/{hash_pdf}")
async def verificar_documento(hash_pdf: str):
    """Contra-prova: este arquivo corresponde a algum dossiê emitido?

    Recebe a IMPRESSÃO DIGITAL, nunca o arquivo. Quem verifica calcula o
    SHA-256 no próprio navegador e envia só o hash — o dossiê não sai da
    máquina dele. Além de rápido e barato, resolve o problema de confiança na
    ordem certa: ninguém deveria precisar entregar um documento sigiloso a um
    terceiro para descobrir se ele é legítimo.

    Aberto de propósito, sem autenticação e sem cobrança. O efeito antifraude
    vem da EXISTÊNCIA da conferência, não do preço: ninguém adultera um
    documento que qualquer um confere em dois segundos. Cobrar aqui mataria
    justamente o que faz isso funcionar.

    Não há risco de enumeração: um SHA-256 tem 2^256 possibilidades, e para
    ter o hash é preciso ter o arquivo. Quem tem o arquivo já sabe de que
    ativo ele é.
    """
    h = (hash_pdf or "").strip().lower()
    # Formato antes de consultar: 64 hex. Recusar aqui evita transformar erro
    # de digitação em consulta ao banco, e deixa a mensagem específica.
    if len(h) != 64 or any(c not in "0123456789abcdef" for c in h):
        raise HTTPException(
            status_code=400,
            detail="Impressão digital inválida. Informe um SHA-256 (64 caracteres).",
        )

    try:
        res = (
            get_supabase_admin().table("dossie_emitidos")
            .select("protocolo, emitido_em, tamanho_bytes, created_at")
            .eq("hash_pdf", h).order("created_at", desc=True).limit(1).execute()
        )
    except Exception as ex:
        logging.getLogger(__name__).error(f"Falha ao consultar emissão {h[:12]}: {ex}")
        raise HTTPException(status_code=503, detail="Não foi possível consultar agora. Tente novamente.")

    if not res.data:
        # NÃO é erro HTTP: "não corresponde" é uma resposta legítima e é
        # metade do serviço. Devolver 404 faria o front tratar como falha e
        # mostrar "erro" onde deveria mostrar um veredito.
        return {
            "corresponde": False,
            "hash": h,
            "mensagem": "Esta impressão digital não corresponde a nenhum dossiê "
                        "emitido pelo Yachts Atlas. O arquivo pode ter sido "
                        "alterado após a emissão, ou não ter origem nesta plataforma.",
        }

    d = res.data[0]
    return {
        "corresponde": True,
        "hash": h,
        "protocolo": d.get("protocolo"),
        "emitido_em": "/".join(reversed(str(d.get("emitido_em"))[:10].split("-"))),
        "tamanho_bytes": d.get("tamanho_bytes"),
        "mensagem": "Documento íntegro. Esta impressão digital corresponde "
                    "exatamente ao dossiê emitido pelo Yachts Atlas.",
    }


# Fuso fixo em vez de ZoneInfo: o Brasil não tem horário de verão desde 2019,
# e ZoneInfo("America/Sao_Paulo") depende do pacote tzdata, que existe no
# contêiner e pode faltar na máquina de quem roda local. Data de emissão que
# aparece diferente em dois lugares é o tipo de coisa que faz um perito
# desconfiar do documento inteiro.
_FUSO_BR = timezone(timedelta(hours=-3))


def _emissao_legivel(registro: dict) -> str:
    """Data da emissão com a hora, quando ela existir.

    Três vias emitidas no mesmo dia apareciam como três linhas idênticas —
    "EMITIDO EM 23/08/2026" três vezes. Quem estava com uma delas na mão não
    tinha como saber qual era a sua; sabia apenas que uma das três deveria
    bater. Num documento que vai para seguradora, isso lê como desleixo.

    A hora vem de `created_at` (o instante em que a emissão foi registrada),
    não de `emitido_em`, que é DATE e é o campo coberto pela assinatura do QR.
    Aqui é só apresentação — a assinatura continua sobre protocolo + data.
    """
    data = "/".join(reversed(str(registro.get("emitido_em"))[:10].split("-")))
    bruto = registro.get("created_at")
    if not bruto:
        return data
    try:
        ts = datetime.fromisoformat(str(bruto).replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return f"{data} · {ts.astimezone(_FUSO_BR):%H:%M}"
    except (ValueError, TypeError):
        # Formato inesperado não pode derrubar a verificação: a data sozinha
        # já cumpre o essencial.
        return data


@router.get("/{protocolo}")
async def verificar(
    protocolo: str,
    s: str = Query(..., description="Assinatura do documento (vem no QR)"),
    e: str = Query(..., description="Data de emissão do documento (DD/MM/AAAA)"),
):
    """Confirma a autenticidade de um dossiê emitido.

    Devolve o mínimo necessário para o portador do PDF conferir se o documento
    em mãos corresponde ao que a plataforma custodia.
    """
    if not _confere_assinatura(protocolo, e, s):
        # Mesma resposta para assinatura inválida e protocolo inexistente:
        # distinguir os dois casos entregaria um oráculo de enumeração.
        raise HTTPException(
            status_code=404,
            detail="Documento não localizado. Confira se o protocolo e o código "
                   "de verificação correspondem ao PDF em mãos.",
        )

    supabase = get_supabase_admin()

    ativo_res = (
        supabase.table("ativos")
        .select("id, nome_reg, marca, modelo, ano_fabricacao, comprimento, "
                "classificacao, arquivado_em")
        .eq("id", protocolo).execute()
    )
    if not ativo_res.data:
        raise HTTPException(
            status_code=404,
            detail="Documento não localizado. Confira se o protocolo e o código "
                   "de verificação correspondem ao PDF em mãos.",
        )
    ativo = ativo_res.data[0]

    registros = (
        supabase.table("registros")
        .select("id, hash_sha256, created_at, retifica_id")
        .eq("ativo_id", protocolo).execute().data or []
    )

    com_hash = sum(1 for r in registros if r.get("hash_sha256"))
    retificacoes = sum(1 for r in registros if r.get("retifica_id"))
    datas = sorted(r["created_at"] for r in registros if r.get("created_at"))

    documentos = (
        supabase.table("documentos").select("id", count="exact")
        .eq("ativo_id", protocolo).execute()
    )

    nome = ativo.get("nome_reg") or " ".join(
        x for x in [ativo.get("marca"), ativo.get("modelo")] if x
    ) or "—"

    comprimento = ativo.get("comprimento")
    ficha = " · ".join(str(x) for x in [
        ativo.get("marca"), ativo.get("modelo"),
        f"{float(comprimento):g} pés".replace(".", ",") if comprimento else None,
        ativo.get("ano_fabricacao"),
    ] if x)

    # Impressão digital dos dossiês já emitidos para este protocolo.
    #
    # É o que fecha a lacuna da assinatura: ela cobre protocolo + data, não o
    # conteúdo. Quem recebesse um dossiê legítimo podia editar valores, apagar
    # o histórico de sinistros, e o QR continuaria dizendo "autêntico".
    #
    # Com o hash aqui, quem tem o PDF em mãos calcula o SHA-256 do próprio
    # arquivo e compara. Bateu, é o original; não bateu, foi mexido depois da
    # emissão. A plataforma não precisa guardar o arquivo — basta lembrar a
    # impressão digital dele.
    emitidos = []
    try:
        res = (
            get_supabase_admin().table("dossie_emitidos")
            .select("hash_pdf, emitido_em, created_at")
            .eq("protocolo", protocolo)
            .order("created_at", desc=True)
            .limit(5).execute()
        )
        emitidos = [
            {"hash": d.get("hash_pdf"), "emitido_em": _emissao_legivel(d)}
            for d in (res.data or []) if d.get("hash_pdf")
        ]
    except Exception as ex:
        logging.getLogger(__name__).error(f"Falha ao ler emissões de {protocolo}: {ex}")

    return {
        "autentico": True,
        "protocolo": protocolo,
        "emitido_em": e,
        # Lista, e não um valor só: o mesmo ativo pode ter mais de um dossiê
        # emitido (atualização depois de novo registro selado), e todos são
        # legítimos. Mostrar só o último faria o portador de uma via anterior
        # concluir, erradamente, que o documento dele foi adulterado.
        "documentos_emitidos": emitidos,
        "embarcacao": {"nome": nome, "ficha": ficha or None,
                       "classificacao": (ativo.get("classificacao") or "").upper() or None},
        "custodia": {
            "registros_selados": len(registros),
            "documentos_selados": documentos.count or 0,
            "retificacoes": retificacoes,
            "desde": ("/".join(reversed(str(datas[0])[:10].split("-"))) if datas else None),
            "arquivado": bool(ativo.get("arquivado_em")),
        },
        "integridade": {
            "registros_com_hash": com_hash,
            "total": len(registros),
            "integro": com_hash == len(registros) and len(registros) > 0,
            "algoritmo": "SHA-256 · append-only",
        },
        # O que a plataforma NÃO devolve aqui, e por quê.
        "aviso": "Esta verificação confirma a autenticidade do documento e a "
                 "integridade da cadeia de custódia. O conteúdo do dossiê "
                 "(histórico, valores e dados do proprietário) não é exposto "
                 "publicamente.",
    }
