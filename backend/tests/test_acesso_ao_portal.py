# -*- coding: utf-8 -*-
"""
O card Dados da Embarcação diz se o dono já entrou no Portal.

POR QUE EXISTE (15/09/2026). Depois de salvo, o cadastro do barco não aparecia
em tela nenhuma — nem o e-mail do dono. A Marina não tinha como saber se o
cliente dela usava o Portal, nem por que o código "não chegou". Três barcos de
teste estavam com WhatsApp e SEM e-mail: o dono deles nunca teria entrado, e
nada na tela avisava.

O que estes testes protegem é a honestidade da resposta. A tentação é mostrar
o último login da conta que tem aquele e-mail — mas se o e-mail for o da própria
Marina, "último acesso ontem" seria o gerente, não o dono.
"""
import inspect
import os
import types
from datetime import datetime, timezone

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

from app.api.v1 import ativos
from app.api.v1.ativos import _situacao_do_portal


def _conta(perfil="armador", ultimo=None):
    return types.SimpleNamespace(
        email="roberto@email.com",
        user_metadata={"perfil": perfil} if perfil else {},
        last_sign_in_at=ultimo,
    )


def _nunca_chamar(_):
    raise AssertionError("sem e-mail não pode nem perguntar ao Auth")


def test_sem_email_nao_consulta_nada():
    for vazio in (None, "", "   "):
        assert _situacao_do_portal(vazio, buscar=_nunca_chamar) == {
            "situacao": "sem_email", "ultimo_acesso": None,
        }


def test_sem_conta_e_nunca_entrou():
    assert _situacao_do_portal("roberto@email.com", buscar=lambda e: None)["situacao"] == "nunca_entrou"


def test_conta_criada_sem_login_e_nunca_entrou():
    """A conta nasce quando o código é PEDIDO. Pedir não é entrar."""
    r = _situacao_do_portal("roberto@email.com", buscar=lambda e: _conta(ultimo=None))
    assert r == {"situacao": "nunca_entrou", "ultimo_acesso": None}


def test_armador_que_entrou_traz_a_data():
    quando = datetime(2026, 8, 24, 2, 59, tzinfo=timezone.utc)
    r = _situacao_do_portal("roberto@email.com", buscar=lambda e: _conta(ultimo=quando))
    assert r["situacao"] == "entrou"
    assert r["ultimo_acesso"].startswith("2026-08-24")


def test_email_de_outra_conta_nao_mostra_o_login_dela():
    """E-mail da própria Marina gravado como dono: o login é do gerente."""
    quando = datetime(2026, 9, 15, tzinfo=timezone.utc)
    for perfil in (None, "marina"):
        r = _situacao_do_portal("gerente@marina.com", buscar=lambda e, p=perfil: _conta(perfil=p, ultimo=quando))
        assert r == {"situacao": "outra_conta", "ultimo_acesso": None}


def test_busca_em_minusculas():
    vistos = []
    _situacao_do_portal("  Roberto@Email.COM ", buscar=lambda e: vistos.append(e))
    assert vistos == ["roberto@email.com"]


def test_so_a_marina_dona_pergunta():
    """O armador lê o barco, mas esta pergunta é da Marina — mesma trava do
    PATCH do proprietário: dono do ativo ou admin."""
    fonte = inspect.getsource(ativos.acesso_do_proprietario)
    assert 'str(achado.data[0].get("usuario_id")) != str(user_id)' in fonte
    assert "403" in fonte
    assert "proprietario_email.eq" not in fonte
