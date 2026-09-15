# -*- coding: utf-8 -*-
"""
A foto tem que cair na prateleira certa da galeria.

São dois vocabulários com nomes parecidos: a FICHA organiza o serviço
(`casco`, `eletrica`) e a GALERIA organiza a foto no dossiê (`casco_exterior`,
`eletronica`). Onde coincidem, funcionou por acaso; onde divergem, a foto some
em "Outros".

Aconteceu duas vezes: em 23/08/2026 com `galeria_seguranca` (registrado no
próprio `coberturaFotos.ts`) e em 15/09/2026 com duas fotos tiradas na aba
"Integridade do Casco". Na segunda vez o painel dizia "Outros" e o dossiê dizia
"Casco" — as duas telas discordando sobre a mesma foto.

O teste que mais importa aqui é o último: ele lê as categorias reais das fichas
do frontend e exige que cada uma chegue a uma prateleira que EXISTE na galeria.
Ficha nova cujo nome não bate quebra a suíte, em vez de mandar foto de cliente
para "Outros" em silêncio.
"""
import re
from pathlib import Path

import pytest

from app.services.categorias_galeria import para_galeria
from app.services.dossie_data import GALERIA_LABELS

RAIZ = Path(__file__).resolve().parents[2]
FICHAS_TS = RAIZ / "frontend" / "src" / "config" / "servicosCategorias.ts"


def test_casco_vai_para_a_integridade_do_casco():
    """O caso concreto de 15/09/2026."""
    assert para_galeria("casco") == "casco_exterior"
    assert GALERIA_LABELS["casco_exterior"] == "Integridade do Casco"


def test_eletrica_vai_para_eletronica():
    assert para_galeria("eletrica") == "eletronica"


def test_o_que_ja_bate_passa_intacto():
    """Traduzir o que já está certo criaria uma segunda fonte para a mesma
    verdade — e uma delas envelheceria."""
    for igual in ("motor", "interior", "pintura", "seguranca", "embarcacao"):
        assert para_galeria(igual) == igual


def test_o_prefixo_antigo_e_removido():
    """Fotos gravadas como `galeria_seguranca` existem no banco desde antes."""
    assert para_galeria("galeria_seguranca") == "seguranca"
    assert para_galeria("galeria_casco") == "casco_exterior"


def test_categoria_desconhecida_passa_e_nao_some():
    """Inventar destino esconderia a categoria nova. A galeria já resolve o que
    não reconhece — e aí ela aparece em 'Outros' porque ninguém a previu, não
    porque alguém a traduziu errado."""
    assert para_galeria("categoria_que_nao_existe") == "categoria_que_nao_existe"
    assert para_galeria(None) == ""
    assert para_galeria("  CASCO  ") == "casco_exterior"


@pytest.mark.skipif(not FICHAS_TS.exists(), reason="frontend não está neste checkout")
def test_toda_ficha_tem_prateleira_na_galeria():
    """A guarda que impede o defeito de voltar com outro nome."""
    fonte = FICHAS_TS.read_text(encoding="utf-8")
    bloco = fonte.split("export const SERVICOS")[1].split("}")[0]
    fichas = re.findall(r"^\s*(\w+):", bloco, re.M)
    assert fichas, "não consegui ler as categorias das fichas"

    # `dossie` é a ficha genérica do próprio dossiê, não gera foto de galeria.
    orfas = {
        f: para_galeria(f) for f in fichas
        if f != "dossie" and para_galeria(f) not in GALERIA_LABELS
    }
    assert not orfas, (
        "Fichas cuja foto não tem prateleira na galeria (vão cair em 'Outros'): "
        + ", ".join(f"{f} -> {destino}" for f, destino in sorted(orfas.items()))
        + ". Ou crie a categoria na galeria, ou mapeie em services/categorias_galeria.py"
    )
