# -*- coding: utf-8 -*-
"""
O e-mail de 1º toque da indicação.

Até aqui a marina indicada só recebia WhatsApp. O e-mail existe agora, e o que
precisa continuar verdadeiro é o que este arquivo cobra:

  1. ele só fala com quem está marcado 'pendente' — as dez linhas antigas da
     tabela são lead de teste e ensaio, e um lote descuidado escreveria para
     todas de uma vez;
  2. `dry_run` não manda nada, nem por e-mail. É o ensaio que existe para
     alguém LER o texto antes de ele sair;
  3. o texto cumpre a mesma disciplina do WhatsApp: sem preço, com saída.
"""
import pytest

from app.services import prospeccao_service as prosp


# --- o texto ---------------------------------------------------------------

def test_o_assunto_carrega_quem_indicou():
    """É a única coisa na mensagem que a marina reconhece."""
    assunto, _, _ = prosp.montar_email("Pedro Simon", "Marina Bento", "Marina Sul")
    assert "Marina Bento" in assunto
    assert "Marina Sul" in assunto


def test_espaco_sobrando_no_nome_nao_atravessa():
    """O mesmo espaço que quebra o negrito do WhatsApp sujaria o assunto."""
    assunto, html, texto = prosp.montar_email("Pedro", "Marina Portugal ", " Marina Sul")
    # O espaco sobrando vira espaco DOBRADO no meio da frase — e, no HTML,
    # encosta na tag: e assim que ele aparece.
    assert "  " not in assunto
    assert "  " not in texto
    assert "Marina Portugal indicou a Marina Sul" in assunto
    assert "Marina Portugal</strong>" in html


def test_a_saida_esta_escrita():
    """Prometer saída é o que separa abordagem de denúncia — e denúncia é o
    que queima o domínio, do mesmo jeito que queima o número."""
    _, html, texto = prosp.montar_email("Pedro", "Marina Bento", "Marina Sul")
    assert "SAIR" in texto
    assert "SAIR" in html


def test_o_primeiro_toque_nao_abre_preco():
    """Número no primeiro contato encerra a conversa antes de existir valor.
    A regra é a mesma do WhatsApp; aqui ela também vale."""
    _, html, texto = prosp.montar_email("Pedro", "Marina Bento", "Marina Sul")
    for proibido in ("250", "200", "R$", "US$", "mensalidade"):
        assert proibido not in texto, f"o texto abriu preço: {proibido}"
        assert proibido not in html, f"o html abriu preço: {proibido}"


def test_nao_promete_certificado_da_embarcacao():
    """O Atlas certifica a INTEGRIDADE do registro, não o estado do barco —
    inspecionar embarcação é atribuição de órgão competente."""
    _, _, texto = prosp.montar_email("Pedro", "Marina Bento", "Marina Sul")
    assert "certificad" not in texto.lower()
    assert "selo de integridade" in texto.lower()


# --- o disparo -------------------------------------------------------------

class _Consulta:
    def __init__(self, linhas):
        self.linhas = linhas
        self.filtros = []

    def select(self, *a, **k):
        return self

    def or_(self, expressao):
        self.filtros.append(expressao)
        return self

    def lte(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def update(self, dados):
        self.atualizacoes.append(dados)
        return self

    def execute(self):
        return type("R", (), {"data": self.linhas})()


class _Banco:
    def __init__(self, linhas):
        self.consulta = _Consulta(linhas)
        self.consulta.atualizacoes = []

    def table(self, _nome):
        return self.consulta


@pytest.fixture
def lead_pronto():
    return [{
        "id": "abc", "marina_name": "Marina Sul", "contact_name": "Pedro Simon",
        "whatsapp": "5512999999999", "source": "Marina Bento",
        "email": "pedro@exemplo.com", "email_status": "pendente",
        "whatsapp_status": "nao_enviar",
    }]


def test_ensaio_nao_manda_email(monkeypatch, lead_pronto):
    enviados = []
    monkeypatch.setattr(prosp, "get_supabase_admin", lambda: _Banco(lead_pronto))
    monkeypatch.setattr(
        "app.services.email_service.send_email",
        lambda *a, **k: enviados.append(a) or True,
    )

    resumo = prosp.disparar_lote(dry_run=True)

    assert enviados == [], "o dry run mandou e-mail de verdade"
    assert resumo["emails"] == 1
    assert resumo["amostra_email"]["para"] == "pedro@exemplo.com"


def test_quem_nao_esta_pendente_nao_recebe(monkeypatch):
    """A linha marcada 'nao_enviar' é lead de teste. Ela não pode sair no lote
    só porque o e-mail passou a existir."""
    antigo = [{
        "id": "velho", "marina_name": "Marina de Teste", "contact_name": "Fulano",
        "whatsapp": "5512999999999", "source": "Marina X",
        "email": "teste@exemplo.com", "email_status": "nao_enviar",
        "whatsapp_status": "nao_enviar",
    }]
    enviados = []
    monkeypatch.setattr(prosp, "get_supabase_admin", lambda: _Banco(antigo))
    monkeypatch.setattr(
        "app.services.email_service.send_email",
        lambda *a, **k: enviados.append(a) or True,
    )

    resumo = prosp.disparar_lote(dry_run=False)

    assert enviados == []
    assert resumo["emails"] == 0


def test_a_fila_pergunta_pelos_dois_canais(monkeypatch, lead_pronto):
    """Se a consulta voltar a filtrar só por WhatsApp, o lead que já recebeu a
    mensagem nunca receberia o e-mail — e vice-versa."""
    banco = _Banco(lead_pronto)
    monkeypatch.setattr(prosp, "get_supabase_admin", lambda: banco)
    monkeypatch.setattr("app.services.email_service.send_email", lambda *a, **k: True)

    prosp.disparar_lote(dry_run=True)

    assert any("email_status.eq.pendente" in f for f in banco.consulta.filtros)
    assert any("whatsapp_status.eq.pendente" in f for f in banco.consulta.filtros)
