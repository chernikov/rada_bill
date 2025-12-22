"""
Bill-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class BillCreate(BaseModel):
    """Model for creating a new bill"""
    number: str = Field(..., description="Bill number (e.g., '12414')")
    source: str = Field(..., description="Source: manual, telegram, web")
    userId: Optional[str] = Field(None, description="User ID (Firebase UID or Telegram chatId)")


class BillUpdate(BaseModel):
    """Model for updating a bill"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class Bill(BaseModel):
    """Bill model"""
    id: str
    number: str
    title: Optional[str] = None
    description: Optional[str] = None
    status: str  # draft, active, downloading, error, archived
    userId: Optional[str] = None
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        from_attributes = True
