# -*- coding: utf-8 -*-
"""
Corrigir o dono do barco — a regra que a tela de edição depende.

POR QUE EXISTE (16/09/2026). O card Dados da Embarcação passou a EDITAR o
proprietário: a Marina corrige o WhatsApp, acrescenta o e-mail que faltava,
troca o dono quando o barco é vendido. A rota já existia e nunca tinha teste;
agora tem tela em cima dela, e três regras não podem escorregar sem ninguém
perceber:

  • SEM E-MAIL, O VÍNCULO CAI INTEIRO. É o caminho de barco vendido: guardar
    o telefone e o nome de quem vendeu seria manter dado pessoal sem uso — e o
    dono antigo continuaria aparecendo no dossiê como titular;
  • o e-mail é gravado em MINÚSCULAS, senão o armador não acha o próprio barco
    porque a Marina digitou "Roberto@Email.com";
  • o documento é mascarado NA ENTRADA, e reenviar o mascarado (é o que a tela
    faz, porque é o que ela recebeu do banco) não pode estragá-lo.
"""
import asyncio
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1 import ativos as api_ativos
from app.api.v1.ativos import ProprietarioDoAtivo, definir_proprietario

MARINA = "11111111-1111-1111-1111-111111111111"
BARCO = "YA-IATE-2015-3A38"


class _Tabela:
    def __init__(self, banco, nome):
        self._banco = banco
        self._nome = nome

    def select(self, *a, **k):
        return self

    def update(self, dados):
        self._banco.gravado = dados
        return self

    def eq(self, *a, **k):
        return self

    def execute(self):
        if self._nome == "ativos":
            return types.SimpleNamespace(data=[{"id": BARCO, "usuario_id": MARINA}])
        return types.SimpleNamespace(data=[{"user_role": "marina_manager"}])


class _Banco:
    def __init__(self):
        self.gravado = None

    def table(self, nome):
        return _Tabela(self, nome)


@pytest.fixture
def banco(monkeypatch):
    b = _Banco()
    monkeypatch.setattr(api_ativos, "get_supabase_admin", lambda: b)
    return b


def _salvar(dados):
    # asyncio.run em vez de pytest-asyncio: a suíte não tem o plugin, e um
    # endpoint async não justifica uma dependência nova.
    return asyncio.run(definir_proprietario(BARCO, ProprietarioDoAtivo(**dados), user_id=MARINA))


def test_corrigir_o_whatsapp_mantem_o_resto(banco):
    """O caso do dia a dia: o dono trocou de número."""
    _salvar({
        "proprietario_email": "roberto@email.com",
        "proprietario_telefone": "+5512991187251",
        "proprietario_nome": "Roberto Alves",
    })
    assert banco.gravado["proprietario_telefone"] == "+5512991187251"
    assert banco.gravado["proprietario_nome"] == "Roberto Alves"
    assert banco.gravado["proprietario_email"] == "roberto@email.com"


def test_email_gravado_em_minusculas(banco):
    _salvar({"proprietario_email": "Roberto@Email.COM"})
    assert banco.gravado["proprietario_email"] == "roberto@email.com"


def test_sem_email_o_vinculo_cai_inteiro(banco):
    """Barco vendido: não guarda contato nem identidade de quem vendeu."""
    r = _salvar({
        "proprietario_email": None,
        "proprietario_telefone": "+5512991187251",
        "proprietario_nome": "Roberto Alves",
        "proprietario_documento": "123.456.789-00",
    })
    assert banco.gravado == {
        "proprietario_email": None,
        "proprietario_telefone": None,
        "proprietario_nome": None,
        "proprietario_documento": None,
    }
    assert "removido" in r["message"]


def test_documento_completo_nunca_chega_ao_banco(banco):
    _salvar({
        "proprietario_email": "roberto@email.com",
        "proprietario_documento": "123.456.789-00",
    })
    assert banco.gravado["proprietario_documento"] == "***.456.789-**"


def test_reenviar_o_mascarado_nao_estraga(banco):
    """A tela devolve o que leu — e o que ela lê já está mascarado."""
    _salvar({
        "proprietario_email": "roberto@email.com",
        "proprietario_documento": "***.456.789-**",
    })
    assert banco.gravado["proprietario_documento"] == "***.456.789-**"
