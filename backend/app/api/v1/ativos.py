"""
Yachts Atlas — Ativos Endpoints
Alinhado ao schema REAL do banco (legado): ativos.usuario_id + ativos.comprimento.
Usa a chave de serviço (o backend já autentica o usuário via get_current_user_id).
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.models import AtivoCreate
from app.core.pii import mascarar_documento
from app.core.supabase import get_supabase_admin
from app.core.security import get_current_user_id
from app.core.campo import usuario_ou_campo
from app.core.authz import email_do_usuario
from datetime import datetime, timezone
import uuid
import logging

router = APIRouter()


logger = logging.getLogger(__name__)
def _id_usuario_ou_campo(token: dict = Depends(usuario_ou_campo)) -> str:
    """Id da conta, aceitando o aparelho do pátio.

    A lista da frota é a única leitura que o app de campo faz: sem ela, o
    colaborador não tem como escolher o barco. Devolve o id da MARINA, então o
    filtro por dono logo abaixo continua o mesmo — ele vê a frota dela, e nada
    além do que ela já vê.
    """
    return token.get("sub")


def _e_do_patio(token: dict = Depends(usuario_ou_campo)) -> bool:
    """Se esta requisição veio do aparelho do pátio.

    ISTO EXISTE PORQUE O CÓDIGO DE CAMPO HERDAVA ADMIN. O token de campo
    devolve o id da MARINA dona dele — e se essa conta tem perfil `admin`, o
    filtro por dono era pulado e a lista voltava com a frota da plataforma
    inteira. Apareceu em 15/09/2026: o aparelho do pátio abriu mostrando dez
    embarcações de quatro Marinas diferentes.

    Hoje só a conta do fundador é admin, então nenhuma Marina viu a frota de
    outra. Mas o desenho estava errado: o código de campo é o acesso mais fraco
    do sistema — um papel que pode ser colado num painel do pátio — e acesso
    fraco não pode herdar privilégio de administrador por causa de quem é o
    dono da conta.
    """
    return (token or {}).get("escopo") == "campo"


def _role(supabase, user_id: str) -> str | None:
    if user_id == "maintenance-admin":
        return "admin"
    prof = supabase.table("profiles").select("user_role").eq("id", user_id).execute()
    return prof.data[0].get("user_role") if prof.data else None


def _enrich(ativo: dict) -> dict:
    """Compat com o frontend: expõe comprimento_pes a partir de comprimento."""
    if ativo is not None and "comprimento_pes" not in ativo:
        ativo["comprimento_pes"] = ativo.get("comprimento")
    return ativo


def _anexar_total_fotos(supabase, ativos: list[dict]) -> None:
    """Conta as fotos (tipo='foto') de cada ativo em UMA única consulta (sem N+1)
    e injeta `total_fotos` em cada item. Falha de forma silenciosa => 0."""
    ids = [a["id"] for a in ativos if a.get("id")]
    contagem: dict[str, int] = {}
    if ids:
        try:
            # Exclui a vitrine (fotos de apresentação, separadas do pool de 460)
            res = (
                supabase.table("documentos")
                .select("ativo_id")
                .in_("ativo_id", ids)
                .eq("tipo", "foto")
                .neq("categoria", "vitrine")
                .execute()
            )
            for row in (res.data or []):
                aid = row.get("ativo_id")
                if aid:
                    contagem[aid] = contagem.get(aid, 0) + 1
        except Exception:
            pass
    for a in ativos:
        a["total_fotos"] = contagem.get(a.get("id"), 0)


def _anexar_saude(supabase, ativos: list[dict]) -> None:
    """Injeta `health_status` — o estado de cada sistema — em UMA consulta.

    ESTE CAMPO NUNCA EXISTIU. O painel lê `ativo.health_status` desde sempre
    (AtivoHub.tsx) e nenhum caminho do backend o produzia: não é coluna de
    `ativos` nem era calculado em lugar nenhum. O resultado é que o cabeçalho
    de TODA embarcação dizia "nenhum dos 10 sistemas avaliado", inclusive as
    que tinham registro selado — enquanto o dossiê da mesma embarcação
    imprimia "Motor: conforme, conformidade 100%".

    Painel e dossiê discordando sobre o mesmo barco, e a errada era a tela que
    a Marina abre todo dia.

    A regra vem de `dossie_data.saude_por_chave`, a MESMA que o PDF usa. Não há
    segunda fórmula aqui — foi ter duas que criou o problema.
    """
    ids = [a["id"] for a in ativos if a.get("id")]
    if not ids:
        return
    try:
        from app.services.dossie_data import saude_por_chave

        # A view resolve a cadeia de retificação: registro corrigido sai da
        # conta, e quem vale é a correção. Sem isso um problema já resolvido
        # puxaria a categoria para baixo para sempre.
        linhas = (
            supabase.table("vw_registros_situacao")
            .select("ativo_id, categoria, status, situacao, dados")
            .in_("ativo_id", ids).execute().data
            or []
        )
    except Exception as e:  # pragma: no cover - degradacao proposital
        # Sem os registros, o painel volta a dizer "não avaliado" — que é o
        # comportamento de antes, e não uma informação inventada.
        logger.warning(f"Falha ao calcular a saúde dos ativos: {e}")
        return

    por_ativo: dict[str, list[dict]] = {}
    for linha in linhas:
        por_ativo.setdefault(linha.get("ativo_id"), []).append(linha)

    for a in ativos:
        a["health_status"] = saude_por_chave(
            por_ativo.get(a.get("id"), []), a.get("tipo")
        )


@router.get("")
async def list_ativos(
    incluir_arquivados: bool = False,
    user_id: str = Depends(_id_usuario_ou_campo),
    do_patio: bool = Depends(_e_do_patio),
):
    """Lista os ativos em operação.

    Arquivado sai da lista por padrão — mas continua no banco com todo o
    histórico selado, e volta com `?incluir_arquivados=true`. Arquivar é o
    substituto da exclusão: registro selado não pode ser apagado.
    """
    supabase = get_supabase_admin()
    # O aparelho do pátio nunca é admin, mesmo quando a conta dele é.
    role = None if do_patio else _role(supabase, user_id)
    q = supabase.table("ativos").select("*")
    if role != "admin":
        # Dois caminhos para o mesmo barco, e nunca pela mesma porta:
        #   • a MARINA é `usuario_id` — opera, edita e sela;
        #   • o ARMADOR é `proprietario_email` — só lê.
        #
        # Sem o segundo, dar acesso ao dono exigiria emprestar a conta da
        # marina — e aí ele enxergaria a frota inteira, de todos os clientes
        # dela. A leitura-apenas do armador é garantida nos outros endpoints,
        # que continuam exigindo `usuario_id` (ver core/authz.py).
        email = email_do_usuario(user_id)
        if email:
            q = q.or_(f"usuario_id.eq.{user_id},proprietario_email.eq.{email}")
        else:
            q = q.eq("usuario_id", user_id)
    if not incluir_arquivados:
        q = q.is_("arquivado_em", "null")
    response = q.order("created_at", desc=True).execute()
    ativos = [_enrich(a) for a in (response.data or [])]
    _anexar_total_fotos(supabase, ativos)
    _anexar_saude(supabase, ativos)
    return ativos


@router.post("")
async def create_ativo(ativo: AtivoCreate, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()

    tipo = ativo.tipo.value if hasattr(ativo.tipo, "value") else ativo.tipo
    ativo_id = f"YA-{str(tipo).upper()}-{ativo.ano_fabricacao}-{str(uuid.uuid4())[:4].upper()}"

    # Dono do ativo = usuário logado (ou owner_id explícito, se enviado).
    owner = str(ativo.owner_id) if getattr(ativo, "owner_id", None) else user_id
    if owner == "maintenance-admin":
        owner = None

    data = {
        "id": ativo_id,
        "usuario_id": owner,
        "tipo": tipo,
        "marca": ativo.marca,
        "modelo": ativo.modelo,
        "ano_fabricacao": ativo.ano_fabricacao,
        "classificacao": "bronze",
        "progresso": 0,
        "status": "ativo",
    }

    # Nome da embarcação. Opcional: barco sem nome registrado cai no
    # `marca + modelo` das telas, que é o comportamento que sempre existiu.
    nome = (getattr(ativo, "nome_reg", None) or "").strip()
    if nome:
        data["nome_reg"] = nome

    # Coluna real é 'comprimento'. Aceita comprimento_pes (front) ou metros.
    comp = getattr(ativo, "comprimento_pes", None) or getattr(ativo, "comprimento_metres", None)
    if comp:
        data["comprimento"] = comp

    # Especificações e motorização. A lista anterior tinha só três campos e o
    # schema não declarava nenhum deles — o getattr lia None e nada era
    # gravado. Agora são os dez que a tabela realmente tem.
    for attr in (
        "largura", "calado", "capacidade_passageiros", "num_cabines",
        "capacidade_tanque", "modelo_motor", "potencia_motor",
        "num_motores", "tipo_combustivel",
    ):
        v = getattr(ativo, attr, None)
        if v not in (None, "", 0):
            data[attr] = v
    mat = getattr(ativo, "material_casco", None)
    if mat:
        data["material_casco"] = mat.value if hasattr(mat, "value") else mat

    # E-mail do dono, em minúsculas: é a chave de acesso dele ao Portal do
    # Proprietário, e ninguém digita e-mail com a mesma caixa duas vezes.
    # Guardar como veio faria o armador não achar o próprio barco por causa
    # de uma maiúscula.
    dono = (getattr(ativo, "proprietario_email", None) or "").strip().lower()
    if dono:
        data["proprietario_email"] = dono
    zap = (getattr(ativo, "proprietario_telefone", None) or "").strip()
    if zap:
        data["proprietario_telefone"] = zap

    # Identidade do titular. Vai impressa no dossiê — o documento precisa dizer
    # de quem é o barco, e até agora só dizia quem custodia.
    nome_titular = (getattr(ativo, "proprietario_nome", None) or "").strip()
    if nome_titular:
        data["proprietario_nome"] = nome_titular
    # Mascarado ANTES de gravar -- ver core/pii.py e o comentario em
    # `vincular_proprietario`. O completo nao entra no banco em caminho nenhum.
    doc_titular = mascarar_documento(getattr(ativo, "proprietario_documento", None))
    if doc_titular:
        data["proprietario_documento"] = doc_titular

    try:
        response = supabase.table("ativos").insert(data).execute()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao cadastrar embarcação: {e}")

    if response.data:
        return _enrich(response.data[0])
    raise HTTPException(status_code=400, detail="Falha ao cadastrar embarcação")


@router.get("/{ativo_id}")
async def get_ativo(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()
    response = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    role = _role(supabase, user_id)
    if role != "admin" and str(ativo.get("usuario_id")) != str(user_id):
        # Armador do próprio barco também abre a ficha — só não mexe nela.
        dono = (ativo.get("proprietario_email") or "").strip().lower()
        if not dono or dono != email_do_usuario(user_id):
            raise HTTPException(status_code=403, detail="Not authorized for this asset")
    ativo = _enrich(ativo)
    _anexar_total_fotos(supabase, [ativo])
    return ativo


@router.delete("/{ativo_id}")
async def arquivar_ativo(
    ativo_id: str,
    motivo: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    """Arquiva o ativo. NÃO exclui.

    Um ativo com registros selados não pode ser apagado: a cadeia de custódia
    é o produto. Arquivar tira o ativo da operação e preserva o histórico.
    """
    supabase = get_supabase_admin()
    response = supabase.table("ativos").select("id, usuario_id, arquivado_em").eq("id", ativo_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    role = _role(supabase, user_id)
    if role != "admin" and str(ativo.get("usuario_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to archive this asset")
    if ativo.get("arquivado_em"):
        raise HTTPException(status_code=409, detail="Ativo já está arquivado")

    # arquivado_por é uuid; o acesso de manutenção usa o literal "maintenance-admin"
    try:
        arquivado_por = str(uuid.UUID(str(user_id)))
    except (ValueError, AttributeError, TypeError):
        arquivado_por = None
        motivo = f"[{user_id}] {motivo or 'arquivado via acesso de manutenção'}"

    supabase.table("ativos").update({
        "arquivado_em": datetime.now(timezone.utc).isoformat(),
        "arquivado_por": arquivado_por,
        "arquivado_motivo": motivo,
    }).eq("id", ativo_id).execute()

    return {
        "message": "Ativo arquivado",
        "ativo_id": ativo_id,
        "historico_preservado": True,
    }


class ProprietarioDoAtivo(BaseModel):
    """Dados do dono. E-mail vazio desfaz o vínculo — barco vendido."""
    proprietario_email: Optional[EmailStr] = None
    proprietario_telefone: Optional[str] = None
    # Identidade, não acesso. Nome e documento vão IMPRESSOS no dossiê; o
    # e-mail e o telefone continuam servindo só de porta para o Portal e não
    # entram no documento, que circula entre corretor, comprador e seguradora.
    proprietario_nome: Optional[str] = None
    proprietario_documento: Optional[str] = None


@router.patch("/{ativo_id}/proprietario")
async def definir_proprietario(
    ativo_id: str,
    data: ProprietarioDoAtivo,
    user_id: str = Depends(get_current_user_id),
):
    """
    Define quem é o dono da embarcação, pelo e-mail.

    É o que dá ao armador acesso ao Portal do Proprietário: ele entra
    digitando este e-mail, recebe um código de uso único e enxerga só os
    barcos marcados com ele. A marina não escolhe senha nenhuma para o dono —
    apenas afirma de quem é o barco, que é a única coisa que só ela sabe.

    Endpoint próprio, e não um update genérico de ativo, porque isto muda
    QUEM VÊ o histórico. Merece uma porta identificável no log de auditoria.

    Barco vendido: a marina troca o e-mail. O dono antigo perde o acesso na
    hora e o histórico não se mexe — registro selado não se apaga.
    """
    supabase = get_supabase_admin()
    achado = supabase.table("ativos").select("id, usuario_id").eq("id", ativo_id).execute()
    if not achado.data:
        raise HTTPException(status_code=404, detail="Ativo not found")

    role = _role(supabase, user_id)
    if role != "admin" and str(achado.data[0].get("usuario_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized for this asset")

    email = (data.proprietario_email or "").strip().lower() or None
    telefone = (data.proprietario_telefone or "").strip() or None
    # Sem e-mail não há dono: o telefone sozinho não abre porta nenhuma, e
    # deixá-lo para trás guardaria o contato de quem já vendeu o barco.
    nome = (data.proprietario_nome or "").strip() or None
    # O documento e MASCARADO ANTES de gravar: o completo nunca entra no
    # banco. Ele so servia para identificar o titular no dossie, que ja o
    # imprimia mascarado -- guardar os digitos do meio era risco de vazamento
    # sem contrapartida de uso. Minimizacao, LGPD art. 6, III. Ver core/pii.py.
    documento = mascarar_documento(data.proprietario_documento)
    supabase.table("ativos").update({
        "proprietario_email": email,
        "proprietario_telefone": telefone if email else None,
        # Nome e documento seguem a mesma regra do telefone: sem dono, some
        # tudo. Barco vendido não guarda a identidade de quem vendeu.
        "proprietario_nome": nome if email else None,
        "proprietario_documento": documento if email else None,
    }).eq("id", ativo_id).execute()

    return {
        "ativo_id": ativo_id,
        "proprietario_email": email,
        "proprietario_telefone": telefone if email else None,
        "proprietario_nome": nome if email else None,
        "proprietario_documento": documento if email else None,
        "message": "Proprietário definido" if email else "Vínculo do proprietário removido",
    }


@router.get("/{ativo_id}/progresso")
async def get_progresso(ativo_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_admin()
    response = supabase.table("ativos").select("progresso, classificacao, usuario_id").eq("id", ativo_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = response.data[0]
    role = _role(supabase, user_id)
    if role != "admin" and str(ativo.get("usuario_id")) != str(user_id):
        raise HTTPException(status_code=403, detail="Not authorized to access this asset progress")
    try:
        from app.services.asset_score_service import calcular_saude_ativo
        return calcular_saude_ativo(ativo_id)
    except Exception:
        return {"progresso": ativo["progresso"], "classificacao": ativo["classificacao"]}
