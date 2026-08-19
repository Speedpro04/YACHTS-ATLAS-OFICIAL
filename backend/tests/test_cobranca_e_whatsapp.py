"""
Regressão da régua de cobrança e do envio de WhatsApp.

Os dois defeitos que estes testes existem para impedir são silenciosos — o
sistema não reclama de nenhum dos dois:

  • mandar o mesmo aviso de cobrança duas vezes para um cliente;
  • um telefone mal formatado que a Evolution aceita e nunca entrega.

O primeiro custa credibilidade; o segundo faz a marina ser cortada sem nunca
ter sido avisada.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.core.config import settings
from app.services import cobranca_service
from app.services.cobranca_service import MARCOS_DE_AVISO, avisar, marco_devido
from app.services.whatsapp_service import enviar_whatsapp, normalizar_telefone


# --------------------------------------------------------------------------
# Telefone: o formato que a Evolution exige
# --------------------------------------------------------------------------

@pytest.mark.parametrize("digitado", [
    "(48) 99123-4567",
    "+55 48 99123-4567",
    "55 48 99123 4567",
    "5548991234567",
    "48991234567",
    "048 99123-4567",      # zero de DDD não existe em número internacional
])
def test_telefone_vira_digitos_com_ddi(digitado):
    assert normalizar_telefone(digitado) == "5548991234567"


@pytest.mark.parametrize("invalido", [None, "", "   ", "abc", "12345", "(48)"])
def test_telefone_impossivel_nao_e_enviado(invalido):
    """Melhor não enviar do que entregar na caixa de outra pessoa."""
    assert normalizar_telefone(invalido) is None


def test_sem_provedor_configurado_nao_quebra():
    """WhatsApp desligado é estado normal — o aviso ainda sai por e-mail."""
    assert enviar_whatsapp("48991234567", "oi") is False


# --------------------------------------------------------------------------
# Evolution: o corpo do sendText mudou entre versões
# --------------------------------------------------------------------------

class _ClienteFalso:
    """Dublê do httpx.Client que devolve status combinados, em ordem."""

    def __init__(self, *status):
        self._status = list(status)
        self.corpos = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def post(self, url, json=None, headers=None):
        import httpx
        self.corpos.append(json)
        pedido = httpx.Request("POST", url)
        return httpx.Response(self._status.pop(0), request=pedido)


@pytest.fixture
def evolution_falsa(monkeypatch):
    monkeypatch.setattr(settings, "WHATSAPP_PROVIDER", "evolution")
    monkeypatch.setattr(settings, "EVOLUTION_BASE_URL", "https://whatsapp.exemplo.online")
    monkeypatch.setattr(settings, "EVOLUTION_API_KEY", "chave-de-teste")
    monkeypatch.setattr(settings, "EVOLUTION_INSTANCE", "Programa-Atlas")

    def instalar(*status):
        cliente = _ClienteFalso(*status)
        monkeypatch.setattr(
            "app.services.whatsapp_service.httpx.Client", lambda **kw: cliente
        )
        return cliente

    return instalar


def test_formato_novo_e_o_primeiro_tentado(evolution_falsa):
    cliente = evolution_falsa(200)

    assert enviar_whatsapp("5512978138934", "oi") is True
    assert cliente.corpos == [{"number": "5512978138934", "text": "oi"}]


def test_corpo_recusado_cai_no_formato_antigo(evolution_falsa):
    """Uma build que só aceita o formato v1 responde 400 e não manda nada."""
    cliente = evolution_falsa(400, 200)

    assert enviar_whatsapp("5512978138934", "oi") is True
    assert cliente.corpos[1] == {"number": "5512978138934", "textMessage": {"text": "oi"}}


@pytest.mark.parametrize("status", [401, 404])
def test_chave_ou_instancia_errada_nao_tenta_o_outro_formato(evolution_falsa, status):
    """Trocar o corpo não conserta chave inválida — insistir só esconde o erro real."""
    cliente = evolution_falsa(status, 200)

    assert enviar_whatsapp("5512978138934", "oi") is False
    assert len(cliente.corpos) == 1


# --------------------------------------------------------------------------
# Régua: qual aviso mandar, e uma vez só
# --------------------------------------------------------------------------

def test_primeiro_dia_dispara_o_aviso_zero():
    assert marco_devido(0, []) == 0


def test_rodar_de_novo_no_mesmo_dia_nao_reenvia():
    """O defeito clássico da régua: cliente recebendo cobrança em duplicidade."""
    assert marco_devido(0, [0]) is None
    assert marco_devido(9, [0, 7]) is None


def test_entre_marcos_nao_manda_nada():
    assert marco_devido(3, [0]) is None


def test_dia_seguinte_ao_marco_ainda_recupera_o_aviso():
    """
    Se o cron falhar no dia 7, o aviso sai no dia 8 — não some.

    Uma régua com janela exata ('faltam exatamente 7 dias') perde o aviso para
    sempre quando a rotina não roda naquele dia.
    """
    assert marco_devido(8, [0]) == 7


def test_rotina_parada_manda_so_o_aviso_mais_recente():
    """Três dias parada não pode virar três e-mails de uma vez na caixa dela."""
    assert marco_devido(22, [0, 7, 15]) == 20


def test_quem_nunca_foi_avisado_recebe_o_marco_atual():
    assert marco_devido(25, []) == max(MARCOS_DE_AVISO)


def test_sem_atraso_nao_ha_o_que_avisar():
    assert marco_devido(None, []) is None
    assert marco_devido(-1, []) is None


# --------------------------------------------------------------------------
# O envio registra o que saiu
# --------------------------------------------------------------------------

@pytest.fixture
def envio_falso(monkeypatch):
    registro = {"emails": [], "whatsapps": [], "metadata": []}

    monkeypatch.setattr(
        "app.services.email_service.send_email",
        lambda to, subject, html, text=None: registro["emails"].append((to, subject)) or True,
    )
    monkeypatch.setattr(
        "app.services.whatsapp_service.enviar_whatsapp",
        lambda tel, texto: registro["whatsapps"].append((tel, texto)) or True,
    )
    monkeypatch.setattr(
        "app.services.stripe_service.StripeService._atualizar_metadata",
        staticmethod(lambda uid, mudancas, preservar=(): registro["metadata"].append(mudancas)),
    )
    return registro


def _marina_devendo():
    return {
        "email": "marina@exemplo.com",
        "nome": "Marina Teste",
        "telefone": "(48) 99123-4567",
        "fatura_url": "https://invoice.stripe.com/i/abc",
        "pagamento": "pago",
    }


def test_aviso_sai_pelos_dois_canais_e_fica_registrado(envio_falso):
    assert avisar("user-1", _marina_devendo(), 0) is True

    assert envio_falso["emails"] and envio_falso["whatsapps"]
    assert envio_falso["metadata"] == [{cobranca_service.CHAVE_AVISOS: [0]}]


def test_registro_preserva_os_avisos_anteriores(envio_falso):
    """Sobrescrever a lista faria a régua reenviar tudo na execução seguinte."""
    metadata = _marina_devendo() | {cobranca_service.CHAVE_AVISOS: [0, 7]}

    avisar("user-1", metadata, 15)

    assert envio_falso["metadata"] == [{cobranca_service.CHAVE_AVISOS: [0, 7, 15]}]


def test_aviso_do_corte_leva_o_link_da_fatura(envio_falso):
    """Link de checkout criaria uma segunda assinatura em vez de quitar a dívida."""
    avisar("user-1", _marina_devendo(), settings.DIAS_ATE_CORTE_INADIMPLENCIA)

    _, texto = envio_falso["whatsapps"][0]
    assert "https://invoice.stripe.com/i/abc" in texto
    assert "suspenso" in texto.lower()


def test_marina_sem_telefone_ainda_recebe_o_e_mail(envio_falso):
    metadata = _marina_devendo()
    metadata["telefone"] = None

    assert avisar("user-1", metadata, 7) is True
    assert envio_falso["emails"]


# --------------------------------------------------------------------------
# Avisos do fundador: WhatsApp e e-mail, e só
# --------------------------------------------------------------------------

def test_aviso_do_fundador_sai_pelos_dois_canais(envio_falso, monkeypatch):
    """
    Redundância proposital: saber que uma marina parou de pagar não pode
    depender de um único canal estar de pé naquele dia.
    """
    from app.services.notify_service import notificar_fundador

    monkeypatch.setattr(settings, "ALERTA_WHATSAPP", "48991234567")
    monkeypatch.setattr(settings, "ALERTA_EMAIL", "fundador@exemplo.com")

    assert notificar_fundador("Falha no pagamento", "Assinatura sub_123.") is True

    assert envio_falso["whatsapps"][0][0] == "48991234567"
    assert envio_falso["emails"][0] == ("fundador@exemplo.com", "Falha no pagamento")


def test_sem_canal_configurado_o_aviso_nao_derruba_o_fluxo(monkeypatch):
    """O pagamento já aconteceu — falhar em avisar não pode levantar exceção."""
    from app.services.notify_service import notificar_fundador

    monkeypatch.setattr(settings, "ALERTA_WHATSAPP", "")
    monkeypatch.setattr(settings, "ALERTA_EMAIL", "")
    monkeypatch.setattr(settings, "EMAIL_SENDER", "")

    assert notificar_fundador("Qualquer coisa", "corpo") is False
