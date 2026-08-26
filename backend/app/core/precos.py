"""
Yachts Atlas — Qual link de pagamento abrir.

Um lugar só. Antes a escolha estava em `leads.py` (cadastro novo) e em
`acesso.py` (marina bloqueada querendo voltar), e a LP de Lançamento tinha a
terceira cópia no `href` do botão. Quando os links em dólar foram desativados no
painel, em 26/08/2026, os três passaram a mandar gente para uma página que só
diz "The link is no longer active" — e nenhum deles sabia disso.

A regra: marina brasileira paga em real; o resto do mundo, em dólar. Mas link
não configurado NUNCA é oferecido — vazio aqui significa "esse caminho não
existe hoje", e é melhor cobrar na outra moeda que mandar a marina para uma
porta fechada.

O preço anunciado nas páginas continua em dólar. O real é forma de pagamento,
não oferta diferente.
"""
from __future__ import annotations

from app.core.config import settings

UFS_DO_BRASIL = frozenset({
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
})


def e_do_brasil(uf: str | None) -> bool:
    return (uf or "").strip().upper() in UFS_DO_BRASIL


def link_de_checkout(fundadora: bool, uf: str | None = None) -> tuple[str, str]:
    """
    Devolve (url, moeda) do checkout que esta marina deve abrir.

    Marina brasileira vai para o real: sem os 4,38% de IOF, sem o spread do
    cartao — que nao vem para nos, vai para o governo e para o banco dela — e
    com bandeira nacional (Elo, Hipercard), que em dolar nao passa de jeito
    nenhum. Em 19/08/2026 um Visa recusou US$ 250 com "moeda nao aceita"; foi
    o que trouxe esta regra.

    Sem nenhum link configurado devolve ("", ""), e quem chama decide o que
    fazer. Devolver URL vazia e ruim; devolver URL morta e pior, porque parece
    que funcionou.
    """
    em_real = (settings.STRIPE_LINK_MARINA_FUNDADORA_BRL if fundadora
               else settings.STRIPE_LINK_MARINA_OFICIAL_BRL) or ""
    em_dolar = (settings.STRIPE_LINK_MARINA_FUNDADORA if fundadora
                else settings.STRIPE_LINK_MARINA_OFICIAL) or ""

    if e_do_brasil(uf):
        preferencia = ((em_real, "brl"), (em_dolar, "usd"))
    else:
        preferencia = ((em_dolar, "usd"), (em_real, "brl"))

    for url, moeda in preferencia:
        if url.strip():
            return url.strip(), moeda
    return "", ""
