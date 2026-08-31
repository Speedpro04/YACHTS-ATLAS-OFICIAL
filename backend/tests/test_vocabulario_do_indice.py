"""
Três fatos diferentes, três nomes diferentes — e nenhum deles é "saúde".

A plataforma media três coisas distintas e chamava duas delas de saúde:

    Índice de Custódia    quão COMPLETO é o registro       asset_score_service
    Conformidade          como estão os itens registrados  dossie_data._prontidao
    Perfil de Manutenção  programada × corretiva           dossie_pdf, por seção

O painel já tinha migrado para o vocabulário certo. O dossiê ficou para trás
de dois jeitos:

1. imprimia "Indicador de Saúde — Manutenção: 65% Preventiva / 35% Corretiva".
   Isso não é saúde nem índice: é hábito de manutenção. Um casco perfeito
   atendido só na quebra pontua mal; um casco comprometido com plano
   preventivo em dia pontua bem. O comprador lia **condição da embarcação**
   onde havia postura de manutenção;

2. `_prontidao` afirmava no próprio docstring ser "a mesma fórmula do painel".
   Não era — o painel é ponderado (50/25/15/10) e responde outra pergunta. O
   comentário convidava o próximo a "uniformizar" duas contas legítimas que
   medem coisas diferentes.

Por que a palavra saiu de vez: **a Yachts Atlas não inspeciona embarcação.**
Ela custodia o registro que a marina lançou. Um número chamado "saúde" afirma
sobre o barco; os três nomes acima afirmam sobre o registro — que é o que a
plataforma pode sustentar diante de uma seguradora.
"""
from pathlib import Path

import pytest

SERVICOS = Path(__file__).resolve().parents[1] / "app" / "services"
PDF = SERVICOS / "dossie_pdf.py"
DADOS = SERVICOS / "dossie_data.py"


def _codigo(caminho: Path) -> str:
    """Só o código: os comentários citam o nome antigo de propósito, para
    quem ler entender o que mudou e por quê."""
    return "\n".join(l for l in caminho.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith("#"))


# ─────────────────────────────────────────────────────────────────────────────
# A palavra não volta ao documento
# ─────────────────────────────────────────────────────────────────────────────

def test_o_dossie_nao_chama_nada_de_saude():
    """Único lugar do produto onde "Saúde" ainda aparecia para quem lê."""
    assert "Indicador de Saúde" not in _codigo(PDF), (
        "voltou a chamar de saúde a proporção preventiva × corretiva"
    )


def test_o_perfil_de_manutencao_tem_o_nome_do_que_mede():
    codigo = _codigo(PDF)
    assert codigo.count('f"Perfil de Manutenção — {label}:"') == 2, (
        "os dois rótulos (Manutenção e Elétrica) precisam do mesmo nome"
    )


def test_o_rotulo_cobre_as_duas_secoes():
    """Manutenção e Elétrica/Eletrônica usam o mesmo indicador; se uma ficar
    com nome diferente, o leitor acha que são métricas distintas."""
    codigo = _codigo(PDF)
    i = codigo.find('if cat in ("manutencao", "eletrica")')
    assert i > 0
    bloco = codigo[i:i + 2500]
    assert bloco.count("Perfil de Manutenção") == 2


# ─────────────────────────────────────────────────────────────────────────────
# As duas contas continuam separadas — e honestas sobre isso
# ─────────────────────────────────────────────────────────────────────────────

def test_prontidao_nao_finge_ser_a_formula_do_painel():
    fonte = DADOS.read_text(encoding="utf-8")
    i = fonte.find("def _prontidao")
    doc = fonte[i:i + 1200]
    assert "Índice de segurança — mesma fórmula do painel" not in doc, (
        "voltou a afirmar que as duas contas são a mesma"
    )
    assert "NÃO é a mesma fórmula do painel" in doc, (
        "o docstring precisa NEGAR a equivalência, não só omiti-la: era a "
        "afirmação de igualdade que convidava a fundir as duas contas"
    )
    assert "Índice de Custódia" in doc and "asset_score_service" in doc, (
        "o docstring precisa dizer QUAL é a outra conta e onde ela mora"
    )


def test_as_duas_contas_seguem_existindo():
    """O conserto não foi fundir as duas: foi parar de chamá-las do mesmo
    nome. Fundir apagaria uma pergunta que o produto responde."""
    assert "def _prontidao" in DADOS.read_text(encoding="utf-8")
    assert (SERVICOS / "asset_score_service.py").exists()


def test_a_terceira_implementacao_nao_e_mais_citada():
    """`AssetHealthDashboard.tsx` era uma terceira conta, com um terceiro nome
    ("Índice de Segurança"), renderizada em lugar nenhum — e cinco comentários
    do backend a apontavam como a referência que espelham."""
    raiz = Path(__file__).resolve().parents[2]
    assert not (raiz / "frontend" / "src" / "components"
                / "AssetHealthDashboard.tsx").exists()
    for arq in ("asset_score_service.py", "dossie_data.py"):
        assert "AssetHealthDashboard" not in _codigo(SERVICOS / arq), (
            f"{arq} voltou a apontar para um componente removido"
        )
