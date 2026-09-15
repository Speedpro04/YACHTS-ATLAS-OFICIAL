# -*- coding: utf-8 -*-
"""
O painel e o dossiê dizem o MESMO sobre o estado do barco.

O DEFEITO. O cabeçalho da embarcação lê `ativo.health_status` desde sempre
(AtivoHub.tsx) — e esse campo nunca foi produzido: não é coluna de `ativos` e
nenhum caminho do backend o calculava. Então ele dizia "Conformidade — nenhum
dos 10 sistemas avaliado" para TODA embarcação, sempre, inclusive as que tinham
registro selado. Enquanto isso o dossiê da mesma embarcação imprimia
"Motor: conforme · Conformidade 100%".

Painel e dossiê discordando sobre o mesmo barco, e a errada era a tela que a
Marina abre todo dia.

A regra agora é uma só: `saude_por_chave`, a mesma função que o PDF usa. Estes
testes existem para que continue sendo uma só.
"""
import inspect

from app.api.v1 import ativos
from app.services.dossie_data import saude_por_chave, _saude_por_categoria


def _reg(categoria, status="concluido", **extra):
    return {"categoria": categoria, "status": status, "situacao": "vigente", **extra}


def test_categoria_com_registro_concluido_fica_conforme():
    assert saude_por_chave([_reg("motor")], "iate")["motor"] == "ok"


def test_categoria_sem_registro_nao_entra():
    """Não avaliado fica FORA da conta — não soma nem penaliza. É o que
    permite '100% sobre 1 de 11' ser uma frase honesta."""
    saude = saude_por_chave([_reg("motor")], "iate")
    assert "casco" not in saude
    assert list(saude) == ["motor"]


def test_atencao_em_categoria_de_risco_vale_critico():
    """Casco e sinistros não têm meio-termo: avaria e sinistro aberto valem 0,
    não 50. A regra é do dossiê e vale igual no painel."""
    assert saude_por_chave([_reg("casco", "atencao")], "iate")["casco"] == "critical"
    assert saude_por_chave([_reg("motor", "atencao")], "iate")["motor"] == "warning"


def test_o_vocabulario_e_o_que_o_painel_entende():
    """O painel pesa 'ok'/'info'=100, 'warning'=50, e QUALQUER outra coisa=0.
    Mandar 'warn' daqui faria uma ressalva leve valer zero — o barco pareceria
    pior do que é, sem ninguém entender por quê."""
    estados = set(saude_por_chave(
        [_reg("motor", "atencao"), _reg("casco"), _reg("documentacao", "pendente")],
        "iate",
    ).values())
    assert estados <= {"ok", "warning", "critical"}
    assert "warn" not in estados and "crit" not in estados


def test_o_dossie_continua_usando_a_mesma_regra():
    """As duas saídas nascem da mesma função. Se alguém duplicar o cálculo, as
    duas telas voltam a poder divergir — que é o defeito inteiro."""
    fonte = inspect.getsource(_saude_por_categoria)
    assert "_saude_bruta" in fonte, "o dossiê passou a calcular por conta própria"


def test_a_lista_de_ativos_anexa_a_saude():
    fonte = inspect.getsource(ativos.list_ativos)
    assert "_anexar_saude" in fonte, (
        "o painel voltaria a dizer 'nenhum sistema avaliado' para todo mundo"
    )


def test_a_saude_le_a_view_que_resolve_retificacao():
    """Registro retificado sai da conta; vale a correção. Ler a tabela crua
    faria um problema já corrigido puxar a categoria para baixo para sempre."""
    fonte = inspect.getsource(ativos._anexar_saude)
    assert "vw_registros_situacao" in fonte
