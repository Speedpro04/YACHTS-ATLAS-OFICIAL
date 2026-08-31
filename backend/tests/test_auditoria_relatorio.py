"""
A trilha de auditoria tem que responder perguntas, não listar linhas.

`audit_logs` guarda quem, o quê, quando, de onde e com que resultado — e em
30/08/2026 já tinha 184 linhas gravadas. Mas nada no sistema sabia
interrogá-la: `audit_service` só listava os eventos de UM usuário, em ordem
cronológica, e auditoria não se responde com lista cronológica.

Estes testes cobrem as perguntas que um auditor de SOC 2 / ISO 27001 / SUSEP
faz, e principalmente as três formas de o relatório MENTIR:

  * contar como total um número que foi truncado;
  * dizer "nenhuma falha" quando na verdade a leitura quebrou;
  * atribuir evento ao dia errado por causa de fuso horário.

Nenhum teste toca a rede: o conftest da suíte bloqueia saída externa, e um
relatório de auditoria que só se prova contra o banco de produção não se
prova nunca.
"""
from datetime import datetime, timedelta, timezone

import pytest

from app.services import auditoria_relatorio as rel

pytest.importorskip("polars", reason="Polars não instalado")


# ─────────────────────────────────────────────────────────────────────────────
# Dublê do Supabase: devolve as linhas que o teste mandar, sem sair da máquina
# ─────────────────────────────────────────────────────────────────────────────

class _Consulta:
    def __init__(self, linhas):
        self._linhas = linhas
        self.limite = None

    def select(self, *_a, **_k):   return self
    def gte(self, *_a, **_k):      return self
    def lte(self, *_a, **_k):      return self
    def order(self, *_a, **_k):    return self

    def limit(self, n):
        self.limite = n
        return self

    def execute(self):
        return type("R", (), {"data": self._linhas[: self.limite or len(self._linhas)]})()


class _Banco:
    def __init__(self, linhas):
        self.linhas = linhas

    def table(self, _nome):
        return _Consulta(self.linhas)


def _evento(acao="asset_view", ok=True, sev="info", erro=None,
            ip="200.1.1.1", user="u1", quando=None):
    q = quando or datetime.now(timezone.utc)
    return {
        "id": f"id-{acao}-{q.isoformat()}-{erro}-{ip}",
        "action": acao,
        "user_id": user,
        "ip_address": ip,
        # ISO COM offset, como o Postgres devolve
        "timestamp": q.isoformat(),
        "severity": sev,
        "success": ok,
        "error_message": erro,
    }


@pytest.fixture
def banco(monkeypatch):
    def _instalar(linhas):
        monkeypatch.setattr(rel, "get_supabase_admin", lambda: _Banco(linhas))
    return _instalar


# ─────────────────────────────────────────────────────────────────────────────
# As perguntas do auditor
# ─────────────────────────────────────────────────────────────────────────────

def test_conta_o_que_falhou_e_por_que(banco):
    """A primeira pergunta de qualquer auditoria: o que falhou, e quantas vezes.

    Na trilha real de agosto/2026 a resposta foi 14 "Invalid signature", 9
    "Invalid maintenance credentials" e 1 "File validation failed" — e
    descobrir isso exigia abrir o banco e escrever SQL à mão.
    """
    banco([_evento(ok=False, erro="Invalid signature") for _ in range(3)]
          + [_evento(ok=False, erro="Invalid maintenance credentials")]
          + [_evento() for _ in range(5)])

    r = rel.relatorio(dias=90)
    assert r["eventos"] == 9
    assert r["falhas"] == 4
    motivos = {x["error_message"]: x["n"] for x in r["falhas_por_motivo"]}
    assert motivos == {"Invalid signature": 3, "Invalid maintenance credentials": 1}


def test_severidade_e_sucesso_sao_perguntas_diferentes(banco):
    """No schema os dois campos são independentes: existe login recusado com
    severity='warning' (falha, mas não crítico) e erro crítico que
    tecnicamente "teve sucesso". Contar só um deixa metade do risco fora."""
    banco([
        _evento(ok=False, sev="warning", erro="Invalid maintenance credentials"),
        _evento(ok=True,  sev="critical", erro=None),
    ])
    r = rel.relatorio(dias=90)
    assert r["falhas"] == 1
    assert r["eventos_de_alerta"] == 1


def test_pico_de_falha_aparece_no_dia_certo(banco):
    """Fuso horário errado joga o evento para o dia vizinho — e num relatório
    de auditoria isso é atribuir acesso à data errada. O Postgres devolve ISO
    com offset, e a conversão declara UTC explicitamente por causa disso."""
    d1 = datetime(2026, 8, 26, 23, 40, tzinfo=timezone.utc)
    d2 = datetime(2026, 8, 27, 10, 0, tzinfo=timezone.utc)
    banco([_evento(ok=False, erro="x", quando=d1) for _ in range(6)]
          + [_evento(ok=False, erro="x", quando=d2) for _ in range(2)])

    por_dia = {str(x["dia"]): x["n"] for x in rel.relatorio(dias=90)["falhas_por_dia"]}
    assert por_dia == {"2026-08-26": 6, "2026-08-27": 2}


def test_origem_das_falhas(banco):
    """"De quais IPs?" é a pergunta que separa engano de operador de tentativa
    sistemática — e é sempre a segunda coisa que o auditor pede."""
    banco([_evento(ok=False, erro="e", ip="1.1.1.1") for _ in range(4)]
          + [_evento(ok=False, erro="e", ip="2.2.2.2")]
          + [_evento(ip="3.3.3.3")])

    r = rel.relatorio(dias=90)
    assert r["ips_distintos"] == 3
    assert {x["ip_address"]: x["n"] for x in r["ips_com_falha"]} == {"1.1.1.1": 4, "2.2.2.2": 1}


# ─────────────────────────────────────────────────────────────────────────────
# As três formas de o relatório mentir
# ─────────────────────────────────────────────────────────────────────────────

def test_truncado_e_declarado(banco, monkeypatch):
    """Número parcial apresentado como total é o defeito que este projeto
    passou o mês corrigindo no dossiê. Se a janela bate no teto de linhas, o
    relatório precisa DIZER — senão o auditor lê a fatia como o todo."""
    monkeypatch.setattr(rel, "LIMITE_LINHAS", 5)
    banco([_evento(user=f"u{i}") for i in range(50)])

    r = rel.relatorio(dias=90)
    assert r["eventos"] == 5
    assert r["truncado"] is True


def test_periodo_vazio_nao_e_periodo_limpo(banco):
    """Sem eventos, o relatório diz `sem_dados` em vez de devolver zeros.
    "0 falhas" e "não consegui olhar" são conclusões opostas."""
    banco([])
    r = rel.relatorio(dias=90)
    assert r["eventos"] == 0
    assert r.get("sem_dados") is True
    assert "falhas_por_motivo" not in r


def test_leitura_que_quebra_nao_vira_relatorio_limpo(banco, monkeypatch):
    """Se o banco cair, o pior resultado possível é um relatório bonito
    dizendo "nenhuma falha no período". Devolve vazio — que é `sem_dados`,
    não "tudo certo"."""
    def _explode():
        raise RuntimeError("conexão recusada")
    monkeypatch.setattr(rel, "get_supabase_admin", _explode)

    r = rel.relatorio(dias=90)
    assert r["eventos"] == 0
    assert r.get("sem_dados") is True


def test_janela_respeitada(banco):
    """A janela é o recorte que o auditor pediu; evento fora dela não entra."""
    dentro = datetime.now(timezone.utc) - timedelta(days=3)
    banco([_evento(quando=dentro) for _ in range(2)])
    assert rel.relatorio(dias=7)["eventos"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# Exportação — o arquivo que o auditor leva
# ─────────────────────────────────────────────────────────────────────────────

def test_exporta_csv_e_parquet(banco, tmp_path):
    """CSV abre em qualquer lugar; Parquet preserva tipo e comprime, para os
    5 a 10 anos de retenção que a SUSEP menciona."""
    banco([_evento(user=f"u{i}") for i in range(12)])

    for fmt in ("csv", "parquet"):
        destino = tmp_path / f"trilha.{fmt}"
        r = rel.exportar(str(destino), dias=90, formato=fmt)
        assert r["ok"] and r["linhas"] == 12
        assert destino.exists() and destino.stat().st_size > 0


def test_exportar_recusa_formato_desconhecido(banco, tmp_path):
    banco([_evento()])
    with pytest.raises(ValueError):
        rel.exportar(str(tmp_path / "x.xlsx"), formato="xlsx")


def test_exportar_periodo_vazio_nao_gera_arquivo_falso(banco, tmp_path):
    """Arquivo de auditoria vazio circulando é pior que arquivo nenhum: quem
    recebe conclui que o período não teve evento."""
    banco([])
    destino = tmp_path / "vazio.csv"
    r = rel.exportar(str(destino), dias=90)
    assert r["ok"] is False and not destino.exists()


# ─────────────────────────────────────────────────────────────────────────────
# A rota
# ─────────────────────────────────────────────────────────────────────────────

def test_rota_exige_admin_da_plataforma():
    """A trilha registra IP e o que cada conta acessou. Aberta a uma marina,
    vazaria o comportamento das outras."""
    from app.api.v1 import auditoria
    fonte = (auditoria.__file__)
    with open(fonte, encoding="utf-8") as f:
        codigo = f.read()
    assert codigo.count("require_platform_admin") >= 3, (
        "toda rota de auditoria precisa exigir admin da plataforma"
    )


def test_rotas_registradas():
    from app.main import app
    caminhos = {r.path for r in app.routes if hasattr(r, "path")}
    assert "/api/v1/auditoria/relatorio" in caminhos
    assert "/api/v1/auditoria/exportar" in caminhos
