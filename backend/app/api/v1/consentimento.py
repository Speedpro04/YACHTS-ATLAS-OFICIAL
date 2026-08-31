"""
Consentimento do titular — a base legal para o dossiê sair para um terceiro.

O QUE FALTAVA
-------------
A plataforma já registrava **para quem** o dossiê foi, quando e para quê
(`dossie_solicitacoes` + `dossie_saidas`). O que não existia era o outro lado:
o armador ter dito que **pode**. Sem isso, o compartilhamento tem trilha e
não tem base legal — a LGPD pede as duas coisas, e uma seguradora auditando
pergunta pelas duas.

ONDE O CONSENTIMENTO É COLHIDO
------------------------------
Uma vez, no cadastro do ativo, e não a cada liberação. A escolha é do
fundador (31/08/2026) e tem motivo de produto: pedir aprovação do armador a
cada envio mata a promessa de velocidade — o comprador está no píer
esperando, e o armador pode estar navegando. Autorizar a marina a emitir
dossiês daquela embarcação é o mesmo ato de confiança que já existe quando
ele entrega o barco à marina.

POR QUE APPEND-ONLY
-------------------
Consentimento se dá e se retira (LGPD art. 8º, §5º). Uma coluna booleana em
`ativos` apagaria a retirada anterior a cada mudança e, pior, poderia ter a
data alterada em silêncio — `ativos` aceita UPDATE. Aqui cada evento é uma
linha, e o gatilho `trg_ativo_consentimentos_imutavel` recusa UPDATE e
DELETE: retirar é registrar um evento `revogado`, nunca apagar o anterior.

O nome e o documento do titular são **fotografados** na linha. Barco troca de
dono, e o consentimento do dono anterior não vale para o novo.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, field_validator

from app.core.authz import get_ativo_autorizado
from app.core.pii import mascarar_documento
from app.core.security import get_current_user
from app.core.supabase import get_supabase_admin

logger = logging.getLogger(__name__)
router = APIRouter()

# Versionado: o texto muda com o tempo, e uma auditoria precisa saber COM O
# QUE o titular concordou naquela data — não com o que o site diz hoje.
TERMO_VERSAO = "2026-08-31"
TERMO_TEXTO = (
    "O titular autoriza a marina depositária a emitir o Dossiê de Custódia "
    "desta embarcação e a compartilhá-lo com terceiros por ela identificados "
    "— comprador, corretor, seguradora ou perito — para as finalidades de "
    "avaliação, seguro, vistoria ou transação. O dossiê reúne dados da "
    "embarcação, o histórico de serviços registrado pela marina e os "
    "documentos depositados. O documento do titular é exibido de forma "
    "mascarada. Cada compartilhamento é registrado com destinatário, data e "
    "finalidade, e fica disponível ao titular. Esta autorização pode ser "
    "retirada a qualquer momento, sem efeito retroativo sobre dossiês já "
    "entregues."
)

VIAS = ("contrato_marina", "assinatura_digital", "email", "presencial")


class ConsentimentoEntrada(BaseModel):
    evento: str
    obtido_via: str
    titular_nome: Optional[str] = None
    titular_documento: Optional[str] = None
    observacao: Optional[str] = None

    @field_validator("evento")
    @classmethod
    def _evento(cls, v: str) -> str:
        if v not in ("concedido", "revogado"):
            raise ValueError('evento deve ser "concedido" ou "revogado"')
        return v

    @field_validator("obtido_via")
    @classmethod
    def _via(cls, v: str) -> str:
        if v not in VIAS:
            raise ValueError(f"obtido_via deve ser um de: {', '.join(VIAS)}")
        return v


def consentimento_vigente(ativo_id: str) -> dict:
    """Estado atual = último evento. Sem linha nenhuma, sem consentimento.

    Falha de leitura devolve `vigente=None`, nunca True nem False: `True`
    liberaria um compartilhamento sem base legal por causa de uma queda de
    rede; `False` bloquearia uma marina que está em ordem. Quem chama decide
    o que fazer com o "não sei" — e a liberação, que é o ato de risco,
    recusa.
    """
    try:
        res = get_supabase_admin().rpc(
            "fn_consentimento_vigente", {"p_ativo_id": ativo_id}
        ).execute()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Falha ao ler consentimento de {ativo_id}: {e}")
        return {"vigente": None, "evento": None, "registrado_em": None,
                "termo_versao": None, "titular_nome": None}

    linhas = res.data or []
    if not linhas:
        return {"vigente": False, "evento": None, "registrado_em": None,
                "termo_versao": None, "titular_nome": None}
    linha = linhas[0]
    return {
        "vigente": bool(linha.get("vigente")),
        "evento": linha.get("evento"),
        "registrado_em": linha.get("registrado_em"),
        "termo_versao": linha.get("termo_versao"),
        "titular_nome": linha.get("titular_nome"),
    }


@router.get("/{ativo_id}/consentimento")
async def ler_consentimento(ativo_id: str, user: dict = Depends(get_current_user)):
    """Estado do consentimento, mais o termo em vigor para a tela exibir."""
    get_ativo_autorizado(ativo_id, str(user["sub"]))
    estado = consentimento_vigente(ativo_id)
    estado["termo_atual_versao"] = TERMO_VERSAO
    estado["termo_atual_texto"] = TERMO_TEXTO
    estado["desatualizado"] = bool(
        estado["vigente"] and estado["termo_versao"] != TERMO_VERSAO
    )
    return estado


@router.post("/{ativo_id}/consentimento", status_code=201)
async def registrar_consentimento(
    ativo_id: str,
    entrada: ConsentimentoEntrada,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Grava um evento de consentimento. Não edita o anterior — acrescenta."""
    ativo = get_ativo_autorizado(ativo_id, str(user["sub"]))

    # Se a tela não mandou, cai para o que já está no cadastro: é o mesmo
    # titular, e repetir a digitação só cria divergência entre as duas telas.
    nome = entrada.titular_nome or (ativo or {}).get("proprietario_nome")
    doc = entrada.titular_documento or (ativo or {}).get("proprietario_documento")

    try:
        get_supabase_admin().table("ativo_consentimentos").insert({
            "ativo_id": ativo_id,
            "evento": entrada.evento,
            "titular_nome": nome,
            # Mascarado aqui também: a linha de consentimento não é motivo
            # para o CPF voltar a existir em texto plano numa segunda tabela.
            "titular_documento": mascarar_documento(doc),
            "termo_versao": TERMO_VERSAO,
            "termo_texto": TERMO_TEXTO,
            "obtido_via": entrada.obtido_via,
            "observacao": entrada.observacao,
            "registrado_por": str(user["sub"]) if user.get("sub") else None,
        }).execute()
    except Exception as e:  # noqa: BLE001
        logger.error(f"Falha ao registrar consentimento de {ativo_id}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Não foi possível registrar o consentimento. Tente novamente.",
        )

    return consentimento_vigente(ativo_id)


@router.get("/{ativo_id}/consentimento/historico")
async def historico_consentimento(ativo_id: str,
                                  user: dict = Depends(get_current_user)):
    """A sequência inteira. É o que uma auditoria pede: não basta dizer que
    há consentimento hoje, é preciso mostrar quando foi dado e se já foi
    retirado alguma vez."""
    get_ativo_autorizado(ativo_id, str(user["sub"]))
    try:
        res = (get_supabase_admin().table("ativo_consentimentos")
               .select("evento, obtido_via, titular_nome, termo_versao, "
                       "observacao, registrado_em")
               .eq("ativo_id", ativo_id)
               .order("registrado_em", desc=True)
               .execute())
        return {"eventos": res.data or []}
    except Exception as e:  # noqa: BLE001
        logger.error(f"Falha ao ler histórico de consentimento de {ativo_id}: {e}")
        raise HTTPException(status_code=503, detail="Histórico indisponível.")
