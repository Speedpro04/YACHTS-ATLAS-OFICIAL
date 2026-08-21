"""
Regressão do desfecho de avaria — o "antes e depois" e o seu desfecho.

O caso real: rombo no casco. Antes disto, a marina registrava uma vistoria com
status "Crítico (Avaria Estrutural)" e, meses depois, outra com "Excelente".
Dois registros soltos — nada ligava um ao outro, e no dossiê o leitor tinha
que adivinhar que o segundo resolveu o primeiro.

Comercialmente isso é caro: **"este barco teve um rombo" derruba o valor;
"teve um rombo, reparado pelo estaleiro X, com laudo de ultrassom anexado e
vistoriado" preserva** — às vezes aumenta, porque prova que a estrutura foi
auditada de perto. O dossiê não vale por esconder avaria: vale por provar que
foi resolvida direito.

O que estes testes protegem:

  • `resolve_id` chegar ao banco (sem isso, o vínculo se perde e a metade boa
    da história some);
  • ele NÃO se confundir com `retifica_id` — retificar é "eu estava errado",
    resolver é "aquilo aconteceu e acabou". Misturar faria o dossiê mostrar
    uma avaria real como se fosse erro de digitação.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import inspect

from app.api.v1.registros import RegistroCreate, RetificacaoCreate


def test_registro_aceita_o_vinculo_de_desfecho():
    r = RegistroCreate(
        ativo_id="YA-IATE-2015-3A38",
        categoria="casco",
        resolve_id="11111111-1111-1111-1111-111111111111",
    )
    assert r.resolve_id == "11111111-1111-1111-1111-111111111111"


def test_vinculo_e_opcional():
    """Vistoria de rotina não resolve nada — a maioria dos registros é assim."""
    r = RegistroCreate(ativo_id="YA-IATE-2015-3A38", categoria="casco")
    assert r.resolve_id is None


def test_o_insert_leva_o_vinculo():
    """
    Sem esta linha, o campo era aceito na API e descartado no banco — o pior
    tipo de falha, porque a tela mostraria sucesso e o vínculo não existiria.
    """
    from app.api.v1 import registros
    fonte = inspect.getsource(registros)
    assert '"resolve_id": data.resolve_id' in fonte


def test_resolver_nao_e_retificar():
    """
    São conceitos distintos e precisam continuar distintos.

    Retificação exige motivo e marca o original como corrigido; desfecho não
    corrige nada — os dois registros seguem válidos e a cronologia é o produto.
    """
    campos_retificacao = set(RetificacaoCreate.model_fields)
    assert "retifica_id" in campos_retificacao
    assert "motivo_retificacao" in campos_retificacao
    # O registro comum resolve, mas não retifica.
    campos_registro = set(RegistroCreate.model_fields)
    assert "resolve_id" in campos_registro
    assert "retifica_id" not in campos_registro


# --------------------------------------------------------------------------
# A ficha do casco separa os dois momentos
# --------------------------------------------------------------------------

def _ficha_sinistro() -> str:
    from pathlib import Path
    caminho = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "config" / "servicosCategorias.ts"
    )
    texto = caminho.read_text(encoding="utf-8")
    inicio = texto.index("const FICHA_SINISTRO")
    return texto[inicio:texto.index("const FICHA_ELETRICA")]


def test_ficha_pergunta_qual_o_momento():
    ficha = _ficha_sinistro()
    assert "'momento'" in ficha
    for opcao in ("Ocorrencia do sinistro", "Reparo concluido"):
        assert opcao in ficha


def test_sinistro_transborda_de_um_sistema_so():
    """
    Encalhe atinge casco, helice, eixo e leme; incendio atinge motor, eletrica
    e interior. Caixas independentes, e nao escolha unica — e essa lista que
    diz ao perito e ao comprador o tamanho real do evento.
    """
    ficha = _ficha_sinistro()
    for sistema in ("sis_casco", "sis_propulsao", "sis_governo", "sis_eletrica",
                    "sis_eletronica", "sis_interior", "sis_conves", "sis_auxiliares"):
        assert sistema in ficha
        pos = ficha.index(sistema)
        assert "checkbox" in ficha[pos:pos + 200]


def test_casco_continua_sendo_vistoria_de_rotina():
    """
    Sem avaria, o gerente preenche a vistoria e pronto.

    Empurrar campos de sinistro para o Casco faria TODA vistoria carregar o
    peso de um evento que quase nunca aconteceu — e a maioria das vistorias e
    rotina.
    """
    from pathlib import Path
    caminho = (
        Path(__file__).resolve().parents[2]
        / "frontend" / "src" / "config" / "servicosCategorias.ts"
    )
    texto = caminho.read_text(encoding="utf-8")
    # Corta no cabecalho da secao: as constantes SIN_* ficam ANTES do
    # `const FICHA_SINISTRO` e entrariam na fatia do casco.
    casco = texto[texto.index("const FICHA_CASCO"):texto.index("SINISTROS & REPAROS")]
    assert "momento" not in casco
    assert "tipo_sinistro" not in casco


def test_campos_do_reparo_nao_aparecem_na_avaria():
    """
    Espessura final e laudo só existem DEPOIS do conserto.

    Misturados num formulário só, a marina preenchia sem saber se descrevia o
    problema ou a solução — e o dossiê saía ambíguo justamente na parte que o
    comprador mais olha.
    """
    ficha = _ficha_sinistro()
    for campo in ("reparo_estaleiro", "reparo_descricao", "reparo_valor_real"):
        pos = ficha.index(campo)
        trecho = ficha[pos:pos + 400]
        assert "SIN_REPARO" in trecho, f"{campo} precisa aparecer só no reparo"


def test_foto_do_antes_e_do_depois_sao_obrigatorias_no_seu_momento():
    """
    É a comparação que prova o reparo — a mesma proa, o mesmo ângulo.

    Sem obrigar, a marina registra o conserto sem imagem e o dossiê fica com a
    má notícia documentada e a boa notícia só no texto.
    """
    ficha = _ficha_sinistro()
    assert "foto_sinistro" in ficha and "foto_reparo" in ficha
    for campo in ("foto_sinistro", "foto_reparo"):
        pos = ficha.index(f"key: '{campo}'")
        assert "requiredIf" in ficha[pos:pos + 500], f"{campo} deve ser exigida no seu momento"
