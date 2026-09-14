"""
O aparelho do pátio entra sem a senha da Marina — e não alcança mais nada.

Até aqui o colaborador do píer usava a conta da própria Marina, e com ela podia
selar registro, emitir dossiê, liberar documento a terceiro e ver a frota
inteira. O código de campo separa isso.

O teste mais importante deste arquivo é o do FAIL-CLOSED: o token de campo é
recusado por `get_current_user`, a porta de todo o sistema, e só passa nas três
rotas que o abrem de propósito. Rota escrita amanhã por alguém que nunca leu o
`core/campo.py` já nasce fechada — e é isso que precisa continuar verdadeiro.
"""
import inspect

import pytest
from fastapi import HTTPException

from app.core import campo as nucleo


# --- o código em si ---

def test_codigo_nao_tem_caractere_ambiguo():
    # Ele é ditado por telefone e digitado no sol, com a mão suja. Zero e "O",
    # um e "I" viram chamado de suporte, não erro de digitação.
    for _ in range(40):
        gerado = nucleo.gerar_codigo().replace("-", "")
        assert not set(gerado) & set("O0I1L")
        assert len(gerado) == 8


def test_hash_ignora_formato_mas_nao_o_conteudo():
    # A pessoa digita com hífen, sem hífen, em minúscula. Nada disso muda o
    # código; trocar uma letra muda.
    igual = {nucleo._hash("ABCD-2345"), nucleo._hash("abcd2345"), nucleo._hash(" ABCD-2345 ")}
    assert len(igual) == 1
    assert nucleo._hash("ABCD-2345") != nucleo._hash("ABCD-2346")


def test_codigo_em_claro_nunca_e_devolvido_depois():
    """`criar_codigo` é o único ponto que vê o código; o resto só tem hash.

    Escrito contra a assinatura de propósito: se alguém mais tarde acrescentar
    um campo "codigo" ao retorno da listagem, este teste não pega — mas o
    `listar_codigos` seleciona coluna por coluna, e `codigo_hash` não está lá.
    """
    from app.api.v1 import campo as rotas
    fonte = inspect.getsource(rotas.listar_codigos)
    assert "codigo_hash" not in fonte


# --- fail-closed: o token de campo não abre o sistema ---

def _rotas_que_aceitam_campo() -> set[str]:
    """As rotas cuja dependência aceita o token do aparelho."""
    from app.api.v1.router import router
    aceitam = set()
    for rota in getattr(router, "routes", []):
        for dep in getattr(getattr(rota, "dependant", None), "dependencies", []) or []:
            nome = getattr(dep.call, "__name__", "")
            if nome in ("usuario_ou_campo", "_id_usuario_ou_campo"):
                aceitam.add(f"{sorted(rota.methods)[0]} {rota.path}")
    return aceitam


def test_apenas_o_necessario_aceita_o_aparelho_do_patio():
    """Três rotas, e só três.

    Se esta lista crescer sem alguém pensar duas vezes, o código de campo deixa
    de ser um acesso restrito e vira uma segunda senha da Marina — que é
    exatamente o problema que ele veio resolver.
    """
    esperado = {
        "POST /registros/rascunho",          # mandar o pré-dado
        "POST /documentos/upload/{ativo_id}",  # subir a foto (sempre pendente)
        "GET /ativos",                        # escolher o barco
    }
    assert _rotas_que_aceitam_campo() == esperado


@pytest.mark.parametrize("caminho", [
    "/registros/rascunho/{rascunho_id}/selar",
    "/registros/rascunho/{rascunho_id}/enviar-para-ativos",
    "/dossie/{ativo_id}/pdf",
    "/documentos/{doc_id}/aprovar",
    "/campo/codigos",
])
def test_o_que_nao_pode_continua_fechado(caminho):
    assert not any(caminho in r for r in _rotas_que_aceitam_campo())


# --- revogação ---

def test_codigo_revogado_nao_vira_token(monkeypatch):
    """Revogar vale na hora, e não quando o token vencer.

    Celular perdido às 9h não pode continuar mandando registro até o fim da
    semana — por isso cada requisição confere a linha no banco, e não só a
    assinatura do token.
    """
    class _Resp:
        data = [{"id": "x", "usuario_id": "u", "revogado_em": "2026-09-14T10:00:00Z"}]

    class _Tabela:
        def select(self, *a, **k): return self
        def eq(self, *a, **k): return self
        def limit(self, *a, **k): return self
        def execute(self): return _Resp()

    monkeypatch.setattr(nucleo, "get_supabase_admin", lambda: type("S", (), {"table": lambda self, n: _Tabela()})())

    with pytest.raises(HTTPException) as erro:
        nucleo.token_do_codigo("ABCD-2345")
    assert erro.value.status_code == 401


def test_recusa_nao_diz_qual_dos_dois_motivos():
    # "Inválido" e "revogado" dão a mesma resposta: dizer qual dos dois entrega
    # meia informação a quem está tentando adivinhar código.
    fonte = inspect.getsource(nucleo.token_do_codigo)
    assert fonte.count("Código inválido ou revogado.") == 1
