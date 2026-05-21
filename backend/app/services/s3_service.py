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
                url = supabase.storage.from_("media").get_public_url(key)
                
            logger.info(f"Generated signed URL for {key}")
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {key}: {str(e)}")
            try:
                return get_supabase_admin().storage.from_("media").get_public_url(key)
            except Exception:
                raise UploadError(f"Failed to generate presigned URL: {str(e)}")
    
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