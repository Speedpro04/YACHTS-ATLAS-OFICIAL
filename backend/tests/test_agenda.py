"""
Regressão da agenda interna — a régua de cobrança que roda sozinha.

Ela substitui um cron externo, e o motivo é a falha silenciosa: cron some numa
migração de servidor, quebra quando o caminho do Python muda, para quando
alguém recria o container. Ninguém percebe, porque não avisar é
indistinguível de "não havia ninguém devendo" — e o erro aparece na conversa
mais cara possível: a marina cortada dizendo que nunca foi avisada.

Trazer isso para dentro da aplicação cria riscos próprios, e são eles que
estes testes guardam:

  • a agenda não pode derrubar a aplicação (quem paga continua usando o
    sistema mesmo se a cobrança falhar);
  • não pode reprocessar a cada reinício, senão dia de deploy vira varredura
    repetida;
  • e não pode DEIXAR de rodar por causa de cache indisponível — repetir custa
    uma consulta, não rodar custa uma marina cortada sem aviso.
"""
import asyncio
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.services import agenda


def test_iniciar_fora_de_event_loop_nao_quebra():
    """Import em script ou teste não pode explodir nem deixar coroutine solta."""
    agenda.parar()
    agenda.iniciar()          # sem loop rodando
    assert agenda._tarefa is None


def test_iniciar_dentro_do_loop_liga_a_tarefa():
    async def cenario():
        agenda.iniciar()
        ligada = agenda._tarefa is not None and not agenda._tarefa.done()
        agenda.parar()
        return ligada
    assert asyncio.run(cenario())


def test_iniciar_duas_vezes_nao_duplica():
    """Dois startups (recarga do servidor de dev) não podem virar duas réguas."""
    async def cenario():
        agenda.parar()
        agenda.iniciar()
        primeira = agenda._tarefa
        agenda.iniciar()
        mesma = agenda._tarefa is primeira
        agenda.parar()
        return mesma
    assert asyncio.run(cenario())


def test_sem_cache_a_regua_roda(monkeypatch):
    """
    Cache fora do ar não pode calar a cobrança.

    Preferir rodar de novo a não rodar: repetir custa uma consulta; não rodar
    custa uma marina cortada sem nunca ter sido avisada.
    """
    import app.core.cache as cache
    monkeypatch.setattr(cache, "get_client", lambda: None)
    assert agenda._ja_rodou_hoje() is False


def test_marca_do_dia_evita_reprocessar(monkeypatch):
    """Em dia de deploy o container sobe várias vezes; a régua roda uma."""
    guardado = {}
    monkeypatch.setattr(
        "app.core.cache.cache_set_json",
        lambda k, v, ttl=None: guardado.__setitem__(k, v),
    )
    monkeypatch.setattr(
        "app.core.cache.cache_get_json",
        lambda k: guardado.get(k),
    )
    agenda._marcar_rodado()
    assert agenda._ja_rodou_hoje() is True


def test_falha_da_regua_nao_derruba_a_aplicacao(monkeypatch):
    """
    O laço engole o erro e segue.

    Aviso de cobrança que falha não pode tirar do ar o painel de quem está em
    dia — a régua é acessória; o sistema é o produto.
    """
    def explode():
        raise RuntimeError("banco fora do ar")

    monkeypatch.setattr(agenda, "_processar", explode)
    monkeypatch.setattr(agenda, "_ja_rodou_hoje", lambda: False)
    monkeypatch.setattr(agenda, "_ESPERA_INICIAL", 0)

    async def cenario():
        tarefa = asyncio.create_task(agenda._laco())
        await asyncio.sleep(0.15)      # deixa a primeira volta acontecer
        viva = not tarefa.done()       # sobreviveu ao erro
        tarefa.cancel()
        return viva

    assert asyncio.run(cenario())


def test_corte_nao_depende_da_agenda():
    """
    Lembrete executável: quem corta é o porteiro, na leitura.

    Se alguém um dia mover o corte para cá, a régua vira caminho crítico — e
    uma falha dela passaria a cortar (ou deixar de cortar) marina por engano.
    """
    import inspect
    fonte = inspect.getsource(agenda)
    assert "processar_inadimplentes" in fonte
    assert "suspender" not in fonte.lower()
    assert "cortar" not in fonte.lower()
