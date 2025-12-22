"""
Cleanup utility for GCS storage maintenance
Migrated from: src/cleanup.py
"""
import asyncio
from typing import List, Dict
from google.cloud import storage

from backend.config import config


class CleanupService:
    """
    Service for cleaning up GCS storage
    """
    
    def __init__(self):
        self.client = storage.Client(project=config.GOOGLE_CLOUD_PROJECT)
        self.bucket = self.client.bucket(config.GCS_BUCKET_NAME)
    
    async def get_storage_stats(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage stats
        """
        print("📊 Calculating storage statistics...")
        
        total_size = 0
        file_count = 0
        file_types = {}
        
        blobs = self.bucket.list_blobs()
        
        for blob in blobs:
            file_count += 1
            total_size += blob.size
            
            # Get file extension
            ext = blob.name.split('.')[-1].lower() if '.' in blob.name else 'no_ext'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            'totalFiles': file_count,
            'totalSize': total_size,
            'totalSizeFormatted': self._format_size(total_size),
            'fileTypes': file_types
        }
    
    async def delete_bill_data(self, bill_number: str) -> int:
        """
        Delete all data for a specific bill
        
        Args:
            bill_number: Bill number
            
        Returns:
            Number of files deleted
        """
        print(f"🗑️  Deleting all data for bill: {bill_number}")
        
        # Find all files for this bill
        prefix = self._get_bill_prefix(bill_number)
        blobs = self.bucket.list_blobs(prefix=prefix)
        
        deleted_count = 0
        for blob in blobs:
            blob.delete()
            deleted_count += 1
        
        print(f"✅ Deleted {deleted_count} files")
        
        return deleted_count
    
    async def cleanup_old_analyses(self, days: int = 90) -> int:
        """
        Delete analysis files older than specified days
        
        Args:
            days: Age threshold in days
            
        Returns:
            Number of files deleted
        """
        print(f"🗑️  Cleaning up analyses older than {days} days...")
        
        # TODO: Implement age-based cleanup
        # TODO: Use lifecycle policies instead
        
        return 0
    
    def _format_size(self, size_bytes: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def _get_bill_prefix(self, bill_number: str) -> str:
        """Get GCS prefix for bill"""
        try:
            num = int(bill_number)
            
            thousand_start = (num // 1000) * 1000
            thousand_end = thousand_start + 1000
            thousand_folder = f"{thousand_start:04d}-{thousand_end - 1:04d}"
            
            hundred_start = (num // 100) * 100
            hundred_end = hundred_start + 100
            hundred_folder = f"{hundred_start:04d}-{hundred_end - 1:04d}"
            
            bill_folder = f"{num:04d}"
            
            return f"{thousand_folder}/{hundred_folder}/{bill_folder}/"
            
        except ValueError:
            return f"{bill_number}/"
