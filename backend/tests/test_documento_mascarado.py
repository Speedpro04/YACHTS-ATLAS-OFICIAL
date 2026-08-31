"""
O CPF completo não entra no banco.

Até 31/08/2026 o documento do proprietário era gravado inteiro e mascarado
só na SAÍDA, quando o dossiê era impresso. O levantamento daquele dia
mostrou que os dígitos escondidos **nunca eram usados**: o campo entra pelo
formulário do painel e o único consumidor já o imprimia mascarado — não há
validação, busca, cobrança nem verificação de identidade que precise deles.

O fundador decidiu não guardar. Guardar dado pessoal sem uso é assumir risco
de vazamento sem contrapartida (minimização — LGPD art. 6º, III), e numa
auditoria "não temos o dado" sustenta melhor que "o dado está protegido".

Estes testes existem porque essa decisão é fácil de desfazer sem querer:
basta alguém escrever um caminho de gravação novo e esquecer de mascarar.
"""
import pytest

from app.core.pii import mascarar_documento


# ─────────────────────────────────────────────────────────────────────────────
# A regra
# ─────────────────────────────────────────────────────────────────────────────

def test_cpf_esconde_o_miolo():
    """Sobra o suficiente para conferir de quem é, sem servir de insumo."""
    assert mascarar_documento("123.456.789-00") == "***.456.789-**"
    assert mascarar_documento("12345678900") == "***.456.789-**"


def test_cnpj_preserva_a_raiz():
    """São os oito primeiros dígitos que identificam a empresa. A ordem do
    estabelecimento e o verificador não acrescentam identificação e só
    aumentam o estrago se vazarem."""
    assert mascarar_documento("12.345.678/0001-90") == "12.345.678/****-**"
    assert mascarar_documento("12345678000190") == "12.345.678/****-**"


def test_formato_desconhecido_guarda_so_o_fim():
    """Documento estrangeiro ou digitação fora do padrão: preserva os quatro
    últimos, que é o que permite conferência, e esconde o resto."""
    assert mascarar_documento("1234567") == "***4567"


def test_curto_demais_vira_nada():
    """Menos de 5 dígitos não identifica ninguém e provavelmente é digitação
    incompleta. Guardar fragmento não serve para nada e ainda é dado pessoal."""
    assert mascarar_documento("123") is None
    assert mascarar_documento("") is None
    assert mascarar_documento(None) is None
    assert mascarar_documento("   ") is None


def test_idempotente():
    """A MESMA função roda na gravação e rodou no backfill. Se mascarar o já
    mascarado destruísse o valor, o segundo salvamento do mesmo formulário
    apagaria o que restou."""
    uma = mascarar_documento("123.456.789-00")
    assert mascarar_documento(uma) == uma
    assert mascarar_documento(mascarar_documento(uma)) == uma


# ─────────────────────────────────────────────────────────────────────────────
# Contrato: a porta não pode reabrir
# ─────────────────────────────────────────────────────────────────────────────

def test_os_dois_caminhos_de_escrita_mascaram():
    """`ativos.py` grava o documento em dois lugares — no cadastro do ativo e
    no vínculo do proprietário. Os dois precisam mascarar ANTES de gravar.

    Caminho de escrita novo que esqueça disso quebra aqui, que é o único
    lugar onde ainda dá tempo.
    """
    from pathlib import Path
    fonte = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "ativos.py"
             ).read_text(encoding="utf-8")

    assert "from app.core.pii import mascarar_documento" in fonte
    assert fonte.count("mascarar_documento(") >= 2, (
        "os dois caminhos de escrita (cadastro e vínculo) precisam mascarar"
    )
    # O padrão antigo — pegar o valor cru e gravar — não pode voltar.
    assert '(data.proprietario_documento or "").strip()' not in fonte, (
        "voltou a gravar o documento cru em vez de mascarar"
    )


def test_o_dossie_usa_a_mesma_funcao():
    """Duas implementações do mesmo mascaramento divergiriam, e a que ficasse
    errada seria justamente a que ninguém estivesse olhando. É o defeito que
    este projeto passou o mês corrigindo."""
    from app.services import dossie_data
    assert dossie_data._mascarar_documento is mascarar_documento


def test_dossie_nao_imprime_documento_completo():
    """Ponta a ponta: o que chega ao PDF já está mascarado.

    O que fica escondido é o PREFIXO (3 primeiros) e o VERIFICADOR (2
    últimos); os seis do meio permanecem de propósito, porque é o que permite
    ao comprador conferir que o documento é do titular que ele espera. Um
    mascaramento que escondesse tudo não identificaria ninguém e o campo
    perderia a razão de existir no dossiê.
    """
    from app.services.dossie_data import _mascarar_documento
    saida = _mascarar_documento("529.982.247-25")
    assert saida == "***.982.247-**"
    assert "529" not in saida, "o prefixo do CPF vazou"
    assert not saida.endswith("25"), "o verificador vazou"
    # E o documento inteiro, em dígitos, nunca sai
    assert "52998224725" not in saida.replace(".", "").replace("-", "")
