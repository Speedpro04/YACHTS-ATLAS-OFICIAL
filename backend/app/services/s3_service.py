import hashlib
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from app.core.config import settings
import boto3
from botocore.exceptions import ClientError, BotoCoreError


logger = logging.getLogger(__name__)


class FileType(str, Enum):
    PDF = "application/pdf"
    JPG = "image/jpeg"
    JPEG = "image/jpeg"
    PNG = "image/png"


class UploadError(Exception):
    """Custom exception for upload errors"""
    pass


from app.core.supabase import get_supabase_client, get_supabase_admin

logger = logging.getLogger(__name__)


class FileType(str, Enum):
    PDF = "application/pdf"
    JPG = "image/jpeg"
    JPEG = "image/jpeg"
    PNG = "image/png"


class UploadError(Exception):
    """Custom exception for upload errors"""
    pass


class S3Service:
    """High-end storage service integrated with Supabase Storage (media bucket)"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES = [ft.value for ft in FileType]
    WORM_RETENTION_DAYS = 365
    
    def __init__(self):
        try:
            # Ensure Supabase is configured
            self.supabase = get_supabase_client()
            logger.info("S3Service initialized using Supabase Storage client")
        except Exception as e:
            logger.error(f"Failed to initialize storage service: {e}")
            raise UploadError(f"Storage initialization failed: {str(e)}")
    
    def calculate_hash(self, file_bytes: bytes) -> str:
        """Calculate SHA-256 hash for file integrity verification"""
        return hashlib.sha256(file_bytes).hexdigest()
    
    def validate_file(self, file_bytes: bytes, content_type: str) -> Dict[str, Any]:
        """Validate file before upload"""
        errors = []
        
        # Check file size
        if len(file_bytes) > self.MAX_FILE_SIZE:
            errors.append(f"File size exceeds {self.MAX_FILE_SIZE / 1024 / 1024}MB limit")
        
        # Check content type
        if content_type not in self.ALLOWED_MIME_TYPES:
            errors.append(f"Invalid content type: {content_type}")
        
        # Check if file is empty
        if len(file_bytes) == 0:
            errors.append("File is empty")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "size": len(file_bytes),
            "content_type": content_type
        }
    
    def upload_with_worm(self, file_bytes: bytes, key: str, content_type: str = "application/pdf") -> Dict[str, Any]:
        """
        Upload file to Supabase Storage (bucket: media)
        """
        try:
            # Validate file first
            validation = self.validate_file(file_bytes, content_type)
            if not validation["valid"]:
                logger.error(f"File validation failed: {validation['errors']}")
                return {
                    "status": "error",
                    "message": "File validation failed",
                    "errors": validation["errors"]
                }
            
            # Calculate hash before upload
            file_hash = self.calculate_hash(file_bytes)
            logger.info(f"Uploading file {key} to Supabase with hash: {file_hash[:16]}...")
            
            supabase = get_supabase_admin()
            
            # Attempt to remove if already exists to overwrite
            try:
                supabase.storage.from_("media").remove([key])
            except Exception:
                pass
                
            response = supabase.storage.from_("media").upload(
                path=key,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            
            # Get public URL
            try:
                public_url = supabase.storage.from_("media").get_public_url(key)
            except Exception:
                public_url = ""
            
            logger.info(f"Successfully uploaded {key} to Supabase Storage")
            
            return {
                "status": "success",
                "key": key,
                "hash": file_hash,
                "size": len(file_bytes),
                "version_id": "1",
                "worm_retention_days": self.WORM_RETENTION_DAYS,
                "storage": "Supabase Storage",
                "public_url": public_url
            }
            
        except Exception as e:
            logger.error(f"Unexpected error during Supabase storage upload: {str(e)}")
            return {
                "status": "error",
                "message": f"Upload failed: {str(e)}"
            }
    
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate signed URL for secure file access from Supabase Storage"""
        try:
            supabase = get_supabase_admin()
            res = supabase.storage.from_("media").create_signed_url(key, expires_in)
            
            url = None
            if isinstance(res, dict):
                url = res.get("signedURL") or res.get("signedUrl")
            else:
                url = getattr(res, 'signed_url', None) or str(res)
                
            if not url:
                # Sem fallback para URL publica, de proposito. O balde `media`
                # guarda documento de cliente e caminha para ser fechado; com
                # ele privado, get_public_url devolve um endereco que responde
                # 400 — um link que PARECE bom e nao abre. O portador so
                # descobre na frente do comprador ou do perito.
                #
                # Falhar alto aqui e melhor: quem chamou trata, e o erro tem
                # nome. Foi a licao de 23/08/2026, quando "sucesso" e "nem
                # tentei" ficaram indistinguiveis no log por meio dia.
                raise UploadError(f"Supabase nao devolveu URL assinada para {key}")

            logger.info(f"Generated signed URL for {key}")
            return url
        except UploadError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {key}: {str(e)}")
            raise UploadError(f"Failed to generate presigned URL: {str(e)}")

    def urls_assinadas(self, keys: list, expires_in: int = 3600) -> dict:
        """Assina varios caminhos de uma vez. Devolve {caminho: url}.

        Um dossie tem dezenas de fotos; assinar uma a uma seriam dezenas de
        idas ao Supabase, em serie, no meio da geracao do PDF. A API tem
        `create_signed_urls` no plural justamente para isso — uma chamada.

        Caminho que falhar simplesmente NAO entra no resultado. Quem chamou
        decide o que fazer com a ausencia (pular a foto, esconder o botao),
        que e sempre melhor do que entregar um link quebrado no lugar.
        """
        keys = [k for k in dict.fromkeys(keys) if k]
        if not keys:
            return {}

        try:
            resp = get_supabase_admin().storage.from_("media").create_signed_urls(
                keys, expires_in
            )
        except Exception as e:
            logger.error(f"Falha ao assinar {len(keys)} caminhos em lote: {e}")
            return {}

        assinadas = {}
        for item in (resp or []):
            if not isinstance(item, dict):
                continue
            caminho = item.get("path") or item.get("Key")
            url = item.get("signedURL") or item.get("signedUrl")
            if caminho and url and not item.get("error"):
                assinadas[caminho] = url

        faltaram = len(keys) - len(assinadas)
        if faltaram:
            logger.warning(f"{faltaram} de {len(keys)} caminhos ficaram sem URL assinada")
        return assinadas
    
    def download_file(self, key: str) -> bytes:
        """Download file from Supabase Storage"""
        try:
            supabase = get_supabase_admin()
            file_bytes = supabase.storage.from_("media").download(key)
            logger.info(f"Downloaded file {key} from Supabase Storage, size: {len(file_bytes)} bytes")
            return file_bytes
        except Exception as e:
            logger.error(f"Failed to download file {key} from Supabase Storage: {str(e)}")
            raise UploadError(f"Failed to download file: {str(e)}")
    
    def verify_integrity(self, key: str, expected_hash: str) -> Dict[str, Any]:
        """
        Verify file integrity by comparing current hash with expected hash
        """
        try:
            current_hash = self.calculate_hash(self.download_file(key))
            is_valid = current_hash == expected_hash
            
            result = {
                "valid": is_valid,
                "expected_hash": expected_hash,
                "current_hash": current_hash,
                "key": key,
                "verified_at": datetime.utcnow().isoformat()
            }
            
            if is_valid:
                logger.info(f"Integrity verified for {key}")
            else:
                logger.error(f"Integrity check failed for {key}: hash mismatch")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify integrity for {key}: {str(e)}")
            return {
                "valid": False,
                "error": str(e),
                "key": key
            }
    
    def get_file_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from Supabase Storage"""
        try:
            return {
                "size": 0,
                "content_type": "application/octet-stream",
                "last_modified": datetime.utcnow().isoformat(),
                "metadata": {},
                "version_id": "1"
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {key}: {str(e)}")
            return None
    
    def check_file_exists(self, key: str) -> bool:
        """Check if file exists in Supabase Storage"""
        try:
            supabase = get_supabase_admin()
            supabase.storage.from_("media").create_signed_url(key, 10)
            return True
        except Exception:
            return False


def get_s3_service() -> S3Service:
    """Factory function to get S3Service instance"""
    return S3Service()

# Validade do link assinado servido ao painel e ao portal do armador.
#
# 8 horas: cobre uma jornada de trabalho inteira (a marina abre o painel de
# manhã e as miniaturas continuam carregando à tarde, sem recarregar a página)
# e mesmo assim o link morre no mesmo dia. Link assinado que vaza é exposição
# real enquanto vale — só que limitada a UM arquivo, e não ao balde inteiro,
# que é o que se tem hoje com o `media` público.
VALIDADE_LINK_PAINEL = 8 * 3600


def assinar_documentos(documentos: list, expires_in: int = VALIDADE_LINK_PAINEL) -> list:
    """Troca a `url_arquivo` gravada por um link assinado, na hora de servir.

    A URL pública que está no banco só funciona enquanto o balde `media` for
    público — e ele guarda documento de cliente: nota fiscal, apólice, laudo.
    Hoje qualquer pessoa com o endereço baixa sem autenticar nenhuma.

    Assinar na LEITURA, e não regravar o banco, é de propósito:

      * `storage_path` existe em 100% dos documentos; `url_arquivo` só em
        parte deles. O caminho é a fonte confiável, a URL é derivada.
      * link assinado vence. Gravar um no banco seria gravar algo que expira
        num lugar que não expira — o defeito voltaria em oito horas.
      * o frontend não precisa mudar nada: ele lê `url_arquivo` em quatro
        telas e continua lendo.

    Documento sem caminho, ou que falhe ao assinar, sai com `url_arquivo`
    vazia — a tela esconde o botão. Melhor do que entregar um link que
    parece bom e responde 400.
    """
    if not documentos:
        return documentos

    caminhos = [d.get("storage_path") for d in documentos if isinstance(d, dict)]
    assinadas = get_s3_service().urls_assinadas(caminhos, expires_in)

    for d in documentos:
        if isinstance(d, dict):
            d["url_arquivo"] = assinadas.get(d.get("storage_path")) or ""
    return documentos
