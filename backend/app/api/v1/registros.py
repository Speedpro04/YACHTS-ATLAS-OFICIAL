"""
Yachts Atlas — Registros (Cofre Digital Imutável)

Modelo de custódia em dois estágios:

  1. RASCUNHO  (public.registros_rascunho) — livre: edita, salva, descarta.
  2. SELADO    (public.registros)          — append-only: nem UPDATE nem DELETE,
                                             nem com service_role. Selar é INSERT.

Errou depois de selar? Não se apaga: insere-se um registro de RETIFICAÇÃO
apontando para o original (motivo obrigatório). Os dois ficam no dossiê — o
original marcado como retificado, a correção logo abaixo.

A situação (vigente / retificado / retificador) é DERIVADA em
public.vw_registros_situacao — nunca gravada, porque gravar exigiria UPDATE.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase import get_supabase_admin
from app.services.s3_service import get_s3_service
from app.core.security import get_current_user
from app.core.authz import get_ativo_autorizado
from pydantic import BaseModel, Field
from typing import Optional, Any

router = APIRouter()
logger = logging.getLogger(__name__)

# Status válidos conforme o CHECK da tabela
STATUS_VALIDOS = ["registrado", "pendente", "atencao", "concluido"]

# Espelha o CHECK chk_retificacao_motivo no banco
MOTIVO_MIN = 10


class RegistroCreate(BaseModel):
    ativo_id: str
    categoria: str
    titulo: Optional[str] = None
    observacao: Optional[str] = None
    dados: dict[str, Any] = {}
    checklist: list[Any] = []
    status: str = "registrado"
    # Registro ao qual este dá DESFECHO — o reparo que fecha uma avaria.
    #
    # Não confundir com `retifica_id`: retificar é "eu estava errado";
    # resolver é "aquilo aconteceu e acabou". Misturar os dois faria o dossiê
    # mostrar uma avaria real como se fosse erro de digitação.
    #
    # Os dois registros seguem selados, cada um lacrado na sua data — a avaria
    # quando apareceu, o reparo quando terminou. É essa cronologia que dá
    # força ao documento: sem ela, "este barco teve um rombo" fica sem a
    # segunda metade, que é "e foi reparado assim, por quem, com qual laudo".
    resolve_id: Optional[str] = None


class RascunhoUpdate(BaseModel):
    titulo: Optional[str] = None
    observacao: Optional[str] = None
    dados: Optional[dict[str, Any]] = None
    checklist: Optional[list[Any]] = None
    status: Optional[str] = None


class RetificacaoCreate(RegistroCreate):
    """Corrige um registro já selado. O original permanece intacto."""
    retifica_id: str
    motivo_retificacao: str = Field(min_length=MOTIVO_MIN)


def _recalcular_saude(ativo_id: str) -> None:
    """
    Atualiza a nota do ativo depois de selar um registro.

    A nota e calculada por `calcular_saude_ativo`, que persiste em
    `ativos.progresso` e `ativos.classificacao` — mas so rodava quando alguem
    chamava GET /ativos/{id}/progresso, e o frontend nunca chamava. Resultado:
    a marina registrava 16 servicos e o selo continuava "Saude 0% - Bronze",
    parado no valor do cadastro.

    Isso destroi o incentivo que a nota existe para criar. Ela e o argumento de
    que vale a pena alimentar o cofre: se nao se mexe quando a marina trabalha,
    vira enfeite — e no dossie sai um numero que contradiz o proprio conteudo.

    Best-effort: falhar aqui nao pode impedir o registro de ser selado. O
    registro e o produto; a nota e derivada dele e pode ser recalculada depois.
    """
    try:
        from app.services.asset_score_service import calcular_saude_ativo
        calcular_saude_ativo(ativo_id, persistir=True)
    except Exception as e:  # noqa: BLE001
        logger.warning("Nao foi possivel recalcular a saude de %s: %s", ativo_id, e)


def _so_a_marina(ativo_id: str, token: dict) -> None:
    """
    Escrita e da MARINA. O armador le, nao mexe.

    `_owner_do_ativo` apenas DESCOBRE de quem e o ativo para preencher o campo
    — nunca verificou se quem pede tem direito. Sem esta checagem, uma conta
    qualquer escrevia registro no barco de outra marina, e o guardiao central
    (core/authz.py) ficava sendo contornado justamente na tabela que e o
    produto: a cadeia de custodia selada.
    """
    get_ativo_autorizado(ativo_id, str(token.get("sub") if token else ""))


def _pode_ler(ativo_id: str, token: dict) -> None:
    """
    Leitura: a marina dona E o armador do barco.

    `incluir_proprietario=True` e o que deixa o dono acompanhar o proprio
    historico no Portal do Proprietario — ver e direito dele. Alterar nao:
    isso segue exigindo ser a marina.
    """
    get_ativo_autorizado(
        ativo_id, str(token.get("sub") if token else ""), incluir_proprietario=True
    )


def _ativo_do_rascunho(supabase, rascunho_id: str) -> str:
    """
    Descobre a qual ativo o rascunho pertence, para poder autorizar.

    Estes endpoints recebem o id do RASCUNHO, entao a checagem precisa de um
    salto a mais. Sem ele, ficavam abertos: bastava um id de rascunho para
    editar, descartar ou SELAR trabalho de outra marina — e selar e
    irreversivel.
    """
    r = supabase.table("registros_rascunho").select("ativo_id").eq("id", rascunho_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    return r.data[0]["ativo_id"]


def _owner_do_ativo(supabase, ativo_id: str) -> Optional[str]:
    """Retorna o usuario_id (dono) do ativo, para vincular o registro."""
    ativo = supabase.table("ativos").select("usuario_id").eq("id", ativo_id).execute()
    return ativo.data[0]["usuario_id"] if ativo.data else None


def _so_os_ativos_da_conta(supabase, user_id: str) -> list[dict]:
    """Os ativos que esta conta opera — a guarda das rotas SEM `ativo_id` no path.

    `_so_a_marina` e `_pode_ler` pedem um ativo para autorizar, e não servem
    numa lista por conta: não há um ativo, há o conjunto. Este filtro fazia o
    mesmo trabalho, mas escrito à mão dentro do endpoint — e por isso a rede de
    proteção da suíte (que procura por uma guarda NOMEADA em cada bloco de
    rota) apontava o /pre-data como endpoint sem autorização. Não havia
    vazamento; havia uma guarda anônima, que é indistinguível de guarda nenhuma
    para quem lê depois, humano ou teste.

    Mesma regra do /ativos, e não uma nova: abrir exceção aqui seria criar um
    segundo caminho de leitura.
    """
    ativos = (
        supabase.table("ativos").select("id, nome_reg, marca, modelo, ano_fabricacao, comprimento, usuario_id")
        .is_("arquivado_em", "null").execute().data
        or []
    )
    meus = [a for a in ativos if str(a.get("usuario_id")) == user_id]
    if meus:
        return meus
    return ativos if _role_do_usuario(supabase, user_id) == "admin" else []


@router.get("/pre-data")
async def listar_pre_data(token: dict = Depends(get_current_user)):
    """O armario de pre-dados, POR EMBARCACAO.

    O que chega do Atlas Pre-Data e dado CRU: veio do pier, ninguem conferiu,
    nada foi tratado. A tela precisa dizer isso com todas as letras — pre-dado
    com cara de registro e pior que pre-dado nenhum, porque alguem vai ler como
    se fosse verdade conferida.

    AGRUPADO POR ATIVO, sem misturar: dois barcos diferentes sao duas historias
    diferentes, e uma lista corrida faria o revisor conferir o servico de um
    olhando a foto do outro.

    Devolve tambem as FOTOS pendentes de cada ativo, porque texto e imagem
    chegam por caminhos separados (`registros_rascunho` e `documentos`) e quem
    revisa precisa dos dois lado a lado.
    """
    supabase = get_supabase_admin()
    user_id = str(token.get("sub") if token else "")

    meus = _so_os_ativos_da_conta(supabase, user_id)
    if not meus:
        return {"embarcacoes": [], "total_envios": 0}

    ids = [a["id"] for a in meus]

    rascunhos = (
        supabase.table("registros_rascunho").select("*")
        .in_("ativo_id", ids).order("created_at", desc=True).execute().data
        or []
    )
    fotos = (
        supabase.table("documentos").select("id, ativo_id, nome_arquivo, categoria, descricao, created_at, storage_path")
        .in_("ativo_id", ids).eq("status", "pendente").execute().data
        or []
    )

    por_ativo: dict[str, dict] = {}
    for a in meus:
        por_ativo[a["id"]] = {
            "ativo_id": a["id"],
            "nome": a.get("nome_reg") or a["id"],
            "embarcacao": " ".join(x for x in [a.get("marca"), a.get("modelo")] if x),
            "ano": a.get("ano_fabricacao"),
            "pes": a.get("comprimento"),
            "envios": [],
            "fotos_pendentes": [],
        }

    for r in rascunhos:
        alvo = por_ativo.get(r.get("ativo_id"))
        if alvo is not None:
            alvo["envios"].append(r)
    # A FOTO PRECISA SER VISTA, nao nomeada.
    #
    # A aba devolvia `nome_arquivo` e o caminho no storage — e o revisor era
    # convidado a aprovar "IMG_4821.jpg" sem saber se e o barco certo, se a
    # avaria aparece ou se o arquivo e um panfleto de fornecedor. Aprovacao as
    # cegas e carimbo: destroi exatamente o motivo de a revisao existir.
    #
    # A URL e assinada e vale uma hora. O balde `media` e privado (e tem de
    # continuar), entao nao ha link publico a servir: cada revisao gera o seu.
    s3 = get_s3_service()
    for f in fotos:
        alvo = por_ativo.get(f.get("ativo_id"))
        if alvo is None:
            continue
        caminho = f.get("storage_path")
        if caminho:
            try:
                f["url"] = s3.get_presigned_url(caminho, expires_in=3600)
            except Exception as e:  # pragma: no cover - degradacao proposital
                # Sem a imagem a aba ainda serve: mostra o que chegou e deixa
                # aprovar. Falhar a lista inteira porque UMA assinatura nao saiu
                # seria trocar um revisor sem foto por um revisor sem nada.
                logger.warning(f"Falha ao assinar URL da foto {f.get('id')}: {e}")
                f["url"] = None
        alvo["fotos_pendentes"].append(f)

    # So embarcacao COM envio aparece. Lista de frota inteira com zero ao lado
    # de quase todo nome esconde as tres que importam.
    com_envio = [v for v in por_ativo.values() if v["envios"] or v["fotos_pendentes"]]
    com_envio.sort(key=lambda v: len(v["envios"]) + len(v["fotos_pendentes"]), reverse=True)

    return {
        "embarcacoes": com_envio,
        "total_envios": sum(len(v["envios"]) for v in com_envio),
        "total_fotos": sum(len(v["fotos_pendentes"]) for v in com_envio),
    }


def _role_do_usuario(supabase, user_id: str) -> str:
    try:
        r = supabase.table("profiles").select("user_role").eq("id", user_id).execute()
        return (r.data[0].get("user_role") if r.data else "") or ""
    except Exception:
        return ""


# ATENCAO A ORDEM: /pre-data precisa vir ANTES de /{ativo_id}.
#
# O FastAPI casa a primeira rota que bate, e /{ativo_id} aceita qualquer texto
# no lugar do id — inclusive a palavra "pre-data". Com a ordem invertida a aba
# inteira respondia "Ativo nao encontrado", como se o endpoint nao existisse.
@router.get("/{ativo_id}")
async def list_registros(ativo_id: str, token: dict = Depends(get_current_user)):
    """Lista os registros selados de um ativo, com a situação derivada.

    Nao tinha verificacao nenhuma: qualquer conta autenticada lia os registros
    de qualquer barco sabendo o id — e o id e previsivel (YA-IATE-2015-3A38),
    entao bastava trocar os digitos finais para varrer os clientes das outras
    marinas. O historico selado e o produto; vaza-lo destroi o motivo de
    alguem confiar o barco a plataforma.
    """
    _pode_ler(ativo_id, token)
    try:
        supabase = get_supabase_admin()
        result = (
            supabase.table("vw_registros_situacao")
            .select("*")
            .eq("ativo_id", ativo_id)
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_registro(data: RegistroCreate, token: dict = Depends(get_current_user)):
    """Cria um registro imutável."""
    if data.status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"status inválido (use: {', '.join(STATUS_VALIDOS)})")
    _so_a_marina(data.ativo_id, token)
    try:
        supabase = get_supabase_admin()

        usuario_id = _owner_do_ativo(supabase, data.ativo_id)
        if not usuario_id:
            raise HTTPException(status_code=404, detail="Ativo não encontrado")

        result = supabase.table("registros").insert({
            "ativo_id": data.ativo_id,
            "usuario_id": usuario_id,
            "categoria": data.categoria,
            "titulo": data.titulo,
            "observacao": data.observacao,
            "dados": data.dados,
            "checklist": data.checklist,
            "status": data.status,
            "resolve_id": data.resolve_id,
            "created_by": token.get("sub") if token else None,
        }).execute()
        _recalcular_saude(data.ativo_id)
        return result.data[0] if result.data else {}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/retificar")
async def retificar_registro(data: RetificacaoCreate, token: dict = Depends(get_current_user)):
    """Retifica um registro já selado.

    Não altera nem apaga o original: insere um novo registro apontando para ele.
    O dossiê passa a exibir os dois, com o motivo da correção à vista.
    """
    if data.status not in STATUS_VALIDOS:
        raise HTTPException(status_code=400, detail=f"status inválido (use: {', '.join(STATUS_VALIDOS)})")

    supabase = get_supabase_admin()

    _so_a_marina(data.ativo_id, token)

    alvo = supabase.table("registros").select("id, ativo_id").eq("id", data.retifica_id).execute()
    if not alvo.data:
        raise HTTPException(status_code=404, detail="Registro a retificar não encontrado")
    if alvo.data[0]["ativo_id"] != data.ativo_id:
        raise HTTPException(status_code=400, detail="O registro a retificar pertence a outro ativo")

    ja = supabase.table("registros").select("id").eq("retifica_id", data.retifica_id).execute()
    if ja.data:
        raise HTTPException(
            status_code=409,
            detail="Este registro já foi retificado. Retifique a retificação mais recente.",
        )

    usuario_id = _owner_do_ativo(supabase, data.ativo_id)
    if not usuario_id:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")

    try:
        result = supabase.table("registros").insert({
            "ativo_id": data.ativo_id,
            "usuario_id": usuario_id,
            "categoria": data.categoria,
            "titulo": data.titulo,
            "observacao": data.observacao,
            "dados": data.dados,
            "checklist": data.checklist,
            "status": data.status,
            "created_by": token.get("sub") if token else None,
            "retifica_id": data.retifica_id,
            "motivo_retificacao": data.motivo_retificacao,
        }).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Rascunhos (mutáveis, fora da tabela selada) ─────────────────────────

@router.get("/rascunho/{ativo_id}")
async def list_rascunhos(ativo_id: str, token: dict = Depends(get_current_user)):
    # Rascunho e trabalho em andamento da MARINA — ainda nao selado e nao
    # entra no dossie. O armador nao ve o que ela ainda esta digitando.
    _so_a_marina(ativo_id, token)
    supabase = get_supabase_admin()
    result = (
        supabase.table("registros_rascunho").select("*")
        .eq("ativo_id", ativo_id).order("updated_at", desc=True).execute()
    )
    return result.data


@router.post("/rascunho")
async def create_rascunho(data: RegistroCreate, token: dict = Depends(get_current_user)):
    """Cria um rascunho. Editável e descartável — ainda não entra no dossiê."""
    _so_a_marina(data.ativo_id, token)
    supabase = get_supabase_admin()
    usuario_id = _owner_do_ativo(supabase, data.ativo_id)
    if not usuario_id:
        raise HTTPException(status_code=404, detail="Ativo não encontrado")
    novo = {
        "ativo_id": data.ativo_id,
        "usuario_id": usuario_id,
        "categoria": data.categoria,
        "titulo": data.titulo,
        "observacao": data.observacao,
        "dados": data.dados,
        "checklist": data.checklist,
        "created_by": token.get("sub") if token else None,
    }
    # A condicao vinda do campo ("atencao", "pendente", "concluido") era enviada
    # pelo Atlas Pre-Data e descartada aqui: a coluna nao entrava no insert e
    # ficava no default 'rascunho'. Como 'rascunho' nao esta em STATUS_VALIDOS,
    # o selo rebaixava tudo para "registrado" — o sinal de avaria levantado no
    # pier sumia entre o barco e o dossie, sem erro nenhum para avisar.
    if data.status in STATUS_VALIDOS:
        novo["status"] = data.status
    result = supabase.table("registros_rascunho").insert(novo).execute()
    return result.data[0] if result.data else {}


@router.patch("/rascunho/{rascunho_id}")
async def update_rascunho(
    rascunho_id: str, data: RascunhoUpdate, token: dict = Depends(get_current_user)
):
    supabase = get_supabase_admin()
    _so_a_marina(_ativo_do_rascunho(supabase, rascunho_id), token)
    campos = {k: v for k, v in data.model_dump().items() if v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="Nada para atualizar")
    result = supabase.table("registros_rascunho").update(campos).eq("id", rascunho_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    return result.data[0]


@router.delete("/rascunho/{rascunho_id}")
async def descartar_rascunho(rascunho_id: str, token: dict = Depends(get_current_user)):
    """Descarta um rascunho. Só vale antes de selar — depois não há volta."""
    supabase = get_supabase_admin()
    _so_a_marina(_ativo_do_rascunho(supabase, rascunho_id), token)
    supabase.table("registros_rascunho").delete().eq("id", rascunho_id).execute()
    return {"message": "Rascunho descartado"}


def _status_do_selo(rasc: dict) -> str:
    """A condição com que o rascunho vira registro.

    Ordem de procura: a coluna, depois `dados.condicao`, e só então o padrão.

    O meio do caminho existe pelos rascunhos gravados ANTES de `create_rascunho`
    passar a guardar a condição: estão todos com status 'rascunho', que não é
    válido, e a condição deles sobreviveu apenas dentro do jsonb — o Atlas
    Pré-Data grava nos dois lugares. Sem esta leitura, selar um pré-dado antigo
    apagaria de vez o "atenção" levantado no píer, e apagaria em silêncio.
    """
    status = (rasc.get("status") or "").strip()
    if status in STATUS_VALIDOS:
        return status
    do_campo = ((rasc.get("dados") or {}).get("condicao") or "").strip()
    return do_campo if do_campo in STATUS_VALIDOS else "registrado"


@router.post("/rascunho/{rascunho_id}/selar")
async def selar_rascunho(rascunho_id: str, token: dict = Depends(get_current_user)):
    """Sela o rascunho: INSERT na tabela append-only e remove o rascunho.

    Ato irreversível — a partir daqui o registro não pode ser editado nem
    excluído. Correções só por retificação.
    """
    supabase = get_supabase_admin()
    _so_a_marina(_ativo_do_rascunho(supabase, rascunho_id), token)

    r = supabase.table("registros_rascunho").select("*").eq("id", rascunho_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    rasc = r.data[0]

    status = _status_do_selo(rasc)

    try:
        selado = supabase.table("registros").insert({
            "ativo_id": rasc["ativo_id"],
            "usuario_id": rasc["usuario_id"],
            "categoria": rasc["categoria"],
            "titulo": rasc.get("titulo"),
            "observacao": rasc.get("observacao"),
            "dados": rasc.get("dados") or {},
            "checklist": rasc.get("checklist") or [],
            "status": status,
            "created_by": token.get("sub") if token else rasc.get("created_by"),
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao selar: {e}")

    if not selado.data:
        raise HTTPException(status_code=500, detail="Falha ao selar: registro não retornado")

    # só remove o rascunho depois que o selo existe — nunca perde dado
    supabase.table("registros_rascunho").delete().eq("id", rascunho_id).execute()

    return {
        "message": "Registro selado. Não pode mais ser editado nem excluído.",
        "registro": selado.data[0],
    }


@router.get("/stats/{ativo_id}")
async def get_registro_stats(ativo_id: str, token: dict = Depends(get_current_user)):
    # Contagem por categoria tambem e informacao do ativo: dizer quantos
    # registros a marina tem em cada aba ja entrega o tamanho da operacao dela.
    _pode_ler(ativo_id, token)
    """Contagem de registros por status para um ativo."""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("registros").select("status").eq("ativo_id", ativo_id).execute()
        records = result.data or []
        return {
            "total": len(records),
            "registrado": sum(1 for r in records if r["status"] == "registrado"),
            "pendente": sum(1 for r in records if r["status"] == "pendente"),
            "atencao": sum(1 for r in records if r["status"] == "atencao"),
            "concluido": sum(1 for r in records if r["status"] == "concluido"),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
