"""
Yachts Atlas — Documentos Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from app.core.supabase import get_supabase_client
from app.core.security import verify_token
from app.services.s3_service import get_s3_service
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location
import uuid
from datetime import datetime

router = APIRouter()
audit_service = AuditService()


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.get("/ativo/{ativo_id}")
async def list_documentos(
    ativo_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """List documents for an asset with audit tracking"""
    supabase = get_supabase_client()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        response = supabase.table("documentos").select("*").eq("ativo_id", ativo_id).eq("usuario_id", user_id).execute()
        
        # Log document list access
        audit_service.create_audit_log(
            action=AuditAction.DOCUMENT_VIEW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=True,
            location=location,
            details={
                "ativo_id": ativo_id,
                "document_count": len(response.data),
                "action": "list_documents"
            },
            severity=AuditSeverity.INFO
        )
        
        return response.data
        
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.DOCUMENT_VIEW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "ativo_id": ativo_id,
                "action": "list_documents"
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail="Failed to list documents")


@router.post("/upload/{ativo_id}")
async def upload_documento(
    ativo_id: str,
    tipo: str,
    categoria: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Upload document with complete audit tracking and WORM immutability"""
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        contents = await file.read()
        file_hash = s3_service.calculate_hash(contents)
        
        doc_id = str(uuid.uuid4())
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "pdf"
        s3_key = f"ativos/{ativo_id}/docs/{doc_id}.{file_ext}"
        
        # Upload to S3 with WORM protection
        upload_result = s3_service.upload_with_worm(
            file_bytes=contents,
            key=s3_key,
            content_type=file.content_type or "application/pdf"
        )
        
        if upload_result["status"] != "success":
            # Log failed upload
            audit_service.log_document_upload(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                document_id=doc_id,
                ativo_id=ativo_id,
                file_name=file.filename,
                file_size=len(contents),
                file_hash=file_hash,
                success=False,
                error_message=upload_result.get("message", "Unknown error"),
                location=location
            )
            
            raise HTTPException(status_code=500, detail="Failed to upload to S3")
        
        # Get previous hash for chain
        ultimo_hash = supabase.table("documentos").select("hash_sha256").eq("ativo_id", ativo_id).order("uploaded_at", desc=True).limit(1).execute()
        hash_anterior = ultimo_hash.data[0]["hash_sha256"] if ultimo_hash.data else None
        
        # Create document record
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
            "validado_em": datetime.utcnow().isoformat(),
            "s3_version_id": upload_result.get("version_id")
        }
        
        response = supabase.table("documentos").insert(doc_data).execute()
        
        if response.data:
            # Log successful upload
            audit_service.log_document_upload(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                document_id=doc_id,
                ativo_id=ativo_id,
                file_name=file.filename,
                file_size=len(contents),
                file_hash=file_hash,
                success=True,
                location=location
            )
            
            return {
                "id": doc_id,
                "hash": file_hash,
                "storage_path": s3_key,
                "chain_valid": True,
                "storage": "S3 WORM",
                "version_id": upload_result.get("version_id"),
                "worm_retention_days": upload_result.get("worm_retention_days")
            }
        
        # Log database insert failure
        audit_service.log_document_upload(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            document_id=doc_id,
            ativo_id=ativo_id,
            file_name=file.filename,
            file_size=len(contents),
            file_hash=file_hash,
            success=False,
            error_message="Failed to insert document record",
            location=location
        )
        
        raise HTTPException(status_code=400, detail="Failed to register document")
        
    except HTTPException:
        raise
    except Exception as e:
        # Log unexpected error
        audit_service.log_document_upload(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            document_id=str(uuid.uuid4()),
            ativo_id=ativo_id,
            file_name=file.filename if file else "unknown",
            file_size=0,
            file_hash="",
            success=False,
            error_message=str(e),
            location=location
        )
        
        raise HTTPException(status_code=500, detail="Upload failed")


@router.get("/{doc_id}")
async def get_documento(doc_id: str, user_id: str = Depends(get_current_user_id), request: Request = None):
    """Get document details with audit tracking"""
    supabase = get_supabase_client()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        response = supabase.table("documentos").select("*").eq("id", doc_id).eq("usuario_id", user_id).execute()
        
        if response.data:
            # Log document view
            audit_service.create_audit_log(
                action=AuditAction.DOCUMENT_VIEW,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True,
                location=location,
                details={
                    "document_id": doc_id,
                    "ativo_id": response.data[0].get("ativo_id"),
                    "action": "get_document"
                },
                severity=AuditSeverity.INFO
            )
            
            return response.data[0]
        
        # Log document not found
        audit_service.create_audit_log(
            action=AuditAction.DOCUMENT_VIEW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message="Document not found",
            location=location,
            details={
                "document_id": doc_id,
                "action": "get_document"
            },
            severity=AuditSeverity.WARNING
        )
        
        raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        audit_service.create_audit_log(
            action=AuditAction.DOCUMENT_VIEW,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=False,
            error_message=str(e),
            location=location,
            details={
                "document_id": doc_id,
                "action": "get_document"
            },
            severity=AuditSeverity.ERROR
        )
        
        raise HTTPException(status_code=500, detail="Failed to get document")


@router.get("/{doc_id}/download")
async def download_documento(doc_id: str, user_id: str = Depends(get_current_user_id), request: Request = None):
    """Download document with complete audit tracking"""
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        doc = supabase.table("documentos").select("storage_path", "ativo_id", "nome_arquivo").eq("id", doc_id).eq("usuario_id", user_id).execute()
        
        if not doc.data:
            # Log document not found
            audit_service.log_document_download(
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                document_id=doc_id,
                ativo_id="unknown",
                success=False,
                error_message="Document not found",
                location=location
            )
            
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Generate presigned URL
        url = s3_service.get_presigned_url(doc.data[0]["storage_path"])
        
        # Log successful download
        audit_service.log_document_download(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            document_id=doc_id,
            ativo_id=doc.data[0]["ativo_id"],
            success=True,
            location=location
        )
        
        return {"url": url}
        
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        audit_service.log_document_download(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            document_id=doc_id,
            ativo_id="unknown",
            success=False,
            error_message=str(e),
            location=location
        )
        
        raise HTTPException(status_code=500, detail="Failed to generate download URL")