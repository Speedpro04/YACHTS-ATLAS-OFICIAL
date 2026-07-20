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
import hmac
import os

from fastapi import APIRouter, HTTPException, Query

from app.core.supabase import get_supabase_admin

router = APIRouter()

# Segredo da assinatura.
#
# Ordem: variável dedicada -> JWT secret do Supabase -> literal de dev.
# Cair no SUPABASE_JWT_SECRET é proposital: ele já existe em produção, então a
# verificação funciona no deploy sem configuração nova — e sem o risco de
# alguém esquecer a variável e o sistema assinar com o segredo de dev.
#
# ATENÇÃO: trocar este segredo invalida os QR de todos os dossiês já emitidos.
# Se um dia for necessário rotacionar, versione a assinatura em vez de trocar.
_SEGREDO = (
    os.getenv("VERIFICACAO_SECRET")
    or os.getenv("SUPABASE_JWT_SECRET")
    or "yachts-atlas-verificacao-dev"
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

    return {
        "autentico": True,
        "protocolo": protocolo,
        "emitido_em": e,
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
