"""
Admin API endpoints
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/stats")
async def get_stats():
    """
    Dashboard статистика
    """
    # TODO: Implement with Firestore aggregation
    return {
        "totalBills": 0,
        "totalDocuments": 0,
        "totalAnalyses": 0,
        "activeUsers": 0,
        "aiTokensUsed": 0,
        "storageUsed": "0 GB"
    }


@router.get("/logs")
async def get_logs(
    level: str = "info",
    service: str = None,
    startDate: str = None,
    endDate: str = None
):
    """
    Отримати логи системи
    """
    # TODO: Implement with Cloud Logging
    return {"logs": []}
