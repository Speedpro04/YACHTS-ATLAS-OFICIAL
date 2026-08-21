"""
Regressão do registro de indicação.

A página promete: *"Marinas parceiras que indicam novos membros participam dos
dossiês gerados pela indicada durante o período fundador."*

É o motor que leva de 20 para 40 marinas — e o vínculo **só pode ser capturado
no cadastro**. Depois ninguém lembra quem indicou quem: nem a fundadora, nem a
indicada. Não existe reconstruir isso a partir do banco.

Por isso a regra mais importante aqui não é casar o registro certo — é **nunca
descartar o que a marina digitou**. Ela escreve o que lembra: "Marina do
Porto", "falei com o João lá da náutica", um e-mail com typo. Se o sistema só
guardasse o que consegue resolver sozinho, o resto viraria promessa sem prova.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1.leads import _registrar_indicacao


class _Consulta:
    """Dublê encadeável do query builder do Supabase."""

    def __init__(self, banco, tabela):
        self._banco = banco
        self._tabela = tabela
        self._filtros = []
        self._update = None

    def select(self, *a, **k):
        return self

    def update(self, valores):
        self._update = valores
        return self

    def ilike(self, coluna, valor):
        self._filtros.append(("ilike", coluna, valor.strip("%").lower()))
        return self

    def eq(self, coluna, valor):
        self._filtros.append(("eq", coluna, valor))
        return self

    def neq(self, coluna, valor):
        self._filtros.append(("neq", coluna, valor))
        return self

    def limit(self, n):
        return self

    def execute(self):
        if self._update is not None:
            alvo = next((v for op, c, v in self._filtros if c == "slot"), None)
            for linha in self._banco.linhas:
                if linha["slot"] == alvo:
                    linha.update(self._update)
                    self._banco.updates.append((alvo, dict(self._update)))
            return types.SimpleNamespace(data=[])

        achados = []
        for linha in self._banco.linhas:
            ok = True
            for op, coluna, valor in self._filtros:
                atual = str(linha.get(coluna) or "").lower()
                if op == "ilike" and valor not in atual:
                    ok = False
                elif op == "neq" and linha.get(coluna) == valor:
                    ok = False
            if ok:
                achados.append(linha)
        return types.SimpleNamespace(data=achados[:1])


class _Banco:
    def __init__(self, linhas):
        self.linhas = linhas
        self.updates = []

    def table(self, nome):
        return _Consulta(self, nome)


def _cenario():
    return _Banco([
        {"slot": 1, "email": "fundadora@marina.com", "marina_nome": "Marina do Porto",
         "indicacoes_feitas": 0, "indicada_por_slot": None, "indicada_por_texto": None},
        {"slot": 7, "email": "nova@marina.com", "marina_nome": "Náutica Bela",
         "indicacoes_feitas": 0, "indicada_por_slot": None, "indicada_por_texto": None},
    ])


def _dados(indicada_por):
    return types.SimpleNamespace(email="nova@marina.com", indicada_por=indicada_por)


# --------------------------------------------------------------------------
# O texto nunca se perde
# --------------------------------------------------------------------------

@pytest.mark.parametrize("digitado", [
    "Marina do Porto",
    "fundadora@marina.com",
    "falei com o Joao la da nautica",     # não casa com ninguém
    "marina do porrto",                    # typo
])
def test_o_que_ela_digitou_fica_guardado(digitado):
    """
    Vale inclusive quando não casa com registro nenhum.

    O que não resolve sozinho, o fundador resolve à mão olhando o texto — com
    20 marinas isso é trabalho de minutos. Perder o dado não tem conserto.
    """
    banco = _cenario()
    _registrar_indicacao(banco, _dados(digitado))
    nova = next(l for l in banco.linhas if l["slot"] == 7)
    assert nova["indicada_por_texto"] == digitado


def test_email_da_indicante_casa_e_conta_sobe():
    banco = _cenario()
    _registrar_indicacao(banco, _dados("fundadora@marina.com"))
    assert next(l for l in banco.linhas if l["slot"] == 7)["indicada_por_slot"] == 1
    assert next(l for l in banco.linhas if l["slot"] == 1)["indicacoes_feitas"] == 1


def test_nome_da_indicante_tambem_casa():
    """A marina lembra do NOME de quem indicou, raramente do e-mail."""
    banco = _cenario()
    _registrar_indicacao(banco, _dados("Marina do Porto"))
    assert next(l for l in banco.linhas if l["slot"] == 7)["indicada_por_slot"] == 1


def test_sem_correspondencia_nao_inventa_vinculo():
    """
    Creditar a indicação errada é pior que não creditar: vira dinheiro para
    quem não trouxe ninguém, e o certo continua sem receber.
    """
    banco = _cenario()
    _registrar_indicacao(banco, _dados("uma marina que nao existe"))
    nova = next(l for l in banco.linhas if l["slot"] == 7)
    assert nova["indicada_por_slot"] is None
    assert nova["indicada_por_texto"] == "uma marina que nao existe"
    assert next(l for l in banco.linhas if l["slot"] == 1)["indicacoes_feitas"] == 0


def test_ninguem_indica_a_si_mesma():
    """Sem o `neq`, digitar o próprio nome creditaria a indicação a si mesma."""
    banco = _cenario()
    _registrar_indicacao(banco, _dados("Náutica Bela"))
    nova = next(l for l in banco.linhas if l["slot"] == 7)
    assert nova["indicada_por_slot"] is None


# --------------------------------------------------------------------------
# Nunca atrapalha o cadastro
# --------------------------------------------------------------------------

def test_campo_vazio_nao_faz_nada():
    for vazio in (None, "", "   "):
        banco = _cenario()
        _registrar_indicacao(banco, _dados(vazio))
        assert banco.updates == []


def test_banco_fora_do_ar_nao_derruba_o_cadastro():
    """
    O cadastro e o pagamento valem mais que o registro da indicação.

    Falhar aqui não pode impedir a marina de entrar e pagar — o vínculo se
    resolve depois; a venda perdida, não.
    """
    class _Quebrado:
        def table(self, nome):
            raise RuntimeError("banco fora do ar")

    _registrar_indicacao(_Quebrado(), _dados("Marina do Porto"))  # não levanta
