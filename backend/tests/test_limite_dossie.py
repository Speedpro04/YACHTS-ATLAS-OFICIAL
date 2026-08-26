"""
Limite de emissões de dossiê por ativo.

A regra comercial é **4 por ano, por embarcação**. Ela existia só no
`localStorage` do navegador, numa chave por ativo — e por isso não era regra
nenhuma:

* o número na tela mudava conforme o navegador. A marina emitia três no Chrome
  e o Edge continuava mostrando "4 restantes", porque cada janela contava
  sozinha. Foi assim que apareceu, em 26/08/2026: três dossiês emitidos, três
  telas dizendo que nenhum havia saído;
* e trocar de navegador, limpar os dados do site ou apagar uma chave no console
  liberava emissão sem fim. O servidor gerava o PDF sem perguntar quantos já
  tinham saído.

O banco sempre soube: `dossie_emitidos` registra cada emissão com hash e hora.
Faltava a tela perguntar a ele — e o servidor recusar.
"""
import os
import types
from datetime import date, timedelta

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import app.api.v1.dossie as dossie
from app.core.config import settings


class _Consulta:
    """Dublê encadeável do query builder, devolvendo emissões fixas."""

    def __init__(self, linhas):
        self._linhas = linhas

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def gte(self, *a, **k):
        return self

    def order(self, *a, **k):
        return self

    def execute(self):
        return types.SimpleNamespace(data=self._linhas, count=len(self._linhas))


def _banco(qtd_emissoes, dias_atras=30):
    """Banco com `qtd_emissoes` dossiês emitidos há `dias_atras` dias."""
    dia = (date.today() - timedelta(days=dias_atras)).isoformat()
    linhas = [{"emitido_em": dia} for _ in range(qtd_emissoes)]
    return types.SimpleNamespace(table=lambda _nome: _Consulta(linhas))


def _com_banco(monkeypatch, banco):
    monkeypatch.setattr(dossie, "get_supabase_admin", lambda: banco)


def test_ativo_sem_emissao_tem_o_limite_inteiro(monkeypatch):
    _com_banco(monkeypatch, _banco(0))
    s = dossie._saldo_dossie("YA-IATE-2020-XXXX")
    assert s["usados"] == 0
    assert s["restantes"] == settings.DOSSIE_LIMITE_ANUAL
    assert s["permitido"] is True


def test_saldo_desconta_o_que_ja_saiu(monkeypatch):
    """É o caso real de 26/08/2026: um dossiê emitido, três restantes."""
    _com_banco(monkeypatch, _banco(1))
    s = dossie._saldo_dossie("YA-IATE-2020-XXXX")
    assert s["usados"] == 1
    assert s["restantes"] == settings.DOSSIE_LIMITE_ANUAL - 1
    assert s["permitido"] is True


def test_no_limite_o_saldo_zera_e_recusa(monkeypatch):
    _com_banco(monkeypatch, _banco(settings.DOSSIE_LIMITE_ANUAL))
    s = dossie._saldo_dossie("YA-IATE-2020-XXXX")
    assert s["restantes"] == 0
    assert s["permitido"] is False


def test_esgotado_diz_QUANDO_volta_a_poder(monkeypatch):
    """
    Recusar sem dizer até quando é pior que recusar: a marina precisa responder
    ao cliente. A vaga abre 12 meses depois da emissão MAIS ANTIGA ainda dentro
    da janela — é ela que sai da contagem primeiro.
    """
    _com_banco(monkeypatch, _banco(settings.DOSSIE_LIMITE_ANUAL, dias_atras=100))
    s = dossie._saldo_dossie("YA-IATE-2020-XXXX")
    esperado = (date.today() - timedelta(days=100) + timedelta(days=365)).isoformat()
    assert s["reset_em"] == esperado


def test_banco_fora_do_ar_nao_trava_a_marina(monkeypatch):
    """
    Falha ao apurar o saldo não pode impedir a emissão — o servidor ainda tem a
    trava no endpoint. Melhor deixar passar e recusar lá do que travar a marina
    por causa de uma consulta de contagem.
    """
    def _explode():
        raise RuntimeError("banco fora do ar")
    monkeypatch.setattr(dossie, "get_supabase_admin", _explode)
    s = dossie._saldo_dossie("YA-IATE-2020-XXXX")
    assert s["permitido"] is True
    assert s["usados"] == 0


# --------------------------------------------------------------------------
# Categorias de saúde por tipo de embarcação
# --------------------------------------------------------------------------

def test_barco_a_motor_nao_tem_velame():
    """
    Um Fibrafort Focker saiu com "VELAME & RIGGING · NÃO AVALIADO" no relatório
    entregue ao comprador. Categoria que nunca poderá ser preenchida entra na
    conta como buraco permanente e faz o barco parecer incompleto por algo que
    não existe nele.
    """
    from app.services.dossie_data import categorias_do_tipo
    for tipo in ("lancha", "iate", "barco_pesca"):
        chaves = [c for c, _ in categorias_do_tipo(tipo)]
        assert "velame" not in chaves, tipo
        assert "motor" in chaves, tipo


def test_veleiro_tem_velame_no_lugar_do_motor():
    from app.services.dossie_data import categorias_do_tipo
    chaves = [c for c, _ in categorias_do_tipo("veleiro")]
    assert "velame" in chaves
    assert "motor" not in chaves


def test_jetski_nao_tem_interior_nem_pintura():
    """O painel já escondia as duas abas; o dossiê continuava cobrando."""
    from app.services.dossie_data import categorias_do_tipo
    chaves = [c for c, _ in categorias_do_tipo("jetski")]
    assert "interior" not in chaves
    assert "pintura" not in chaves
    assert "velame" not in chaves


def test_tipo_desconhecido_cai_no_barco_a_motor():
    """Sem tipo, o padrão é o caso comum — nunca inventar velame."""
    from app.services.dossie_data import categorias_do_tipo
    for tipo in (None, "", "coisa_nova"):
        assert "velame" not in [c for c, _ in categorias_do_tipo(tipo)]
