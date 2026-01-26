"""
Storage Service - File storage for CSV datasets using S3/R2
"""

import boto3
from botocore.config import Config
from typing import Optional
import uuid
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """
    Service for handling file storage on S3-compatible storage (Cloudflare R2, AWS S3).
    
    Used for:
    - Storing dataset CSV files
    - Generating signed download URLs
    """
    
    def __init__(self):
        # Only initialize if R2/S3 is configured
        if settings.R2_ENDPOINT and settings.R2_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.R2_ENDPOINT,
                aws_access_key_id=settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
                config=Config(signature_version='s3v4')
            )
            self.bucket_name = settings.R2_BUCKET_NAME
            self.is_configured = True
        else:
            self.s3_client = None
            self.bucket_name = None
            self.is_configured = False
            logger.warning("Storage service not configured - R2/S3 credentials missing")
    
    async def upload_csv(
        self,
        file_content: bytes,
        filename: Optional[str] = None
    ) -> str:
        """
        Upload a CSV file to storage.
        
        Args:
            file_content: CSV file bytes
            filename: Optional filename (auto-generated if not provided)
            
        Returns:
            Storage path (e.g., "datasets/abc123.csv")
        """
        if not self.is_configured:
            raise Exception("Storage service not configured")
        
        if not filename:
            filename = f"{uuid.uuid4().hex}.csv"
        
        file_key = f"datasets/{filename}"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content,
                ContentType='text/csv',
                ContentDisposition=f'attachment; filename="{filename}"'
            )
            
            logger.info(f"Uploaded CSV to {file_key}")
            return file_key
            
        except Exception as e:
            logger.error(f"Failed to upload CSV: {e}")
            raise Exception(f"Failed to upload file: {str(e)}")
    
    async def generate_download_url(
        self,
        file_path: str,
        expires_in: int = 3600,
        download_filename: Optional[str] = None
    ) -> str:
        """
        Generate a signed URL for downloading a file.
        
        Args:
            file_path: Path to file in storage (e.g., "datasets/abc123.csv")
            expires_in: URL expiration time in seconds (default 1 hour)
            download_filename: Custom filename for download
            
        Returns:
            Signed download URL
        """
        if not self.is_configured:
            raise Exception("Storage service not configured")
        
        # Handle different path formats
        if file_path.startswith("r2://") or file_path.startswith("s3://"):
            # Extract key from full URL
            parts = file_path.split("/", 3)
            file_key = parts[3] if len(parts) > 3 else file_path
        else:
            file_key = file_path
        
        params = {
            'Bucket': self.bucket_name,
            'Key': file_key
        }
        
        # Add custom filename for download
        if download_filename:
            params['ResponseContentDisposition'] = f'attachment; filename="{download_filename}"'
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params=params,
                ExpiresIn=expires_in
            )
            
            logger.info(f"Generated download URL for {file_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate download URL: {e}")
            raise Exception(f"Failed to generate download URL: {str(e)}")
    
    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage.
        
        Args:
            file_path: Path to file in storage
            
        Returns:
            True if deleted successfully
        """
        if not self.is_configured:
            raise Exception("Storage service not configured")
        
        # Extract key from path
        if file_path.startswith("r2://") or file_path.startswith("s3://"):
            parts = file_path.split("/", 3)
            file_key = parts[3] if len(parts) > 3 else file_path
        else:
            file_key = file_path
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            logger.info(f"Deleted file {file_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file: {e}")
            raise Exception(f"Failed to delete file: {str(e)}")
    
    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage.
        
        Args:
            file_path: Path to file in storage
            
        Returns:
            True if file exists
        """
        if not self.is_configured:
            return False
        
        # Extract key from path
        if file_path.startswith("r2://") or file_path.startswith("s3://"):
            parts = file_path.split("/", 3)
            file_key = parts[3] if len(parts) > 3 else file_path
        else:
            file_key = file_path
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
            
        except self.s3_client.exceptions.ClientError:
            return False
        except Exception:
            return False

    async def download_file(self, file_path: str) -> bytes:
        """
        Download file content from storage.
        
        Args:
            file_path: Path to file in storage
            
        Returns:
            File content as bytes
        """
        if not self.is_configured:
            raise Exception("Storage service not configured")
        
        # Extract key from path
        if file_path.startswith("r2://") or file_path.startswith("s3://"):
            parts = file_path.split("/", 3)
            file_key = parts[3] if len(parts) > 3 else file_path
        else:
            file_key = file_path
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            
            content = response['Body'].read()
            logger.info(f"Downloaded file {file_key}, size: {len(content)} bytes")
            return content
            
        except Exception as e:
            logger.error(f"Failed to download file: {e}")
            raise Exception(f"Failed to download file: {str(e)}")
