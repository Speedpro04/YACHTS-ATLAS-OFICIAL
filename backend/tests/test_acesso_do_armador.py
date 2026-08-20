"""
Regressão do acesso do armador — quem vê o quê, e quem não mexe em nada.

O erro que estes testes existem para impedir é o mais caro do produto:
**mostrar o barco de um cliente para outro**. O dossiê vale porque o histórico
é privado até o dono liberar; vazar isso destrói a confiança que a marina
levou meses construindo.

A regra é simples e tem duas metades, e as duas precisam valer:

  • o armador VÊ o barco dele — reconhecido pelo e-mail que a marina gravou;
  • o armador NÃO ESCREVE nada — nem foto, nem categoria, nem registro.

A segunda metade é a que se perde sem querer: basta alguém liberar o armador
no guardião central e, de repente, ele pode subir foto no próprio dossiê que
deveria ser prova independente.
"""
import os
import types

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest
from fastapi import HTTPException

import app.core.authz as authz
from app.core.authz import get_ativo_autorizado

MARINA = "11111111-1111-1111-1111-111111111111"
ARMADOR = "22222222-2222-2222-2222-222222222222"
ESTRANHO = "33333333-3333-3333-3333-333333333333"

EMAILS = {
    MARINA: "gerente@marina.com",
    ARMADOR: "roberto@email.com",
    ESTRANHO: "outro@email.com",
}


class _Query:
    def __init__(self, retorno):
        self._retorno = retorno

    def select(self, *a, **k):
        return self

    def eq(self, *a, **k):
        return self

    def execute(self):
        return types.SimpleNamespace(data=self._retorno)


class _Admin:
    def __init__(self, ativo, profile=None):
        self._ativo = ativo
        self._profile = profile or {}

    def table(self, nome):
        return _Query([self._ativo] if nome == "ativos" else [self._profile])


@pytest.fixture
def banco(monkeypatch):
    def instalar(ativo, profile=None):
        monkeypatch.setattr(authz, "get_supabase_admin", lambda: _Admin(ativo, profile))
        monkeypatch.setattr(authz, "email_do_usuario", lambda uid: EMAILS.get(uid))
    return instalar


def _barco(dono_email="roberto@email.com"):
    return {
        "id": "YA-IATE-2015-3A38",
        "usuario_id": MARINA,
        "proprietario_email": dono_email,
        "marca": "Marlin Sea",
    }


# --------------------------------------------------------------------------
# O armador vê o barco dele
# --------------------------------------------------------------------------

def test_armador_le_o_proprio_barco(banco):
    banco(_barco())
    assert get_ativo_autorizado("YA-IATE-2015-3A38", ARMADOR, incluir_proprietario=True)


def test_maiuscula_no_email_nao_barra_o_dono(banco):
    """A marina digita 'Roberto@Email.com' e o armador entra em minúsculas."""
    banco(_barco(dono_email="Roberto@Email.COM "))
    assert get_ativo_autorizado("YA-IATE-2015-3A38", ARMADOR, incluir_proprietario=True)


def test_marina_continua_vendo_o_proprio_ativo(banco):
    banco(_barco())
    assert get_ativo_autorizado("YA-IATE-2015-3A38", MARINA)


# --------------------------------------------------------------------------
# O armador NÃO escreve
# --------------------------------------------------------------------------

def test_sem_a_flag_o_armador_e_barrado(banco):
    """
    É assim que upload de foto e troca de categoria ficam fora do alcance dele.

    O padrão é restritivo justamente para que endpoint novo nasça proibido:
    esquecer de liberar é um chamado de suporte; esquecer de proibir é o
    armador escrevendo no dossiê que deveria ser prova independente.
    """
    banco(_barco())
    with pytest.raises(HTTPException) as erro:
        get_ativo_autorizado("YA-IATE-2015-3A38", ARMADOR)
    assert erro.value.status_code == 403


# --------------------------------------------------------------------------
# Ninguém mais entra
# --------------------------------------------------------------------------

def test_estranho_nao_ve_barco_de_ninguem(banco):
    banco(_barco())
    with pytest.raises(HTTPException) as erro:
        get_ativo_autorizado("YA-IATE-2015-3A38", ESTRANHO, incluir_proprietario=True)
    assert erro.value.status_code == 403


def test_barco_sem_dono_definido_nao_libera_ninguem(banco):
    """Campo vazio não pode virar chave-mestra: '' == '' seria catástrofe."""
    for vazio in (None, "", "   "):
        banco(_barco(dono_email=vazio))
        with pytest.raises(HTTPException) as erro:
            get_ativo_autorizado("YA-IATE-2015-3A38", ESTRANHO, incluir_proprietario=True)
        assert erro.value.status_code == 403


def test_conta_sem_email_nao_casa_com_barco_sem_dono(banco, monkeypatch):
    """Manutenção não tem e-mail; None == None não pode abrir porta nenhuma."""
    banco(_barco(dono_email=None))
    monkeypatch.setattr(authz, "email_do_usuario", lambda uid: None)
    with pytest.raises(HTTPException) as erro:
        get_ativo_autorizado("YA-IATE-2015-3A38", ESTRANHO, incluir_proprietario=True)
    assert erro.value.status_code == 403
