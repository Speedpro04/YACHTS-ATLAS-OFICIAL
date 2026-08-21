"""
Conhecimento do PRODUTO para a Capitã Solara.

Por que isto existe
-------------------
A Solara nasceu sabendo normas náuticas — um corpo grande, externo e estável,
que vive no RAG. Mas a marina também pergunta "onde eu coloco a foto do
casco?", e isso o RAG não responde: é conhecimento nosso, pequeno e que muda
toda semana.

Coisa pequena não precisa de busca semântica. Cabe no prompt inteiro, e ali
está sempre presente — inclusive quando a pergunta mistura os dois mundos
("preciso registrar a EPIRB, onde ponho isso no sistema?"), que é justamente
onde um roteador escolheria um lado e perderia metade da resposta.

Por que é GERADO, e não escrito à mão
-------------------------------------
Norma envelhece devagar; produto muda toda semana. Hoje mesmo "Casco /
Exterior" virou "Integridade do Casco" e nasceu "Fotos da Embarcação". Texto
escrito à mão sobre telas que mudam vira mentira em duas semanas — e mentira
dita com convicção, porque ninguém revisa o que a IA respondeu.

Então as listas saem do código que as define. O que é escrito à mão aqui são
só os FLUXOS ("como cadastrar", "como selar"), que mudam devagar porque são
o desenho do produto, não os seus rótulos.

Por que fica num JSON versionado
--------------------------------
A imagem de produção leva `backend/` e o `dist` do frontend — os arquivos
`.ts` não existem lá. Então a extração roda no repositório e o resultado é
commitado ao lado deste módulo.

Isso reintroduz o risco de ficar velho, e por isso existe
`tests/test_conhecimento_produto.py`: ele extrai de novo e compara. Mudou uma
categoria e ninguém regenerou? O teste quebra antes do deploy. É a única
forma de garantir que a Solara não descreva uma tela que não existe mais.

Para regenerar:  python -m app.services.conhecimento_produto
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_AQUI = Path(__file__).resolve().parent
_ARQUIVO = _AQUI / "conhecimento_produto.json"

# Sobe de backend/app/services até a raiz do repositório.
_RAIZ = _AQUI.parents[2]
_CONFIG = _RAIZ / "frontend" / "src" / "config"


# ------------------------------------------------------------------
# Extração — só roda no repositório (o frontend não vai para a imagem)
# ------------------------------------------------------------------

def _ler(nome: str) -> str:
    return (_CONFIG / nome).read_text(encoding="utf-8")


def _secoes_do_dossie() -> list[dict[str, str]]:
    """Categorias do painel técnico que viram seções do dossiê."""
    texto = _ler("dossieCategorias.ts")
    achados = []
    for bloco in re.finditer(
        r"id:\s*'([^']+)'"          # id
        r".*?label:\s*'([^']+)'"    # label
        r".*?descricao:\s*'([^']+)'",  # descricao
        texto,
        re.DOTALL,
    ):
        chave, label, descricao = bloco.groups()
        # `descricao` pode vir de outro bloco se o campo faltar no atual;
        # o recorte por não-guloso já limita, mas o id é a âncora confiável.
        achados.append({"id": chave, "label": label, "descricao": descricao})
    return achados


def _categorias_de_foto() -> dict[str, Any]:
    """Categorias da galeria fotográfica e o teto por embarcação."""
    texto = _ler("coberturaFotos.ts")
    cats = [
        {"key": k, "label": l, "minimo": int(m)}
        for k, l, m in re.findall(
            r"\{\s*key:\s*'([^']+)',\s*label:\s*'([^']+)',\s*minimo:\s*(\d+)\s*\}",
            texto,
        )
    ]
    maximo = re.search(r"MAX_FOTOS\s*=\s*(\d+)", texto)
    return {
        "categorias": cats,
        "max_fotos": int(maximo.group(1)) if maximo else 0,
    }


def _fichas_do_painel() -> list[str]:
    """Categorias que têm ficha técnica rica (formulário detalhado)."""
    texto = _ler("servicosCategorias.ts")
    bloco = re.search(
        r"export const SERVICOS[^{]*\{(.*?)\n\}", texto, re.DOTALL
    )
    if not bloco:
        return []
    return re.findall(r"^\s*(\w+):\s*FICHA_", bloco.group(1), re.MULTILINE)


def extrair_do_frontend() -> dict[str, Any]:
    """Lê os arquivos de configuração do frontend e monta o conhecimento."""
    return {
        "secoes_dossie": _secoes_do_dossie(),
        "fotos": _categorias_de_foto(),
        "fichas_painel": _fichas_do_painel(),
    }


# ------------------------------------------------------------------
# Uso em produção — lê o JSON versionado
# ------------------------------------------------------------------

def carregar() -> dict[str, Any]:
    """O conhecimento gerado. Vazio se o arquivo faltar — nunca levanta."""
    try:
        return json.loads(_ARQUIVO.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(
            "Conhecimento do produto indisponível (%s). A Solara seguirá "
            "respondendo só sobre normas.", e
        )
        return {}


# Fluxos: escritos à mão porque são o desenho do produto, não seus rótulos —
# mudam devagar, e são o que a marina realmente pergunta.
_FLUXOS = """
COMO A MARINA USA O SISTEMA (fluxos principais):

• Cadastrar uma embarcação — menu Ativos → "Adicionar Ativo". Tipo, marca,
  modelo, comprimento e ano são obrigatórios. O e-mail e o WhatsApp do
  proprietário são opcionais e podem ser preenchidos depois.

• Registrar um serviço — abrir a embarcação → escolher a aba da categoria
  (Manutenção, Motor, Elétrica, Casco...) → preencher a ficha → salvar. Ao
  salvar, o registro é SELADO: recebe hash SHA-256 e não pode mais ser
  alterado nem excluído. Correção se faz por retificação, com motivo — o
  registro antigo continua visível, marcado como retificado.

• Enviar fotos — na embarcação, aba de fotos, escolher a categoria e enviar.
  Cada foto é datada, geolocalizada (quando o aparelho permite) e selada.

• Gerar o dossiê — na embarcação, opção de dossiê. Ele é montado a partir do
  que já está registrado no painel: aba preenchida vira seção, aba vazia não
  aparece.

• Dar acesso ao proprietário — basta preencher o e-mail do dono no cadastro
  da embarcação. Ele entra em /acesso-proprietario com esse e-mail, recebe um
  código de uso único e vê SOMENTE o barco dele, em modo leitura: não
  cadastra, não edita, não sela e não enxerga os outros clientes da marina.

• Arquivar uma embarcação — arquivar tira da operação e PRESERVA todo o
  histórico. Não existe excluir: registro selado é a cadeia de custódia, e é
  ela que dá valor ao dossiê.
""".strip()


def montar_texto() -> str:
    """O bloco de conhecimento do produto que entra no prompt da Solara."""
    dados = carregar()
    if not dados:
        return ""

    partes = ["COMO O YACHTS ATLAS FUNCIONA (conhecimento do produto):"]

    secoes = dados.get("secoes_dossie") or []
    if secoes:
        partes.append(
            "\nCategorias do painel técnico (cada uma vira uma seção do dossiê):"
        )
        partes += [f"- {s['label']}: {s['descricao']}" for s in secoes]

    fotos = dados.get("fotos") or {}
    cats = fotos.get("categorias") or []
    if cats:
        teto = fotos.get("max_fotos") or 0
        partes.append(
            f"\nGaleria fotográfica — até {teto} fotos por embarcação, "
            "organizadas nestas categorias:"
        )
        partes += [
            f"- {c['label']} (recomendado: {c['minimo']} fotos)" for c in cats
        ]

    partes.append("\n" + _FLUXOS)
    return "\n".join(partes)


if __name__ == "__main__":
    dados = extrair_do_frontend()
    _ARQUIVO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Conhecimento regenerado em {_ARQUIVO}")
    print(f"  {len(dados['secoes_dossie'])} seções do dossiê")
    print(f"  {len(dados['fotos']['categorias'])} categorias de foto "
          f"(teto {dados['fotos']['max_fotos']})")
    print(f"  {len(dados['fichas_painel'])} fichas do painel")
