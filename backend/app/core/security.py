"""
Yachts Atlas — Security Utilities
"""
import logging
from datetime import datetime, timedelta
from fastapi import Depends, Header, HTTPException
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def _internal_jwt_secret() -> str | None:
    """Segredo do crachá do login de manutenção.

    Antes assinava com o SUPABASE_JWT_SECRET, que está publicado no histórico
    do Git e nunca foi rotacionado: quem tivesse o valor forjava
    {"sub": "maintenance-admin"} e virava platform_admin sem senha nenhuma.

    Sem fallback de propósito. Faltando a variável, o login de manutenção para
    de emitir e de aceitar crachá — em vez de voltar a assinar com o segredo
    vazado ou com a service key. O MAINTENANCE_MASTER_TOKEN não passa por aqui
    e continua abrindo o acesso.
    """
    return settings.MAINTENANCE_JWT_SECRET or None


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    segredo = _internal_jwt_secret()
    if not segredo:
        raise RuntimeError(
            "MAINTENANCE_JWT_SECRET não configurado: o login de manutenção "
            "está desligado. Use o MAINTENANCE_MASTER_TOKEN."
        )
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, segredo, algorithm=ALGORITHM)


def _decode_internal_token(token: str) -> dict | None:
    segredo = _internal_jwt_secret()
    if not segredo:
        return None
    try:
        payload = jwt.decode(token, segredo, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_current_user(authorization: str = Header(None)) -> dict:
    """
    Dependência unificada: lê o JWT da sessão Supabase no header Authorization
    e valida via Supabase Auth. Aceita também o token interno de manutenção.
    Retorna {sub, email, role}.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    token = authorization.split(" ", 1)[1].strip()

    # Bypass de manutenção (admin da plataforma)
    if (
        settings.MAINTENANCE_BYPASS_ENABLED
        and settings.MAINTENANCE_MASTER_TOKEN
        and token == settings.MAINTENANCE_MASTER_TOKEN
    ):
        return {"sub": "maintenance-admin", "email": None, "role": "platform_admin"}

    # Token interno do login de manutenção
    internal = _decode_internal_token(token)
    if internal and internal.get("sub") == "maintenance-admin":
        return {"sub": "maintenance-admin", "email": None, "role": "platform_admin"}

    try:
        from app.core.supabase import get_supabase_admin
        res = get_supabase_admin().auth.get_user(token)
        user = getattr(res, "user", None)
        if not user:
            raise HTTPException(status_code=401, detail="Sessão inválida")
        # Porteiro do acesso pago. Checado a cada requisição, e não só no
        # login: o corte por inadimplência precisa valer para quem já está
        # com a sessão aberta, senão a marina cortada segue usando até o
        # token vencer. O metadata já veio nesta resposta — custo zero.
        _barrar_se_devendo(getattr(user, "user_metadata", None))
        return {"sub": user.id, "email": getattr(user, "email", None), "role": None}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Sessão inválida")


def _barrar_se_devendo(user_metadata: dict | None) -> None:
    """
    Aplica a regra de acesso pago (app/core/acesso.py).

    402 e não 403 de propósito: o frontend distingue "não pode" de "precisa
    pagar" pelo código, e mostra a tela de regularização com o link certo em
    vez de um erro genérico que faz a marina achar que perdeu a senha.
    """
    from app.core.acesso import avaliar_acesso

    bloqueio = avaliar_acesso(user_metadata)
    if bloqueio:
        raise HTTPException(status_code=402, detail=bloqueio.as_dict())


def get_current_user_id(user: dict = Depends(get_current_user)) -> str:
    return user["sub"]


def require_platform_admin(user: dict = Depends(get_current_user)) -> dict:
    """Restringe ao admin da plataforma (manutenção) ou perfil com user_role='admin'."""
    if user.get("sub") == "maintenance-admin":
        return user
    try:
        from app.core.supabase import get_supabase_admin
        prof = (
            get_supabase_admin()
            .table("profiles")
            .select("user_role")
            .eq("id", user["sub"])
            .execute()
        )
        role = prof.data[0].get("user_role") if prof.data else None
    except Exception:
        role = None
    if role != "admin":
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user


# ---------------------------------------------------------------------------
# Política de senha — UMA fonte para todo mundo
# ---------------------------------------------------------------------------
# Antes as regras viviam so no RegistroMarina.tsx: 10 caracteres, maiuscula,
# minuscula e numero, conferidas no navegador. O backend recebia `password: str`
# e mandava direto para o `create_user` do Supabase, sem olhar. Quem postasse
# direto em /leads/marina/registrar cadastrava com "123" -- o unico piso real
# era o minimo do proprio Supabase, que vem em 6. E `UsuarioCreate` ainda dizia
# min_length=8, um terceiro numero para o mesmo fato.
#
# Agora a regra mora aqui e os modelos a chamam. Mudar o minimo e mudar UMA
# linha. O texto da falha e o mesmo que a marina le na tela.
SENHA_MINIMO = 10

_REGRAS_SENHA = (
    (f"pelo menos {SENHA_MINIMO} caracteres", lambda s: len(s) >= SENHA_MINIMO),
    ("uma letra maiuscula", lambda s: any(c.isupper() for c in s)),
    ("uma letra minuscula", lambda s: any(c.islower() for c in s)),
    ("um numero", lambda s: any(c.isdigit() for c in s)),
)


def faltas_na_senha(senha: str) -> list[str]:
    """O que a senha ainda nao cumpre. Lista vazia = senha valida."""
    s = senha or ""
    return [texto for texto, cumpre in _REGRAS_SENHA if not cumpre(s)]


def validar_senha(senha: str) -> str:
    """Para usar em `field_validator`. Levanta ValueError com o que falta."""
    faltas = faltas_na_senha(senha)
    if faltas:
        raise ValueError("A senha precisa de " + ", ".join(faltas) + ".")
    return senha


async def senha_vazada(senha: str) -> bool:
    """A senha aparece em vazamento publico conhecido? (HaveIBeenPwned)

    E o mesmo mecanismo do recurso pago do Supabase, que so existe no plano Pro.
    Funciona por k-anonimato: mandamos apenas os 5 primeiros caracteres do
    SHA-1 e recebemos os sufixos daquela faixa; a comparacao final e local.
    A senha nunca sai daqui, e o hash completo tambem nao.

    FALHA ABERTO de proposito: se o HIBP estiver fora do ar, devolve False e
    registra no log. Travar o cadastro de uma marina pagante por causa de
    servico de terceiro seria pior que o problema que isto resolve.
    """
    if not senha:
        return False
    import hashlib
    import httpx

    sha1 = hashlib.sha1(senha.encode("utf-8")).hexdigest().upper()
    prefixo, sufixo = sha1[:5], sha1[5:]
    try:
        async with httpx.AsyncClient(timeout=3.0) as cliente:
            r = await cliente.get(
                f"https://api.pwnedpasswords.com/range/{prefixo}",
                # Add-Padding faz o HIBP devolver respostas de tamanho uniforme:
                # sem isso, o TAMANHO da resposta ja entrega quantos hashes
                # existem naquela faixa para quem observa a rede.
                headers={"Add-Padding": "true", "User-Agent": "YachtsAtlas"},
            )
            r.raise_for_status()
            corpo = r.text
    except Exception as e:
        logger.warning("HIBP indisponivel (%s) — cadastro segue sem a checagem", e)
        return False

    for linha in corpo.splitlines():
        h, _, contagem = linha.partition(":")
        if h.strip() == sufixo and contagem.strip() not in ("", "0"):
            return True
    return False
