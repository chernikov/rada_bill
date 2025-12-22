"""
Document-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Document(BaseModel):
    """Document model"""
    id: str
    billId: str
    filename: str
    fileType: str  # pdf, docx, html, md
    size: int
    gcsPath: str
    uploadedAt: datetime
    
    processing: Optional[dict] = None
    
    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    """Model for document upload"""
    billId: str
    documentId: str
    sequenceNumber: int
