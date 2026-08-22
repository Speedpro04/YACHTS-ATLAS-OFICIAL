"""
Yachts Atlas — Leads (marinas e parceiros)
"""
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.models import LeadMarinaCreate
from app.core.supabase import get_supabase_admin
from app.core.security import require_platform_admin
from app.core.config import settings, LAUNCH_STATES

logger = logging.getLogger(__name__)

router = APIRouter()


def _so_digitos(valor: Optional[str]) -> str:
    """Deixa so os digitos de um telefone.

    O Evolution API precisa do numero cru (DDI+DDD+numero); "(48) 99999-1234"
    e recusado. Existe uma funcao de mesmo nome em verificacao.py, mas aquela
    e do fluxo de assinatura do QR e nao aceita None — importar de la acoplaria
    dois assuntos sem relacao so para economizar tres linhas.
    """
    if not valor:
        return ""
    return "".join(c for c in valor if c.isdigit())

# Oferta da marina paga: 4 vagas fundadoras POR ESTADO a US$ 200/mes
# (SC/SP/RJ/ES/BA = 20 no total), depois US$ 250.
# Os links ficam em env para trocar de conta Stripe sem rebuild do frontend.
# Quantidade e precos vem do config para nao existirem dois numeros de
# lancamento diferentes no mesmo sistema.
VAGAS_POR_ESTADO = settings.LAUNCH_SLOTS_PER_STATE
MINUTOS_DE_RESERVA = settings.MINUTOS_DE_RESERVA_VAGA

# Origens que vendem a vaga fundadora de US$ 200. Só a campanha de lançamento
# entra aqui — o site oficial trabalha a tabela de US$ 250. Qualquer valor fora
# desta lista (inclusive vazio) cai na oferta oficial: preferir cobrar a mais de
# quem merecia menos, que se conserta devolvendo a diferença, a queimar uma das
# 20 vagas com quem nunca viu a campanha, que não se conserta.
ORIGENS_DE_LANCAMENTO = frozenset({"lancamento", "lançamento", "lp-fundadoras", "lp-lancamento"})
# Vêm do config: o porteiro do acesso (app/core/acesso.py) precisa dos mesmos
# links para mandar a marina bloqueada ao checkout do preço que ela contratou.
LINK_MARINA_FUNDADORA = settings.STRIPE_LINK_MARINA_FUNDADORA
LINK_MARINA_OFICIAL = settings.STRIPE_LINK_MARINA_OFICIAL


def _oferta_oficial() -> dict:
    """Oferta do site oficial: US$ 250/mês, sem vaga fundadora envolvida."""
    return {
        "oferta": "oficial",
        "preco_mensal": settings.TRADITIONAL_PRICE_MONTHLY,
        "uf": None,
        "vagas_restantes": None,
        "motivo": "fora_da_campanha_de_lancamento",
        "checkout_url": LINK_MARINA_OFICIAL,
        "reserva_minutos": None,
        "reserva_expira_em": None,
    }


def _oferta_marina(supabase, data) -> dict:
    """
    Escolhe o checkout da marina paga e JA RESERVA a vaga fundadora.

    Sao 4 vagas por ESTADO (SC/SP/RJ/ES/BA). Marina de qualquer outro estado
    vai direto para a oferta oficial de US$ 250 — antes o estado era coletado
    no formulario e descartado, entao 20 marinas de um mesmo estado podiam
    tomar todas as vagas e zerar os outros quatro.

    A vaga e reservada aqui, e nao so no pagamento: entre preencher o
    formulario e pagar havia uma janela em que todas viam "tem vaga" e recebiam
    o link de US$ 200, dando para ter mais gente paga a preco de fundadora do
    que vaga para honrar. A reserva vence sozinha em MINUTOS_DE_RESERVA.

    Exige service role: marinas_fundadoras tem RLS sem politica publica.
    """
    # O preco de fundadora pertence a CAMPANHA de lancamento, nao ao estado da
    # marina. Quem chega pelo site oficial paga a tabela oficial, mesmo estando
    # em SC/SP/RJ/ES/BA e mesmo havendo vaga livre — senao as 20 vagas somem
    # para quem nunca viu a campanha, e a exclusividade da LP nao vale nada.
    if (getattr(data, "origem", None) or "").strip().lower() not in ORIGENS_DE_LANCAMENTO:
        return _oferta_oficial()

    try:
        res = supabase.rpc("reservar_vaga_fundadora", {
            "p_email": data.email,
            "p_uf": data.state or "",
            "p_marina_nome": data.name,
            "p_responsavel": data.name,
            "p_telefone": data.phone,
            "p_minutos": MINUTOS_DE_RESERVA,
        }).execute()
        reserva = res.data if isinstance(res.data, dict) else {}
    except Exception as e:
        # Sem reserva confirmada, manda para o oficial. Cobrar US$ 250 de quem
        # merecia US$ 200 se conserta devolvendo a diferenca; cobrar US$ 200 de
        # quem nao tem vaga cria uma obrigacao impossivel — nao existe 5a vaga
        # em estado nenhum.
        logger.error(f"Falha ao reservar vaga fundadora para {data.email}: {e}")
        reserva = {}

    fundadora = reserva.get("modo") == "fundadora"

    # Hora em que a vaga volta para a fila, para a tela mostrar o prazo exato
    # ("reservada até 14h32") em vez de um "3 horas" que a marina precisa
    # cronometrar sozinha. Só existe quando há reserva: quem já está ativa não
    # tem prazo correndo contra ela.
    expira_em = None
    if fundadora and reserva.get("status") != "ja_ativa":
        expira_em = (
            datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_DE_RESERVA)
        ).isoformat()

    return {
        "oferta": "fundadora" if fundadora else "oficial",
        "preco_mensal": (settings.LAUNCH_PRICE_MONTHLY if fundadora
                         else settings.TRADITIONAL_PRICE_MONTHLY),
        "uf": reserva.get("uf") or (data.state or "").strip().upper() or None,
        "vagas_restantes": reserva.get("vagas_restantes"),
        "motivo": reserva.get("motivo"),
        "checkout_url": LINK_MARINA_FUNDADORA if fundadora else LINK_MARINA_OFICIAL,
        "reserva_minutos": MINUTOS_DE_RESERVA if expira_em else None,
        "reserva_expira_em": expira_em,
    }


def _criar_acesso_marina_paga(supabase, data, oferta: dict) -> Optional[str]:
    """
    Cria o login da marina paga e devolve o ID dela.

    Antes o fluxo pago retornava direto para o Stripe e a senha do formulario
    era descartada: a marina pagava e ficava sem acesso nenhum. Fica marcada
    como pagamento pendente ate o webhook do Stripe confirmar. Best-effort —
    falhar aqui nao pode impedir a marina de pagar.

    O ID e devolvido porque ele precisa VIAJAR NO LINK de pagamento: e por ele
    que o webhook reconhece quem pagou. Ver `_link_com_identidade`.
    """
    try:
        resposta = supabase.auth.admin.create_user({
            "email": data.email,
            "password": data.password,
            "email_confirm": True,
            "user_metadata": {
                "nome": data.name,
                "telefone": data.phone,
                "marina": data.name,
                "programa": "marina_paga",
                "oferta": oferta.get("oferta"),
                "preco_mensal": oferta.get("preco_mensal"),
                "uf": oferta.get("uf"),
                "pagamento": "pendente",
            },
        })
        usuario = getattr(resposta, "user", None) or resposta
        return str(getattr(usuario, "id", "")) or None
    except Exception as e:
        # Conta ja existe = nova tentativa de checkout; a senha antiga continua
        # valendo e ela so faz login. Mas o ID dela ainda precisa ir no link,
        # senao a segunda tentativa de pagamento fica orfa igual a primeira.
        texto = str(e).lower()
        if "already" in texto or "registered" in texto:
            try:
                from app.core.supabase import buscar_usuario_por_email
                achado = buscar_usuario_por_email(data.email)
                return str(getattr(achado, "id", "")) or None if achado else None
            except Exception:
                return None
        logger.error(f"Falha ao criar acesso da marina paga {data.email}: {e}")
        return None


def _link_com_identidade(base: str, user_id: Optional[str], email: Optional[str]) -> str:
    """
    Amarra QUEM esta pagando ao link de pagamento.

    O bug que isto conserta e o mais caro que este sistema podia ter: a marina
    pagava e continuava sem acesso.

    O Payment Link e uma URL fixa e nao carrega metadata. Sem nada nela, o
    webhook so tinha o e-mail do checkout para descobrir de quem era o
    pagamento — e a carteira Link da Stripe usa o e-mail da CARTEIRA, que
    raramente e o mesmo que a marina digitou no cadastro. Quando os dois nao
    batiam, `user_id` ficava nulo: o pagamento nao era gravado em `payments` e
    o acesso NAO era liberado. Aconteceu no teste com cartao real — a tabela
    ficou vazia.

    `client_reference_id` volta no evento do Stripe e nao depende de qual
    e-mail ela usou para pagar. `prefilled_email` ainda ajuda: reduz a chance
    de divergencia e poupa digitacao no celular.
    """
    if not base:
        return base
    params = {}
    if user_id:
        params["client_reference_id"] = user_id
    if email:
        params["prefilled_email"] = email
    if not params:
        return base
    return f"{base}{'&' if '?' in base else '?'}{urlencode(params)}"


class LeadParceiroCreate(BaseModel):
    categoria: str
    empresa: str
    responsavel: str
    email: EmailStr
    telefone: Optional[str] = None
    cidade: Optional[str] = None
    mensagem: Optional[str] = None


class FounderMarinaRegister(BaseModel):
    """Cadastro de uma marina no Programa das 3 Vagas Fundadoras.
    O período gratuito de 6 meses começa a contar a partir deste cadastro."""
    email: EmailStr
    marina_nome: Optional[str] = None
    contact_name: Optional[str] = None
    fleet_size: Optional[str] = None
    source: Optional[str] = None
    meses_gratis: int = 6


class MarinaRegistroPublico(BaseModel):
    """Cadastro público da marina (página /registro-marina).
    Marinas com e-mail pré-autorizado ganham passe grátis (6 meses); as demais
    seguem para o checkout de USD 250/mês."""
    name: str
    email: EmailStr
    password: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    # De onde veio o cadastro. O preço de fundadora é da CAMPANHA de lançamento,
    # não do estado da marina: sem isto, qualquer um que se cadastrasse pelo site
    # oficial levava US$ 200 e consumia uma das 20 vagas sem nunca ter visto a
    # campanha. Ausente ou desconhecido = site oficial = US$ 250.
    origem: Optional[str] = None
    # Quem indicou esta marina — nome ou e-mail da fundadora, como ela lembrar.
    # A pagina promete que quem indica participa dos dossies da indicada, e esse
    # vinculo SO pode ser capturado aqui: depois ninguem lembra quem indicou
    # quem, nem a fundadora nem a indicada. E o motor que leva de 20 para 40.
    indicada_por: Optional[str] = None


def _registrar_indicacao(supabase, data) -> None:
    """
    Grava quem indicou a marina que acabou de se cadastrar.

    Duas coisas acontecem, e a primeira nunca falha:

    1. o texto cru fica guardado como ela digitou. Marina escreve o que lembra
       — "Marina do Porto", "falei com o Joao la da nautica", e-mail com typo —
       e nada disso pode ser descartado por nao casar com um registro;
    2. se der para casar com uma fundadora (por e-mail ou nome), o vinculo vira
       `indicada_por_slot` e a contagem da indicante sobe.

    O que nao casar, o fundador resolve a mao olhando o texto. Com 20 marinas
    isso e trabalho de minutos; perder o dado nao tem conserto.

    Best-effort por definicao: falhar aqui nao pode impedir a marina de se
    cadastrar e pagar.
    """
    texto = (getattr(data, "indicada_por", None) or "").strip()
    if not texto:
        return

    try:
        minha = (
            supabase.table("marinas_lancamento")
            .select("slot")
            .ilike("email", data.email)
            .limit(1)
            .execute()
        )
        if not minha.data:
            logger.info(
                f"Indicacao de {data.email} sem vaga de lancamento — texto nao gravado: {texto!r}"
            )
            return
        meu_slot = minha.data[0]["slot"]

        # 1) o texto cru, sempre
        supabase.table("marinas_lancamento").update(
            {"indicada_por_texto": texto}
        ).eq("slot", meu_slot).execute()

        # 2) tentativa de casar com uma fundadora
        indicante = (
            supabase.table("marinas_lancamento")
            .select("slot, indicacoes_feitas")
            .ilike("email", texto)
            .neq("slot", meu_slot)
            .limit(1)
            .execute()
        )
        if not indicante.data:
            indicante = (
                supabase.table("marinas_lancamento")
                .select("slot, indicacoes_feitas")
                .ilike("marina_nome", f"%{texto}%")
                .neq("slot", meu_slot)
                .limit(1)
                .execute()
            )
        if not indicante.data:
            logger.info(
                f"Indicacao de {data.email} guardada como texto (sem correspondencia): {texto!r}"
            )
            return

        slot_indicante = indicante.data[0]["slot"]
        feitas = (indicante.data[0].get("indicacoes_feitas") or 0) + 1

        supabase.table("marinas_lancamento").update(
            {"indicada_por_slot": slot_indicante}
        ).eq("slot", meu_slot).execute()
        supabase.table("marinas_lancamento").update(
            {"indicacoes_feitas": feitas}
        ).eq("slot", slot_indicante).execute()

        logger.info(
            f"Indicacao registrada: vaga {meu_slot} indicada pela vaga "
            f"{slot_indicante} (total dela: {feitas})"
        )
    except Exception as e:
        # O cadastro e o pagamento valem mais que o registro da indicacao.
        logger.error(f"Falha ao registrar indicacao de {data.email}: {e}")


@router.get("/marina/vagas")
async def vagas_fundadoras():
    """Vagas fundadoras restantes, por estado e no total.

    Serve a página de LANÇAMENTO. A página oficial anuncia só a mensalidade
    de US$ 250 e não consome isto.

    Conta como ocupada tanto a vaga paga quanto a reservada dentro do prazo —
    é o mesmo número que decide o preço no cadastro, para a página nunca
    prometer uma vaga que o checkout vai negar.
    """
    try:
        resumo = get_supabase_admin().rpc("vagas_fundadoras_resumo", {}).execute()
        dados = resumo.data if isinstance(resumo.data, dict) else {}
        return {"estados": list(LAUNCH_STATES), **dados}
    except Exception as e:
        logger.error(f"Falha ao ler vagas fundadoras: {e}")
        raise HTTPException(status_code=500, detail="Falha ao ler vagas fundadoras")


@router.post("/marina")
async def create_marina_lead(data: LeadMarinaCreate):
    """Save marina partner lead to database"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("marina_leads").insert({
            "marina_name": data.marina,
            "contact_name": data.name,
            "email": data.email,
            "fleet_size": data.fleet,
            # So digitos: o Evolution API nao aceita "(48) 99999-1234". Normalizar
            # aqui e a unica garantia — se ficar so no front, qualquer POST direto
            # grava lixo e a abordagem falha calada na hora do disparo.
            "whatsapp": _so_digitos(data.whatsapp) or None,
            "source": data.source,
            "status": "pending",
        }).execute()
        return {
            "message": "Solicitação recebida com sucesso",
            "id": result.data[0]["id"] if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/parceiro")
async def create_partner_lead(data: LeadParceiroCreate):
    """Salva solicitação de parceiro (diretório Parceiros Atlas)."""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("partner_leads").insert({
            "categoria": data.categoria,
            "empresa": data.empresa,
            "responsavel": data.responsavel,
            "email": data.email,
            "telefone": data.telefone,
            "cidade": data.cidade,
            "mensagem": data.mensagem,
            "status": "pending",
        }).execute()
        return {
            "message": "Solicitação recebida com sucesso",
            "id": result.data[0]["id"] if result.data else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/marina")
async def list_marina_leads(_admin: dict = Depends(require_platform_admin)):
    """List all marina leads (admin use)"""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("marina_leads").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marina/founder")
async def register_founder_marina(
    data: FounderMarinaRegister,
    _admin: dict = Depends(require_platform_admin),
):
    """Ocupa uma das 3 vagas fundadoras e inicia a contagem de 6 meses grátis
    a partir de agora (signed_up_at = now; billing_starts_at = +6 meses).

    Seleção manual (admin). Idempotente por e-mail. Quando as 3 vagas esgotam,
    retorna {status: 'sem_vagas'} sem ocupar nada.
    """
    try:
        supabase = get_supabase_admin()
        resp = supabase.rpc("cadastrar_marina_piloto", {
            "p_email": data.email,
            "p_marina_nome": data.marina_nome,
            "p_contact_name": data.contact_name,
            "p_fleet_size": data.fleet_size,
            "p_source": data.source,
            "p_meses_gratis": data.meses_gratis,
        }).execute()
        return resp.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marina/reservar")
async def reservar_vaga_founder(
    data: FounderMarinaRegister,
    _admin: dict = Depends(require_platform_admin),
):
    """Pré-autoriza (reserva) o e-mail de uma marina para uma das 3 vagas grátis.
    NÃO inicia os 6 meses — isso só acontece quando a marina se cadastra.
    Use ao oferecer a vaga por telefone. Idempotente. Esgotou as 3 -> 'sem_vagas'."""
    try:
        supabase = get_supabase_admin()
        resp = supabase.rpc("reservar_vaga_piloto", {
            "p_email": data.email,
            "p_marina_nome": data.marina_nome,
        }).execute()
        return resp.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/marina/registrar")
async def registrar_marina_publica(data: MarinaRegistroPublico):
    """Cadastro público da marina. Se o e-mail estiver pré-autorizado numa das 3
    vagas, cria o acesso GRÁTIS (a marina define a própria senha), dispara a
    contagem dos 6 meses e NÃO vai para o checkout. Caso contrário, sinaliza o
    fluxo pago (USD 250/mês)."""
    supabase = get_supabase_admin()

    # 1) O e-mail é uma das vagas grátis pré-autorizadas?
    try:
        ativa = supabase.rpc("ativar_vaga_piloto", {
            "p_email": data.email,
            "p_marina_nome": data.name,
        }).execute()
        result = ativa.data if isinstance(ativa.data, dict) else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao verificar vaga: {e}")

    status = result.get("status")

    # 2) Não pré-autorizada -> fluxo pago (sem criar conta aqui).
    #    O checkout vem do backend: fundadora (US$ 200) enquanto houver vaga,
    #    oficial (US$ 250) depois. O link fixo no frontend cobrava US$ 250 de
    #    todo mundo e ainda apontava para a conta Stripe antiga (CPF).
    if status == "nao_autorizado":
        oferta = _oferta_marina(supabase, data)
        user_id = _criar_acesso_marina_paga(supabase, data, oferta)
        # Sem a identidade no link, o webhook nao reconhece quem pagou e o
        # acesso nao e liberado. Ver `_link_com_identidade`.
        oferta["checkout_url"] = _link_com_identidade(
            oferta.get("checkout_url"), user_id, data.email
        )
        _registrar_indicacao(supabase, data)
        return {"modo": "pago", **oferta}

    # 3) Vaga grátis: cria/garante o login com a senha escolhida pela marina
    try:
        supabase.auth.admin.create_user({
            "email": data.email,
            "password": data.password,
            "email_confirm": True,
            "user_metadata": {
                "nome": data.name,
                "telefone": data.phone,
                "marina": data.name,
                "programa": "fundador_brinde",
            },
        })
    except Exception as e:
        # Conta já existe (re-cadastro) é tolerável: a marina apenas faz login.
        if "already" not in str(e).lower() and "registered" not in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Falha ao criar acesso: {e}")

    # 4) Guarda os dados extras na vaga (telefone, cidade/UF, site) — best-effort
    try:
        notes = "; ".join(filter(None, [
            f"CNPJ: {data.cnpj}" if data.cnpj else None,
            f"Cidade: {data.city}/{data.state}" if (data.city or data.state) else None,
            f"Site: {data.website}" if data.website else None,
        ]))
        supabase.table("founder_program_spots").update({
            "telefone": data.phone,
            "source": "registro-marina (passe fundador)",
            "pilot_case_notes": notes or None,
        }).eq("email", data.email).execute()
    except Exception:
        pass

    # 5) Avisa o fundador (best-effort)
    try:
        from app.services.notify_service import notificar_fundador
        notificar_fundador(
            "Vaga Fundadora ativada",
            f"{data.name} ({data.email}) acabou de se cadastrar no passe grátis.\n"
            f"6 meses começam agora — cobrança em {str(result.get('billing_starts_at'))[:10]}.",
        )
    except Exception:
        pass

    return {
        "modo": "gratis",
        "marina": data.name,
        "billing_starts_at": result.get("billing_starts_at"),
        "slot_number": result.get("slot_number"),
    }


@router.get("/marina/spots")
async def get_marina_founder_spots():
    """Return founder spot availability for the public marina partnership page."""
    try:
        supabase = get_supabase_admin()
        result = supabase.table("founder_program_spots").select(
            "slot_number,status,marina_name,contact_name,email,billing_status,access_status,updated_at"
        ).order("slot_number").execute()

        spots = result.data or []
        total_spots = 3
        occupied_statuses = {"reserved", "occupied"}
        taken_spots = sum(1 for spot in spots if spot.get("status") in occupied_statuses)
        available_spots = max(total_spots - taken_spots, 0)

        return {
            "total_spots": total_spots,
            "taken_spots": taken_spots,
            "available_spots": available_spots,
            "spots": spots,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
