"""
Regressão das abas do painel técnico.

O defeito que este teste existe para impedir é silencioso: **criar a ficha e
esquecer de criar a aba**.

Aconteceu com Sinistros. A ficha rica foi escrita (`FICHA_SINISTRO`),
registrada em `SERVICOS`, testada — e a aba nunca foi acrescentada à lista de
categorias do `AtivoHub`. Resultado: nem a marina nem o armador conseguiam
chegar nela, e os registros de sinistro do ativo de demonstração ficaram
invisíveis no painel.

Nada quebrava. Nenhum teste falhava. A funcionalidade simplesmente não existia
para quem usa.
"""
import os
import re
from pathlib import Path

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

_FRONT = Path(__file__).resolve().parents[2] / "frontend" / "src"


def _abas_do_painel() -> list[str]:
    t = (_FRONT / "components" / "AtivoHub.tsx").read_text(encoding="utf-8")
    i = t.index("const base: Categoria[] = [")
    j = t.index("\n  ]", i)
    return re.findall(r"key: '(\w+)'", t[i:j])


def _fichas_registradas() -> list[str]:
    t = (_FRONT / "config" / "servicosCategorias.ts").read_text(encoding="utf-8")
    i = t.index("export const SERVICOS")
    return re.findall(r"^\s*(\w+):\s*FICHA_", t[i:t.index("\n}", i)], re.M)


def test_toda_ficha_rica_tem_aba_no_painel():
    """
    Ficha sem aba é trabalho invisível.

    Quebrou? Acrescente a categoria em `categorias()` no AtivoHub.tsx.
    """
    abas = set(_abas_do_painel())
    # `dossie` é o molde padrão, não uma aba de serviço; `velame` substitui
    # `motor` em veleiro, então não aparece na lista base.
    fichas = {f for f in _fichas_registradas() if f not in {"dossie", "velame"}}
    faltando = fichas - abas
    assert not faltando, (
        f"Ficha criada sem aba no painel: {sorted(faltando)}. "
        "Ninguém consegue chegar nela."
    )


def test_sinistros_esta_no_painel():
    """A aba que motivou este teste — ficou de fora quando a ficha foi criada."""
    assert "sinistros" in _abas_do_painel()


def test_abas_nao_se_repetem():
    """Chave duplicada faria a mesma aba aparecer duas vezes na tela."""
    abas = _abas_do_painel()
    assert len(abas) == len(set(abas)), f"aba repetida em {abas}"
