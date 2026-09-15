# -*- coding: utf-8 -*-
"""
O dossiê chama cada campo pelo nome que a Marina viu no formulário.

Quem desenha o formulário é o TypeScript; quem imprime o dossiê é o Python. O
container do backend não carrega o .ts, então a tradução é uma CÓPIA — e cópia
sem guarda envelhece calada.

Este arquivo é a guarda: lê as fichas do frontend e exige que toda chave
declarada lá tenha rótulo aqui. Campo novo no formulário sem rótulo no Python
quebra a suíte, com a instrução de como regerar.

Sem isso, o campo não deixa de existir — ele aparece no PDF com o nome da
coluna. Foi o que o comprador leu em 15/09/2026: "helice estado", onde a
Marina havia escolhido "Estado visual (cavitação, amassados)".
"""
import re
from pathlib import Path

import pytest

from app.services.rotulos_ficha import ROTULOS_FICHA, rotulo_do_campo

FICHAS_TS = (
    Path(__file__).resolve().parents[2]
    / "frontend" / "src" / "config" / "servicosCategorias.ts"
)


def _chaves_do_formulario() -> dict[str, str]:
    texto = FICHAS_TS.read_text(encoding="utf-8")
    pares = re.compile(r"key:\s*'([^']+)'\s*,\s*label:\s*'([^']+)'").findall(texto)
    encontrados: dict[str, str] = {}
    for chave, rotulo in pares:
        encontrados.setdefault(chave, rotulo)
    return encontrados


@pytest.mark.skipif(not FICHAS_TS.exists(), reason="frontend não está neste checkout")
def test_todo_campo_do_formulario_tem_rotulo_no_dossie():
    faltando = sorted(set(_chaves_do_formulario()) - set(ROTULOS_FICHA))
    assert not faltando, (
        "Campos no formulário sem rótulo no dossiê: "
        + ", ".join(faltando)
        + ". Rode: python scripts/gera_rotulos_ficha.py"
    )


@pytest.mark.skipif(not FICHAS_TS.exists(), reason="frontend não está neste checkout")
def test_os_rotulos_nao_divergiram():
    """Renomear o campo na tela e não no dossiê faz os dois documentos
    descreverem a mesma coisa com nomes diferentes."""
    divergentes = {
        k: (v, ROTULOS_FICHA[k])
        for k, v in _chaves_do_formulario().items()
        if k in ROTULOS_FICHA and ROTULOS_FICHA[k] != v
    }
    assert not divergentes, (
        "Rótulo mudou na tela e não no dossiê: "
        + "; ".join(f"{k}: tela={t!r} dossiê={d!r}" for k, (t, d) in divergentes.items())
        + ". Rode: python scripts/gera_rotulos_ficha.py"
    )


def test_o_campo_que_sumiu_do_pdf_agora_tem_nome():
    """O caso concreto que originou tudo isto."""
    assert rotulo_do_campo("helice_estado") == "Estado visual (cavitação, amassados)"


def test_campo_desconhecido_nao_some_do_documento():
    """Ficha antiga, campo removido do formulário: ainda tem que aparecer.
    Sumir do dossiê é pior do que aparecer com nome feio."""
    assert rotulo_do_campo("filtro_oleo_antigo") == "Filtro oleo antigo"
    assert rotulo_do_campo("") == ""
