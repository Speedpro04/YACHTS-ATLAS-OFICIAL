"""
A trava de rede da suíte precisa realmente travar.

Rede de segurança que não funciona é pior que nenhuma: dá a sensação de estar
protegido enquanto os testes continuam falando com números reais. Foi o que
aconteceu três vezes em 22/08/2026.
"""
import pytest

# RuntimeError, e não a classe importada do conftest: dependendo de como o
# pytest carrega o arquivo, `tests.conftest` e `conftest` viram dois módulos
# diferentes, e o `pytest.raises` não reconheceria a exceção como a mesma.
# RedeBloqueadaNoTeste herda de RuntimeError justamente para isto.
BLOQUEIO = RuntimeError


def test_httpx_nao_sai_para_a_rede():
    """Qualquer chamada de verdade tem que falhar, não sair."""
    import httpx
    with pytest.raises(BLOQUEIO, match='rede de verdade|rede real|TESTE TENTOU'):
        httpx.get("https://example.com", timeout=5)


def test_whatsapp_nao_consegue_enviar_de_verdade():
    """
    O caminho exato que enviou mensagem para número real. Ele não pode mais
    chegar na Evolution nem com credencial válida no ambiente.
    """
    from app.services.whatsapp_service import _envia_evolution
    with pytest.raises(BLOQUEIO, match='rede de verdade|rede real|TESTE TENTOU'):
        _envia_evolution("5548991234567", "teste", "Programa-Atlas", "chave")


def test_smtp_nao_conecta():
    import smtplib
    with pytest.raises(BLOQUEIO, match='rede de verdade|rede real|TESTE TENTOU'):
        smtplib.SMTP_SSL("smtp.exemplo.com", 465)


def test_testclient_continua_funcionando():
    """
    A trava barra o TRANSPORTE, não o cliente. Teste de endpoint usa httpx por
    dentro e fala com a app em memória — se isto quebrar, a trava está ampla
    demais e ninguém mais consegue testar rota nenhuma.
    """
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    assert TestClient(app).get("/ping").json() == {"ok": True}
