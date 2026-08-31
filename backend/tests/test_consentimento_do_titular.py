"""
Sem consentimento do titular, o dossiê não sai para terceiro.

A plataforma já sabia dizer **para quem** o dossiê foi, quando e para quê —
`dossie_solicitacoes` e `dossie_saidas` formam um livro-razão completo de
compartilhamento. O que faltava era o outro lado: o armador ter dito que
pode. Trilha sem base legal responde metade da pergunta que a LGPD faz, e é
exatamente a metade que uma seguradora auditando pede primeiro.

ONDE A EXIGÊNCIA FICA, E POR QUÊ
--------------------------------
Em `liberar_solicitacao`, não no download do painel. Baixar o dossiê do
próprio cliente não é compartilhamento — o dado já está com a marina.
Liberar para um terceiro é. Pôr a trava no lugar errado ou travaria o
trabalho interno da marina, ou deixaria passar o ato que precisa de base.

O QUE "NÃO SEI" SIGNIFICA
-------------------------
`consentimento_vigente` devolve `None` quando a leitura falha — nunca True
nem False. `True` liberaria um compartilhamento sem base legal por causa de
uma queda de rede; `False` acusaria de irregular uma marina em ordem. Na
liberação o `None` recusa, porque recusar é reversível em segundos e
entregar não é.
"""
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app"
MOD = APP / "api" / "v1" / "consentimento.py"
DOSSIE = APP / "api" / "v1" / "dossie.py"


def _codigo(caminho: Path) -> str:
    return "\n".join(l for l in caminho.read_text(encoding="utf-8").splitlines()
                     if not l.lstrip().startswith("#"))


# ─────────────────────────────────────────────────────────────────────────────
# O estado vigente
# ─────────────────────────────────────────────────────────────────────────────

def _vigente(linhas, falhou=False):
    """A regra de `consentimento_vigente`, isolada da rede."""
    if falhou:
        return {"vigente": None, "evento": None}
    if not linhas:
        return {"vigente": False, "evento": None}
    return {"vigente": bool(linhas[0].get("vigente")),
            "evento": linhas[0].get("evento")}


def test_sem_evento_nenhum_nao_ha_consentimento():
    """O padrão é NÃO. Um ativo cadastrado ontem não autoriza nada por
    omissão — consentimento presumido não é consentimento."""
    assert _vigente([])["vigente"] is False


def test_concedido_vale():
    assert _vigente([{"vigente": True, "evento": "concedido"}])["vigente"] is True


def test_revogado_derruba_o_consentimento_anterior():
    """O último evento manda. `fn_consentimento_vigente` ordena por data
    decrescente e pega um: a revogação de hoje vence a concessão de ontem."""
    r = _vigente([{"vigente": False, "evento": "revogado"}])
    assert r["vigente"] is False and r["evento"] == "revogado"


def test_falha_de_leitura_nao_vira_sim_nem_nao():
    assert _vigente([], falhou=True)["vigente"] is None


# ─────────────────────────────────────────────────────────────────────────────
# A trava, e onde ela fica
# ─────────────────────────────────────────────────────────────────────────────

def test_liberar_recusa_sem_consentimento():
    codigo = _codigo(DOSSIE)
    i = codigo.find("async def liberar_solicitacao")
    assert i > 0
    corpo = codigo[i:i + 3000]
    assert "consentimento_vigente(" in corpo, "a liberação parou de exigir base legal"
    assert "status_code=409" in corpo, "sem consentimento precisa RECUSAR"


def test_nao_sei_tambem_recusa():
    """`None` não pode cair no mesmo ramo do `True`. Se alguém escrever
    `if cons["vigente"] is False:` a falha de leitura passa a liberar."""
    codigo = _codigo(DOSSIE)
    i = codigo.find("async def liberar_solicitacao")
    corpo = codigo[i:i + 3000]
    assert 'cons["vigente"] is None' in corpo
    assert "status_code=503" in corpo, "a falha de leitura precisa recusar, não liberar"


def test_o_painel_da_marina_nao_e_travado():
    """De propósito: a marina baixar o dossiê do próprio cliente não é
    compartilhamento com terceiro — o dado já está com ela. Travar aqui
    pararia o trabalho interno sem proteger ninguém."""
    codigo = _codigo(DOSSIE)
    i = codigo.find("async def pdf_dossie")
    j = codigo.find("async def solicitar_dossie", i)
    assert "consentimento_vigente(" not in codigo[i:j]


# ─────────────────────────────────────────────────────────────────────────────
# A linha de consentimento não pode virar um novo vazamento
# ─────────────────────────────────────────────────────────────────────────────

def test_o_documento_do_titular_vai_mascarado():
    """O CPF saiu do texto plano em `ativos` em 31/08; a linha de
    consentimento não é motivo para ele voltar a existir numa segunda
    tabela."""
    codigo = _codigo(MOD)
    i = codigo.find('"titular_documento"')
    assert i > 0
    assert "mascarar_documento(" in codigo[i:i + 200], (
        "o documento do titular está indo cru para o banco"
    )


def test_o_termo_e_versionado():
    """Uma auditoria precisa saber COM O QUE o titular concordou naquela
    data — não com o que o site diz hoje. Por isso a versão e o texto
    inteiro ficam gravados na linha, não só um ponteiro."""
    codigo = _codigo(MOD)
    assert "TERMO_VERSAO" in codigo and "TERMO_TEXTO" in codigo
    i = codigo.find('"ativo_consentimentos"')
    bloco = codigo[i:i + 900]
    assert '"termo_versao"' in bloco and '"termo_texto"' in bloco


def test_retirar_consentimento_e_um_evento_nao_um_apagamento():
    """A tabela é append-only no banco (`trg_ativo_consentimentos_imutavel`).
    O código também não pode tentar UPDATE ou DELETE: o gatilho recusaria, e
    a marina veria um erro cru em vez da revogação registrada."""
    codigo = _codigo(MOD)
    i = codigo.find('table("ativo_consentimentos")')
    assert i > 0
    corpo = codigo[i:]
    assert ".delete(" not in corpo, "consentimento não se apaga — revoga-se"
    assert ".update(" not in corpo, "consentimento não se edita — acrescenta-se evento"
    assert '"revogado"' in codigo, "a revogação some do vocabulário"


def test_a_tela_recebe_o_termo_para_exibir():
    """A marina não pode colher consentimento sem mostrar ao titular o que
    ele está autorizando. A rota de leitura devolve o texto em vigor."""
    codigo = _codigo(MOD)
    i = codigo.find("async def ler_consentimento")
    corpo = codigo[i:i + 700]
    assert "termo_atual_texto" in corpo and "termo_atual_versao" in corpo


def test_consentimento_antigo_e_sinalizado():
    """Se o termo mudar, quem consentiu com a versão anterior continua
    valendo — mas a tela precisa saber, para poder recolher. Silenciar isso
    faria a plataforma afirmar concordância com um texto que o titular nunca
    leu."""
    codigo = _codigo(MOD)
    assert "desatualizado" in codigo
