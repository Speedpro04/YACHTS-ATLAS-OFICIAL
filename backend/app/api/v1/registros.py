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
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase import get_supabase_admin
from app.services.s3_service import get_s3_service
from app.core.security import get_current_user
from app.core.campo import usuario_ou_campo
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


class RecusarRascunhoBody(BaseModel):
    """Motivo da recusa do pré-dado. Obrigatório."""
    motivo: str


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
        if alvo is None:
            continue
        # A fila do píer guarda só o que ainda não foi decidido. Recusado e
        # aprovado saem daqui — o primeiro para o arquivo (com motivo e autor),
        # o segundo para a mesa do escritório, dentro da embarcação. Nenhum dos
        # dois é apagado; fila que guarda o que já foi decidido para de ser fila.
        marcas = r.get("dados") or {}
        if marcas.get("recusado_em") or marcas.get("aprovado_em"):
            continue
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

            # A miniatura assina em SEPARADO, e de proposito: foto anterior a
            # 15/09/2026 nao tem miniatura, e a assinatura de um caminho que
            # nao existe levanta. Junto com o original, isso zerava o `url` da
            # foto boa — o acessorio derrubando o essencial.
            try:
                from app.services.miniatura import caminho_da_miniatura
                f["url_miniatura"] = s3.get_presigned_url(
                    caminho_da_miniatura(caminho), expires_in=3600
                )
            except Exception:  # pragma: no cover - degradacao proposital
                f["url_miniatura"] = None
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
async def create_rascunho(data: RegistroCreate, token: dict = Depends(usuario_ou_campo)):
    """Cria um rascunho. Editável e descartável — ainda não entra no dossiê.

    Aceita o aparelho do pátio (`usuario_ou_campo`) porque é exatamente para
    isto que o código de campo existe. O `sub` do token de campo é a MARINA,
    então `_so_a_marina` continua valendo sem exceção nenhuma — o colaborador
    não ganha alcance além do que a conta dela já tem.
    """
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

    # O QUE VEIO DO PIER FICA GUARDADO, e só na PRIMEIRA edição.
    #
    # O escritório pode mudar tudo — quem assina o registro é a Marina, e ela
    # responde por ele. Mas o dossiê vale por ser rastreável: seis meses depois
    # alguém vai perguntar se aquele horímetro foi medido no barco ou digitado
    # na mesa, e a resposta precisa existir. A tela mostra o valor atual; o
    # original mora aqui, e nunca é sobrescrito.
    atual = supabase.table("registros_rascunho").select("*").eq("id", rascunho_id).execute()
    if not atual.data:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")
    antes = atual.data[0]
    dados_atuais = dict(antes.get("dados") or {})
    if not dados_atuais.get("original_do_pier"):
        dados_atuais["original_do_pier"] = {
            "titulo": antes.get("titulo"),
            "observacao": antes.get("observacao"),
            "dados": {k: v for k, v in dados_atuais.items() if k != "original_do_pier"},
            "guardado_em": datetime.now(timezone.utc).isoformat(),
        }
        # Se a edição já traz `dados`, o original entra dentro do que vai ser
        # gravado — senão a próxima escrita apagaria a cópia recém-feita.
        if "dados" in campos:
            campos["dados"] = {**(campos["dados"] or {}), "original_do_pier": dados_atuais["original_do_pier"]}
        else:
            campos["dados"] = dados_atuais

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


@router.post("/rascunho/{rascunho_id}/enviar-para-ativos")
async def enviar_para_ativos(rascunho_id: str, token: dict = Depends(get_current_user)):
    """Tira o pré-dado da fila do píer e põe na mesa do escritório.

    NÃO SELA. Esta é a metade que faltava do fluxo combinado:

        chega (Pré-Data) -> trabalha (Ativos) -> sela (vira prova)

    O que chega do píer chega incompleto de propósito — mão suja, pressa, campo
    que a ficha não perguntou. Selar direto da fila obrigava o escritório a
    escolher entre gravar o erro para sempre ou não gravar nada. Aqui o item só
    muda de lugar: sai da aba Pré-Data, aparece dentro da embarcação como "em
    trabalho", e continua inteiramente editável.

    O registro é o MESMO — não há cópia. Muda a marca em `dados`, e com ela o
    lugar onde a pessoa o encontra. Duplicar aqui criaria duas versões do mesmo
    serviço, e a pergunta "qual delas é a boa?" não teria resposta.
    """
    supabase = get_supabase_admin()
    _so_a_marina(_ativo_do_rascunho(supabase, rascunho_id), token)

    r = supabase.table("registros_rascunho").select("*").eq("id", rascunho_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")

    dados = dict(r.data[0].get("dados") or {})
    if dados.get("recusado_em"):
        raise HTTPException(status_code=409, detail="Este pré-dado foi recusado.")
    if dados.get("aprovado_em"):
        return {"id": rascunho_id, "ja_estava": True}

    dados.update({
        "aprovado_em": datetime.now(timezone.utc).isoformat(),
        "aprovado_por": token.get("sub") if token else None,
    })
    supabase.table("registros_rascunho").update({"dados": dados}).eq("id", rascunho_id).execute()
    return {"id": rascunho_id, "enviado_para_ativos": True}


@router.get("/em-trabalho/{ativo_id}")
async def listar_em_trabalho(ativo_id: str, token: dict = Depends(get_current_user)):
    """O que já saiu do píer e ainda não foi selado, desta embarcação.

    É a mesa do escritório: texto editável + as fotos que o explicam. As fotos
    vêm amarradas pelo `client_id` que o Atlas Pré-Data grava na descrição de
    cada upload e também dentro do rascunho — a chave existia desde o início e
    nunca tinha sido usada para juntar os dois lados.

    Foto que chegou sem envio aparece à parte, na mesma embarcação: ela tem dono
    (o barco), só não tem um serviço explicando o que mostra.
    """
    _so_a_marina(ativo_id, token)
    supabase = get_supabase_admin()

    rascunhos = (
        supabase.table("registros_rascunho").select("*")
        .eq("ativo_id", ativo_id).order("created_at", desc=True).execute().data
        or []
    )
    em_trabalho = [
        r for r in rascunhos
        if (r.get("dados") or {}).get("aprovado_em")
        and not (r.get("dados") or {}).get("recusado_em")
    ]

    # SÓ O QUE VEIO DO PÍER entra na mesa.
    #
    # A embarcação tem documentos de vários caminhos — PDF de laudo, foto subida
    # pelo próprio painel, apólice. Nada disso é pré-dado: já entrou conferido e
    # vive no Painel Técnico. Sem este filtro, um barco com 14 documentos
    # mostrava os 14 como "foto sem registro que a explique", e a mesa de
    # trabalho virava um segundo inventário do que já estava resolvido.
    #
    # A marca é a descrição que o Atlas Pré-Data grava em todo upload:
    # "Atlas Pré-Data · <categoria> · <client_id>".
    fotos = [
        f for f in (
            supabase.table("documentos")
            .select("id, nome_arquivo, categoria, descricao, created_at, storage_path, status")
            .eq("ativo_id", ativo_id).neq("status", "recusado").execute().data
            or []
        )
        if (f.get("descricao") or "").startswith("Atlas Pré-Data")
    ]

    s3 = get_s3_service()
    por_client: dict[str, list] = {}
    soltas: list[dict] = []
    for f in fotos:
        caminho = f.get("storage_path")
        if caminho:
            try:
                f["url"] = s3.get_presigned_url(caminho, expires_in=3600)
            except Exception as e:  # pragma: no cover - degradacao proposital
                logger.warning(f"Falha ao assinar URL da foto {f.get('id')}: {e}")
                f["url"] = None

            # A miniatura assina em SEPARADO, e de proposito: foto anterior a
            # 15/09/2026 nao tem miniatura, e a assinatura de um caminho que
            # nao existe levanta. Junto com o original, isso zerava o `url` da
            # foto boa — o acessorio derrubando o essencial.
            try:
                from app.services.miniatura import caminho_da_miniatura
                f["url_miniatura"] = s3.get_presigned_url(
                    caminho_da_miniatura(caminho), expires_in=3600
                )
            except Exception:  # pragma: no cover - degradacao proposital
                f["url_miniatura"] = None
        # O client_id vai no fim da descrição: "Atlas Pré-Data · Manutenção · <id>"
        dono = (f.get("descricao") or "").split("·")[-1].strip()
        if dono:
            por_client.setdefault(dono, []).append(f)
        else:
            soltas.append(f)

    usadas: set[str] = set()
    itens = []
    for r in em_trabalho:
        cid = (r.get("dados") or {}).get("client_id") or ""
        minhas = por_client.get(cid, [])
        usadas.update(str(f["id"]) for f in minhas)
        itens.append({**r, "fotos": minhas})

    # ÓRFÃ DE VERDADE É A QUE NÃO TEM REGISTRO EM LUGAR NENHUM.
    #
    # Até 15/09/2026 bastava não achar o rascunho para a foto ser chamada de
    # órfã. Só que selar APAGA o rascunho — então, no instante em que o serviço
    # vira prova, as fotos dele passavam a ser anunciadas como "sem registro
    # que as explique", com o registro selado logo ali no dossiê. A tela
    # afirmava o contrário do que o banco dizia.
    #
    # Agora o selo leva as fotos junto, e isso deixa de acontecer. Estas duas
    # consultas existem para os envios anteriores ao conserto — e para o dia em
    # que a aprovação do selo falhar, que é best-effort por construção.
    selados = (
        supabase.table("registros").select("dados")
        .eq("ativo_id", ativo_id).execute().data
        or []
    )

    # TEM DONO EM QUALQUER UM DOS TRÊS LUGARES = NÃO É ÓRFÃ.
    #
    # O serviço de um pré-dado vive em três estados, e a foto continua sendo
    # dele nos três:
    #   1. na fila do Pré-Data  — rascunho ainda não enviado para Ativos;
    #   2. na mesa              — rascunho enviado, em edição;
    #   3. selado               — virou prova.
    #
    # A mesa só enxergava o estado 2. Resultado: foto de serviço que ainda
    # espera na fila (1) e foto de serviço já selado (3) eram as duas
    # anunciadas como "sem registro que as explique" — com o registro existindo
    # e visível em outra aba. Aconteceu nos dois sentidos em 15/09/2026.
    com_dono = {
        str((r.get("dados") or {}).get("client_id"))
        for r in (rascunhos + selados)
        if (r.get("dados") or {}).get("client_id")
    }

    candidatas = soltas + [
        f for lista in por_client.values() for f in lista if str(f["id"]) not in usadas
    ]

    # Aprovada já cumpriu o caminho e entrou no dossiê: não pede decisão de
    # ninguém. A mesa mostra o que ESPERA.
    pendentes = [f for f in candidatas if f.get("status") == "pendente"]

    def _dona(foto: dict) -> str:
        return (foto.get("descricao") or "").split("·")[-1].strip()

    # SELADO SAI DA MESA — imagem e texto. Decisão do Marcos em 15/09/2026, e
    # ela é a leitura certa do que esta tela é: a mesa mostra o que ESPERA
    # trabalho. Serviço selado não espera mais nada de ninguém; ele virou prova
    # e mora no Painel Técnico e no dossiê.
    #
    # A foto pendente de um serviço já selado não fica invisível no sistema: a
    # aba Pré-Data continua listando toda foto pendente da embarcação, e é lá
    # que se aprova. E desde hoje o próprio selo já aprova as fotos do serviço,
    # então este caso só existe para os envios anteriores ao conserto.
    orfas = [f for f in pendentes if _dona(f) not in com_dono]

    return {"em_trabalho": itens, "fotos_sem_registro": orfas, "total": len(itens)}


@router.post("/rascunho/{rascunho_id}/recusar")
async def recusar_rascunho(
    rascunho_id: str, body: RecusarRascunhoBody, token: dict = Depends(get_current_user)
):
    """Tira o pré-dado da fila SEM apagá-lo, com motivo e autor.

    Já existia `DELETE /rascunho/{id}`, e apagar não serve aqui: o que chega do
    píer é trabalho de alguém: sumir com ele em silêncio devolve o colaborador
    ao mesmo erro amanhã e deixa o revisor seguinte sem saber se aquilo foi
    analisado ou perdido.

    A recusa mora em `dados` (`recusado_em`, `recusado_por`, `motivo_recusa`) e
    não na coluna `status`, que agora carrega a CONDIÇÃO do serviço vinda do
    barco — gravar "recusado" ali apagaria o "atenção" que o mecânico levantou,
    que é justamente o que não pode se perder.

    O que some é da FILA, não do banco: a aba lista apenas o que ainda não foi
    recusado.
    """
    motivo = (body.motivo or "").strip()
    if len(motivo) < 3:
        raise HTTPException(status_code=400, detail="Diga o motivo da recusa.")

    supabase = get_supabase_admin()
    _so_a_marina(_ativo_do_rascunho(supabase, rascunho_id), token)

    r = supabase.table("registros_rascunho").select("*").eq("id", rascunho_id).execute()
    if not r.data:
        raise HTTPException(status_code=404, detail="Rascunho não encontrado")

    dados = dict(r.data[0].get("dados") or {})
    if dados.get("recusado_em"):
        return {"id": rascunho_id, "ja_estava": True, "motivo": dados.get("motivo_recusa")}

    dados.update({
        "recusado_em": datetime.now(timezone.utc).isoformat(),
        "recusado_por": token.get("sub") if token else None,
        "motivo_recusa": motivo,
    })
    supabase.table("registros_rascunho").update({"dados": dados}).eq("id", rascunho_id).execute()

    return {"id": rascunho_id, "recusado": True, "motivo": motivo}


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


def _aprovar_as_fotos_do_servico(supabase, rasc: dict, aprovador: str | None) -> list[str]:
    """Aprova as fotos que vieram com este pré-dado, no mesmo ato do selo.

    O PROBLEMA QUE ISTO RESOLVE. Selar gravava o serviço e apagava o rascunho —
    e as fotos ficavam `pendente` para sempre. Como era o rascunho que as
    amarrava ao serviço (pelo `client_id` na descrição), some o rascunho, some
    o vínculo: a foto vira "imagem desta embarcação sem registro que a
    explique". O dossiê exclui pendente de propósito, então o serviço ia para o
    documento probatório SEM a prova. Aconteceu no ensaio de 15/09/2026: motor
    selado, três fotos boas, nenhuma no PDF.

    POR QUE APROVAR AQUI É HONESTO, e não um atalho. Quem sela é o escritório,
    não o píer — a regra "quem captura não aprova" continua de pé. E ele não
    aprova no escuro: a mesa de trabalho mostra as fotos ao lado do texto que
    ele está corrigindo. Selar É a revisão; separar os dois atos só garantia
    que o segundo fosse esquecido.

    Best-effort por necessidade, não por escolha: a esta altura o registro já
    foi inserido numa tabela append-only e não há como voltar atrás. Falhar
    aqui devolve o estado de antes — foto pendente, recuperável na aba
    Pré-Data — e deixa o motivo no log.
    """
    client_id = (rasc.get("dados") or {}).get("client_id")
    if not client_id:
        return []

    try:
        pendentes = (
            supabase.table("documentos")
            .select("id, descricao")
            .eq("ativo_id", rasc["ativo_id"]).eq("status", "pendente")
            .execute().data
            or []
        )
    except Exception as e:  # pragma: no cover - degradacao proposital
        logger.error(f"Falha ao ler as fotos do pré-dado {client_id}: {e}")
        return []

    # O client_id vai no fim da descricao: "Atlas Pré-Data · Motor · <client_id>".
    # Comparar o fim, e nao `in`, para um id nao casar com o de outro envio que
    # por acaso o contenha.
    alvos = [
        d["id"] for d in pendentes
        if (d.get("descricao") or "").split("·")[-1].strip() == str(client_id)
    ]
    if not alvos:
        return []

    quando = datetime.now(timezone.utc).isoformat()
    aprovadas = []
    for doc_id in alvos:
        try:
            supabase.table("documentos").update({
                "status": "verified",
                "validado_em": quando,
            }).eq("id", doc_id).execute()
            aprovadas.append(doc_id)
        except Exception as e:  # pragma: no cover - degradacao proposital
            logger.error(f"Falha ao aprovar a foto {doc_id} ao selar: {e}")

    if aprovadas:
        logger.info(
            f"Selo levou {len(aprovadas)} foto(s) do pré-dado {client_id} "
            f"(aprovadas por {aprovador})"
        )
    return aprovadas


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

    # As fotos vao junto. Precisa ser ANTES do delete: e o rascunho que guarda
    # o `client_id` que as amarra a este servico.
    fotos = _aprovar_as_fotos_do_servico(supabase, rasc, token.get("sub") if token else None)

    # só remove o rascunho depois que o selo existe — nunca perde dado
    supabase.table("registros_rascunho").delete().eq("id", rascunho_id).execute()

    return {
        "message": "Registro selado. Não pode mais ser editado nem excluído.",
        "registro": selado.data[0],
        "fotos_aprovadas": len(fotos),
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
