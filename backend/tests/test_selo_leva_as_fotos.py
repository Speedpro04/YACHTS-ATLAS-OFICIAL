# -*- coding: utf-8 -*-
"""
Selar um serviço leva as fotos dele junto.

O QUE ESTE ARQUIVO IMPEDE DE VOLTAR. Até 15/09/2026, selar gravava o registro
na tabela imutável e apagava o rascunho — e as fotos ficavam `pendente` para
sempre. Como era o rascunho que as amarrava ao serviço (pelo `client_id` na
descrição), apagá-lo cortava o vínculo: a foto virava "imagem desta embarcação
sem registro que a explique".

O dossiê exclui documento pendente de propósito (ver `dossie_data`), então o
efeito final era o pior possível: o serviço ia para o documento probatório
**sem a prova**. Aconteceu no ensaio do Fenix Blue — motor selado, três fotos
boas no cofre, nenhuma no PDF.
"""
import types

import pytest

from app.api.v1 import registros


class _Tabela:
    def __init__(self, banco, nome):
        self.banco = banco
        self.nome = nome
        self._update = None
        self._filtros = {}

    def select(self, *a, **k):
        return self

    def update(self, payload):
        self._update = payload
        return self

    def eq(self, campo, valor):
        self._filtros[campo] = valor
        return self

    def execute(self):
        if self._update is not None:
            self.banco.updates.append((self._filtros.get("id"), self._update))
            return types.SimpleNamespace(data=[])
        return types.SimpleNamespace(data=list(self.banco.pendentes))


class _Banco:
    def __init__(self, pendentes):
        self.pendentes = pendentes
        self.updates = []

    def table(self, nome):
        return _Tabela(self, nome)


CLIENT_ID = "c4996dd2-d0a7-4c1d-b5a9-542341796fee"


def _rascunho(client_id=CLIENT_ID):
    return {"ativo_id": "YA-IATE-2021-5A4E", "dados": {"client_id": client_id}}


def test_as_fotos_do_servico_sao_aprovadas_com_o_selo():
    banco = _Banco([
        {"id": "f1", "descricao": f"Atlas Pré-Data · Motor · {CLIENT_ID}"},
        {"id": "f2", "descricao": f"Atlas Pré-Data · Motor · {CLIENT_ID}"},
    ])

    aprovadas = registros._aprovar_as_fotos_do_servico(banco, _rascunho(), "quem-selou")

    assert set(aprovadas) == {"f1", "f2"}
    for _id, mudanca in banco.updates:
        assert mudanca["status"] == "verified"
        assert mudanca["validado_em"]


def test_nao_encosta_na_foto_de_outro_envio():
    """Dois serviços no mesmo barco, no mesmo dia. Selar um não pode aprovar a
    evidência do outro — que talvez o revisor ainda vá recusar."""
    banco = _Banco([
        {"id": "minha", "descricao": f"Atlas Pré-Data · Motor · {CLIENT_ID}"},
        {"id": "alheia", "descricao": "Atlas Pré-Data · Casco · outro-client-id"},
    ])

    aprovadas = registros._aprovar_as_fotos_do_servico(banco, _rascunho(), "quem-selou")

    assert aprovadas == ["minha"]
    assert [i for i, _ in banco.updates] == ["minha"]


def test_client_id_parecido_nao_casa():
    """A comparação é pelo FIM da descrição, não por `in`: um id que contém o
    outro casaria os dois e aprovaria foto que ninguém conferiu."""
    banco = _Banco([
        {"id": "parecida", "descricao": f"Atlas Pré-Data · Motor · x{CLIENT_ID}y"},
    ])

    assert registros._aprovar_as_fotos_do_servico(banco, _rascunho(), "q") == []
    assert banco.updates == []


def test_sem_client_id_nao_aprova_nada():
    """Registro criado direto no painel não tem `client_id`. Sem ele, aprovar
    'as fotos do serviço' seria aprovar as fotos de qualquer serviço."""
    banco = _Banco([{"id": "f1", "descricao": "Atlas Pré-Data · Motor · algum-id"}])

    assert registros._aprovar_as_fotos_do_servico(banco, {"ativo_id": "x", "dados": {}}, "q") == []
    assert banco.updates == []


def test_falha_de_leitura_nao_derruba_o_selo():
    """A esta altura o registro já está na tabela append-only e não há volta.
    Falhar aqui devolve o estado de antes — foto pendente, recuperável na aba
    Pré-Data — em vez de estourar em cima de um selo que já existe."""
    class _Quebrado:
        def table(self, nome):
            raise RuntimeError("banco fora do ar")

    assert registros._aprovar_as_fotos_do_servico(_Quebrado(), _rascunho(), "q") == []


def test_o_selo_chama_a_aprovacao_antes_de_apagar_o_rascunho():
    """A ordem importa: é o rascunho que guarda o `client_id`. Apagar primeiro
    seria perder o vínculo — exatamente o bug que isto conserta."""
    import inspect
    fonte = inspect.getsource(registros.selar_rascunho)
    chamada = fonte.index("_aprovar_as_fotos_do_servico")
    delete = fonte.index('registros_rascunho").delete()')
    assert chamada < delete, "a aprovação das fotos passou para depois do delete"
