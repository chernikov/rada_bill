"""
Google Cloud Storage service wrapper
"""
from google.cloud import storage
from typing import Optional, BinaryIO
import asyncio

from backend.config import config


class StorageService:
    """
    Service for Google Cloud Storage operations
    """
    
    def __init__(self):
        # Don't specify project - use ADC (Application Default Credentials)
        self.client = storage.Client()
        self.bucket_name = config.GCS_BUCKET_NAME
        self.bucket = self.client.bucket(self.bucket_name)
    
    async def upload_file(
        self,
        file_content: bytes,
        destination_path: str,
        content_type: str = None
    ) -> str:
        """
        Upload file to GCS
        
        Args:
            file_content: File content as bytes
            destination_path: Destination path in bucket
            content_type: MIME type
            
        Returns:
            GCS path (gs://bucket/path)
        """
        print(f"☁️  Uploading to GCS: {destination_path}")
        print(f"   Bucket: {self.bucket_name}, Size: {len(file_content)} bytes, Type: {content_type}")
        
        try:
            blob = self.bucket.blob(destination_path)
            
            if content_type:
                blob.content_type = content_type
            
            # Upload in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                blob.upload_from_string,
                file_content,
                content_type
            )
            
            gcs_path = f"gs://{self.bucket_name}/{destination_path}"
            print(f"✅ Uploaded: {gcs_path}")
            
            return gcs_path
        except Exception as e:
            print(f"❌ GCS upload failed: {type(e).__name__}: {str(e)}")
            raise
    
    async def download_file(self, source_path: str) -> Optional[bytes]:
        """
        Download file from GCS
        
        Args:
            source_path: Source path in bucket
            
        Returns:
            File content as bytes
        """
        print(f"☁️  Downloading from GCS: {source_path}")
        
        blob = self.bucket.blob(source_path)
        
        if not blob.exists():
            print(f"❌ File not found: {source_path}")
            return None
        
        loop = asyncio.get_event_loop()
        content = await loop.run_in_executor(
            None,
            blob.download_as_bytes
        )
        
        return content
    
    async def get_signed_url(
        self,
        blob_path: str,
        expiration_seconds: int = 3600
    ) -> str:
        """
        Generate signed URL for temporary access
        
        Args:
            blob_path: Path to blob in bucket
            expiration_seconds: URL expiration time
            
        Returns:
            Signed URL
        """
        blob = self.bucket.blob(blob_path)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_seconds,
            method="GET"
        )
        
        return url
    
    async def delete_file(self, blob_path: str) -> bool:
        """
        Delete file from GCS
        
        Args:
            blob_path: Path to blob in bucket
            
        Returns:
            True if deleted, False otherwise
        """
        print(f"🗑️  Deleting from GCS: {blob_path}")
        
        blob = self.bucket.blob(blob_path)
        
        if blob.exists():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, blob.delete)
            return True
        
        return False
    
    def generate_bill_path(self, bill_number: str, filename: str) -> str:
        """
        Generate GCS path for bill file following hierarchical structure
        
        Args:
            bill_number: Bill number (e.g., "12414")
            filename: File name
            
        Returns:
            GCS path
        """
        try:
            num = int(bill_number)
        except ValueError:
            return f"{bill_number}/{filename}"
        
        # Thousand range: 12000-12999
        thousand_start = (num // 1000) * 1000
        thousand_end = thousand_start + 1000
        thousand_folder = f"{thousand_start:04d}-{thousand_end - 1:04d}"
        
        # Hundred range: 12400-12499
        hundred_start = (num // 100) * 100
        hundred_end = hundred_start + 100
        hundred_folder = f"{hundred_start:04d}-{hundred_end - 1:04d}"
        
        # Bill folder: 12414
        bill_folder = f"{num:04d}"
        
        return f"{thousand_folder}/{hundred_folder}/{bill_folder}/{filename}"
