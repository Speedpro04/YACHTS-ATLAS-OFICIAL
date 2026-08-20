"""
Yachts Atlas — Autorização de acesso a ativos.
Tolerante aos dois schemas: legado (ativos.usuario_id) e novo
(ativos.owner_id / marina_id + profiles.marina_id / user_role).
"""
from fastapi import HTTPException
from app.core.supabase import get_supabase_admin


def email_do_usuario(user_id: str) -> str | None:
    """E-mail da conta logada, em minúsculas. None se não der para descobrir."""
    if not user_id or user_id == "maintenance-admin":
        return None
    try:
        admin = get_supabase_admin().auth.admin
        resposta = admin.get_user_by_id(user_id)
        usuario = getattr(resposta, "user", None) or resposta
        return (getattr(usuario, "email", "") or "").strip().lower() or None
    except Exception:
        return None


def get_ativo_autorizado(ativo_id: str, user_id: str, incluir_proprietario: bool = False) -> dict:
    """
    Retorna o ativo se o usuário tiver acesso; senão levanta 403/404.

    `incluir_proprietario` libera também o ARMADOR — o dono do barco, que
    entra pelo Portal do Proprietário e é reconhecido pelo e-mail gravado no
    ativo. Ele LÊ o histórico; não cadastra, não edita, não sela.

    O padrão é False de propósito: quem escreve (upload de foto, troca de
    categoria) não passa esta flag, e um endpoint novo nasce restrito até
    alguém decidir o contrário. É mais seguro esquecer de liberar do que
    esquecer de proibir.
    """
    if user_id == "maintenance-admin":
        supabase = get_supabase_admin()
        res = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Ativo not found")
        return res.data[0]

    supabase = get_supabase_admin()
    res = supabase.table("ativos").select("*").eq("id", ativo_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = res.data[0]

    if str(ativo.get("usuario_id") or "") == str(user_id):
        return ativo
    if str(ativo.get("owner_id") or "") == str(user_id):
        return ativo

    prof = supabase.table("profiles").select("*").eq("id", user_id).execute()
    profile = prof.data[0] if prof.data else {}
    if profile.get("user_role") == "admin":
        return ativo
    ativo_marina = ativo.get("marina_id")
    if ativo_marina and str(profile.get("marina_id") or "") == str(ativo_marina):
        return ativo

    # Armador: reconhecido pelo e-mail gravado no barco pela marina. Só chega
    # aqui em endpoint de leitura — ver `incluir_proprietario` no docstring.
    if incluir_proprietario:
        dono = (ativo.get("proprietario_email") or "").strip().lower()
        if dono and dono == email_do_usuario(user_id):
            return ativo

    raise HTTPException(status_code=403, detail="Not authorized for this asset")
