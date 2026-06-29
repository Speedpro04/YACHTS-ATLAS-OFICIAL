"""
Yachts Atlas — Leads (marinas e parceiros)
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.schemas.models import LeadMarinaCreate
from app.core.supabase import get_supabase_admin
from app.core.security import require_platform_admin

router = APIRouter()


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

    # 2) Não pré-autorizada -> fluxo pago (sem criar conta aqui)
    if status == "nao_autorizado":
        return {"modo": "pago"}

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
        from app.services.notify_service import send_telegram
        send_telegram(
            "<b>Vaga Fundadora ativada 🎁</b>\n"
            f"{data.name} ({data.email}) acabou de se cadastrar no passe grátis.\n"
            f"6 meses começam agora — cobrança em {str(result.get('billing_starts_at'))[:10]}."
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
