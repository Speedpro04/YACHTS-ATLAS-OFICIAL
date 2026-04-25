from app.core.config import settings
import boto3
from botocore.exceptions import ClientError
import hashlib
import uuid
from datetime import datetime


class S3Service:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket = settings.S3_BUCKET_NAME
    
    def calculate_hash(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()
    
    def upload_with_worm(self, file_bytes: bytes, key: str, content_type: str = "application/pdf") -> dict:
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=file_bytes,
                ContentType=content_type,
                ObjectLockMode='COMPLIANCE',
                ObjectLockRetentionPeriodDays=365
            )
            return {
                "status": "success",
                "key": key,
                "hash": self.calculate_hash(file_bytes)
            }
        except ClientError as e:
            return {"status": "error", "message": str(e)}
    
    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return self.s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )
    
    def download_file(self, key: str) -> bytes:
        response = self.s3.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()
    
    def verify_integrity(self, key: str, expected_hash: str) -> bool:
        current_hash = self.calculate_hash(self.download_file(key))
        return current_hash == expected_hash


def get_s3_service() -> S3Service:
    return S3Service()