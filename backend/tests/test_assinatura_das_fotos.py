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


# --- nao pedir o que nao existe -------------------------------------------

def test_a_miniatura_so_e_assinada_para_quem_tem():
    """Foto anterior a 15/09/2026 nao tem miniatura.

    Pedir a assinatura assim mesmo custava uma ida perdida ao storage por foto
    E escrevia ERROR no log — para uma condicao normal e prevista. ERROR que
    toca a toa ensina a ignorar ERROR, e ai o que toca de verdade passa batido.

    A coluna `tem_miniatura` responde antes de perguntar ao storage.
    """
    for funcao in (registros.listar_em_trabalho, registros.listar_pre_data):
        fonte = inspect.getsource(funcao)
        assert 'if f.get("tem_miniatura")' in fonte, (
            f"{funcao.__name__}: voltou a assinar miniatura sem perguntar se existe"
        )


def test_a_consulta_traz_a_coluna():
    """Sem ela no select, `tem_miniatura` vem vazio e NENHUMA miniatura e
    assinada — as telas voltariam a baixar o original de 3 MB."""
    for funcao in (registros.listar_em_trabalho, registros.listar_pre_data):
        fonte = inspect.getsource(funcao)
        # O select da foto e o que traz storage_path; a coluna tem que vir com ele.
        selects = [b for b in fonte.split("select(") if "storage_path" in b[:400]]
        assert selects, f"{funcao.__name__}: nao achei o select das fotos"
        assert any("tem_miniatura" in b[:400] for b in selects), (
            f"{funcao.__name__}: a coluna saiu do select"
        )


def test_o_upload_so_marca_se_o_envio_deu_certo():
    """Marcar por otimismo devolveria o erro que a coluna veio eliminar."""
    from app.api.v1 import documentos
    fonte = inspect.getsource(documentos.upload_documento)
    assert 'tem_miniatura = envio.get("status") == "success"' in fonte
