"""
O limitador de taxa é lógica de segurança: se ele falhar aberto, ninguém
percebe até alguém abusar. Estes testes existem para que "sem Redis" nunca
volte a significar "sem limite" — que foi exatamente o defeito encontrado em
24/08/2026, quando o único limitador do sistema (o do chatbot) devolvia True
sempre que o Redis faltava, e produção nunca teve Redis.
"""
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core import limite_taxa
from app.core.limite_taxa import limite, permitido


@pytest.fixture(autouse=True)
def _memoria_limpa(monkeypatch):
    """Cada teste começa com o balde vazio e SEM Redis.

    Sem Redis de propósito: é a configuração de produção hoje, e é justamente
    a que estava desprotegida.
    """
    limite_taxa._memoria.clear()
    monkeypatch.setattr(limite_taxa, "get_redis", lambda: None)
    yield
    limite_taxa._memoria.clear()


def test_deixa_passar_ate_o_teto_e_barra_o_seguinte():
    for i in range(5):
        assert permitido("k", 5, 60) is True, f"barrou na tentativa {i + 1}"
    assert permitido("k", 5, 60) is False


def test_sem_redis_ainda_limita():
    """O coração do defeito antigo: sem Redis, limitava zero."""
    assert limite_taxa.get_redis() is None
    for _ in range(3):
        permitido("sem-redis", 3, 60)
    assert permitido("sem-redis", 3, 60) is False


def test_chaves_diferentes_nao_se_atrapalham():
    for _ in range(5):
        permitido("form_indicacao:1.1.1.1", 5, 60)
    assert permitido("form_indicacao:1.1.1.1", 5, 60) is False
    # Outro IP, e o mesmo IP em outro formulário, seguem livres.
    assert permitido("form_indicacao:2.2.2.2", 5, 60) is True
    assert permitido("form_dossie:1.1.1.1", 5, 60) is True


def test_a_janela_desliza(monkeypatch):
    agora = [1000.0]
    monkeypatch.setattr(limite_taxa.time, "monotonic", lambda: agora[0])

    for _ in range(3):
        assert permitido("j", 3, 60) is True
    assert permitido("j", 3, 60) is False

    agora[0] += 61  # a janela venceu
    assert permitido("j", 3, 60) is True, "deveria liberar depois da janela"


def test_nao_cresce_sem_limite_com_ip_variando(monkeypatch):
    """Atacante trocando de IP não pode virar vazamento de memória."""
    monkeypatch.setattr(limite_taxa, "_MAX_CHAVES", 50)
    for i in range(500):
        permitido(f"ip-{i}", 5, 60)
    assert len(limite_taxa._memoria) <= 50


def test_redis_quebrado_cai_na_memoria_em_vez_de_liberar(monkeypatch):
    class RedisQuebrado:
        def incr(self, *a, **k):
            raise RuntimeError("conexao caiu")

    monkeypatch.setattr(limite_taxa, "get_redis", lambda: RedisQuebrado())
    for _ in range(2):
        assert permitido("degrada", 2, 60) is True
    assert permitido("degrada", 2, 60) is False, "Redis caindo nao pode abrir o portao"


def test_endpoint_responde_429_com_retry_after():
    app = FastAPI()

    @app.post("/porta", dependencies=[Depends(limite("porta", 2, 60))])
    async def porta():
        return {"ok": True}

    cliente = TestClient(app)
    assert cliente.post("/porta").status_code == 200
    assert cliente.post("/porta").status_code == 200

    r = cliente.post("/porta")
    assert r.status_code == 429
    assert r.headers.get("Retry-After") == "60"


def test_ip_vem_do_proxy_e_nao_do_container():
    """Atrás do nginx, todo mundo chega com o mesmo IP interno.

    Sem ler o X-Forwarded-For, o limitador trataria o mundo inteiro como um
    visitante só e bloquearia todos ao primeiro abuso.
    """
    app = FastAPI()

    @app.post("/p", dependencies=[Depends(limite("p", 1, 60))])
    async def p():
        return {"ok": True}

    cliente = TestClient(app)
    a = {"X-Forwarded-For": "203.0.113.10"}
    b = {"X-Forwarded-For": "203.0.113.99"}

    assert cliente.post("/p", headers=a).status_code == 200
    assert cliente.post("/p", headers=a).status_code == 429
    # Visitante diferente não pode pagar pelo abuso do primeiro.
    assert cliente.post("/p", headers=b).status_code == 200
