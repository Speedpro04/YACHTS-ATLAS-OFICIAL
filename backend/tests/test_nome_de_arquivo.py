"""
Regressão do nome de arquivo enviado ao storage.

O Supabase Storage recusa chave com acento ou espaço e devolve 400. O frontend
engolia esse erro atrás de "servidor acordando, tente novamente" — a marina
insistia para sempre num arquivo que nunca ia subir, sem nenhuma pista do
motivo.

Aconteceu em produção com `iate 38 pés.jfif`. Foto com acento e espaço no nome
é a regra no Brasil, não a exceção: é o padrão do WhatsApp, do celular e de
quem salva a foto com o nome do barco.
"""
import os

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")

import pytest

from app.api.v1.documentos import _nome_seguro

PROIBIDOS = set(" áàâãéêíóôõúüçÁÉÍÓÚÇ#?%&+")


@pytest.mark.parametrize("original", [
    "iate 38 pés.jfif",                    # o caso real que quebrou
    "Lancha Açucena – casco.JPG",
    "nota fiscal (2).pdf",
    "motor #1 revisão 2024.png",
    "  espaços  nas  pontas .jpeg",
])
def test_nome_vira_chave_aceitavel(original):
    seguro = _nome_seguro(original)
    assert not (set(seguro) & PROIBIDOS), f"{seguro!r} ainda tem caractere proibido"
    assert seguro == seguro.strip("-.")


def test_extensao_e_preservada():
    """Sem a extensão o navegador não sabe abrir o arquivo depois."""
    assert _nome_seguro("iate 38 pés.jfif").endswith(".jfif")
    assert _nome_seguro("Contrato Final.PDF").endswith(".PDF")


def test_nome_sem_nenhum_caractere_valido_nao_vira_vazio():
    """Chave vazia faria o storage recusar de novo, por outro motivo."""
    assert _nome_seguro("日本語.jpg")
    assert _nome_seguro("###")
    assert _nome_seguro("")
    assert _nome_seguro(None)


def test_nome_gigante_e_cortado():
    """Chave de storage tem limite; nome de 400 caracteres derruba o upload."""
    assert len(_nome_seguro("a" * 400 + ".jpg")) <= 120


def test_acento_vira_a_letra_sem_acento():
    """Trocar por '-' deixaria 'p-s' — feio no lugar de 'pes' e sem ganho."""
    assert "pes" in _nome_seguro("pés.jpg")
    assert "acucena" in _nome_seguro("açucena.jpg").lower()
