"""
Yachts Atlas — Dossiê

Dois caminhos de acesso ao dossiê:
 1. Dono / marina (autenticado): acessa o próprio dossiê livremente. O dossiê
    NÃO é mais vendido pela plataforma — o pagamento é direto marina <-> dono.
 2. Terceiros (broker / comprador / seguradora): solicitam por formulário aberto
    (POST /solicitar); a Yachts Atlas libera manualmente (POST .../liberar) e o
    acesso é feito por uma página simples no celular, protegida por senha-mestra.
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Response, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.security import get_current_user
from app.core.supabase import get_supabase_admin
from app.core.authz import get_ativo_autorizado
from app.middleware.tracking import get_client_ip, get_user_agent
from app.services.dossie_data import montar_dados_dossie
from app.core.limite_taxa import limite
import hashlib
from app.services.dossie_pdf import gerar_pdf_dossie
from app.services.alert_service import send_email_alert
from app.api.v1.consentimento import consentimento_vigente
from app.services.notify_service import notificar_fundador

logger = logging.getLogger(__name__)

router = APIRouter()

FINALIDADES = {"venda", "seguro", "outro"}


def _assert_acesso_ativo(ativo_id: str, user: dict) -> None:
    """Só o dono/marina do ativo (ou admin da plataforma) acessa o dossiê."""
    get_ativo_autorizado(ativo_id, str(user["sub"]))


def _check_master(senha: str) -> bool:
    """Compara a senha informada com a senha-mestra (timing-safe)."""
    master = settings.DOSSIER_MASTER_PASSWORD
    if not master:
        return False
    return secrets.compare_digest(str(senha), str(master))


# ----------------------------------------------------------------------------
# 1) Dono / marina (autenticado)
# ----------------------------------------------------------------------------

@router.get("/emitidos/contagem")
async def contar_emitidos(user: dict = Depends(get_current_user)):
    """
    Quantos dossiês esta marina já emitiu.

    Existe porque o painel mostrava **0** mesmo depois de emitir: ele pedia o
    número ao endpoint de TABELA DE PREÇOS (`/payments/plans`), lendo um campo
    `dossier_count` que não existe em lugar nenhum do backend. Vinha `undefined`
    todas as vezes, e o card ficava zerado desde sempre.

    Conta por `emitido_por` — quem emitiu. A tabela `dossie_emitidos` é o
    livro-razão das emissões e já registra hash do PDF, tamanho e canal; aqui só
    se pergunta quantas foram.

    Declarado ANTES de `/{ativo_id}/dados` por clareza de leitura: rota fixa
    antes de rota com parâmetro, para ninguém precisar conferir se colidem.
    """
    supabase = get_supabase_admin()
    usuario_id = user.get("sub") if user else None
    if not usuario_id:
        return {"total": 0}
    try:
        res = (
            supabase.table("dossie_emitidos")
            .select("id", count="exact")
            .eq("emitido_por", usuario_id)
            .execute()
        )
        return {"total": res.count or 0}
    except Exception as e:  # noqa: BLE001 — contador não derruba o painel
        logger.error(f"Falha ao contar dossiês emitidos de {usuario_id}: {e}")
        return {"total": 0}


@router.get("/{ativo_id}/dados")
async def dados_dossie(ativo_id: str, user: dict = Depends(get_current_user)):
    """
    Retorna o pacote de dados do dossiê montado a partir do banco real
    (ativos + registros + documentos). É a fonte que o gerador de PDF consome.
    """
    _assert_acesso_ativo(ativo_id, user)
    try:
        return montar_dados_dossie(ativo_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _registrar_emissao(ativo_id: str, pdf: bytes, dados: dict,
                       emitido_por: str | None, canal: str) -> str:
    """Grava a impressão digital do PDF emitido e devolve o hash.

    Existe porque a assinatura do QR cobre **protocolo + data de emissão**, e
    não o conteúdo. Quem recebesse um dossiê legítimo podia abrir o PDF, mudar
    "R$ 89 mil" para "R$ 340 mil", apagar o histórico de sinistros — e o QR
    continuaria dizendo "Documento autêntico", porque protocolo e data não
    mudaram.

    O que fecha isso não é assinar melhor: é a plataforma LEMBRAR o que emitiu.
    Com o hash registrado, quem tem o PDF em mãos calcula o SHA-256 do próprio
    arquivo e compara com o que a verificação informa. Bateu, é o original;
    não bateu, foi mexido depois da emissão.

    A tabela é append-only no BANCO (trigger que recusa UPDATE e DELETE), pelo
    mesmo princípio dos registros selados: capacidade que não existe não pode
    ser abusada — nem pela service_role, nem por quem tiver a chave.

    Best-effort: falhar em registrar não pode impedir a entrega do dossiê que
    o cliente pediu e pagou. Devolve o hash de qualquer forma, porque ele é
    calculado aqui e impresso no documento.
    """
    digest = hashlib.sha256(pdf).hexdigest()
    try:
        ident = dados.get("identificacao") or {}
        get_supabase_admin().table("dossie_emitidos").insert({
            "ativo_id": ativo_id,
            "protocolo": ativo_id,
            "emitido_em": datetime.now(timezone.utc).date().isoformat(),
            "hash_pdf": digest,
            "tamanho_bytes": len(pdf),
            "emitido_por": emitido_por,
            "canal": canal,
        }).execute()
    except Exception as e:
        logger.error(f"Falha ao registrar emissão do dossiê {ativo_id}: {e}")
    return digest


def _saldo_dossie(ativo_id: str) -> dict:
    """
    Quantos dossiês este ativo ainda pode emitir nos próximos 12 meses.

    A conta vivia SÓ no `localStorage` do navegador, numa chave por ativo. Duas
    consequências, e a segunda é a grave:

    1. o número na tela mudava conforme o navegador — a marina emitia três num
       e o outro continuava mostrando "4 restantes", porque cada janela contava
       sozinha;
    2. e o limite não era limite: trocar de navegador, limpar dados do site ou
       apagar uma chave no console liberava emissão sem fim.

    O banco sempre soube — `dossie_emitidos` registra cada emissão com hash e
    hora. Faltava a tela perguntar a ele, e o servidor recusar.

    O que decide o comportamento do gerente é o que ESTÁ NA TELA: ele vê "ainda
    pode gerar" e promete o dossiê ao cliente. Banco certo com tela errada é,
    para quem usa, um sistema errado.
    """
    limite_anual = settings.DOSSIE_LIMITE_ANUAL
    desde = (datetime.now(timezone.utc) - timedelta(days=365)).date().isoformat()
    try:
        # Dentro do try junto com a consulta: se o cliente falhar ao ser criado,
        # a exceção escapava e derrubava a EMISSÃO, não só a contagem. Apurar
        # saldo é acessório; gerar o dossiê é o que a marina veio fazer.
        supabase = get_supabase_admin()
        # A cota mede o que a MARINA emitiu, nao quantas vezes o documento foi
        # baixado. Sao duas perguntas diferentes, e ate 31/08/2026 a conta
        # respondia a errada: contava TODA linha de `dossie_emitidos`,
        # inclusive as de canal `acesso_link`, gravadas a cada vez que o
        # destinatario abre o link que ja lhe foi liberado.
        #
        # O efeito era o cliente errado pagar a conta: um comprador que
        # abrisse o dossie quatro vezes esgotava o ano da marina, e a marina
        # -- que pagou -- ficava trancada fora do proprio ativo. Pior, a via
        # do link nunca checou limite nenhum: o terceiro seguia baixando
        # depois do bloqueio, enquanto o dono nao conseguia mais emitir.
        res = (
            supabase.table("dossie_emitidos")
            .select("emitido_em")
            .eq("ativo_id", ativo_id)
            .eq("canal", "painel")
            .gte("emitido_em", desde)
            .execute()
        )
        linhas = [{"quando": str(r.get("emitido_em"))[:10]}
                  for r in (res.data or []) if r.get("emitido_em")]

        # Mais as liberacoes para terceiro: UMA por pedido liberado, que e o
        # ato da marina. Reabrir o mesmo link nao gasta cota de novo.
        lib = (
            supabase.table("dossie_solicitacoes")
            .select("liberado_em")
            .eq("ativo_id", ativo_id)
            .eq("status", "liberado")
            .gte("liberado_em", desde)
            .execute()
        )
        linhas += [{"quando": str(r.get("liberado_em"))[:10]}
                   for r in (lib.data or []) if r.get("liberado_em")]

        linhas.sort(key=lambda r: r["quando"])
        usados = len(linhas)
    except Exception as e:  # noqa: BLE001 — saldo não derruba a emissão
        logger.error(f"Falha ao apurar saldo de dossiês de {ativo_id}: {e}")
        return {"limite": limite_anual, "usados": 0, "restantes": limite_anual,
                "permitido": True, "reset_em": None}

    restantes = max(0, limite_anual - usados)
    # Quando esgota, o próximo lugar abre 12 meses depois da emissão MAIS ANTIGA
    # ainda dentro da janela — é ela que sai da contagem primeiro.
    reset_em = None
    if restantes == 0 and linhas:
        mais_antiga = linhas[0].get("quando")
        if mais_antiga:
            reset_em = (datetime.fromisoformat(str(mais_antiga)) + timedelta(days=365)).date().isoformat()

    return {"limite": limite_anual, "usados": usados, "restantes": restantes,
            "permitido": restantes > 0, "reset_em": reset_em}


@router.get("/{ativo_id}/saldo")
async def saldo_dossie(ativo_id: str, user: dict = Depends(get_current_user)):
    """Saldo de emissões do ativo — é o número que a tela mostra ao gerente."""
    _assert_acesso_ativo(ativo_id, user)
    return _saldo_dossie(ativo_id)


@router.get("/{ativo_id}/pdf")
async def pdf_dossie(ativo_id: str, user: dict = Depends(get_current_user)):
    """Gera o PDF do dossiê do dono/marina (só seções com dado)."""
    _assert_acesso_ativo(ativo_id, user)

    # A recusa acontece AQUI, no servidor, e não na tela. Enquanto morou só no
    # navegador, o limite era um pedido: bastava outra janela para ignorá-lo.
    saldo = _saldo_dossie(ativo_id)
    if not saldo["permitido"]:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Limite de {saldo['limite']} dossiês por ano atingido para este ativo. "
                f"Nova emissão a partir de {saldo['reset_em']}."
            ),
        )

    try:
        dados = montar_dados_dossie(ativo_id)
        pdf = gerar_pdf_dossie(dados)
        # A plataforma passa a LEMBRAR o que emitiu. Sem isto, um dossiê
        # legítimo podia ser editado depois da entrega e o QR continuaria
        # validando — a assinatura cobre protocolo e data, não o conteúdo.
        _registrar_emissao(ativo_id, pdf, dados, user.get("sub"), "painel")
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="dossie_{ativo_id}.pdf"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ----------------------------------------------------------------------------
# 2) Terceiros — coleta de pedido (formulário aberto)
# ----------------------------------------------------------------------------

class DossieSolicitacao(BaseModel):
    ativo_id: Optional[str] = None
    marina_nome: Optional[str] = None
    solicitante_nome: str
    solicitante_email: EmailStr
    solicitante_telefone: Optional[str] = None
    finalidade: str = "outro"
    mensagem: Optional[str] = None


@router.post("/solicitar", dependencies=[Depends(limite("form_dossie", 5, 60))])
async def solicitar_dossie(data: DossieSolicitacao):
    """Coleta um pedido de dossiê (público). Status inicial: pendente."""
    supabase = get_supabase_admin()
    finalidade = data.finalidade if data.finalidade in FINALIDADES else "outro"

    row = {
        "ativo_id": data.ativo_id,
        "marina_nome": data.marina_nome,
        "solicitante_nome": data.solicitante_nome,
        "solicitante_email": str(data.solicitante_email),
        "solicitante_telefone": data.solicitante_telefone,
        "finalidade": finalidade,
        "mensagem": data.mensagem,
        "status": "pendente",
    }
    try:
        res = supabase.table("dossie_solicitacoes").insert(row).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Falha ao registrar pedido: {e}")

    rec = res.data[0] if res.data else {}

    # Avisa a Yachts Atlas do novo pedido (best-effort)
    try:
        send_email_alert(
            to_email=settings.EMAIL_SENDER or "yachtsatlas@gmail.com",
            subject="Novo pedido de dossiê",
            body=(
                "Novo pedido de dossiê recebido.\n\n"
                f"Solicitante: {data.solicitante_nome}\n"
                f"E-mail: {data.solicitante_email}\n"
                f"Telefone: {data.solicitante_telefone or '-'}\n"
                f"Finalidade: {finalidade}\n"
                f"Ativo: {data.ativo_id or '-'}\n"
                f"Marina: {data.marina_nome or '-'}\n"
                f"Mensagem: {data.mensagem or '-'}\n"
            ),
        )
    except Exception:
        pass

    # Ping instantâneo no celular do fundador (WhatsApp/e-mail, best-effort)
    try:
        notificar_fundador(
            "Novo pedido de dossiê",
            f"Nome: {data.solicitante_nome}\n"
            f"E-mail: {data.solicitante_email}\n"
            f"Telefone: {data.solicitante_telefone or '-'}\n"
            f"Finalidade: {finalidade}\n"
            f"Ativo: {data.ativo_id or '-'}\n"
            f"Marina: {data.marina_nome or '-'}",
        )
    except Exception:
        pass

    return {
        "id": rec.get("id"),
        "status": "pendente",
        "message": "Pedido recebido. A Yachts Atlas entrará em contato para liberar o dossiê.",
    }


# ----------------------------------------------------------------------------
# 2b) Painel da Yachts Atlas (autenticado) — listar e liberar pedidos
# ----------------------------------------------------------------------------

@router.get("/solicitacoes")
async def listar_solicitacoes(
    status: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Lista os pedidos de dossiê (opcionalmente filtrando por status)."""
    supabase = get_supabase_admin()
    query = supabase.table("dossie_solicitacoes").select("*").order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    return query.execute().data or []


@router.post("/solicitacoes/{solicitacao_id}/liberar")
async def liberar_solicitacao(
    solicitacao_id: str,
    request: Request,
    user: dict = Depends(get_current_user),
):
    """Libera o dossiê para o solicitante e envia o link de acesso por e-mail."""
    supabase = get_supabase_admin()
    res = supabase.table("dossie_solicitacoes").select("*").eq("id", solicitacao_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    sol = res.data[0]

    # Liberar E a emissao: e aqui que a marina decide entregar o dossie a um
    # terceiro. Ate 31/08/2026 esta via nao consultava a cota -- o limite so
    # existia no botao do painel, entao bastava liberar por pedido para passar
    # dos quatro do ano sem que nada recusasse.
    #
    # Cobrar no momento da liberacao, e nao no download, poe o gasto em quem
    # decide: o destinatario reabrir o link nao tira nada da marina.
    _ativo = sol.get("ativo_id")
    if _ativo:
        saldo = _saldo_dossie(_ativo)
        if not saldo["permitido"]:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Limite de {saldo['limite']} dossies por ano atingido para este ativo. "
                    f"Nova emissao a partir de {saldo['reset_em']}."
                ),
            )

    # BASE LEGAL — sem consentimento do titular, o dossie nao sai.
    #
    # A plataforma ja registrava PARA QUEM o documento foi, quando e para que
    # (`dossie_solicitacoes` + `dossie_saidas`). Faltava o outro lado: o
    # armador ter dito que pode. Trilha sem base legal responde metade da
    # pergunta que a LGPD -- e uma seguradora auditando -- faz.
    #
    # A checagem fica AQUI, e nao no download do painel, porque este e o ato
    # de compartilhar com terceiro. A marina baixar o dossie do proprio
    # cliente nao e compartilhamento: o dado ja esta com ela.
    if _ativo:
        cons = consentimento_vigente(_ativo)
        if cons["vigente"] is None:
            # Nao sabemos. Recusar e reversivel; entregar nao e.
            raise HTTPException(
                status_code=503,
                detail="Nao foi possivel confirmar o consentimento do titular. Tente novamente.",
            )
        if not cons["vigente"]:
            faltou = ("o titular retirou o consentimento"
                      if cons["evento"] == "revogado"
                      else "o consentimento do titular nao foi registrado")
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Nao e possivel liberar este dossie: {faltou}. "
                    "Registre a autorizacao do armador na ficha da embarcacao."
                ),
            )

    now = datetime.now(timezone.utc).isoformat()
    supabase.table("dossie_solicitacoes").update({
        "status": "liberado",
        "liberado_em": now,
        "liberado_por": user.get("sub"),
        "updated_at": now,
    }).eq("id", solicitacao_id).execute()

    base = str(request.base_url).rstrip("/")
    link = f"{base}/api/v1/dossie/acesso/{solicitacao_id}"

    # E-mail com o link — a senha NÃO vai no e-mail (segurança da senha-mestra).
    try:
        send_email_alert(
            to_email=sol["solicitante_email"],
            subject="Seu dossiê foi liberado",
            body=(
                f"Olá {sol.get('solicitante_nome', '')},\n\n"
                "Seu acesso ao dossiê foi liberado pela Yachts Atlas.\n\n"
                f"Abra no celular: {link}\n\n"
                "Na página será pedida a senha de acesso, que a Yachts Atlas "
                "informa a você separadamente, por segurança.\n\n"
                "Yachts Atlas — Custódia Digital de Ativos Náuticos\n"
            ),
        )
    except Exception:
        pass

    return {"id": solicitacao_id, "status": "liberado", "acesso_url": link}


@router.get("/saidas")
async def listar_saidas(
    ativo_id: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Livro-razão de dossiês que saíram: pra quem, qual marina, qual barco, quando."""
    supabase = get_supabase_admin()
    query = supabase.table("dossie_saidas").select("*").order("created_at", desc=True)
    if ativo_id:
        query = query.eq("ativo_id", ativo_id)
    return query.execute().data or []


@router.post("/solicitacoes/{solicitacao_id}/recusar")
async def recusar_solicitacao(
    solicitacao_id: str,
    user: dict = Depends(get_current_user),
):
    """Marca um pedido como recusado."""
    supabase = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()
    res = supabase.table("dossie_solicitacoes").update({
        "status": "recusado",
        "updated_at": now,
    }).eq("id", solicitacao_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    return {"id": solicitacao_id, "status": "recusado"}


# ----------------------------------------------------------------------------
# 2d) Teste do canal de avisos (WhatsApp e e-mail)
# ----------------------------------------------------------------------------

@router.post("/avisos/teste")
async def testar_aviso(user: dict = Depends(get_current_user)):
    """
    Confirma que os avisos operacionais chegam.

    Vale a pena rodar depois de mexer nas variáveis: descobrir que o canal
    está errado no dia em que uma marina para de pagar é caro demais.

    Configuração: ALERTA_WHATSAPP (seu número) e ALERTA_EMAIL (seu e-mail).
    """
    ok = notificar_fundador(
        "Teste de aviso",
        "Se você recebeu isto, o canal de avisos da Yachts Atlas está funcionando.",
    )
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Nenhum canal entregou. Verifique ALERTA_WHATSAPP, ALERTA_EMAIL, "
                   "EMAIL_PASSWORD e a configuração da Evolution.",
        )
    return {"status": "enviado"}


# ----------------------------------------------------------------------------
# 2c) Acesso por senha (página pública, mobile-first)
# ----------------------------------------------------------------------------

def _render_acesso_page(mensagem_html: str = "") -> str:
    """Página de senha, servida pelo backend (funciona em qualquer celular)."""
    return _ACESSO_PAGE.replace("<!--MSG-->", mensagem_html)


@router.get("/acesso/{solicitacao_id}", response_class=HTMLResponse)
async def acesso_page(solicitacao_id: str):
    """Mostra a página de senha para o dossiê liberado."""
    supabase = get_supabase_admin()
    res = supabase.table("dossie_solicitacoes").select("status").eq("id", solicitacao_id).execute()
    if not res.data:
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Link inválido. Verifique com a Yachts Atlas.</p>"), status_code=404)
    if res.data[0].get("status") != "liberado":
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Este dossiê ainda não foi liberado.</p>"), status_code=403)
    return HTMLResponse(_render_acesso_page())


@router.post(
    "/acesso/{solicitacao_id}",
    # Forca bruta na senha-mestra que devolve o PDF de um cliente.
    # 5 tentativas por quarto de hora, por IP E por solicitacao: quem
    # erra de verdade acerta dentro disso; robo nao chega a lugar nenhum.
    dependencies=[Depends(limite("senha_dossie", 5, 900, por_rota=True))],
)
async def acesso_processar(
    request: Request, solicitacao_id: str, senha: str = Form(...)
):
    """Valida a senha-mestra e devolve o PDF do dossiê liberado."""
    supabase = get_supabase_admin()
    res = supabase.table("dossie_solicitacoes").select("*").eq("id", solicitacao_id).execute()
    if not res.data:
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Link inválido.</p>"), status_code=404)
    sol = res.data[0]

    if sol.get("status") != "liberado":
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Este dossiê ainda não foi liberado.</p>"), status_code=403)

    if not _check_master(senha):
        # Senha errada vira registro. O limite de taxa BARRA a força bruta; a
        # trilha é o que a torna VISÍVEL — sem ela, mil tentativas e nenhuma
        # tentativa têm a mesma aparência depois do fato. Best-effort: falhar
        # em auditar não pode virar 500 na cara de quem só errou a senha.
        try:
            from app.services.audit_service import (
                audit_service, AuditAction, AuditSeverity,
            )
            audit_service.create_audit_log(
                action=AuditAction.UNAUTHORIZED_ACCESS,
                user_id="anonymous",
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                success=False,
                severity=AuditSeverity.WARNING,
                details={
                    "evento": "senha_mestra_incorreta",
                    "solicitacao_id": solicitacao_id,
                    "ativo_id": sol.get("ativo_id"),
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"Falha ao auditar senha incorreta: {e}")
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Senha incorreta. Tente novamente.</p>"), status_code=401)

    ativo_id = sol.get("ativo_id")
    if not ativo_id:
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Pedido sem ativo vinculado. Contate a Yachts Atlas.</p>"), status_code=400)

    # Registra o acesso (controle — não vira bagunça)
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("dossie_solicitacoes").update({
        "acessos": (sol.get("acessos") or 0) + 1,
        "ultimo_acesso": now,
        "updated_at": now,
    }).eq("id", solicitacao_id).execute()

    # Livro-razão de saídas: pra quem foi, qual marina, qual barco.
    #
    # ANTES da entrega, e OBRIGATÓRIO. Era `try/except: pass` — se o insert
    # falhasse, o dossiê saía e o rastro não, em silêncio. Num livro-razão de
    # compartilhamento isso é o inverso do desejado: o registro é o produto,
    # não um efeito colateral dele.
    #
    # É a diferença entre este registro e o de `_registrar_emissao`, que
    # continua best-effort de propósito: lá o que se perde é a impressão
    # digital de um PDF que a plataforma já sabe ter emitido; aqui o que se
    # perde é a única prova de que o documento saiu, e para quem. Sem ela, a
    # resposta a "quem recebeu o dossiê deste barco?" fica errada para
    # sempre — e é pergunta de LGPD e de auditoria de seguradora.
    #
    # Recusar a entrega é a escolha conservadora: o solicitante tenta de novo
    # em segundos; um compartilhamento sem rastro não se conserta depois.
    try:
        supabase.table("dossie_saidas").insert({
            "solicitacao_id": solicitacao_id,
            "ativo_id": ativo_id,
            "marina_nome": sol.get("marina_nome"),
            "destinatario_nome": sol.get("solicitante_nome"),
            "destinatario_email": sol.get("solicitante_email"),
            "finalidade": sol.get("finalidade"),
            "canal": "acesso_link",
        }).execute()
    except Exception as e:                                    # noqa: BLE001
        logger.error("Dossie: falha ao registrar saida da solicitacao %s: %s",
                     solicitacao_id, e)
        return HTMLResponse(_render_acesso_page(
            "<p class='msg erro'>Não foi possível registrar a entrega neste momento. "
            "O dossiê não é liberado sem esse registro — tente novamente em instantes.</p>"),
            status_code=503)

    try:
        dados = montar_dados_dossie(ativo_id)
        pdf = gerar_pdf_dossie(dados)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Terceiro (corretor, comprador, seguradora) — é justamente a via em que o
    # documento sai do controle da marina, então é a que MAIS precisa da
    # impressão digital registrada.
    # `sol` vem de `dossie_solicitacoes`, que tem `solicitante_email` — NÃO
    # `destinatario_email`, que é coluna de `dossie_saidas`. O nome errado
    # fazia isto gravar None sempre: a impressão digital do PDF ia para o
    # banco sem identificar quem recebeu, justamente na via em que o
    # documento sai do controle da marina.
    _registrar_emissao(ativo_id, pdf, dados,
                       sol.get("solicitante_email"), "acesso_link")

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="dossie_{ativo_id}.pdf"'},
    )


_ACESSO_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
  <meta name="robots" content="noindex, nofollow" />
  <title>Yachts Atlas — Acesso ao Dossiê</title>
  <style>
    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    body {
      margin: 0; min-height: 100vh; display: flex; align-items: center; justify-content: center;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: radial-gradient(circle at 50% 0%, #021a3d 0%, #010c20 70%);
      color: #fff; padding: 24px;
    }
    .card {
      width: 100%; max-width: 380px; background: rgba(255,255,255,0.02);
      border: 1px solid rgba(255,255,255,0.06); border-radius: 6px;
      padding: 40px 28px; text-align: center; box-shadow: 0 24px 60px rgba(0,0,0,0.5);
    }
    .brand { color: #c5a059; font-weight: 800; letter-spacing: 0.3em; font-size: 13px;
      text-transform: uppercase; margin-bottom: 8px; }
    .sub { color: rgba(255,255,255,0.45); font-size: 11px; letter-spacing: 0.15em;
      text-transform: uppercase; margin-bottom: 32px; }
    h1 { font-size: 18px; font-weight: 600; margin: 0 0 24px; }
    input[type=password] {
      width: 100%; padding: 16px; font-size: 16px; text-align: center; letter-spacing: 0.2em;
      background: #010c20; border: 1px solid rgba(255,255,255,0.12); border-radius: 4px;
      color: #fff; outline: none; margin-bottom: 18px;
    }
    input[type=password]:focus { border-color: #c5a059; }
    button {
      width: 100%; padding: 16px; font-size: 13px; font-weight: 800; letter-spacing: 0.2em;
      text-transform: uppercase; background: #c5a059; color: #010c20; border: 0;
      border-radius: 4px; cursor: pointer;
    }
    button:active { background: #b38f4d; }
    .msg { font-size: 13px; margin: 0 0 18px; padding: 10px; border-radius: 4px; }
    .erro { background: rgba(220,60,60,0.12); color: #ff8a8a; border: 1px solid rgba(220,60,60,0.25); }
    .foot { margin-top: 26px; font-size: 10px; color: rgba(255,255,255,0.3);
      letter-spacing: 0.1em; }
  </style>
</head>
<body>
  <form class="card" method="post" action="">
    <div class="brand">Yachts Atlas</div>
    <div class="sub">Custódia Digital de Ativos Náuticos</div>
    <h1>Acesso ao Dossiê</h1>
    <!--MSG-->
    <input type="password" name="senha" placeholder="Senha de acesso" autocomplete="off"
      inputmode="text" autofocus required />
    <button type="submit">Abrir Dossiê</button>
    <div class="foot">Acesso registrado e auditado.</div>
  </form>
</body>
</html>"""
