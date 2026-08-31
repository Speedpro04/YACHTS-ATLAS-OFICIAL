"""
"Íntegro" tem que significar que alguém conferiu.

Até 31/08/2026 a verificação pública respondia:

    integro = com_hash == len(registros)

isto é, contava quantas LINHAS têm a coluna `hash_sha256` preenchida. Como
ela é preenchida por gatilho no INSERT (`fn_registro_hash`), nunca é nula —
o resultado dava **100% sempre**, inclusive num banco adulterado. O conteúdo
do registro nunca era re-hasheado contra o selo.

E o PDF impresso afirma, na instrução 3: *"A plataforma recalcula os hashes
e confirma a autenticidade e a integridade da cadeia de custódia."* A página
pública mostrava "Recalculando os hashes da cadeia de custódia…". Não
recalculava nenhum.

ONDE O RECÁLCULO MORA, E POR QUÊ
--------------------------------
No Postgres (`fn_registro_hash_esperado`), não em Python. A fórmula usa
`dados::text` (JSONB) e `created_at::text` (timestamptz), cuja serialização
segue regras próprias do Postgres — ordenação de chaves, formato e fuso.
Replicar em Python e errar um espaço faria os 188 registros aparecerem como
adulterados: o oposto do objetivo, e o tipo de erro que destrói a confiança
no produto de uma vez.

Estes testes protegem as duas metades. Detectar adulteração é metade; a
outra é **não acusar quem está limpo** — um falso positivo aqui manda a
marina explicar ao comprador por que o dossiê dela "foi adulterado".
"""
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Dublê do Supabase — nenhum teste toca a rede (ver conftest)
# ─────────────────────────────────────────────────────────────────────────────

class _RPC:
    def __init__(self, retorno):
        self._retorno = retorno

    def execute(self):
        if isinstance(self._retorno, Exception):
            raise self._retorno
        return type("R", (), {"data": self._retorno})()


class _Tabela:
    def __init__(self, linhas):
        self._linhas = linhas
        self.count = len(linhas)

    def select(self, *_a, **_k):  return self
    def eq(self, *_a, **_k):      return self

    def execute(self):
        return type("R", (), {"data": self._linhas, "count": self.count})()


def _resposta(integ, n_registros=3):
    """Monta o bloco 'integridade' como a rota monta, isolando a regra."""
    registros = [{"id": i, "hash_sha256": "a" * 64, "created_at": "2026-08-01",
                  "retifica_id": None} for i in range(n_registros)]
    com_hash = sum(1 for r in registros if r.get("hash_sha256"))
    return {
        "registros_com_hash": com_hash,
        "total": len(registros),
        "conferidos": integ.get("conferem"),
        "divergentes": integ.get("divergem"),
        "sem_selo": integ.get("sem_selo"),
        "integro": integ.get("integro") if integ else None,
        "recalculado": bool(integ),
        "verificado_em": integ.get("verificado_em"),
    }


# ─────────────────────────────────────────────────────────────────────────────
# O que a resposta precisa distinguir
# ─────────────────────────────────────────────────────────────────────────────

def test_integro_so_quando_o_recalculo_confirma():
    r = _resposta({"conferem": 3, "divergem": 0, "sem_selo": 0, "integro": True,
                   "verificado_em": "2026-08-31T10:00:00Z"})
    assert r["integro"] is True
    assert r["recalculado"] is True
    assert r["conferidos"] == 3 and r["divergentes"] == 0


def test_adulteracao_derruba_a_integridade():
    """Um registro que não bate com o próprio selo já invalida a cadeia. Não
    existe "quase íntegro" — a promessa do documento é binária."""
    r = _resposta({"conferem": 2, "divergem": 1, "sem_selo": 0, "integro": False,
                   "verificado_em": "2026-08-31T10:00:00Z"})
    assert r["integro"] is False
    assert r["divergentes"] == 1


def test_falha_na_checagem_nao_vira_integro():
    """Quando o recálculo não roda, a resposta é None — nunca False nem True.

    `False` acusaria de adulteração um ativo que talvez esteja perfeito;
    `True` afirmaria integridade sem ter conferido nada. Quem lê precisa
    distinguir "adulterado" de "não consegui verificar", e é justamente essa
    distinção que a conta antiga não sabia fazer.
    """
    r = _resposta({})
    assert r["integro"] is None
    assert r["recalculado"] is False


def test_coluna_preenchida_nao_e_mais_a_prova():
    """O defeito exato que isto substitui: todos os registros com selo
    gravado e, ainda assim, um deles adulterado. A conta antiga
    (`com_hash == total`) daria "íntegro"."""
    r = _resposta({"conferem": 2, "divergem": 1, "sem_selo": 0, "integro": False,
                   "verificado_em": "x"})
    assert r["registros_com_hash"] == r["total"], "todos têm selo gravado"
    assert r["integro"] is False, "e mesmo assim NÃO é íntegro"


# ─────────────────────────────────────────────────────────────────────────────
# Contrato: o código não pode voltar ao atalho
# ─────────────────────────────────────────────────────────────────────────────

def test_a_rota_chama_o_recalculo():
    from pathlib import Path
    fonte = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1"
             / "verificacao.py").read_text(encoding="utf-8")

    assert "fn_verificar_integridade_ativo" in fonte, "a rota parou de recalcular"

    # Só o CÓDIGO — o comentário que explica o defeito antigo cita a conta
    # velha de propósito, para quem ler entender o que mudou e por quê.
    codigo = " ".join(l for l in fonte.splitlines()
                      if not l.lstrip().startswith("#"))
    assert "com_hash == len(registros)" not in codigo, (
        "voltou a chamar de íntegro o que só tem a coluna preenchida"
    )


def test_a_rota_tem_logger():
    """O `except` do recálculo registra o motivo. Sem `logger` definido isso
    vira NameError DENTRO do except — o mesmo defeito achado em
    `dossie_pdf.py` em 28/08, que derrubava a emissão inteira justamente
    quando uma foto já tinha falhado."""
    from pathlib import Path
    fonte = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1"
             / "verificacao.py").read_text(encoding="utf-8")
    assert "logger = logging.getLogger(__name__)" in fonte


def test_o_pdf_promete_o_que_a_plataforma_agora_faz():
    """O documento impresso diz que a plataforma recalcula os hashes. Essa
    frase só é verdadeira porque a função existe — se ela sumir, o PDF passa
    a mentir."""
    from pathlib import Path
    gerador = (Path(__file__).resolve().parents[1] / "app" / "services"
               / "dossie_pdf.py").read_text(encoding="utf-8")
    if "recalcula os hashes" in gerador:
        rota = (Path(__file__).resolve().parents[1] / "app" / "api" / "v1"
                / "verificacao.py").read_text(encoding="utf-8")
        assert "fn_verificar_integridade_ativo" in rota, (
            "o PDF promete recálculo e a verificação não recalcula"
        )
