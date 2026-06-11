"""
Yachts Atlas — Integridade Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase import get_supabase_client
from app.core.security import get_current_user_id
from app.services.s3_service import get_s3_service

router = APIRouter()


@router.get("/{doc_id}/verify")
async def verify_documento(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    # Get document
    doc_response = supabase.table("documentos").select("*").eq("id", doc_id).execute()
    if not doc_response.data:
        raise HTTPException(status_code=404, detail="Document not found")
    doc_info = doc_response.data[0]
    ativo_id = doc_info["ativo_id"]
    
    # Verify authorization
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    user_marina_id = profile.get("marina_id")
    
    ativo_response = supabase.table("ativos").select("marina_id", "owner_id").eq("id", ativo_id).execute()
    if not ativo_response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = ativo_response.data[0]
    
    authorized = False
    if user_role == "admin":
        authorized = True
    elif user_role == "marina_manager" and user_marina_id and str(ativo.get("marina_id")) == str(user_marina_id):
        authorized = True
    elif user_role == "owner" and str(ativo.get("owner_id")) == str(user_id):
        authorized = True
        
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to verify this document")
        
    is_valid = s3_service.verify_integrity(doc_info["storage_path"], doc_info["hash_sha256"])
    valid_status = is_valid.get("valid", False) if isinstance(is_valid, dict) else bool(is_valid)
    
    return {
        "document_id": doc_id,
        "hash_original": doc_info["hash_sha256"],
        "is_valid": valid_status,
        "storage": "Supabase Storage",
        "verified_at": doc_info.get("created_at")
    }


@router.get("/ativo/{ativo_id}/relatorio")
async def gerar_relatorio_integridade(
    ativo_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    # Verify authorization
    profile_response = supabase.table("profiles").select("*").eq("id", user_id).execute()
    if not profile_response.data:
        raise HTTPException(status_code=404, detail="Profile not found")
    profile = profile_response.data[0]
    
    user_role = profile.get("user_role")
    user_marina_id = profile.get("marina_id")
    
    ativo_response = supabase.table("ativos").select("marina_id", "owner_id").eq("id", ativo_id).execute()
    if not ativo_response.data:
        raise HTTPException(status_code=404, detail="Ativo not found")
    ativo = ativo_response.data[0]
    
    authorized = False
    if user_role == "admin":
        authorized = True
    elif user_role == "marina_manager" and user_marina_id and str(ativo.get("marina_id")) == str(user_marina_id):
        authorized = True
    elif user_role == "owner" and str(ativo.get("owner_id")) == str(user_id):
        authorized = True
        
    if not authorized:
        raise HTTPException(status_code=403, detail="Not authorized to access this asset report")
        
    docs = supabase.table("documentos").select("*").eq("ativo_id", ativo_id).execute()
    
    total_docs = len(docs.data)
    docs_verificados = 0
    docs_pendentes = []
    
    for doc in docs.data:
        is_valid = s3_service.verify_integrity(doc["storage_path"], doc["hash_sha256"])
        valid_status = is_valid.get("valid", False) if isinstance(is_valid, dict) else bool(is_valid)
        if valid_status:
            docs_verificados += 1
        else:
            parts = doc.get("storage_path", "").split("/")
            filename_part = parts[-1] if parts else "documento.pdf"
            nome_arquivo = filename_part.split("_", 1)[1] if "_" in filename_part else filename_part
            
            docs_pendentes.append({
                "id": doc["id"],
                "nome": nome_arquivo,
                "tipo": doc["tipo"]
            })
            
    return {
        "ativo_id": ativo_id,
        "total_documentos": total_docs,
        "documentos_verificados": docs_verificados,
        "documentos_alterados": len(docs_pendentes),
        "documentos_pendentes": docs_pendentes,
        "status": "VERIFICADO" if len(docs_pendentes) == 0 else "INTEGRIDADE COMPROMETIDA",
        "storage": "Supabase Storage"
    }