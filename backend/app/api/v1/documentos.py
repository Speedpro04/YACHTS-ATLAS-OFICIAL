"""
Yachts Atlas — Documentos Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from app.core.supabase import get_supabase_client
from app.core.security import verify_token
from app.services.s3_service import get_s3_service
import uuid
from datetime import datetime

router = APIRouter()


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.get("/ativo/{ativo_id}")
async def list_documentos(
    ativo_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    response = supabase.table("documentos").select("*").eq("ativo_id", ativo_id).eq("usuario_id", user_id).execute()
    return response.data


@router.post("/upload/{ativo_id}")
async def upload_documento(
    ativo_id: str,
    tipo: str,
    categoria: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    contents = await file.read()
    file_hash = s3_service.calculate_hash(contents)
    
    doc_id = str(uuid.uuid4())
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
    s3_key = f"ativos/{ativo_id}/docs/{doc_id}.{file_ext}"
    
    upload_result = s3_service.upload_with_worm(
        file_bytes=contents,
        key=s3_key,
        content_type=file.content_type or "application/pdf"
    )
    
    if upload_result["status"] != "success":
        raise HTTPException(status_code=500, detail="Failed to upload to S3")
    
    ultimo_hash = supabase.table("documentos").select("hash_sha256").eq("ativo_id", ativo_id).order("uploaded_at", desc=True).limit(1).execute()
    hash_anterior = ultimo_hash.data[0]["hash_sha256"] if ultimo_hash.data else None
    
    doc_data = {
        "id": doc_id,
        "ativo_id": ativo_id,
        "usuario_id": user_id,
        "nome_arquivo": file.filename,
        "tipo": tipo,
        "categoria": categoria,
        "hash_sha256": file_hash,
        "tamanho_bytes": len(contents),
        "mime_type": file.content_type,
        "storage_path": s3_key,
        "uploaded_by": user_id,
        "uploaded_at": datetime.utcnow().isoformat(),
        "hash_anterior": hash_anterior,
        "status": "verified",
        "validado_em": datetime.utcnow().isoformat()
    }
    
    response = supabase.table("documentos").insert(doc_data).execute()
    
    if response.data:
        return {
            "id": doc_id,
            "hash": file_hash,
            "storage_path": s3_key,
            "chain_valid": True,
            "storage": "S3 WORM"
        }
    
    raise HTTPException(status_code=400, detail="Failed to register document")


@router.get("/{doc_id}")
async def get_documento(doc_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    response = supabase.table("documentos").select("*").eq("id", doc_id).eq("usuario_id", user_id).execute()
    
    if response.data:
        return response.data[0]
    
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{doc_id}/download")
async def download_documento(doc_id: str, user_id: str = Depends(get_current_user_id)):
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    doc = supabase.table("documentos").select("storage_path").eq("id", doc_id).eq("usuario_id", user_id).execute()
    
    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    url = s3_service.get_presigned_url(doc.data[0]["storage_path"])
    return {"url": url}