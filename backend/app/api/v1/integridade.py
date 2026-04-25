"""
Yachts Atlas — Integridade Endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
from app.core.supabase import get_supabase_client
from app.core.security import verify_token
from app.services.s3_service import get_s3_service

router = APIRouter()


def get_current_user_id(token: str = Depends(verify_token)) -> str:
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.get("sub")


@router.get("/{doc_id}/verify")
async def verify_documento(
    doc_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    doc = supabase.table("documentos").select("*").eq("id", doc_id).eq("usuario_id", user_id).execute()
    
    if not doc.data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = doc.data[0]
    is_valid = s3_service.verify_integrity(doc_info["storage_path"], doc_info["hash_sha256"])
    
    return {
        "document_id": doc_id,
        "hash_original": doc_info["hash_sha256"],
        "is_valid": is_valid,
        "storage": "S3 WORM",
        "verified_at": doc_info.get("validado_em")
    }


@router.get("/ativo/{ativo_id}/relatorio")
async def gerar_relatorio_integridade(
    ativo_id: str,
    user_id: str = Depends(get_current_user_id)
):
    supabase = get_supabase_client()
    s3_service = get_s3_service()
    
    docs = supabase.table("documentos").select("*").eq("ativo_id", ativo_id).eq("usuario_id", user_id).execute()
    
    if not docs.data:
        raise HTTPException(status_code=404, detail="No documents found")
    
    total_docs = len(docs.data)
    docs_verificados = 0
    docs_pendentes = []
    
    for doc in docs.data:
        is_valid = s3_service.verify_integrity(doc["storage_path"], doc["hash_sha256"])
        if is_valid:
            docs_verificados += 1
        else:
            docs_pendentes.append({
                "id": doc["id"],
                "nome": doc["nome_arquivo"],
                "tipo": doc["tipo"]
            })
    
    return {
        "ativo_id": ativo_id,
        "total_documentos": total_docs,
        "documentos_verificados": docs_verificados,
        "documentos_alterados": len(docs_pendentes),
        "documentos_pendentes": docs_pendentes,
        "status": "VERIFICADO" if len(docs_pendentes) == 0 else "INTEGRIDADE COMPROMETIDA",
        "storage": "S3 WORM"
    }