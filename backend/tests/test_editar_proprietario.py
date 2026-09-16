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

import inspect

import pytest
from fastapi import HTTPException

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

    def insert(self, dados):
        self._banco.inseridos.append(dados)
        return self

    def eq(self, *a, **k):
        return self

    def limit(self, *a, **k):
        return self

    def execute(self):
        if self._nome == "ativos":
            return types.SimpleNamespace(data=[{
                "id": BARCO, "usuario_id": MARINA,
                "proprietario_nome": self._banco.dono_atual,
                "proprietario_email": "antigo@email.com" if self._banco.dono_atual else None,
            }])
        if self._nome == "registros":
            return types.SimpleNamespace(data=self._banco.cadeia)
        return types.SimpleNamespace(data=[{"user_role": "marina_manager"}])


class _Banco:
    def __init__(self, dono_atual="Roberto Alves", cadeia=None):
        self.gravado = None
        self.inseridos = []
        self.dono_atual = dono_atual
        # O que já existe na cadeia de proprietários deste barco.
        self.cadeia = cadeia or []

    def table(self, nome):
        return _Tabela(self, nome)


@pytest.fixture
def banco(monkeypatch):
    b = _Banco()
    monkeypatch.setattr(api_ativos, "get_supabase_admin", lambda: b)
    return b


@pytest.fixture
def instalar(monkeypatch):
    def _instalar(**kw):
        b = _Banco(**kw)
        monkeypatch.setattr(api_ativos, "get_supabase_admin", lambda: b)
        return b
    return _instalar


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


# --- transferência de propriedade -------------------------------------------
#
# Barco vendido que CONTINUA na mesma Marina: muda o dono, não muda o
# histórico. O dossiê tem uma seção para isso ("02 — Histórico de
# Proprietários") e ela só se enchia à mão. Agora a Marina diz, ao salvar, se
# foi correção ou transferência — e só a segunda vira elo da cadeia.


def _transferir(banco, **extra):
    dados = {
        "proprietario_email": "comprador@email.com",
        "proprietario_nome": "Ana Beatriz Lima",
        "evento": "transferencia",
        "tipo_transferencia": "Compra e Venda",
        "data_transferencia": "2026-09-16",
    }
    dados.update(extra)
    return _salvar(dados)


def test_correcao_nao_escreve_no_dossie(instalar):
    """O caso mais comum é o e-mail digitado errado. Virar elo da cadeia
    encheria a prova de erro de digitação."""
    banco = instalar()
    _salvar({"proprietario_email": "roberto@email.com", "evento": "correcao"})
    assert banco.inseridos == []


def test_sem_dizer_o_evento_nada_e_registrado(instalar):
    """Quem chama a rota sem o campo novo continua no comportamento de sempre."""
    banco = instalar()
    _salvar({"proprietario_email": "roberto@email.com"})
    assert banco.inseridos == []


def test_transferencia_fecha_o_antigo_e_abre_o_novo(instalar):
    banco = instalar()
    r = _transferir(banco)
    assert r["transferencia_registrada"] == 2
    antigo, novo = banco.inseridos
    assert antigo["dados"] == {
        "nome": "Roberto Alves", "periodo": "até 16/09/2026",
        "tipo": "Proprietário Original",
    }
    assert novo["dados"] == {
        "nome": "Ana Beatriz Lima", "periodo": "desde 16/09/2026",
        "tipo": "Compra e Venda",
    }
    assert all(i["categoria"] == "proprietarios" for i in banco.inseridos)


def test_periodo_nao_inventa_data_de_inicio(instalar):
    """A plataforma não sabe quando o dono anterior comprou o barco — sabe
    quando ele saiu. 'até' e 'desde' são verdade; '2019 – 2026' seria chute."""
    banco = instalar()
    _transferir(banco)
    periodos = [i["dados"]["periodo"] for i in banco.inseridos]
    assert periodos == ["até 16/09/2026", "desde 16/09/2026"]


def test_cadeia_ja_existente_nao_ganha_dono_duplicado(instalar):
    """Se a Marina já lançou o histórico à mão, repetir o antigo inventaria
    um proprietário a mais."""
    banco = instalar(cadeia=[{"id": "reg-1"}])
    r = _transferir(banco)
    assert r["transferencia_registrada"] == 1
    assert banco.inseridos[0]["dados"]["nome"] == "Ana Beatriz Lima"


def test_barco_sem_dono_anterior_so_abre_o_novo(instalar):
    banco = instalar(dono_atual=None)
    r = _transferir(banco)
    assert r["transferencia_registrada"] == 1


def test_tipo_invalido_e_recusado(instalar):
    """O dossiê imprime este texto. 'Sei lá' não pode virar tipo de
    transferência num documento que circula entre corretor e seguradora."""
    instalar()
    with pytest.raises(HTTPException) as erro:
        _transferir(None, tipo_transferencia="Sei lá")
    assert erro.value.status_code == 400


def test_o_registro_da_transferencia_e_imutavel(instalar):
    """Insert, nunca update: a cadeia é append-only como o resto da custódia."""
    banco = instalar()
    _transferir(banco)
    fonte = inspect.getsource(api_ativos._registrar_transferencia)
    assert ".insert(" in fonte
    assert ".update(" not in fonte
