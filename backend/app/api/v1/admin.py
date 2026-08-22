"""
Yachts Atlas — Admin Maintenance Endpoints
"""
from fastapi import APIRouter, Depends
from app.core.security import require_platform_admin
from app.core.config import settings

router = APIRouter()


@router.get("/maintenance/status")
async def maintenance_status(_admin: dict = Depends(require_platform_admin)):
    return {
        "status": "ok",
        "maintenance_bypass_enabled": settings.MAINTENANCE_BYPASS_ENABLED,
        "allowed_origins": settings.cors_origins,
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY and settings.STRIPE_WEBHOOK_SECRET),
        "supabase_configured": bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY),
    }


def _mascara(valor: str | None, ver: int = 4) -> str | None:
    """Mostra o suficiente para reconhecer o valor, nunca o valor inteiro.

    Diagnóstico que imprime segredo em tela vira segredo em print de tela, em
    log de proxy e em histórico de chat. O que se precisa saber aqui é "está
    preenchido e é o que eu acho que é", não o conteúdo.
    """
    if not valor:
        return None
    if len(valor) <= ver * 2:
        return "*" * len(valor)
    return f"{valor[:ver]}{'*' * (len(valor) - ver * 2)}{valor[-ver:]}"


@router.get("/diagnostico-avisos")
async def diagnostico_avisos(_admin: dict = Depends(require_platform_admin)):
    """
    Por que os avisos do fundador não estão saindo — sem precisar adivinhar.

    Existe porque `notificar_fundador` é best-effort por construção: ele não
    levanta exceção quando um canal está mal configurado, apenas pula. Isso é
    proposital (falhar em avisar não pode derrubar um pagamento), mas cria um
    ponto cego — configuração errada em produção é indistinguível de "não havia
    o que avisar". Foi exatamente assim que a queda do WhatsApp passou horas
    despercebida em 22/08/2026.

    NÃO ENVIA NADA. Só lê a configuração, testa a conexão da instância e diz o
    que está faltando. Segredos saem mascarados.
    """
    faltando: list[str] = []

    # --- WhatsApp ---
    provedor = settings.WHATSAPP_PROVIDER
    if not provedor:
        faltando.append("WHATSAPP_PROVIDER")
    if not settings.ALERTA_WHATSAPP:
        faltando.append("ALERTA_WHATSAPP")

    instancia = settings.EVOLUTION_INSTANCE_PROSPECCAO
    if not instancia:
        faltando.append("EVOLUTION_INSTANCE_PROSPECCAO")

    # Estado real da instância por onde o aviso sai. É aqui que aparece o erro
    # de digitação no nome: a Evolution responde 404 e o aviso morre em
    # silêncio, sem nada no log da aplicação.
    conexao: dict = {"consultado": False}
    if provedor == "evolution" and instancia and settings.EVOLUTION_BASE_URL:
        try:
            import httpx
            chave = (settings.EVOLUTION_API_KEY_PROSPECCAO
                     or settings.AUTHENTICATION_API_KEY)
            r = httpx.get(
                f"{settings.EVOLUTION_BASE_URL.rstrip('/')}/instance/connectionState/{instancia}",
                headers={"apikey": chave}, timeout=8,
            )
            conexao = {"consultado": True, "http": r.status_code,
                       "resposta": r.text[:160]}
            if r.status_code == 404:
                faltando.append(
                    f"instancia '{instancia}' nao existe na Evolution "
                    "(conferir hifen vs underscore)"
                )
            elif r.status_code == 401:
                faltando.append("EVOLUTION_API_KEY_PROSPECCAO invalida (401)")
        except Exception as e:
            conexao = {"consultado": True, "erro": f"{type(e).__name__}: {e}"}

    # --- E-mail ---
    # ALERTA_EMAIL vazio NÃO desliga o e-mail: _destino_email cai no
    # EMAIL_SENDER, que tem padrão. Quem desliga de fato é a senha do SMTP.
    destino_email = settings.ALERTA_EMAIL or settings.EMAIL_SENDER or None
    if not settings.EMAIL_PASSWORD:
        faltando.append("EMAIL_PASSWORD (o e-mail e' pulado sem ela)")
    if not destino_email:
        faltando.append("ALERTA_EMAIL/EMAIL_SENDER")

    return {
        "whatsapp": {
            "provedor": provedor or None,
            "base_url": settings.EVOLUTION_BASE_URL or None,
            "instancia_transacional": settings.EVOLUTION_INSTANCE or None,
            "instancia_do_aviso": instancia or None,
            "chave_do_aviso": _mascara(settings.EVOLUTION_API_KEY_PROSPECCAO
                                       or settings.AUTHENTICATION_API_KEY),
            "destino_alerta": _mascara(settings.ALERTA_WHATSAPP, 6),
            "conexao": conexao,
        },
        "email": {
            "remetente": settings.EMAIL_SENDER or None,
            "smtp": f"{settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT}",
            "senha_configurada": bool(settings.EMAIL_PASSWORD),
            "destino_alerta": destino_email,
        },
        "webhook_optout": {
            "token_configurado": bool(settings.WHATSAPP_WEBHOOK_TOKEN),
        },
        "pronto_para_avisar": not faltando,
        "faltando": faltando,
    }
