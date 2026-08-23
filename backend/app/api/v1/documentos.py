"""
Yachts Atlas — Documentos Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from pydantic import BaseModel
from app.core.supabase import get_supabase_client, get_supabase_admin
from app.core.security import get_current_user_id
from app.core.authz import get_ativo_autorizado
from app.services.vision_service import classificar_foto, CATEGORIAS as GALERIA_CATS
from app.services.s3_service import get_s3_service
from app.services.audit_service import AuditService, AuditAction, AuditSeverity
from app.middleware.tracking import get_client_ip, get_user_agent, get_client_location
import re
import unicodedata
import uuid
from datetime import datetime

router = APIRouter()
audit_service = AuditService()


def _nome_seguro(nome: str | None) -> str:
    """
    Nome de arquivo aceitável como chave no Supabase Storage.

    O storage recusa chave com acento ou espaço e devolve 400 — e o frontend
    mostrava "servidor acordando, tente novamente", mandando a marina insistir
    para sempre num arquivo que nunca ia subir. Foto chamada
    "iate 38 pés.jfif" e nome de embarcação com acento sao a regra no Brasil,
    nao a excecao.

    Sanitiza SO a chave do storage. O nome original continua sendo gravado em
    documentos.nome_arquivo — e ele que a marina ve na tela.
    """
    base = unicodedata.normalize("NFKD", nome or "arquivo")
    base = base.encode("ascii", "ignore").decode("ascii")      # tira acento
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-.")   # espaço e o resto
    base = re.sub(r"-{2,}", "-", base)
    # Nome inteiro em caracteres proibidos (ex.: "日本語.jpg") vira vazio.
    return (base or "arquivo")[:120]


class ClassificarFotoBody(BaseModel):
    url: str


class MoverCategoriaBody(BaseModel):
    categoria: str  # chave da galeria, ex.: 'motor' (sem o prefixo 'galeria_')


@router.post("/classificar")
async def classificar_foto_endpoint(
    body: ClassificarFotoBody,
    _user_id: str = Depends(get_current_user_id),
):
    """Sugere a categoria da galeria para a foto (semi-automático).
    A sugestão é um ponto de partida — o usuário confirma/corrige na UI."""
    categoria = classificar_foto(body.url)
    return {"categoria": categoria}


@router.patch("/{doc_id}/categoria")
async def mover_categoria(
    doc_id: str,
    body: MoverCategoriaBody,
    user_id: str = Depends(get_current_user_id),
):
    """Move uma foto para outra categoria da galeria (correção de 1 clique).
    Só metadado — o arquivo e o hash permanecem imutáveis."""
    chave = (body.categoria or "").replace("galeria_", "").strip()
    if chave not in GALERIA_CATS:
        raise HTTPException(status_code=400, detail="Categoria inválida")
    supabase = get_supabase_admin()
    res = supabase.table("documentos").select("ativo_id").eq("id", doc_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    get_ativo_autorizado(res.data[0]["ativo_id"], user_id)
    supabase.table("documentos").update({"categoria": f"galeria_{chave}"}).eq("id", doc_id).execute()
    return {"id": doc_id, "categoria": f"galeria_{chave}"}


@router.get("/ativo/{ativo_id}")
async def list_documentos(
    ativo_id: str,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """List documents for an asset with audit tracking"""
    supabase = get_supabase_admin()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        # Check authorization (tolerante aos dois schemas)
        get_ativo_autorizado(ativo_id, user_id, incluir_proprietario=True)

        response = supabase.table("documentos").select("*").eq("ativo_id", ativo_id).execute()
        
        # Populate nome_arquivo dynamically from storage_path
        documents = []
        for doc in response.data:
            parts = doc.get("storage_path", "").split("/")
            filename_part = parts[-1] if parts else "documento.pdf"
            if "_" in filename_part:
                doc["nome_arquivo"] = filename_part.split("_", 1)[1]
            else:
                doc["nome_arquivo"] = filename_part
            documents.append(doc)

        # Link assinado no lugar da URL publica gravada. O balde `media` guarda
        # documento de cliente e vai ser fechado; a URL do banco so funciona
        # enquanto ele for publico. Assinado aqui, na leitura, o frontend nao
        # muda nada — ele le `url_arquivo` como sempre leu.
        from app.services.s3_service import assinar_documentos
        documents = assinar_documentos(documents)
            
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
                "document_count": len(documents),
                "action": "list_documents"
            },
            severity=AuditSeverity.INFO
        )
        
        return documents
        
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
    latitude: float | None = None,
    longitude: float | None = None,
    geo_precisao: float | None = None,
    geo_fonte: str | None = None,
    descricao: str | None = None,
    user_id: str = Depends(get_current_user_id),
    request: Request = None
):
    """Upload document with complete audit tracking"""
    # Insert via service key: o backend já autorizou via get_ativo_autorizado;
    # a chave anônima é barrada pelo RLS da tabela documentos.
    supabase = get_supabase_admin()
    s3_service = get_s3_service()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        # Check permission (tolerante aos dois schemas)
        get_ativo_autorizado(ativo_id, user_id)

        contents = await file.read()
        file_hash = s3_service.calculate_hash(contents)
        
        doc_id = str(uuid.uuid4())
        s3_key = f"ativos/{ativo_id}/docs/{doc_id}_{_nome_seguro(file.filename)}"
        
        # Upload to Storage
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
            
            raise HTTPException(status_code=500, detail="Failed to upload file")
        
        # Create document record (colunas existentes na tabela documentos)
        doc_data = {
            "id": doc_id,
            "ativo_id": ativo_id,
            "usuario_id": None if user_id == "maintenance-admin" else user_id,
            "nome_arquivo": file.filename,
            "tipo": tipo,
            "categoria": categoria,
            "url_arquivo": upload_result.get("public_url") or "",
            "storage_path": s3_key,
            "hash_sha256": file_hash,
            "tamanho_bytes": len(contents),
            "mime_type": file.content_type,
            "nivel": 1,
            "status": "verified"
        }

        # Geolocalização do dispositivo no momento do upload (opcional)
        if latitude is not None and longitude is not None:
            doc_data["latitude"] = latitude
            doc_data["longitude"] = longitude
            doc_data["geo_precisao"] = geo_precisao
            doc_data["geo_fonte"] = geo_fonte or "dispositivo"

        # Descrição livre do que está catalogado (opcional)
        if descricao and descricao.strip():
            doc_data["descricao"] = descricao.strip()[:300]

        response = supabase.table("documentos").insert(doc_data).execute()
        
        if response.data:
            # Log de auditoria nunca pode derrubar o upload (best-effort)
            try:
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
            except Exception:
                pass

            return {
                "id": doc_id,
                "hash": file_hash,
                "storage_path": s3_key,
                "chain_valid": True,
                "storage": "Supabase Storage",
                "public_url": upload_result.get("public_url")
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
    supabase = get_supabase_admin()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        response = supabase.table("documentos").select("*").eq("id", doc_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Document not found")
        doc = response.data[0]
        ativo_id = doc["ativo_id"]
        
        # Authorization check (tolerante aos dois schemas)
        get_ativo_autorizado(ativo_id, user_id, incluir_proprietario=True)

        # Dynamically set nome_arquivo
        parts = doc.get("storage_path", "").split("/")
        filename_part = parts[-1] if parts else "documento.pdf"
        if "_" in filename_part:
            doc["nome_arquivo"] = filename_part.split("_", 1)[1]
        else:
            doc["nome_arquivo"] = filename_part

        # Idem da listagem: a URL gravada morre junto com o balde publico.
        from app.services.s3_service import assinar_documentos
        assinar_documentos([doc])
            
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
                "ativo_id": ativo_id,
                "action": "get_document"
            },
            severity=AuditSeverity.INFO
        )
        
        return doc
        
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
    supabase = get_supabase_admin()
    s3_service = get_s3_service()
    
    # Get client information
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    location = get_client_location(request)
    
    try:
        response = supabase.table("documentos").select("*").eq("id", doc_id).execute()
        if not response.data:
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
            
        doc = response.data[0]
        ativo_id = doc["ativo_id"]
        
        # Check permissions (tolerante aos dois schemas)
        get_ativo_autorizado(ativo_id, user_id, incluir_proprietario=True)

        # Generate URL
        url = s3_service.get_presigned_url(doc["storage_path"])
        
        # Log successful download
        audit_service.log_document_download(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            document_id=doc_id,
            ativo_id=ativo_id,
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
