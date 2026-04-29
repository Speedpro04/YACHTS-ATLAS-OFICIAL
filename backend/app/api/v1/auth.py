"""
Yachts Atlas — Authentication Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from app.schemas.models import UsuarioCreate, UsuarioResponse
from app.core.supabase import get_supabase_admin
from app.core.security import hash_password, verify_password, create_access_token
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location

router = APIRouter()
audit_service = AuditService()


@router.post("/signup")
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


@router.post("/login")
async def login(email: str, password: str, request: Request):
    """Login with complete audit tracking"""
    supabase = get_supabase_admin()
    
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


@router.post("/logout")
async def logout(token: str, request: Request):
    """Logout with audit tracking"""
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
async def get_me(token: str, request: Request):
    """Get current user info with audit tracking"""
    supabase = get_supabase_admin()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        user = supabase.auth.get_user(token)
        
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