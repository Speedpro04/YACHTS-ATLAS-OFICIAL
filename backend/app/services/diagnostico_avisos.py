"""
Yachts Atlas — Por que o aviso ao fundador não saiu.

`notificar_fundador` é best-effort de propósito: canal mal configurado é
pulado, não levantado. Falhar em avisar não pode derrubar o pagamento que
gerou o aviso. O preço disso é um ponto cego — em produção, "variável sumiu no
deploy" fica **idêntico** a "não havia nada para avisar".

Custou um dia inteiro em 23/08/2026: indicações entrando, e-mail chegando,
WhatsApp mudo, e nenhuma linha no log dizendo por quê. A resposta estava a uma
consulta de distância o tempo todo; o que faltava era alguém perguntar.

Este módulo é essa pergunta, num lugar só. Quem chama:

  * `GET /api/v1/admin/diagnostico-avisos` — sob demanda, com token de admin.
  * o boot da aplicação — sozinho, a cada deploy, direto no log do EasyPanel.

O segundo é o que importa: variável perdida num deploy aparece no MESMO log
que já se olha depois de subir, sem precisar suspeitar de nada antes.

NÃO ENVIA MENSAGEM NENHUMA. Lê configuração e pergunta o estado da conexão.
Segredo sai mascarado — diagnóstico que imprime chave vira chave em print de
tela, em log de proxy e em histórico de conversa.
"""
from __future__ import annotations

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# Curto de propósito: isto roda no boot. Evolution fora do ar não pode segurar
# a aplicação subindo — o diagnóstico é informação, não dependência.
_TIMEOUT = httpx.Timeout(5.0, connect=3.0)


def mascara(valor: str | None, ver: int = 4) -> str | None:
    """Mostra o suficiente para reconhecer o valor, nunca o valor inteiro."""
    if not valor:
        return None
    if len(valor) <= ver * 2:
        return "*" * len(valor)
    return f"{valor[:ver]}{'*' * (len(valor) - ver * 2)}{valor[-ver:]}"


def estado_dos_avisos(*, consultar_rede: bool = True) -> dict:
    """Devolve o estado dos dois canais e a lista do que está faltando."""
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
    # de digitação no nome: a Evolution responde 404, o aviso morre em silêncio
    # e nada disso chega ao log da aplicação.
    conexao: dict = {"consultado": False}
    if consultar_rede and provedor == "evolution" and instancia and settings.EVOLUTION_BASE_URL:
        try:
            chave = (settings.EVOLUTION_API_KEY_PROSPECCAO
                     or settings.AUTHENTICATION_API_KEY)
            r = httpx.get(
                f"{settings.EVOLUTION_BASE_URL.rstrip('/')}/instance/connectionState/{instancia}",
                headers={"apikey": chave}, timeout=_TIMEOUT,
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
            elif r.status_code == 200 and '"state":"open"' not in r.text:
                # Instância existe mas não está pareada com o WhatsApp. A API
                # aceita o POST de envio e nada é entregue: o pior dos modos de
                # falhar, porque parece sucesso dos dois lados.
                faltando.append(f"instancia '{instancia}' desconectada do WhatsApp")
        except Exception as e:
            conexao = {"consultado": True, "erro": f"{type(e).__name__}: {e}"}

    # --- E-mail ---
    # ALERTA_EMAIL vazio NÃO desliga o e-mail: o destino cai no EMAIL_SENDER,
    # que tem padrão. Quem desliga de fato é a senha do SMTP.
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
            "chave_do_aviso": mascara(settings.EVOLUTION_API_KEY_PROSPECCAO
                                      or settings.AUTHENTICATION_API_KEY),
            "destino_alerta": mascara(settings.ALERTA_WHATSAPP, 6),
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


def conferir_no_boot() -> None:
    """
    Imprime o estado dos canais de aviso no log, a cada subida.

    Em ERROR quando falta alguma coisa, de propósito: o log de deploy é lido
    de relance, e uma linha de INFO no meio de cem se perde. Se o fundador não
    vai ser avisado, isso não é informação — é defeito.

    Nunca levanta. Diagnóstico que derruba o boot é pior que o problema que
    ele diagnostica.
    """
    try:
        estado = estado_dos_avisos()
    except Exception as e:  # pragma: no cover — rede/config imprevisível
        logger.error(f"AVISOS AO FUNDADOR: nao foi possivel conferir ({e})")
        return

    zap = estado["whatsapp"]
    if estado["pronto_para_avisar"]:
        logger.info(
            "AVISOS AO FUNDADOR: OK | WhatsApp %s -> instancia %s (%s) | e-mail %s",
            zap["destino_alerta"], zap["instancia_do_aviso"],
            zap["conexao"].get("http", "?"), estado["email"]["destino_alerta"],
        )
        return

    logger.error(
        "AVISOS AO FUNDADOR INCOMPLETOS — FALTANDO: %s | WhatsApp destino=%s "
        "instancia=%s conexao=%s | e-mail destino=%s senha=%s",
        ", ".join(estado["faltando"]),
        zap["destino_alerta"], zap["instancia_do_aviso"], zap["conexao"],
        estado["email"]["destino_alerta"], estado["email"]["senha_configurada"],
    )
