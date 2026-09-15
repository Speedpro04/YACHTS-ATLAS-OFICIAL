# -*- coding: utf-8 -*-
"""
A miniatura nunca pode derrubar o original.

O QUE ACONTECEU EM 15/09/2026. A assinatura da miniatura entrou dentro do mesmo
`try` que assina o arquivo original — e o `except` daquele bloco zera o `url`.
Foto anterior à mudança não tem miniatura, então assinar um caminho que não
existe levantava exceção e levava o `url` da foto boa junto: três fotos
perfeitamente legíveis viraram ícone de câmera na tela de revisão.

O acessório derrubou o essencial, que é o oposto do que aquele bloco existe
para fazer. Este teste lê o código e exige que as duas assinaturas vivam em
blocos separados.

É um teste de forma, e não de comportamento, porque o comportamento depende do
storage. Preso ao texto? Sim — e é isso mesmo: a regra aqui é estrutural.
"""
import inspect

from app.api.v1 import registros


def _blocos_de_assinatura(fonte: str) -> list[str]:
    """Os trechos entre cada `try:` e o `except` que o fecha."""
    partes = []
    for pedaco in fonte.split("try:")[1:]:
        partes.append(pedaco.split("except")[0])
    return partes


def test_o_original_e_a_miniatura_assinam_em_blocos_separados():
    for funcao in (registros.listar_em_trabalho, registros.listar_pre_data):
        fonte = inspect.getsource(funcao)
        juntos = [
            b for b in _blocos_de_assinatura(fonte)
            if "get_presigned_url(caminho," in b and "caminho_da_miniatura" in b
        ]
        assert not juntos, (
            f"{funcao.__name__}: a miniatura voltou para o try do original — "
            "foto sem miniatura vai zerar a URL da foto boa"
        )


def test_a_falha_da_miniatura_nao_apaga_o_url():
    """O `except` da miniatura não pode encostar no campo do original."""
    for funcao in (registros.listar_em_trabalho, registros.listar_pre_data):
        fonte = inspect.getsource(funcao)
        depois_da_mini = fonte.split("caminho_da_miniatura")[-1]
        # Até o fim do tratamento de erro daquele bloco.
        trecho = depois_da_mini.split("alvo")[0] if "alvo" in depois_da_mini else depois_da_mini
        assert 'f["url"] = None' not in trecho, (
            f"{funcao.__name__}: o except da miniatura está zerando o url do original"
        )


def test_as_duas_telas_oferecem_miniatura():
    """Se uma delas parar de oferecer, volta a baixar 3 MB por quadradinho."""
    for funcao in (registros.listar_em_trabalho, registros.listar_pre_data):
        assert "url_miniatura" in inspect.getsource(funcao), (
            f"{funcao.__name__} parou de oferecer a miniatura"
        )
