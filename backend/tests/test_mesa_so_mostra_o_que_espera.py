# -*- coding: utf-8 -*-
"""
Selado sai da mesa de trabalho — imagem e texto.

A mesa mostra o que ESPERA trabalho. Serviço selado não espera mais nada de
ninguém: virou prova, e prova mora no Painel Técnico e no dossiê.

O DEFEITO QUE ISTO FECHA. "Órfã" era definida por ausência: foto cujo
`client_id` não achava rascunho. Só que selar APAGA o rascunho — então, no
instante em que o serviço virava prova, as fotos dele passavam a ser anunciadas
como "sem registro que as explique", com o registro selado logo ali no dossiê.
A tela afirmava o contrário do que o banco dizia, e ficava assim para sempre.

Órfã de verdade é a foto que não tem registro em lugar nenhum — nem rascunho,
nem selo.
"""
import inspect

from app.api.v1 import registros


def test_a_mesa_consulta_os_registros_selados():
    """Sem olhar a tabela `registros`, 'órfã' volta a significar 'não achei o
    rascunho' — e todo serviço selado devolve as fotos dele para a mesa."""
    fonte = inspect.getsource(registros.listar_em_trabalho)
    assert 'table("registros")' in fonte, (
        "a mesa parou de consultar os selados — as fotos de serviço selado vão "
        "voltar a aparecer como órfãs"
    )
    assert "clients_selados" in fonte


def test_orfa_exclui_quem_tem_selo():
    fonte = inspect.getsource(registros.listar_em_trabalho)
    linha = [l for l in fonte.splitlines() if "orfas = " in l]
    assert linha, "não achei a definição de órfãs"
    assert "not in clients_selados" in linha[0], (
        "a exclusão dos selados saiu do cálculo das órfãs"
    )


def test_a_mesa_nao_devolve_bloco_de_selado():
    """Selado sai inteiro: nem no bloco de órfãs, nem num bloco próprio.
    Decisão do fundador em 15/09/2026."""
    fonte = inspect.getsource(registros.listar_em_trabalho)
    assert "fotos_de_servico_selado" not in fonte


def test_a_foto_aprovada_continua_fora():
    """Aprovada já cumpriu o caminho e entrou no dossiê. Ela não pede decisão
    de ninguém — e a regra antiga, que já valia, não pode se perder no meio
    desta mudança."""
    fonte = inspect.getsource(registros.listar_em_trabalho)
    assert 'f.get("status") == "pendente"' in fonte
