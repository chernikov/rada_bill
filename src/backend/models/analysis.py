"""
Analysis-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AnalysisCreate(BaseModel):
    """Model for creating analysis"""
    billId: str
    scope: str = Field(..., description="all, documents, summary")
    documentIds: Optional[List[str]] = None
    userId: str
    source: str = Field(..., description="web, telegram")
    saveToFile: bool = True


class Analysis(BaseModel):
    """Analysis model"""
    id: str
    billId: str
    result: Optional[dict] = None
    processing: dict
    ai: dict
    storage: Optional[dict] = None
    createdAt: datetime
    
    class Config:
        from_attributes = True
