"""
Opt-out da prospecção: o "responda SAIR" precisa funcionar de verdade.

Os dois defeitos que estes testes impedem são de sinal oposto, e os dois caros:

  • bloquear DE MENOS — quem pediu para sair recebe de novo, denuncia, e o
    número da prospecção é banido. É o ativo mais frágil da operação;
  • bloquear DE MAIS — "não quero cancelar, quero saber mais" some da lista, e
    a marina se perde exatamente no momento em que ela respondeu.

O endpoint é público (a Evolution chama de fora) e escreve na blocklist, então
o token também é testado: sem ele, qualquer um bloqueia qualquer número.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import whatsapp as wh
from app.core.config import settings

TOKEN = "token-de-teste"


@pytest.fixture
def cliente(monkeypatch):
    """App mínimo só com o webhook, e a blocklist trocada por um registro."""
    monkeypatch.setattr(settings, "WHATSAPP_WEBHOOK_TOKEN", TOKEN, raising=False)

    bloqueados: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "app.services.prospeccao_service.bloquear",
        lambda tel, motivo="": bloqueados.append((tel, motivo)) or True,
    )

    app = FastAPI()
    app.include_router(wh.router, prefix="/whatsapp")
    return TestClient(app), bloqueados


def _evento(texto: str, telefone: str = "5548991234567", from_me: bool = False) -> dict:
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": f"{telefone}@s.whatsapp.net", "fromMe": from_me},
            "message": {"conversation": texto},
        },
    }


# --------------------------------------------------------------------------
# Reconhecer o pedido de saída
# --------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "SAIR", "sair", "  Sair  ", "sair.", "PARAR", "cancelar",
    "remover", "stop", "unsubscribe", "Pare!",
])
def test_pedido_de_saida_entra_na_blocklist(cliente, texto):
    c, bloqueados = cliente
    r = c.post(f"/whatsapp/webhook?token={TOKEN}", json=_evento(texto))
    assert r.status_code == 200
    assert r.json()["acao"] == "opt_out"
    assert bloqueados and bloqueados[0][0] == "5548991234567"


@pytest.mark.parametrize("texto", [
    "não quero cancelar, quero saber mais",
    "vou sair do escritório agora, me liga amanhã",
    "pode parar de me mandar preço, prefiro conversar",
    "Faz sentido sim, vamos conversar",
    "Quanto custa?",
    "",
])
def test_conversa_normal_nao_bloqueia(cliente, texto):
    """
    Bloquear de mais é perder a marina no momento em que ela respondeu.
    Todos estes CONTÊM uma palavra de saída — e nenhum é um pedido de saída.
    """
    c, bloqueados = cliente
    r = c.post(f"/whatsapp/webhook?token={TOKEN}", json=_evento(texto))
    assert r.status_code == 200
    assert r.json()["acao"] == "sem_acao"
    assert bloqueados == []


def test_mensagem_do_proprio_atlas_e_ignorada(cliente):
    """
    O que o Atlas envia volta no webhook. Sem esta guarda, o disparo se
    auto-bloquearia no dia em que o texto contivesse a palavra.
    """
    c, bloqueados = cliente
    r = c.post(f"/whatsapp/webhook?token={TOKEN}", json=_evento("SAIR", from_me=True))
    assert r.json()["acao"] == "ignorado_proprio"
    assert bloqueados == []


# --------------------------------------------------------------------------
# Token: o endpoint é público e escreve na blocklist
# --------------------------------------------------------------------------

def test_sem_token_nao_bloqueia(cliente):
    c, bloqueados = cliente
    r = c.post("/whatsapp/webhook", json=_evento("SAIR"))
    assert r.json()["acao"] == "token_invalido"
    assert bloqueados == []


def test_token_errado_nao_bloqueia(cliente):
    c, bloqueados = cliente
    r = c.post("/whatsapp/webhook?token=chute", json=_evento("SAIR"))
    assert r.json()["acao"] == "token_invalido"
    assert bloqueados == []


def test_sem_segredo_configurado_o_webhook_fica_desligado(cliente, monkeypatch):
    """Vazio = desligado, não aberto. Preferir não receber a aceitar de qualquer um."""
    c, bloqueados = cliente
    monkeypatch.setattr(settings, "WHATSAPP_WEBHOOK_TOKEN", "", raising=False)
    r = c.post(f"/whatsapp/webhook?token={TOKEN}", json=_evento("SAIR"))
    assert r.json()["acao"] == "desligado"
    assert bloqueados == []


# --------------------------------------------------------------------------
# Robustez: webhook que levanta exceção vira reenvio em loop
# --------------------------------------------------------------------------

@pytest.mark.parametrize("corpo", [
    {}, {"data": None}, {"data": []}, {"data": {"key": {}}},
    {"data": {"key": {"remoteJid": "x@s.whatsapp.net"}, "message": {}}},
])
def test_corpo_estranho_responde_200_sem_quebrar(cliente, corpo):
    c, _ = cliente
    r = c.post(f"/whatsapp/webhook?token={TOKEN}", json=corpo)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_texto_em_extendedTextMessage_tambem_vale(cliente):
    """A Evolution usa formatos diferentes conforme o tipo da mensagem."""
    c, bloqueados = cliente
    corpo = {"data": {
        "key": {"remoteJid": "5548991234567@s.whatsapp.net", "fromMe": False},
        "message": {"extendedTextMessage": {"text": "SAIR"}},
    }}
    r = c.post(f"/whatsapp/webhook?token={TOKEN}", json=corpo)
    assert r.json()["acao"] == "opt_out"
    assert bloqueados


# --------------------------------------------------------------------------
# A promessa da mensagem e o código têm que combinar
# --------------------------------------------------------------------------

def test_a_mensagem_promete_a_palavra_que_o_webhook_reconhece():
    """
    Se alguém trocar o texto para "responda PARAR" e o webhook não reconhecer,
    a promessa vira mentira em silêncio — ninguém percebe até a denúncia.
    """
    from app.services.prospeccao_service import MENSAGEM_1
    assert "SAIR" in MENSAGEM_1
    assert wh._quer_sair("SAIR")
