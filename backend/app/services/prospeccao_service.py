"""
Yachts Atlas — Prospecção de marinas indicadas (WhatsApp).

Fluxo de um disparo:

    lê leads com whatsapp_status='pendente'
        -> normaliza o número
        -> consulta a blocklist  (quem pediu SAIR)
        -> monta a mensagem a partir de TEMPLATE FIXO
        -> envia pela instância de PROSPECÇÃO (nunca a transacional)
        -> grava o resultado no próprio lead
        -> espera PAUSA_ENTRE_ENVIOS antes do próximo

Decisões:

  • SEM IA. A mensagem é template com substituição de variável. Ela carrega
    condição comercial ("12 meses", "100%"), e texto gerado a cada envio seria
    (a) risco de prometer o que não foi combinado e (b) sinal de bot para o
    WhatsApp, que classifica por padrão. Quando houver IA neste processo, ela
    entra na RESPOSTA, não na saída.

  • Os números comerciais são CONSTANTES deste módulo. Não vêm de banco, não
    vêm de modelo, não são digitados na hora. Mudou a oferta, muda aqui, num
    lugar só — e o que foi enviado ontem continua rastreável.

  • Instância separada, sempre: `enviar_whatsapp(..., prospeccao=True)`. A
    instância transacional entrega código de login e régua de cobrança; um ban
    por denúncia de spam lá derruba as duas coisas junto.

  • Ritmo, não rajada. `PAUSA_ENTRE_ENVIOS` e `LOTE_MAXIMO` existem para o
    número não ser banido no primeiro dia. É o ativo mais frágil da operação.

  • Idempotente por status: o lead sai de 'pendente' assim que é tratado. Uma
    falha de rede no meio do lote não faz a marina receber duas vezes.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from app.core.config import settings
from app.core.supabase import get_supabase_admin
from app.services.whatsapp_service import (
    enviar_whatsapp,
    normalizar_telefone,
    prospeccao_ativa,
)

logger = logging.getLogger(__name__)

# --- Condições comerciais -----------------------------------------------
# Fonte única do que a mensagem promete. Ver a memória do projeto: o Oficial
# trata SOMENTE US$ 250/mês e 12 meses de dossiê 100%.
MESES_DOSSIE_INDICACAO = 12
PERCENTUAL_DOSSIE = 100

# --- Ritmo ---------------------------------------------------------------
# Conservador de propósito. Número novo disparando em volume é o padrão que o
# WhatsApp bane. Subir isto só depois do número estar aquecido.
LOTE_MAXIMO = 20
PAUSA_ENTRE_ENVIOS = 45  # segundos

LINK = "https://yachtsatlas.online"

# O nome de quem indicou aparece DUAS vezes, e a primeira na segunda linha.
# É o único ativo que separa esta mensagem de um disparo frio qualquer: se ele
# aparece só no fim, a marina já leu tudo como propaganda antes de chegar lá.
#
# O que a mensagem NÃO faz, de propósito:
#   • não diz "todos estão aderindo" — a rede está em formação e o contador
#     mostra 0 de 20 vagas. Afirmação que o interlocutor desmente em um clique
#     custa mais do que ganha, ainda mais em mensagem não solicitada;
#   • não diz que a rede está começando ("primeiras vagas", "estamos abrindo").
#     Isso entrega o estágio da operação para quem não precisa saber, e enfraquece
#     a proposta em vez de criar urgência. A condição especial se sustenta no
#     fato de ELA ter sido indicada, que é sobre ela e não sobre nós;
#   • não abre o preço. "Condição especial" convida a responder; número no
#     primeiro toque encerra a conversa antes de existir valor.
MENSAGEM_1 = (
    "Olá, {responsavel}. Aqui é do *Yachts Atlas*.\n\n"
    "A *{indicadora}* indicou a {indicada} para o nosso "
    "*Programa de Custódia*.\n\n"
    # "sua Marina", com M maiúsculo: fala com ELA, não sobre uma categoria.
    # A maiúscula é deliberada — trata a Marina como instituição, do mesmo modo
    # que se escreve o nome de uma empresa. Não "corrigir" para minúscula.
    # "selo de integridade", NÃO "dossiê certificado". O Atlas não inspeciona
    # embarcação nem emite certificado — isso é atribuição de órgão competente,
    # e a própria FAQ do site diz isso. O que ele certifica é a INTEGRIDADE do
    # registro (SHA-256, selo imutável, QR que valida). Prometer certificação
    # do ativo em mensagem comercial é promessa que o produto não cumpre.
    "Organizamos documentos, laudos e todo o histórico de cada embarcação num "
    "*Dossiê Náutico* com selo de integridade — e cada dossiê emitido vira "
    "receita para sua Marina.\n\n"
    "A indicação da *{indicadora}* garante condição especial para vocês.\n\n"
    # Instrução explícita antes do link. Link solto no meio do texto é fácil de
    # passar batido; dizer o que fazer com ele é o que transforma leitura em
    # clique.
    "Acesse a página e conheça o programa:\n"
    "{link}\n\n"
    "Faz sentido conversarmos?\n\n"
    # A saída fica em itálico e por último: cumpre o dever de transparência sem
    # roubar a atenção da pergunta. Só pode existir porque o webhook de opt-out
    # existe (api/v1/whatsapp.py) — prometer saída que não funciona é o que
    # transforma "não quero" em denúncia, e denúncia é o que bane o número.
    "_Se preferir não receber, é só responder SAIR._"
)


def _limpo(valor: str | None) -> str:
    """Tira espaco das pontas.

    Nao e frescura de formatacao: o nome vai ENTRE ASTERISCOS na mensagem, e o
    WhatsApp nao aceita negrito que fecha depois de um espaco — "*Marina X *"
    chega com os asteriscos a mostra. O cadastro ja limpa na entrada; isto aqui
    protege as linhas que entraram sujas antes disso.
    """
    return (valor or "").strip()


def montar_mensagem(responsavel: str, indicadora: str, indicada: str) -> str:
    """Preenche o template. Nada aqui e gerado — so substituido."""
    primeiro_nome = _limpo(responsavel).split()
    return MENSAGEM_1.format(
        responsavel=primeiro_nome[0] if primeiro_nome else "tudo bem",
        indicadora=_limpo(indicadora) or "uma marina parceira",
        indicada=_limpo(indicada) or "sua marina",
        link=LINK,
    )


# --- O e-mail, primeiro toque ---------------------------------------------
# Mesma disciplina do WhatsApp, e pelas mesmas razoes: sem preco, sem dizer
# que a rede esta comecando, e "selo de integridade" em vez de "dossie
# certificado" — o Atlas nao inspeciona embarcacao, ele certifica a
# INTEGRIDADE do registro.
#
# O assunto carrega o nome de QUEM INDICOU, que e a unica coisa nesta mensagem
# que a marina reconhece. "Conheca o Yachts Atlas" seria mais um assunto de
# oferta na caixa dela; o nome de um colega nao e.
ASSUNTO_EMAIL = "{indicadora} indicou a {indicada} ao Yachts Atlas"

PARAGRAFOS_EMAIL = (
    "A <strong style=\"color:#ffffff\">{indicadora}</strong> indicou a "
    "{indicada} para o nosso <strong style=\"color:#ffffff\">Programa de "
    "Custódia</strong>.",

    "Organizamos documentos, laudos e todo o histórico de cada embarcação num "
    "<strong style=\"color:#ffffff\">Dossiê Náutico</strong> com selo de "
    "integridade: cada registro fechado com assinatura SHA-256 e um QR que "
    "qualquer pessoa pode conferir. E cada dossiê emitido vira receita para "
    "sua Marina.",

    "A indicação da <strong style=\"color:#ffffff\">{indicadora}</strong> "
    "garante condição especial para vocês.",

    "Faz sentido conversarmos?",
)

# Em texto puro, para quem le o e-mail sem HTML — e para o log.
_SEM_TAG = ("<strong style=\"color:#ffffff\">", "</strong>")


def montar_email(responsavel: str, indicadora: str, indicada: str) -> tuple[str, str, str]:
    """Devolve (assunto, html, texto). Nada gerado — so substituido."""
    from app.services.email_service import moldura_html

    primeiro_nome = _limpo(responsavel).split()
    dados = {
        "responsavel": primeiro_nome[0] if primeiro_nome else "tudo bem",
        "indicadora": _limpo(indicadora) or "Uma marina parceira",
        "indicada": _limpo(indicada) or "sua marina",
    }

    assunto = ASSUNTO_EMAIL.format(**dados)
    paragrafos = [linha.format(**dados) for linha in PARAGRAFOS_EMAIL]

    # O rodape nao e cortesia: e o que separa abordagem de spam. So pode
    # existir porque alguem le a caixa e atende o pedido — o mesmo motivo pelo
    # qual o WhatsApp so promete "responda SAIR" depois de existir o webhook
    # de opt-out.
    rodape = (
        "Você recebeu este e-mail porque a {indicadora} indicou a sua Marina. "
        "Se preferir não receber, é só responder com SAIR."
    ).format(**dados)

    html = moldura_html(
        kicker="Programa de Custódia",
        titulo=f"Olá, {dados['responsavel']}.",
        paragrafos=paragrafos,
        cta_texto="Conhecer o programa",
        cta_url=LINK,
        rodape=rodape,
    )

    texto = "\n\n".join(
        [f"Olá, {dados['responsavel']}. Aqui é do Yachts Atlas."]
        + [linha.replace(_SEM_TAG[0], "").replace(_SEM_TAG[1], "") for linha in paragrafos]
        + [f"Acesse: {LINK}", rodape]
    )
    return assunto, html, texto


def esta_bloqueado(supabase, telefone: str) -> bool:
    """Se o número pediu para não receber mais.

    Falha fechada: se a consulta der erro, tratamos como bloqueado. Mandar
    para quem pediu SAIR é o que gera denúncia — e denúncia é o que bane o
    número. Na dúvida, não enviar custa menos.
    """
    try:
        r = (
            supabase.table("whatsapp_blocklist")
            .select("telefone")
            .eq("telefone", telefone)
            .limit(1)
            .execute()
        )
        return bool(r.data)
    except Exception as e:
        logger.error(f"Blocklist ilegível para {telefone}: {e} — tratando como bloqueado")
        return True


def bloquear(telefone: Optional[str], motivo: str = "pediu SAIR") -> bool:
    """Põe um número na blocklist. Chamada pelo webhook de resposta.

    Chamada por `api/v1/whatsapp.py` quando a marina responde SAIR. Também
    serve para bloquear à mão um número que pediu por outro caminho.
    """
    numero = normalizar_telefone(telefone)
    if not numero:
        return False
    try:
        get_supabase_admin().table("whatsapp_blocklist").upsert(
            {"telefone": numero, "motivo": motivo},
            on_conflict="telefone",
        ).execute()
        logger.info(f"Número {numero} entrou na blocklist ({motivo})")
        return True
    except Exception as e:
        logger.error(f"Falha ao bloquear {numero}: {e}")
        return False


def _marcar(supabase, lead_id: str, status: str, erro: Optional[str] = None) -> None:
    """Tira o lead de 'pendente'. Falhar aqui repetiria o envio no próximo lote."""
    dados = {"whatsapp_status": status, "whatsapp_erro": erro}
    if status == "enviado":
        dados["whatsapp_enviado_em"] = "now()"
    try:
        supabase.table("marina_leads").update(dados).eq("id", lead_id).execute()
    except Exception as e:
        logger.error(f"Falha ao marcar lead {lead_id} como {status}: {e}")


def _limite_de_carencia(minutos: Optional[int]) -> str:
    """Instante-limite: só entram leads criados ANTES disto.

    A carência não é atraso técnico — é a janela em que um lead errado ainda
    pode ser tirado da fila. Mensagem enviada não volta; lead na fila, sim.
    """
    if minutos is None:
        minutos = settings.PROSPECCAO_CARENCIA_MINUTOS
    corte = datetime.now(timezone.utc) - timedelta(minutes=max(0, minutos))
    return corte.isoformat()


def _marcar_email(supabase, lead_id: str, status: str, erro: Optional[str] = None) -> None:
    """Tira o lead da fila de e-mail. O par do `_marcar`, para o outro canal.

    Sem isto o lote seguinte reenviaria a mesma mensagem — e receber a mesma
    abordagem duas vezes é o que transforma interesse em denúncia.
    """
    dados = {"email_status": status, "email_erro": erro}
    if status == "enviado":
        dados["email_enviado_em"] = "now()"
    try:
        supabase.table("marina_leads").update(dados).eq("id", lead_id).execute()
    except Exception as e:
        logger.error(f"Falha ao marcar e-mail do lead {lead_id} como {status}: {e}")


def disparar_lote(
    limite: int = LOTE_MAXIMO,
    dry_run: bool = False,
    carencia_minutos: Optional[int] = None,
) -> dict:
    """Dispara um lote de prospecção. Devolve o resumo do que aconteceu.

    DOIS CANAIS, um gatilho. O e-mail é o primeiro toque e sai antes do
    WhatsApp, na mesma passada. Poderia sair sozinho no momento da indicação,
    mas então uma abordagem comercial partiria sem ninguém olhar — exatamente o
    que esta rota evita desde que nasceu. Um gatilho só também significa uma
    conferência só: o `dry_run` mostra os dois textos antes de qualquer envio.

    Cada canal tem o seu estado (`email_status`, `whatsapp_status`), então um
    lead pode ter o e-mail entregue e o WhatsApp recusado sem que um repita o
    trabalho do outro no lote seguinte.

    `dry_run=True` monta tudo e não envia nada — serve para conferir as
    mensagens com dados reais antes de falar com marina de verdade.
    """
    from app.services.email_service import send_email

    supabase = get_supabase_admin()

    # A instância de WhatsApp fora do ar não pode cancelar o lote: o e-mail não
    # depende dela. Antes isto era um `return` no topo, e uma indisponibilidade
    # do WhatsApp levava o outro canal junto.
    zap_ligado = dry_run or prospeccao_ativa()

    resumo = {
        "enviados": 0, "bloqueados": 0, "sem_numero": 0, "falharam": 0,
        "emails": 0, "emails_falharam": 0, "emails_sem_endereco": 0,
        "dry_run": dry_run, "amostra": None, "amostra_email": None,
    }
    if not zap_ligado:
        resumo["aviso"] = ("instância de prospecção não configurada "
                           "(EVOLUTION_INSTANCE_PROSPECCAO) — só o e-mail sai")

    try:
        leads = (
            supabase.table("marina_leads")
            .select("id, marina_name, contact_name, whatsapp, source, "
                    "email, email_status, whatsapp_status")
            .or_("whatsapp_status.eq.pendente,email_status.eq.pendente")
            .lte("created_at", _limite_de_carencia(carencia_minutos))
            .order("created_at")
            .limit(limite)
            .execute()
        ).data or []
    except Exception as e:
        logger.error(f"Falha ao ler leads de prospecção: {e}")
        return {"erro": str(e), "enviados": 0}

    for i, lead in enumerate(leads):

        # --- E-MAIL: primeiro toque ------------------------------------
        if (lead.get("email_status") or "") == "pendente":
            destino = (lead.get("email") or "").strip()
            if not destino:
                resumo["emails_sem_endereco"] += 1
                if not dry_run:
                    _marcar_email(supabase, lead["id"], "sem_endereco")
            else:
                assunto, html, texto = montar_email(
                    responsavel=lead.get("contact_name", ""),
                    indicadora=lead.get("source", ""),
                    indicada=lead.get("marina_name", ""),
                )
                if dry_run:
                    resumo["emails"] += 1
                    if resumo["amostra_email"] is None:
                        resumo["amostra_email"] = {
                            "para": destino, "assunto": assunto, "texto": texto,
                        }
                elif send_email(destino, assunto, html, texto):
                    resumo["emails"] += 1
                    _marcar_email(supabase, lead["id"], "enviado")
                else:
                    resumo["emails_falharam"] += 1
                    _marcar_email(supabase, lead["id"], "falhou",
                                  "SMTP recusou ou não está configurado")

        # --- WHATSAPP: reforço -----------------------------------------
        if (lead.get("whatsapp_status") or "") != "pendente" or not zap_ligado:
            continue

        numero = normalizar_telefone(lead.get("whatsapp"))
        if not numero:
            resumo["sem_numero"] += 1
            if not dry_run:
                _marcar(supabase, lead["id"], "sem_numero")
            continue

        if esta_bloqueado(supabase, numero):
            resumo["bloqueados"] += 1
            if not dry_run:
                _marcar(supabase, lead["id"], "bloqueado")
            continue

        texto_zap = montar_mensagem(
            responsavel=lead.get("contact_name", ""),
            indicadora=lead.get("source", ""),
            indicada=lead.get("marina_name", ""),
        )

        if dry_run:
            resumo["enviados"] += 1
            if resumo["amostra"] is None:
                resumo["amostra"] = {"para": numero, "texto": texto_zap}
            continue

        if enviar_whatsapp(numero, texto_zap, prospeccao=True):
            resumo["enviados"] += 1
            _marcar(supabase, lead["id"], "enviado")
        else:
            resumo["falharam"] += 1
            _marcar(supabase, lead["id"], "falhou", "envio recusado pelo provedor")

        # Ritmo: só entre envios de verdade, e não depois do último.
        if i < len(leads) - 1:
            time.sleep(PAUSA_ENTRE_ENVIOS)

    # Volta vazia é o estado NORMAL: na maioria das vezes não há lead com a
    # carência vencida. Em INFO, isso escreveu uma linha a cada 60 segundos
    # durante dias — e o `agenda.py`, que chama esta função, já dizia no
    # próprio comentário que só queria registrar quando algo acontecesse.
    if any(resumo.get(k) for k in ("enviados", "falharam", "bloqueados",
                                   "emails", "emails_falharam")):
        logger.info(f"Prospecção — lote concluído: {resumo}")
    else:
        logger.debug(f"Prospecção — nada na fila: {resumo}")
    return resumo


if __name__ == "__main__":
    # Conferir a mensagem antes de falar com marina de verdade:
    #     python -m app.services.prospeccao_service          (dry run)
    #     python -m app.services.prospeccao_service --enviar (dispara)
    import sys

    enviar = "--enviar" in sys.argv
    print(f"instância prospecção: {settings.EVOLUTION_INSTANCE_PROSPECCAO or '(não configurada)'}")
    print(f"modo               : {'ENVIO REAL' if enviar else 'dry run (nada sai)'}")
    resultado = disparar_lote(dry_run=not enviar)
    amostra = resultado.pop("amostra", None)
    amostra_email = resultado.pop("amostra_email", None)
    print(resultado)
    if amostra:
        print("\n--- amostra ---")
        print(f"para: {amostra['para']}\n")
        print(amostra["texto"])

    if amostra_email:
        print("\n--- amostra do e-mail ---")
        print(f"para   : {amostra_email['para']}")
        print(f"assunto: {amostra_email['assunto']}\n")
        print(amostra_email["texto"])
