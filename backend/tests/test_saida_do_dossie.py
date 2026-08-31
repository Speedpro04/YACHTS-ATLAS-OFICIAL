"""
O dossiê não sai sem deixar rastro.

`dossie_saidas` é o livro-razão de compartilhamento: uma linha por vez que o
documento vai para um terceiro, com destinatário, finalidade, canal e IP. É
o que responde *"quem recebeu este dossiê, quando e para quê"* — pergunta de
LGPD (art. 37, registro das operações de tratamento) e de auditoria de
seguradora.

Até 31/08/2026 esse insert vivia dentro de `try/except: pass`. Se falhasse,
**a entrega acontecia e o rastro não**, em silêncio. Num livro-razão o
registro é o produto, não um efeito colateral dele — e um compartilhamento
sem rastro não se conserta depois, enquanto uma entrega recusada o
solicitante repete em segundos.

O contraste com `_registrar_emissao`, que continua best-effort de propósito,
é a régua: lá o que se perde é a impressão digital de um PDF que a
plataforma já sabe ter emitido; aqui o que se perde é a única prova de que o
documento saiu.
"""
from pathlib import Path

import pytest

ROTA = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "dossie.py"


@pytest.fixture(scope="module")
def fonte() -> str:
    return ROTA.read_text(encoding="utf-8")


def _sem_comentarios(texto: str) -> str:
    """Só o código. Os comentários citam o padrão antigo de propósito, para
    quem ler entender o que mudou e por quê."""
    return "\n".join(l for l in texto.splitlines() if not l.lstrip().startswith("#"))


# ─────────────────────────────────────────────────────────────────────────────
# O registro é condição para a entrega
# ─────────────────────────────────────────────────────────────────────────────

def test_falha_ao_registrar_a_saida_impede_a_entrega(fonte):
    """O `except` do insert em `dossie_saidas` precisa INTERROMPER o fluxo.

    Se ele voltar a engolir a exceção, o dossiê passa a sair sem rastro
    de novo — e ninguém percebe, porque o sintoma é a AUSÊNCIA de uma linha.
    """
    codigo = _sem_comentarios(fonte)
    i = codigo.find('supabase.table("dossie_saidas").insert(')
    assert i > 0, "o registro da saída sumiu do fluxo de entrega"

    trecho = codigo[i:i + 1400]
    assert "except Exception" in trecho, "o insert perdeu o tratamento de erro"
    assert "status_code=503" in trecho, (
        "falhar ao registrar a saída precisa RECUSAR a entrega, não seguir em frente"
    )
    # O padrão exato que foi removido não pode voltar.
    assert "except Exception:\n        pass" not in trecho, (
        "voltou a engolir a falha: o dossiê sairia sem rastro"
    )


def test_registro_vem_antes_de_gerar_o_pdf(fonte):
    """Ordem importa: registrar primeiro, entregar depois. Registrar DEPOIS
    de gerar significaria gastar a geração para descobrir no fim que não dá
    para registrar — e a tentação seria entregar assim mesmo."""
    codigo = _sem_comentarios(fonte)
    registro = codigo.find('supabase.table("dossie_saidas").insert(')
    geracao = codigo.find("gerar_pdf_dossie(dados)", registro)
    assert registro > 0 and geracao > registro, (
        "o registro da saída precisa vir ANTES da geração do PDF"
    )


# ─────────────────────────────────────────────────────────────────────────────
# O bug do campo que não existia
# ─────────────────────────────────────────────────────────────────────────────

def test_impressao_digital_identifica_quem_recebeu(fonte):
    """`sol` vem de `dossie_solicitacoes`, que tem `solicitante_email` — e NÃO
    `destinatario_email`, que é coluna de `dossie_saidas`.

    Com o nome errado, `_registrar_emissao` gravava None SEMPRE: a impressão
    digital do PDF ia ao banco sem identificar o destinatário, justamente na
    via em que o documento sai do controle da marina.
    """
    codigo = _sem_comentarios(fonte)
    assert 'sol.get("destinatario_email")' not in codigo, (
        "voltou a ler um campo que não existe em dossie_solicitacoes"
    )
    assert 'sol.get("solicitante_email")' in codigo


def test_a_saida_registra_quem_o_que_e_para_que(fonte):
    """Sem finalidade e destinatário, a linha não responde à pergunta que a
    tabela existe para responder."""
    codigo = _sem_comentarios(fonte)
    i = codigo.find('supabase.table("dossie_saidas").insert(')
    bloco = codigo[i:i + 600]
    for campo in ("destinatario_nome", "destinatario_email", "finalidade",
                  "ativo_id", "marina_nome", "canal"):
        assert campo in bloco, f"a saída deixou de registrar {campo}"


# ─────────────────────────────────────────────────────────────────────────────
# A régua entre os dois registros
# ─────────────────────────────────────────────────────────────────────────────

def test_registrar_emissao_segue_best_effort(fonte):
    """`_registrar_emissao` continua best-effort DE PROPÓSITO, e o contraste
    com `dossie_saidas` é a régua: perder a impressão digital de um PDF que a
    plataforma sabe ter emitido é recuperável; perder a prova de que o
    documento saiu, e para quem, não é.

    Se um dia alguém "uniformizar" os dois, que seja por decisão — não por
    parecerem iguais.
    """
    assert "Best-effort" in fonte, (
        "a justificativa de por que a impressão digital NÃO bloqueia sumiu"
    )
