"""
S3 Storage Service for file uploads.
"""
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from django.conf import settings
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class S3Service:
    """سرویس مدیریت فایل در S3."""
    
    def __init__(self):
        """Initialize S3 client."""
        endpoint_url = settings.S3_ENDPOINT_URL
        
        # Configure boto3 client with signature version
        boto_config = Config(
            signature_version='s3v4',
            s3={'addressing_style': 'path'}
        )
            
        self.s3_client = boto3.client(
            's3',
            endpoint_url=endpoint_url,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            region_name=settings.S3_REGION,
            use_ssl=settings.S3_USE_SSL,
            config=boto_config
        )
        self.bucket_name = settings.S3_TEMP_BUCKET
        self.temp_prefix = "temp_uploads/"
        
        # Create bucket if it doesn't exist
        self._ensure_bucket_exists()
        
    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Bucket {self.bucket_name} already exists")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                try:
                    self.s3_client.create_bucket(Bucket=self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                except Exception as create_error:
                    logger.error(f"Failed to create bucket: {create_error}")
                    raise
            elif error_code == '403':
                # Bucket exists but we don't have permission to check - that's OK
                logger.warning(f"Bucket {self.bucket_name} exists but access check forbidden (403) - continuing anyway")
            else:
                logger.error(f"Error checking bucket: {e}")
                raise
    
    def upload_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        content_type: str = 'application/octet-stream'
    ) -> dict:
        """
        آپلود فایل به MinIO.
        
        Args:
            file_content: محتوای فایل به صورت bytes
            filename: نام فایل اصلی
            user_id: شناسه کاربر
            content_type: نوع محتوای فایل
            
        Returns:
            {
                'object_key': 'temp_uploads/user123/file.pdf',
                'filename': 'document.pdf',
                'size_bytes': 1024,
                'content_type': 'application/pdf',
                'expires_at': '2024-11-30T12:00:00',
                'bucket_name': 'shared-storage'
            }
        """
        # تولید کلید یکتا
        file_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        object_key = f"{self.temp_prefix}{user_id}/{timestamp}_{file_id}_{filename}"
        
        # محاسبه زمان انقضا (24 ساعت)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        
        try:
            # آپلود به S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_content,
                ContentType=content_type
            )
            
            logger.info(f"Uploaded file: {object_key} ({len(file_content)} bytes)")
            
            return {
                'object_key': object_key,
                'filename': filename,
                'size_bytes': len(file_content),
                'content_type': content_type,
                'expires_at': expires_at.isoformat(),
                'bucket_name': self.bucket_name
            }
        except Exception as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def generate_presigned_url(
        self,
        object_key: str,
        expiration: int = 3600
    ) -> str:
        """
        تولید URL امن با زمان انقضا.
        
        Args:
            object_key: کلید فایل در MinIO
            expiration: زمان انقضا به ثانیه (پیش‌فرض 1 ساعت)
            
        Returns:
            URL امن برای دانلود فایل
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': object_key
                },
                ExpiresIn=expiration
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, object_key: str) -> bool:
        """
        حذف فایل از MinIO.
        
        Args:
            object_key: کلید فایل در MinIO
            
        Returns:
            True اگر حذف موفق باشد
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            logger.info(f"Deleted file: {object_key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            return False


# سرویس سراسری
s3_service = S3Service()
