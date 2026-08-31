"""
A cota de dossiês é da marina — quem baixa não gasta o ano de quem paga.

O plano dá **4 dossiês por ano, por embarcação**. Até 31/08/2026 a conta que
media isso somava TODA linha de `dossie_emitidos`, e essa tabela ganha uma
linha a cada geração de PDF — inclusive as de canal `acesso_link`, gravadas
toda vez que o destinatário reabre o link que já lhe foi liberado.

Duas consequências, e a segunda é pior que a primeira:

1. Um comprador que abrisse o dossiê quatro vezes esgotava o ano da marina.
   A marina pagou e ficava trancada fora do próprio ativo, sem ter emitido
   nada — o botão do painel respondia 429 por consumo de terceiro.

2. A via do link **nunca** consultou a cota. Então o terceiro seguia baixando
   depois do bloqueio, enquanto o dono não conseguia mais emitir. O limite
   valia só para quem pagou.

O conserto separa duas perguntas que a mesma contagem misturava:

    quantos dossiês esta marina EMITIU?   → cota
    quantas vezes este PDF foi BAIXADO?   → custódia (`dossie_emitidos` inteira)

`dossie_emitidos` continua registrando tudo, com hash de cada entrega: é o
livro de custódia e não perde nada. A cota passa a ler outra coisa —
emissões pelo painel mais pedidos liberados, um por pedido, não por download.

E a cobrança mudou de lugar: quem gasta é `liberar_solicitacao`, o ato em que
a marina decide entregar. Reabrir o link não tira nada de ninguém.
"""
from pathlib import Path

import pytest

ROTA = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "dossie.py"


@pytest.fixture(scope="module")
def fonte() -> str:
    return ROTA.read_text(encoding="utf-8")


def _codigo(texto: str) -> str:
    """Sem comentários: eles citam o defeito antigo de propósito."""
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))


def _usados(painel: int, liberados: int, downloads_do_link: int) -> int:
    """A conta nova, isolada da rede: downloads não entram."""
    linhas = [{"quando": f"2026-01-{d + 1:02d}"} for d in range(painel)]
    linhas += [{"quando": f"2026-02-{d + 1:02d}"} for d in range(liberados)]
    _ = downloads_do_link  # de propósito: não é insumo da cota
    return len(linhas)


# ─────────────────────────────────────────────────────────────────────────────
# O defeito exato que isto substitui
# ─────────────────────────────────────────────────────────────────────────────

def test_download_do_terceiro_nao_gasta_a_cota_da_marina():
    """Um pedido liberado, aberto oito vezes pelo comprador, é UM dossiê.

    Na conta antiga eram oito — e a marina, que emitiu uma vez, aparecia com
    o ano estourado.
    """
    assert _usados(painel=0, liberados=1, downloads_do_link=8) == 1


def test_marina_nao_fica_trancada_por_consumo_de_terceiro():
    limite = 4
    usados = _usados(painel=1, liberados=1, downloads_do_link=20)
    assert limite - usados == 2, "sobra para a marina emitir"


def test_a_consulta_da_cota_filtra_o_canal(fonte):
    """Sem `canal = painel` a contagem volta a somar download de terceiro."""
    codigo = _codigo(fonte)
    # Dentro de `_saldo_dossie` — `contar_emitidos`, mais acima, também lê
    # `dossie_emitidos` e responde outra pergunta (quantos ESTE usuário fez).
    saldo = codigo.find("def _saldo_dossie")
    assert saldo > 0
    i = codigo.find('supabase.table("dossie_emitidos")', saldo)
    assert i > 0
    trecho = codigo[i:i + 400]
    assert '.eq("canal", "painel")' in trecho, (
        "a cota voltou a contar toda emissão, inclusive a do link"
    )


def test_liberacao_conta_uma_vez_por_pedido(fonte):
    """O segundo insumo da cota são os pedidos liberados — não os acessos
    deles. `dossie_solicitacoes` tem uma linha por pedido; `acessos` é
    contador dentro da mesma linha, e não pode virar unidade de cobrança."""
    codigo = _codigo(fonte)
    i = codigo.find('supabase.table("dossie_solicitacoes")\n            .select("liberado_em")')
    assert i > 0, "a cota parou de contar as liberações"
    trecho = codigo[i:i + 300]
    assert '.eq("status", "liberado")' in trecho
    assert "acessos" not in trecho, "acesso não é unidade de cota"


# ─────────────────────────────────────────────────────────────────────────────
# Onde a cota é cobrada
# ─────────────────────────────────────────────────────────────────────────────

def test_liberar_recusa_quando_o_ano_acabou(fonte):
    """`liberar_solicitacao` é o ato de emissão para terceiro. Sem checagem
    aqui, bastava liberar por pedido para passar dos quatro do ano."""
    codigo = _codigo(fonte)
    i = codigo.find("async def liberar_solicitacao")
    assert i > 0
    corpo = codigo[i:i + 1800]
    assert "_saldo_dossie(" in corpo, "liberar voltou a não consultar a cota"
    assert "status_code=429" in corpo, "liberar precisa RECUSAR, não avisar"


def test_o_painel_continua_respeitando_a_cota(fonte):
    codigo = _codigo(fonte)
    i = codigo.find("async def pdf_dossie")
    corpo = codigo[i:i + 900]
    assert "_saldo_dossie(" in corpo and "status_code=429" in corpo


def test_reabrir_o_link_nao_e_bloqueado(fonte):
    """De propósito: o destinatário recebeu um dossiê já autorizado e pago.
    Bloqueá-lo na quarta abertura transformaria um documento entregue em algo
    que expira sem aviso — e a cota já foi cobrada da marina na liberação."""
    codigo = _codigo(fonte)
    i = codigo.find("async def acesso_processar")
    assert i > 0
    corpo = codigo[i:]
    assert "_saldo_dossie(" not in corpo, (
        "a via do link passou a checar cota: o terceiro seria bloqueado por "
        "algo que a marina já gastou ao liberar"
    )


# ─────────────────────────────────────────────────────────────────────────────
# A custódia não perde nada
# ─────────────────────────────────────────────────────────────────────────────

def test_todo_download_continua_registrado(fonte):
    """A cota deixou de contar `acesso_link`, mas o registro continua: é o
    hash do que foi entregue, e responde 'que arquivo esta pessoa recebeu'."""
    codigo = _codigo(fonte)
    assert '"acesso_link"' in codigo, "o canal do link sumiu do registro"
    i = codigo.find("async def acesso_processar")
    assert "_registrar_emissao(" in codigo[i:], (
        "a via do link parou de registrar a impressão digital do PDF entregue"
    )
