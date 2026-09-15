# -*- coding: utf-8 -*-
"""
Yachts Atlas — da categoria da FICHA para a categoria da GALERIA.

São dois vocabulários com nomes parecidos, e é aí que mora o defeito.

  • a FICHA técnica organiza o SERVIÇO: `casco`, `eletrica`, `manutencao`…
    (frontend/src/config/servicosCategorias.ts)
  • a GALERIA organiza a FOTO no dossiê: `casco_exterior`, `eletronica`…
    (frontend/src/config/coberturaFotos.ts)

Onde eles coincidem — `motor`, `interior`, `pintura`, `seguranca` — tudo
funcionou por acaso. Onde divergem, a foto some: o Atlas Pré-Data envia a
categoria da ficha, a galeria não reconhece e joga em "Outros".

Aconteceu em 15/09/2026 com duas fotos tiradas na aba "Integridade do Casco":
chegaram como `casco`, e o painel as pendurou em "Outros". O mesmo arquivo de
configuração do front já registra um episódio idêntico em 23/08 com
`galeria_seguranca`.

A tradução acontece na ESCRITA, não na leitura. Gravar já na categoria certa
conserta o painel e o dossiê de uma vez — traduzir na exibição obrigaria as
duas telas a lembrar, e uma delas ia esquecer. Foi assim que o painel e o
dossiê passaram a discordar da primeira vez.
"""

# Só o que diverge. Categoria que já nasce com o nome da galeria passa direto —
# listar tudo aqui criaria uma segunda fonte para a mesma verdade.
_DA_FICHA_PARA_GALERIA = {
    "casco": "casco_exterior",
    "eletrica": "eletronica",
    # Serviço de manutenção fotografa peça trocada e serviço feito: é registro
    # de intervenção, e o par antes/depois é onde o comprador procura por isso.
    "manutencao": "antes_depois",
    # Drenagem e porão são parte da integridade do casco para quem avalia.
    "drenagem": "casco_exterior",
    # Velame é do veleiro, que não tem motor. A galeria não tem categoria
    # própria; exterior é onde o comprador procura mastro e vela.
    "velame": "casco_exterior",
    # Sinistro é avaria: quem avalia procura isso junto da integridade do
    # casco, e não numa gaveta separada.
    "sinistros": "casco_exterior",

    # --- Sem prateleira própria, e isto É a decisão ---------------------
    # As duas abaixo vão para "Outros" DE PROPÓSITO, escrito, e não por
    # descuido. Diário de bordo e apólice não produzem foto que o comprador
    # procure numa galeria de 460 imagens; forçá-las numa categoria existente
    # sujaria a prateleira de quem procura casco ou motor.
    #
    # Se um dia qualquer uma merecer categoria própria, ela nasce em
    # `coberturaFotos.ts` e GALERIA_LABELS, e a linha aqui sai.
    "operacao": "outros",
    "seguro": "outros",
}


def para_galeria(categoria: str | None) -> str:
    """A categoria sob a qual a foto deve ser arquivada.

    Desconhecida passa intacta: a galeria já resolve o que não reconhece
    mandando para "Outros", e inventar destino aqui esconderia a categoria
    nova em vez de deixá-la aparecer.
    """
    chave = str(categoria or "").strip().lower().replace("galeria_", "")
    return _DA_FICHA_PARA_GALERIA.get(chave, chave)
