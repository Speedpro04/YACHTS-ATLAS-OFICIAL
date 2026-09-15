# -*- coding: utf-8 -*-
"""Gera backend/app/services/rotulos_ficha.py a partir das fichas do frontend.

A fonte da verdade sobre QUAIS campos existem e o TypeScript, que e quem
desenha o formulario. Este script copia os rotulos para o Python, que e quem
imprime o dossie. Um teste confere a copia.
"""
import re
from pathlib import Path

FONTE = Path("frontend/src/config/servicosCategorias.ts")
DESTINO = Path("backend/app/services/rotulos_ficha.py")

texto = FONTE.read_text(encoding="utf-8")
pares = re.compile(r"key:\s*'([^']+)'\s*,\s*label:\s*'([^']+)'").findall(texto)

rotulos = {}
for chave, rotulo in pares:
    rotulos.setdefault(chave, rotulo)

cabecalho = '''"""
Yachts Atlas — rotulos dos campos da ficha tecnica.

De onde isto vem. Quem desenha o formulario e o frontend
(`frontend/src/config/servicosCategorias.ts`): la cada campo tem `key` e
`label`. Quem imprime o dossie e o Python. Sem esta ponte, o PDF so sabia o
nome da COLUNA — e o comprador lia "helice estado" onde a Marina digitou
"Estado visual (cavitacao, amassados)".

Por que e uma copia, e nao uma leitura. O container do backend nao tem o
TypeScript: a imagem final so carrega o Python e o `dist` ja compilado. Ler o
.ts em tempo de execucao funcionaria no seu computador e falharia em producao,
que e a pior combinacao possivel.

Como a copia se mantem honesta. `tests/test_rotulos_da_ficha.py` le o .ts e
exige que toda chave declarada la exista aqui. Campo novo no formulario sem
rotulo aqui quebra a suite — e a mensagem diz como regerar.

GERADO AUTOMATICAMENTE. Nao editar a mao: rode
`python scripts/gera_rotulos_ficha.py` na raiz do repositorio.
"""

ROTULOS_FICHA: dict[str, str] = {
'''

linhas = [f'    {chave!r}: {rotulo!r},' for chave, rotulo in sorted(rotulos.items())]

rodape = '''}


def rotulo_do_campo(chave: str) -> str:
    """O rotulo que a Marina viu no formulario. Sem rotulo, a chave legivel.

    O fallback e proposital: campo antigo, ou gravado por versao anterior do
    app, ainda precisa aparecer no dossie. Melhor "Filtro oleo" do que o campo
    sumir do documento — foi o que aconteceu ate 15/09/2026.
    """
    conhecido = ROTULOS_FICHA.get(chave)
    if conhecido:
        return conhecido
    return str(chave).replace("_", " ").strip().capitalize()
'''

DESTINO.write_text(cabecalho + "\n".join(linhas) + "\n" + rodape, encoding="utf-8")
print(f"{DESTINO}: {len(rotulos)} rotulos")
