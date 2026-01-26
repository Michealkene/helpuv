import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from app.core.config import settings
import uuid

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url=settings.R2_ENDPOINT,
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = settings.R2_BUCKET_NAME
    
    async def upload_dataset_csv(self, file, dataset_id: int) -> str:
        """Upload CSV to R2 and return file path"""
        file_key = f"datasets/{uuid.uuid4()}.csv"
        
        try:
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                file_key,
                ExtraArgs={'ContentType': 'text/csv'}
            )
            
            return f"r2://{self.bucket_name}/{file_key}"
        except ClientError as e:
            raise Exception(f"Upload failed: {str(e)}")
    
    async def generate_download_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate signed URL for CSV download"""
        file_key = file_path.replace(f"r2://{self.bucket_name}/", "")
        
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ResponseContentDisposition': f'attachment; filename="{file_key.split("/")[-1]}"'
                },
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            raise Exception(f"URL generation failed: {str(e)}")