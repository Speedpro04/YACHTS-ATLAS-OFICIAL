"""
Yachts Atlas — Authentication Endpoints
"""
from fastapi import APIRouter, Header, HTTPException, Depends, Request
from app.schemas.models import UsuarioCreate, UsuarioResponse, MaintenanceLoginRequest, LoginRequest
from app.core.supabase import get_supabase_admin
from app.core.limite_taxa import limite
from app.core.security import hash_password, verify_password, create_access_token
from app.core.acesso import avaliar_acesso
from app.core.config import settings
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location
from datetime import timedelta

router = APIRouter()
audit_service = AuditService()


@router.post(
    "/maintenance/login",
    # A porta de administrador da plataforma. So o fundador usa, entao o
    # teto pode ser apertado: quem sabe a senha acerta em duas tentativas.
    dependencies=[Depends(limite("login_manutencao", 5, 900))],
)
async def maintenance_login(data: MaintenanceLoginRequest, request: Request):
    """Owner maintenance login via environment-managed credentials"""
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)

    if not settings.MAINTENANCE_USERNAME or not settings.MAINTENANCE_PASSWORD:
        raise HTTPException(status_code=503, detail="Maintenance credentials not configured")

    # Sem o segredo dedicado nao ha como assinar o cracha. Avisa claro em vez de
    # estourar 500 — e lembra do caminho que continua aberto.
    if not settings.MAINTENANCE_JWT_SECRET:
        raise HTTPException(
            status_code=503,
            detail="MAINTENANCE_JWT_SECRET nao configurado: login de manutencao "
                   "indisponivel. Use o master token.",
        )

    if data.username != settings.MAINTENANCE_USERNAME or data.password != settings.MAINTENANCE_PASSWORD:
        audit_service.log_login(
            user_id="maintenance-admin",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid maintenance credentials",
            location=location
        )
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        data={"sub": "maintenance-admin", "role": "owner"},
        expires_delta=timedelta(hours=8)
    )

    audit_service.log_login(
        user_id="maintenance-admin",
        ip_address=ip_address,
        user_agent=user_agent,
        success=True,
        location=location
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": "maintenance-admin",
        "role": "owner",
        "expires_in_hours": 8
    }


@router.post(
    "/signup",
    # Criar conta e evento raro por IP. Teto baixo impede fabricar contas
    # em massa — cada uma delas dispara e-mail e ocupa linha no banco.
    dependencies=[Depends(limite("signup", 3, 3600))],
)
async def signup(user: UsuarioCreate, request: Request):
    """Register new user with complete audit tracking"""
    supabase = get_supabase_admin()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "nome": user.nome,
                    "telefone": user.telefone,
                    "whatsapp": user.whatsapp
                }
            }
        })
        
        if response.user:
            # Log successful signup
            audit_service.create_audit_log(
                action=AuditAction.SIGNUP,
                user_id=response.user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                location=location,
                details={
                    "email": user.email,
                    "nome": user.nome,
                    "signup_timestamp": response.user.created_at.isoformat() if response.user.created_at else None
                },
                severity=AuditSeverity.INFO
            )
            
            return {"message": "User created", "user_id": response.user.id}
        
        # Log failed signup
        audit_service.create_audit_log(
            action=AuditAction.SIGNUP,
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            location=location,
            details={
                "email": user.email,
                "nome": user.nome
            },
            severity=AuditSeverity.WARNING
        )
        
        raise HTTPException(status_code=400, detail="Failed to create user")
        
    except Exception as e:
        # Log signup error
        audit_service.create_audit_log(
            action=AuditAction.SIGNUP,
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "email": user.email,
                "nome": user.nome
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/login",
    # Forca bruta na senha de quem guarda documento de cliente.
    #
    # 20 em 15 minutos e folgado para gente de verdade (erra duas, tres
    # vezes no maximo) e mesmo um escritorio de marina inteiro atras do
    # mesmo IP cabe. Para robo e inutil: com senha de 10 caracteres
    # exigindo maiuscula, minuscula e numero, 1900 tentativas por dia nao
    # chegam a lugar nenhum.
    dependencies=[Depends(limite("login", 20, 900))],
)
async def login(data: LoginRequest, request: Request):
    """Login with complete audit tracking"""
    supabase = get_supabase_admin()

    email = data.email
    password = data.password

    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)

    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.session:
            # Senha certa, mas o acesso depende do pagamento. Devolver o motivo
            # aqui (e não um 401 genérico) é o que faz a marina ir pagar em vez
            # de ligar achando que perdeu a senha.
            bloqueio = avaliar_acesso(getattr(response.user, "user_metadata", None))
            if bloqueio:
                audit_service.log_login(
                    user_id=response.user.id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=False,
                    error_message=f"acesso bloqueado: {bloqueio.motivo}",
                    location=location
                )
                raise HTTPException(status_code=402, detail=bloqueio.as_dict())

            # Log successful login
            audit_service.log_login(
                user_id=response.user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                location=location
            )

            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": response.user.id
            }
        
        # Log failed login
        audit_service.log_login(
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Invalid credentials",
            location=location
        )
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    except HTTPException:
        raise
    except Exception as e:
        # Log login error
        audit_service.log_login(
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location
        )
        
        raise HTTPException(status_code=401, detail="Invalid credentials")


def _bearer_token(authorization: str | None) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Token ausente")
    return authorization.split(" ", 1)[1].strip()


@router.post("/logout")
async def logout(request: Request, authorization: str = Header(None)):
    """Logout with audit tracking"""
    token = _bearer_token(authorization)
    supabase = get_supabase_admin()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        # Get user info before logout
        user = supabase.auth.get_user(token)
        user_id = user.user.id if user.user else "anonymous"
        
        supabase.auth.sign_out()
        
        # Log successful logout
        audit_service.create_audit_log(
            action=AuditAction.LOGOUT,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "logout_timestamp": supabase.auth.get_user(token).user.created_at.isoformat() if user.user else None
            },
            severity=AuditSeverity.INFO
        )
        
        return {"message": "Logged out"}
        
    except Exception as e:
        # Log logout error
        audit_service.create_audit_log(
            action=AuditAction.LOGOUT,
            user_id="unknown",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            severity=AuditSeverity.WARNING
        )
        
        return {"message": "Logged out"}


@router.get("/me")
async def get_me(request: Request, authorization: str = Header(None)):
    """Get current user info with audit tracking"""
    token = _bearer_token(authorization)
    supabase = get_supabase_admin()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        user = supabase.auth.get_user(token)

        # /me é o que o frontend chama para montar a sessão. Sem o porteiro
        # aqui, a marina cortada continuaria vendo o painel carregar.
        bloqueio = avaliar_acesso(getattr(user.user, "user_metadata", None) if user.user else None)
        if bloqueio:
            raise HTTPException(status_code=402, detail=bloqueio.as_dict())

        # Log user info access
        audit_service.create_audit_log(
            action=AuditAction.ASSET_VIEW,  # Using existing action for now
            user_id=user.user.id if user.user else "anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "action": "get_user_info",
                "timestamp": user.user.created_at.isoformat() if user.user and user.user.created_at else None
            },
            severity=AuditSeverity.INFO
        )
        
        return user.user

    except HTTPException:
        # O 402 do porteiro precisa chegar ao frontend com o motivo do bloqueio;
        # cair no handler abaixo o transformaria num 401 sem explicação.
        raise
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.ASSET_VIEW,
            user_id="anonymous",
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            severity=AuditSeverity.WARNING
        )
        
        raise HTTPException(status_code=401, detail="Invalid token")
