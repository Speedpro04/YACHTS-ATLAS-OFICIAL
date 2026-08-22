"""
Trava de rede para a suíte de testes.

Por que existe
--------------
Em 22/08/2026 a suíte mandou WhatsApp DE VERDADE três vezes, em ocasiões
diferentes, para números reais — uma delas para um terceiro que não tem nada a
ver com o Atlas. Todas pelo mesmo motivo: o teste dependia de o ambiente estar
mal configurado para não enviar. No dia em que o `.env` local ganhou credencial
boa, os testes começaram a falar com gente de verdade.

Tapar buraco por buraco não funciona. Cada teste novo que tocar um serviço de
envio é uma chance de esquecer o dublê, e a falha só aparece quando alguém
recebe a mensagem — quando já é tarde.

O que esta trava faz
--------------------
Bloqueia, para TODOS os testes, qualquer saída de rede real: httpx (Evolution,
Stripe, Supabase, OpenAI), requests e SMTP. Teste que tentar sair da máquina
falha com uma mensagem dizendo o que fazer, em vez de entregar a um estranho.

O custo do descuido é assimétrico: um teste que não roda é um teste que se
conserta; uma mensagem enviada em nome da empresa não se desfaz.

Como testar código que faz rede
-------------------------------
Use um dublê explícito — `monkeypatch.setattr(...)` sobre a função de envio, ou
o fixture `envio_falso` em `test_cobranca_e_whatsapp.py`. Se precisar mesmo de
rede (nunca deveria, num teste de unidade), marque com
`@pytest.mark.usa_rede_de_verdade` e assuma o que isso significa.
"""
from __future__ import annotations

import pytest


class RedeBloqueadaNoTeste(RuntimeError):
    """Levantada quando um teste tenta sair para a rede sem dublê."""


_AVISO = (
    "\n\n"
    "  ===================================================================\n"
    "  TESTE TENTOU USAR A REDE DE VERDADE — bloqueado por tests/conftest.py\n"
    "  ===================================================================\n"
    "  Chamada: {alvo}\n\n"
    "  Isto existe porque a suite ja enviou WhatsApp real para numeros de\n"
    "  terceiros. Um teste que nao roda se conserta; uma mensagem enviada\n"
    "  em nome da empresa, nao.\n\n"
    "  Use um duble:  monkeypatch.setattr('modulo.funcao', lambda ...: ...)\n"
    "  Ou o fixture `envio_falso` de test_cobranca_e_whatsapp.py\n"
)


def _barra(alvo: str):
    def _proibido(*_args, **_kwargs):
        raise RedeBloqueadaNoTeste(_AVISO.format(alvo=alvo))
    return _proibido


@pytest.fixture(autouse=True)
def sem_rede_de_verdade(request, monkeypatch):
    """Ativa em todo teste. Escapa só quem pedir explicitamente."""
    if request.node.get_closest_marker("usa_rede_de_verdade"):
        return

    # httpx — Evolution, Stripe, Supabase e OpenAI passam por aqui.
    #
    # Barra o TRANSPORTE, não o cliente. O TestClient do FastAPI também é
    # httpx, mas fala com a aplicação em memória por um ASGITransport e nunca
    # toca a rede — bloquear `Client.request` derrubaria todo teste de
    # endpoint, que é justamente o que a gente quer poder escrever.
    #
    # HTTPTransport é o único caminho que abre socket de verdade.
    try:
        import httpx
        monkeypatch.setattr(httpx.HTTPTransport, "handle_request",
                            _barra("httpx (rede real)"), raising=False)
        monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request",
                            _barra("httpx async (rede real)"), raising=False)
    except ImportError:
        pass

    # requests — caso alguma dependência use.
    try:
        import requests
        monkeypatch.setattr(requests.sessions.Session, "request",
                            _barra("requests.Session.request"), raising=False)
    except ImportError:
        pass

    # SMTP — o caminho do e-mail.
    try:
        import smtplib
        for classe in ("SMTP", "SMTP_SSL"):
            monkeypatch.setattr(getattr(smtplib, classe), "__init__",
                                _barra(f"smtplib.{classe}"), raising=False)
    except ImportError:
        pass


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "usa_rede_de_verdade: libera a trava de rede para este teste. "
        "Usar só quando não houver alternativa, e sabendo que ele pode "
        "enviar mensagem de verdade.",
    )
