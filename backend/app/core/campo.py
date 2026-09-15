"""
Yachts Atlas — o acesso do aparelho do pátio.

O PROBLEMA QUE ISTO RESOLVE. Até aqui, o colaborador que registra serviço no
píer entrava no Atlas Pré-Data com a conta da própria Marina. A mesma senha abre
o painel oficial — e com ela dá para selar registro (irreversível), emitir
dossiê (gasta uma das 4 do ano), liberar documento para terceiro e ver a frota
inteira. Pior: a regra "quem captura não aprova", que o sistema afirma cumprir,
era impossível de verificar, porque os dois lados eram a mesma credencial.

O DESENHO, e a razão de ser assim:

  1. A Marina gera um CÓDIGO no painel, com apelido ("Celular do pátio").
  2. O app de campo entra com o código — nunca com e-mail e senha.
  3. O código vira um token que só serve para ENVIAR pré-dado.

FAIL-CLOSED, e é o que sustenta tudo. O token de campo é recusado por
`get_current_user`, que é a porta de todo o sistema. Ele só passa nas rotas que
explicitamente o aceitam, e são três. Qualquer rota existente — ou escrita amanhã
por alguém que nunca leu este arquivo — já nasce fechada para ele. O contrário
(aceitar em tudo e bloquear nas sensíveis) dependeria de lembrar de bloquear uma
por uma, e é o tipo de lista que envelhece mal.

O QUE ISTO NÃO É: identidade de PESSOA. Dois funcionários no mesmo celular
produzem registros indistinguíveis, e o nome que aparece no pré-dado continua
sendo o que a pessoa digita. A identidade por pessoa é a E2-a.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from app.core.security import create_access_token, _decode_internal_token
from app.core.supabase import get_supabase_admin

logger = logging.getLogger(__name__)

# Sem 0/O e 1/I/L: o código é ditado por telefone e digitado com a mão suja, no
# sol. Ambiguidade aqui não é detalhe estético — é chamado de suporte.
_ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_TAMANHO = 8

# Sete dias, e não uma hora: o colaborador não vai digitar código a cada turno.
# Quem limita o estrago é o ESCOPO, não o relógio — e a revogação é imediata,
# porque cada requisição confere a linha no banco.
VALIDADE = timedelta(days=7)


def gerar_codigo() -> str:
    """Um código legível, com entropia de sobra (31^8 ≈ 8,5 × 10^11)."""
    bruto = "".join(secrets.choice(_ALFABETO) for _ in range(_TAMANHO))
    return f"{bruto[:4]}-{bruto[4:]}"


def _hash(codigo: str) -> str:
    """SHA-256 do código normalizado.

    Não é senha de usuário — é segredo de alta entropia gerado por nós, então
    não precisa de KDF lento. O que precisa é nunca ficar em claro no banco.
    """
    limpo = (codigo or "").strip().upper().replace("-", "").replace(" ", "")
    return hashlib.sha256(limpo.encode()).hexdigest()


def criar_codigo(usuario_id: str, apelido: str, criado_por: str | None) -> str:
    """Cria o código e devolve ele em claro UMA ÚNICA VEZ.

    Depois disto só existe o hash. Se a Marina perder o código, gera outro e
    revoga o antigo — que é exatamente o comportamento que se quer de um
    segredo.
    """
    supabase = get_supabase_admin()
    codigo = gerar_codigo()
    supabase.table("codigos_campo").insert({
        "usuario_id": usuario_id,
        "apelido": (apelido or "Aparelho de campo").strip()[:60],
        "codigo_hash": _hash(codigo),
        "criado_por": criado_por,
    }).execute()
    return codigo


def _nome_da_marina(usuario_id: str) -> str | None:
    """O nome que a Marina se deu no cadastro, para a tela do pátio mostrar.

    Best-effort de propósito: o colaborador não pode ficar sem entrar porque o
    nome não veio. Sem ele o app mostra um rótulo neutro — chato, nunca
    impeditivo.
    """
    try:
        resposta = get_supabase_admin().auth.admin.get_user_by_id(usuario_id)
        usuario = getattr(resposta, "user", None) or resposta
        meta = getattr(usuario, "user_metadata", None) or {}
        nome = (meta.get("marina") or meta.get("nome") or "").strip()
        return nome or None
    except Exception as e:  # pragma: no cover - degradação proposital
        logger.warning(f"Falha ao ler o nome da Marina {usuario_id}: {e}")
        return None


def token_do_codigo(codigo: str) -> dict:
    """Troca o código por um token de campo. Levanta 401 se não valer.

    A mensagem de recusa é uma só para código inexistente e para código
    revogado: dizer qual dos dois é entregar meia resposta a quem está tentando
    adivinhar.
    """
    supabase = get_supabase_admin()
    achados = (
        supabase.table("codigos_campo").select("*")
        .eq("codigo_hash", _hash(codigo)).limit(1).execute().data
        or []
    )
    if not achados or achados[0].get("revogado_em"):
        raise HTTPException(status_code=401, detail="Código inválido ou revogado.")

    registro = achados[0]
    agora = datetime.now(timezone.utc).isoformat()
    try:
        supabase.table("codigos_campo").update({"ultimo_uso_em": agora}).eq(
            "id", registro["id"]
        ).execute()
    except Exception as e:  # pragma: no cover - degradação proposital
        # Saber a data do último uso é conveniência; recusar a entrada do
        # colaborador porque o carimbo falhou seria trocar o essencial pelo
        # acessório.
        logger.warning(f"Falha ao carimbar uso do código de campo: {e}")

    token = create_access_token(
        {
            "sub": f"campo:{registro['id']}",
            "escopo": "campo",
            "marina": str(registro["usuario_id"]),
        },
        expires_delta=VALIDADE,
    )
    return {
        "token": token,
        "apelido": registro.get("apelido"),
        "validade_dias": VALIDADE.days,
        # O app nao pode trazer o nome da Marina escrito no proprio codigo: ele
        # e um so para todas. Quem sabe de quem e o aparelho e o codigo, e o
        # codigo esta aqui.
        "marina": _nome_da_marina(str(registro["usuario_id"])),
    }


def _token_de_campo(authorization: str | None) -> dict | None:
    """Lê o token de campo do header, se for um. None para qualquer outra coisa."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    dados = _decode_internal_token(authorization.split(" ", 1)[1].strip())
    if not dados or dados.get("escopo") != "campo":
        return None
    return dados


def usuario_ou_campo(authorization: str = Header(None)) -> dict:
    """Dependência das rotas que o app de campo usa. Aceita os dois acessos.

    Devolve sempre o formato de `get_current_user`, com um extra: `escopo` vem
    como "campo" quando a requisição veio do aparelho do pátio. Quem usa isto
    decide o que muda — no upload, por exemplo, a foto entra pendente de revisão
    por imposição, não por escolha de quem envia.

    O `sub` é o id da MARINA, e não do código: é ela que opera o ativo, e a
    autorização de todo o sistema é por ativo. O id do código fica em
    `codigo_id`, para a trilha saber de qual aparelho veio.
    """
    campo = _token_de_campo(authorization)
    if campo:
        # Revogação vale AGORA, e não quando o token vencer. Celular perdido às
        # 9h não pode continuar mandando registro até o fim da semana.
        try:
            supabase = get_supabase_admin()
            codigo_id = str(campo.get("sub", "")).split(":", 1)[-1]
            linha = (
                supabase.table("codigos_campo").select("revogado_em")
                .eq("id", codigo_id).limit(1).execute().data
                or []
            )
            if not linha or linha[0].get("revogado_em"):
                raise HTTPException(status_code=401, detail="Acesso revogado.")
        except HTTPException:
            raise
        except Exception as e:  # pragma: no cover
            # Aqui a falha FECHA. Não dá para afirmar que o acesso continua
            # válido sem conseguir ler a revogação.
            logger.error(f"Falha ao conferir revogação do código de campo: {e}")
            raise HTTPException(status_code=503, detail="Não foi possível validar o acesso.")

        return {
            "sub": campo.get("marina"),
            "email": None,
            "role": None,
            "escopo": "campo",
            "codigo_id": codigo_id,
        }

    # Não é token de campo: segue o caminho normal, com todas as suas checagens
    # (sessão do Supabase, bypass de manutenção, corte por inadimplência).
    from app.core.security import get_current_user
    return get_current_user(authorization)
