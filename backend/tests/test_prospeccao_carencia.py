"""
A carência é a janela em que um lead errado ainda pode ser tirado da fila
antes de virar mensagem. Mensagem enviada não volta; lead na fila, sim.

Estes testes existem porque em 24/08/2026 sete leads de teste ficaram em fila
de prospecção — um deles apontando para 5555978138934, um número no Rio Grande
do Sul que ninguém digitou. Se o disparo estivesse ligado naquele dia, um
estranho teria recebido abordagem comercial do Yachts Atlas.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.core.config import settings
from app.services import prospeccao_service as ps


def test_carencia_padrao_vem_da_configuracao():
    """Trocar 5 por 30 tem de ser variável de ambiente, não deploy."""
    limite = ps._limite_de_carencia(None)
    esperado = datetime.now(timezone.utc) - timedelta(
        minutes=settings.PROSPECCAO_CARENCIA_MINUTOS
    )
    calculado = datetime.fromisoformat(limite)
    assert abs((calculado - esperado).total_seconds()) < 5


def test_carencia_maior_recua_mais_no_tempo():
    cedo = datetime.fromisoformat(ps._limite_de_carencia(5))
    tarde = datetime.fromisoformat(ps._limite_de_carencia(30))
    # 30 min de carência exige lead MAIS ANTIGO que 5 min de carência.
    assert tarde < cedo
    assert abs((cedo - tarde).total_seconds() - 25 * 60) < 5


def test_carencia_zero_nao_vira_futuro():
    """Zero libera na hora, mas o limite não pode passar do agora.

    Um limite no futuro pegaria leads que ainda nem foram criados — e um
    valor negativo por engano na variável de ambiente faria exatamente isso.
    """
    # O "agora" de referência vem DEPOIS da chamada: a função calcula o dela
    # no momento em que roda, e capturar antes faria o teste falhar por
    # microssegundos — o que já aconteceu ao escrever isto.
    zero = datetime.fromisoformat(ps._limite_de_carencia(0))
    negativo = datetime.fromisoformat(ps._limite_de_carencia(-99))
    depois = datetime.now(timezone.utc)
    assert zero <= depois
    assert negativo <= depois


def test_desligada_por_padrao():
    """Deploy não pode começar a abordar gente sozinho."""
    assert settings.PROSPECCAO_AUTOMATICA is False, (
        "PROSPECCAO_AUTOMATICA deve começar desligada: é a única rotina que "
        "fala com quem nunca pediu contato"
    )


def test_mensagem_tem_o_link_e_a_saida():
    texto = ps.montar_mensagem("Ana Paula Souza", "Marina Esperanza", "Marina Alfa")
    assert "https://yachtsatlas.online" in texto
    assert "SAIR" in texto, "prometer saída é o que evita a denúncia que bane o número"
    assert "Ana" in texto and "Souza" not in texto, "trata pelo primeiro nome"
    assert "Marina Esperanza" in texto


def test_mensagem_nao_promete_certificacao_do_ativo():
    """O Atlas não inspeciona embarcação.

    Prometer "dossiê certificado" numa mensagem comercial é promessa que o
    produto não cumpre e que a própria FAQ do site desmente. O que se certifica
    é a INTEGRIDADE do registro.
    """
    texto = ps.montar_mensagem("Ana", "Marina X", "Marina Y").lower()
    assert "certificad" not in texto
    assert "selo de integridade" in texto


def test_sem_responsavel_nao_quebra_a_saudacao():
    texto = ps.montar_mensagem("", "Marina X", "Marina Y")
    assert texto.startswith("Olá,")
    assert "{" not in texto, "sobrou marcador do template sem substituir"
