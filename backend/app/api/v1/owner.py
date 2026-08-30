"""
Yachts Atlas — Owner Access (cadastro da palavra secreta do proprietário)
A Edge Function `verify-owner-secret` VERIFICA; este endpoint DEFINE.
Hash bcrypt (passlib) — compatível com o bcrypt.compare da Edge Function.
"""
import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from app.core.supabase import get_supabase_admin
from app.core.security import hash_password, require_platform_admin

logger = logging.getLogger(__name__)
router = APIRouter()


class OwnerSecretSet(BaseModel):
    user_id: str
    secret_word: str = Field(min_length=3)


class PedidoDeCodigo(BaseModel):
    email: EmailStr


@router.post("/codigo")
async def enviar_codigo_de_acesso(data: PedidoDeCodigo):
    """
    Manda ao armador o código de acesso ao portal, por e-mail e WhatsApp.

    O armador não cria senha e não tem nada para esquecer: digita o e-mail,
    recebe um código de uso único e entra. O segredo é a caixa dele — coisa
    que só ele tem. Diferente de CPF ou nome da embarcação, que estão no
    próprio dossiê e circulam com ele para comprador, corretor e seguradora.

    Quem diz de quem é o barco é a MARINA, ao gravar `proprietario_email` no
    cadastro. Aqui só se confere se algum barco aponta para este e-mail.

    Responde 200 sempre, mesmo para e-mail desconhecido: dizer "não existe"
    entregaria de graça quem é dono de barco na plataforma.
    """
    email = data.email.strip().lower()
    supabase = get_supabase_admin()

    try:
        achados = (
            supabase.table("ativos")
            .select("id, proprietario_telefone")
            .eq("proprietario_email", email)
            .is_("arquivado_em", "null")
            .limit(1)
            .execute()
        )
    except Exception as e:
        logger.error(f"Falha ao procurar barcos de {email}: {e}")
        return {"enviado": True}

    if not achados.data:
        logger.info(f"Pedido de código para {email}: nenhum barco vinculado")
        return {"enviado": True}

    telefone = (achados.data[0].get("proprietario_telefone") or "").strip()

    # A conta nasce na primeira entrada, sem senha: quem autentica é o código.
    try:
        supabase.auth.admin.create_user({
            "email": email,
            "email_confirm": True,
            "user_metadata": {"perfil": "armador"},
        })
    except Exception as e:
        if "already" not in str(e).lower() and "registered" not in str(e).lower():
            logger.error(f"Falha ao criar acesso do armador {email}: {e}")

    # O código é gerado pelo próprio Supabase — a validação continua sendo
    # dele. A gente só escolhe o carteiro, e manda pelos dois caminhos.
    try:
        link = supabase.auth.admin.generate_link({"type": "magiclink", "email": email})
        props = getattr(link, "properties", None) or {}
        codigo = getattr(props, "email_otp", None) or (
            props.get("email_otp") if isinstance(props, dict) else None
        )
    except Exception as e:
        logger.error(f"Falha ao gerar código para {email}: {e}")
        return {"enviado": True}

    if not codigo:
        logger.error(f"Supabase não devolveu código para {email}")
        return {"enviado": True}

    texto = (
        f"Seu código de acesso à Yachts Atlas é {codigo}.\n\n"
        "Ele vale por poucos minutos e serve uma vez só. "
        "Se não foi você quem pediu, ignore esta mensagem."
    )

    try:
        from app.services.email_service import send_email
        send_email(
            email,
            "Seu código de acesso à Yachts Atlas",
            f"<p>Seu código de acesso é <strong style='font-size:22px;letter-spacing:3px'>{codigo}</strong></p>"
            "<p>Ele vale por poucos minutos e serve uma vez só.</p>"
            "<p style='color:#888;font-size:13px'>Se não foi você quem pediu, ignore esta mensagem.</p>",
            texto,
        )
    except Exception as e:
        logger.error(f"Falha ao enviar código por e-mail para {email}: {e}")

    if telefone:
        try:
            from app.services.whatsapp_service import enviar_whatsapp
            enviar_whatsapp(telefone, texto)
        except Exception as e:
            logger.error(f"Falha ao enviar código por WhatsApp para {email}: {e}")

    return {"enviado": True}


@router.post("/secret")
async def definir_palavra_secreta(data: OwnerSecretSet, _admin: dict = Depends(require_platform_admin)):
    """Define/atualiza a palavra secreta (hash) de um proprietário."""
    try:
        supabase = get_supabase_admin()
        supabase.table("owner_access").upsert({
            "user_id": data.user_id,
            "secret_word_hash": hash_password(data.secret_word),
            "updated_at": "now()",
        }).execute()
        return {"message": "Palavra secreta definida"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
