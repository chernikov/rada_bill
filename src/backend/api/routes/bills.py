"""
Bills API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

router = APIRouter()


@router.get("")
async def list_bills(
    status: Optional[str] = None,
    userId: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sortBy: str = "createdAt",
    order: str = "desc"
):
    """
    Список законопроєктів з фільтрацією та пагінацією
    """
    # TODO: Implement with Firestore
    return {
        "bills": [],
        "total": 0,
        "page": page,
        "pages": 0
    }


@router.get("/{billId}")
async def get_bill(billId: str):
    """
    Отримати деталі законопроєкту
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Bill not found")


@router.post("")
async def create_bill(bill_data: dict):
    """
    Створити новий законопроєкт (запускає завантаження)
    """
    # TODO: Implement with background job
    return {
        "billId": "...",
        "number": bill_data.get("number"),
        "status": "downloading",
        "jobId": "..."
    }


@router.put("/{billId}")
async def update_bill(billId: str, bill_data: dict):
    """
    Оновити законопроєкт
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Bill not found")


@router.delete("/{billId}")
async def delete_bill(billId: str):
    """
    Видалити законопроєкт
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Bill not found")


@router.get("/{billId}/status")
async def get_bill_status(billId: str):
    """
    Перевірити статус завантаження законопроєкту
    """
    # TODO: Implement
    return {
        "status": "active",
        "progress": 100,
        "message": "Completed"
    }
