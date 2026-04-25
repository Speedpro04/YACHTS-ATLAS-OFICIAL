"""
Yachts Atlas — Authentication Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.schemas.models import UsuarioCreate, UsuarioResponse
from app.core.supabase import get_supabase_admin
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter()


@router.post("/signup")
async def signup(user: UsuarioCreate):
    supabase = get_supabase_admin()
    
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
        return {"message": "User created", "user_id": response.user.id}
    
    raise HTTPException(status_code=400, detail="Failed to create user")


@router.post("/login")
async def login(email: str, password: str):
    supabase = get_supabase_admin()
    
    response = supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    
    if response.session:
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": response.user.id
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")


@router.post("/logout")
async def logout(token: str):
    supabase = get_supabase_admin()
    supabase.auth.sign_out()
    return {"message": "Logged out"}


@router.get("/me")
async def get_me(token: str):
    supabase = get_supabase_admin()
    user = supabase.auth.get_user(token)
    return user.user