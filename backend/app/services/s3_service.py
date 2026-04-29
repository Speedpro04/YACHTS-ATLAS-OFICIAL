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


class S3Service:
    """High-end S3 service with WORM (Write Once, Read Many) immutability"""
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_MIME_TYPES = [ft.value for ft in FileType]
    WORM_RETENTION_DAYS = 365
    
    def __init__(self):
        try:
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.bucket = settings.S3_BUCKET_NAME
            logger.info(f"S3Service initialized for bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"Failed to initialize S3Service: {e}")
            raise UploadError(f"S3 initialization failed: {str(e)}")
    
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
        Upload file with WORM (Write Once, Read Many) immutability
        Uses Object Lock to ensure files cannot be modified or deleted
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
            logger.info(f"Uploading file {key} with hash: {file_hash[:16]}...")
            
            # Upload with Object Lock for immutability
            response = self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
                ObjectLockMode='COMPLIANCE',
                ObjectLockRetainUntilDate=datetime.utcnow().replace(
                    microsecond=0
                ).replace(
                    year=datetime.utcnow().year + 1
                ).isoformat() + 'Z',
                ObjectLockLegalHoldStatus='OFF',
                Metadata={
                    'upload-timestamp': datetime.utcnow().isoformat(),
                    'original-hash': file_hash,
                    'content-type': content_type
                }
            )
            
            logger.info(f"Successfully uploaded {key} with WORM protection")
            
            return {
                "status": "success",
                "key": key,
                "hash": file_hash,
                "size": len(file_bytes),
                "version_id": response.get('VersionId'),
                "worm_retention_days": self.WORM_RETENTION_DAYS,
                "storage": "S3 WORM"
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_msg = e.response['Error']['Message']
            logger.error(f"S3 ClientError during upload: {error_code} - {error_msg}")
            
            return {
                "status": "error",
                "message": f"S3 upload failed: {error_code}",
                "error_code": error_code
            }
        except BotoCoreError as e:
            logger.error(f"BotoCoreError during upload: {str(e)}")
            return {
                "status": "error",
                "message": f"AWS service error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            return {
                "status": "error",
                "message": f"Upload failed: {str(e)}"
            }
    
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for secure file access"""
        try:
            url = self.s3.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket, 'Key': key},
                ExpiresIn=expires_in
            )
            logger.info(f"Generated presigned URL for {key}")
            return url
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL for {key}: {str(e)}")
            raise UploadError(f"Failed to generate presigned URL: {str(e)}")
    
    def download_file(self, key: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            file_bytes = response['Body'].read()
            logger.info(f"Downloaded file {key}, size: {len(file_bytes)} bytes")
            return file_bytes
        except ClientError as e:
            logger.error(f"Failed to download file {key}: {str(e)}")
            raise UploadError(f"Failed to download file: {str(e)}")
    
    def verify_integrity(self, key: str, expected_hash: str) -> Dict[str, Any]:
        """
        Verify file integrity by comparing current hash with expected hash
        Returns detailed verification result
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
        """Get file metadata from S3"""
        try:
            response = self.s3.head_object(Bucket=self.bucket, Key=key)
            return {
                "size": response['ContentLength'],
                "content_type": response['ContentType'],
                "last_modified": response['LastModified'].isoformat(),
                "metadata": response.get('Metadata', {}),
                "version_id": response.get('VersionId')
            }
        except ClientError as e:
            logger.error(f"Failed to get metadata for {key}: {str(e)}")
            return None
    
    def check_file_exists(self, key: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"Error checking file existence for {key}: {str(e)}")
            return False


def get_s3_service() -> S3Service:
    """Factory function to get S3Service instance"""
    return S3Service()