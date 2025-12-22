"""
Analyses API endpoints
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/bills/{billId}/analyze")
async def analyze_bill(billId: str, analysis_data: dict):
    """
    Запустити аналіз законопроєкту
    """
    # TODO: Implement with Celery task
    return {
        "analysisId": "...",
        "status": "pending",
        "estimatedTime": "3-7 хвилин",
        "jobId": "...",
        "gcsPath": f"gs://learn-documents-prod/..."
    }


@router.get("/bills/{billId}/analyses")
async def list_bill_analyses(billId: str):
    """
    Отримати результати аналізів законопроєкту
    """
    # TODO: Implement
    return {"analyses": []}


@router.get("/{analysisId}")
async def get_analysis(analysisId: str, format: str = "json"):
    """
    Отримати конкретний аналіз
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Analysis not found")


@router.get("/{analysisId}/progress")
async def get_analysis_progress(analysisId: str):
    """
    Перевірити прогрес аналізу
    """
    # TODO: Implement
    return {
        "status": "processing",
        "progress": 0,
        "message": "Starting analysis..."
    }


@router.get("/{analysisId}/export")
async def export_analysis(analysisId: str, format: str = "pdf"):
    """
    Експортувати аналіз
    """
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")
