"""
Emitir dossiê é ato de computador — e ler continua sendo de qualquer tela.

A trava vale para os dois atos que EMITEM (o PDF do painel e a liberação de um
pedido de terceiro). O que o comprador usa — pedir pelo formulário e abrir o link
recebido — tem que continuar funcionando no celular, senão a entrega quebra.
"""
import pytest

from app.core.dispositivo import e_aparelho_de_mao


CELULARES = [
    # iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    # Android
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36",
    # iPad — tablet também não emite
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]

COMPUTADORES = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Firefox/121.0",
]


@pytest.mark.parametrize("ua", CELULARES)
def test_celular_e_tablet_sao_reconhecidos(ua):
    assert e_aparelho_de_mao(ua) is True


@pytest.mark.parametrize("ua", COMPUTADORES)
def test_computador_passa(ua):
    assert e_aparelho_de_mao(ua) is False


def test_user_agent_ausente_nao_bloqueia():
    # Sem cabeçalho não dá para afirmar que é celular, e a trava é política de
    # uso, não autenticação: na dúvida, deixa passar e o resto do fluxo decide.
    assert e_aparelho_de_mao("") is False
    assert e_aparelho_de_mao(None) is False


def test_so_as_rotas_de_emissao_exigem_desktop():
    """As duas que emitem exigem; as do comprador, não.

    Escrito contra a rota, e não contra a intenção: é fácil alguém mais tarde
    'proteger tudo' e derrubar o acesso do comprador, que lê no celular.
    """
    from app.api.v1 import dossie
    from app.core.dispositivo import exigir_desktop

    def exige(caminho: str, metodo: str) -> bool:
        for rota in dossie.router.routes:
            if rota.path == caminho and metodo in rota.methods:
                return any(
                    getattr(d.call, "__name__", "") == exigir_desktop.__name__
                    for d in rota.dependant.dependencies
                )
        raise AssertionError(f"rota não encontrada: {metodo} {caminho}")

    assert exige("/{ativo_id}/pdf", "GET") is True
    assert exige("/solicitacoes/{solicitacao_id}/liberar", "POST") is True

    # O comprador: pede de onde estiver e abre o link no telefone.
    assert exige("/solicitar", "POST") is False
    assert exige("/acesso/{solicitacao_id}", "GET") is False
