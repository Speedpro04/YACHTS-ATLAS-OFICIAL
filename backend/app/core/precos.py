"""
Yachts Atlas — Qual link de pagamento abrir.

Um lugar só. Antes a escolha estava em `leads.py` (cadastro novo) e em
`acesso.py` (marina bloqueada querendo voltar), e a LP de Lançamento tinha a
terceira cópia no `href` do botão. Quando os links em dólar foram desativados no
painel, em 26/08/2026, os três passaram a mandar gente para uma página que só
diz "The link is no longer active" — e nenhum deles sabia disso.

Preco unico: toda marina paga R$ 897/mes, em real.
"""
from __future__ import annotations

from app.core.config import settings

UFS_DO_BRASIL = frozenset({
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO", "MA", "MG", "MS",
    "MT", "PA", "PB", "PE", "PI", "PR", "RJ", "RN", "RO", "RR", "RS", "SC",
    "SE", "SP", "TO",
})


def link_de_checkout() -> tuple[str, str]:
    """
    Devolve (url, moeda) do checkout da marina: um preco so, um link so, em real.

    Sem link configurado devolve ("", ""), e quem chama decide o que fazer.
    Devolver URL vazia e ruim; devolver URL morta e pior, porque parece que
    funcionou. Os links antigos de fundadora e de R$ 1.250 nunca voltam daqui:
    a tela diz R$ 897 e o checkout precisa dizer o mesmo.
    """
    url = (settings.STRIPE_LINK_MARINA_BRL or "").strip()
    return (url, "brl") if url else ("", "")
