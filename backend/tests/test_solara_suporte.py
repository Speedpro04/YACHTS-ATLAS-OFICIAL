"""
Regressão do suporte de produto da Capitã Solara.

Ela sempre soube normas. Agora também sabe COMO USAR o Yachts Atlas — e essa
segunda perna tem dois jeitos silenciosos de quebrar:

  • o conhecimento do produto envelhecer sem ninguém notar, e a Solara passar
    a descrever com convicção uma tela que não existe mais;
  • a porta de escopo abrir demais, e ela responder qualquer assunto — o que
    destrói justamente a credibilidade que a torna útil.

O primeiro é o mais perigoso porque erra em silêncio: ninguém revisa o que a
IA respondeu para uma marina.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.services import conhecimento_produto as cp
from app.services.chatbot_guardrails import SYSTEM_PROMPT, parece_duvida_de_produto


# --------------------------------------------------------------------------
# O conhecimento não pode envelhecer
# --------------------------------------------------------------------------

def test_conhecimento_esta_em_dia_com_o_codigo():
    """
    O JSON versionado precisa refletir os arquivos de configuração ATUAIS.

    A imagem de produção não leva o frontend, então o conhecimento é extraído
    aqui e commitado. Sem este teste, mudar uma categoria e esquecer de
    regenerar faria a Solara ensinar uma tela que não existe — com toda a
    convicção, e sem ninguém perceber.

    Quebrou?  python -m app.services.conhecimento_produto
    """
    assert cp.extrair_do_frontend() == cp.carregar(), (
        "Conhecimento do produto desatualizado. Regenere com: "
        "python -m app.services.conhecimento_produto"
    )


def test_categorias_de_foto_batem_com_o_painel():
    dados = cp.carregar()
    cats = {c["key"] for c in dados["fotos"]["categorias"]}
    # Duas que nasceram da revisão do painel: o barco por fora e a condição
    # estrutural do casco, que antes dividiam o mesmo balde.
    assert {"embarcacao", "casco_exterior"} <= cats
    assert dados["fotos"]["max_fotos"] > 0


def test_prompt_carrega_o_conhecimento():
    assert "COMO O YACHTS ATLAS FUNCIONA" in SYSTEM_PROMPT
    # Um rótulo real e um fluxo real — se sumirem, o bloco veio vazio.
    assert "Integridade do Casco" in SYSTEM_PROMPT
    assert "Dar acesso ao proprietário" in SYSTEM_PROMPT


def test_prompt_proibe_inventar_tela():
    """A regra que impede o pior erro: mandar clicar num menu que não existe."""
    assert "1-B." in SYSTEM_PROMPT
    assert "não estiver lá" in SYSTEM_PROMPT


def test_solara_sem_conhecimento_ainda_atende_normas(monkeypatch):
    """
    Se o arquivo gerado sumir, ela degrada — não cai.

    Perder o suporte de produto é um chamado; perder a Solara inteira é o
    painel sem assistente nenhum.
    """
    from app.services import chatbot_guardrails as g
    monkeypatch.setattr(cp, "carregar", lambda: {})
    prompt = g._com_produto("PROMPT BASE")
    assert prompt == "PROMPT BASE"


# --------------------------------------------------------------------------
# A porta de escopo: nem fechada demais, nem aberta demais
# --------------------------------------------------------------------------

@pytest.mark.parametrize("pergunta", [
    "onde coloco a foto do casco?",
    "como eu gero o dossiê?",
    "não consigo cadastrar a embarcação",
    "em que aba fica a manutenção?",
    "como dou acesso ao proprietário do barco?",
    "onde clico para selar o registro?",
    "não acho a tela de fotos",
    "qual campo preencho com o horímetro?",
])
def test_duvida_de_produto_passa(pergunta):
    """Sem isto, a pergunta morre na busca por normas — não casa com nenhuma."""
    assert parece_duvida_de_produto(pergunta)


@pytest.mark.parametrize("pergunta", [
    "qual a capital da França?",
    "me conte uma piada",
    "como está o tempo hoje?",
    "como faço um bolo de cenoura?",
    "quem vai ganhar o campeonato?",
])
def test_assunto_alheio_continua_barrado(pergunta):
    """
    Repare que "como faço um bolo" tem a forma de pergunta de caminho.

    É por isso que a detecção exige as DUAS coisas — a forma E uma palavra do
    produto. Só o "como" abriria a porta para o mundo inteiro.
    """
    assert not parece_duvida_de_produto(pergunta)


@pytest.mark.parametrize("pergunta", [
    "o que diz a NORMAM-211 sobre colete salva-vidas?",
    "qual a validade da bateria da EPIRB?",
    "preciso de AIS na minha lancha?",
])
def test_pergunta_de_norma_segue_pelo_rag(pergunta):
    """Norma tem fonte própria; desviá-la para o produto perderia a citação."""
    assert not parece_duvida_de_produto(pergunta)


def test_mencao_a_barco_sozinha_nao_basta():
    """
    "Quanto custa um barco novo?" fala de barco e tem forma de pergunta — mas
    não é sobre o sistema. Deixar passar seria a Solara opinando sobre preço
    de mercado, que ela não sabe e não deve.
    """
    assert not parece_duvida_de_produto("quanto custa um barco novo?")
    assert not parece_duvida_de_produto("meu barco é bonito")
