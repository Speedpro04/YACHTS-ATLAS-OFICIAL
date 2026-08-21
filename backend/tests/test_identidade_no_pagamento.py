"""
Regressão do vínculo entre quem se cadastra e quem paga.

É o bug mais caro que este sistema podia ter: **a marina paga e continua sem
acesso**.

O Payment Link é uma URL fixa e não carrega metadata. Sem identificação nela, o
webhook só tinha o e-mail do checkout para descobrir de quem era o pagamento —
e a carteira Link da Stripe usa o e-mail da CARTEIRA, que raramente é o mesmo
que a marina digitou no cadastro. Quando os dois não batiam, `user_id` ficava
nulo, o pagamento não era gravado em `payments` e o acesso NÃO era liberado.

Não é hipótese: aconteceu no teste com cartão real. A tabela `payments` ficou
vazia enquanto a cobrança tinha sido feita.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

from urllib.parse import parse_qs, urlparse

import pytest

from app.api.v1.leads import _link_com_identidade

BASE = "https://buy.stripe.com/test_abc123"
UID = "11111111-1111-1111-1111-111111111111"


def _params(url: str) -> dict:
    return {k: v[0] for k, v in parse_qs(urlparse(url).query).items()}


def test_link_leva_quem_esta_pagando():
    """Sem isto, o webhook não sabe de quem é o pagamento."""
    p = _params(_link_com_identidade(BASE, UID, "marina@exemplo.com"))
    assert p["client_reference_id"] == UID
    assert p["prefilled_email"] == "marina@exemplo.com"


def test_link_ja_com_query_nao_quebra():
    """Payment Link pode vir com parâmetro; concatenar com '?' faria uma URL inválida."""
    p = _params(_link_com_identidade(f"{BASE}?locale=pt-BR", UID, "m@e.com"))
    assert p["locale"] == "pt-BR"
    assert p["client_reference_id"] == UID


def test_sem_id_ainda_preenche_o_email():
    """
    Falhar em criar a conta não pode tirar da marina a chance de pagar.

    Sem o id, sobra o caminho antigo (casar pelo e-mail) — que é pior, mas é
    melhor que link nenhum. O `prefilled_email` aumenta a chance de o e-mail
    do checkout bater com o do cadastro.
    """
    p = _params(_link_com_identidade(BASE, None, "marina@exemplo.com"))
    assert "client_reference_id" not in p
    assert p["prefilled_email"] == "marina@exemplo.com"


def test_sem_nada_devolve_o_link_original():
    assert _link_com_identidade(BASE, None, None) == BASE


def test_link_vazio_nao_inventa_url():
    """Link não configurado tem que continuar vazio — e falhar visivelmente."""
    assert _link_com_identidade("", UID, "m@e.com") == ""


@pytest.mark.parametrize("email", ["marina+atlas@exemplo.com", "contato@marina-do-porto.com.br"])
def test_email_com_caractere_especial_e_escapado(email):
    """'+' cru na URL vira espaço e o preenchimento chega errado."""
    p = _params(_link_com_identidade(BASE, UID, email))
    assert p["prefilled_email"] == email


def test_webhook_prefere_o_link_ao_email():
    """
    A identidade do link vence o e-mail do checkout.

    É a metade que fecha o conserto: de nada adianta o link carregar o id se o
    webhook continuar procurando só pelo e-mail da carteira.
    """
    import inspect
    from app.services.stripe_service import StripeService

    fonte = inspect.getsource(StripeService._handle_checkout_completed)
    pos_link = fonte.index("client_reference_id")
    pos_email = fonte.index("buscar_usuario_por_email")
    assert pos_link < pos_email, (
        "O webhook precisa tentar o client_reference_id ANTES de cair no "
        "e-mail — senão a carteira Link continua deixando o pagamento órfão."
    )
