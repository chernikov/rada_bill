"""
Documents API endpoints
"""
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/bills/{billId}/documents")
async def list_bill_documents(billId: str):
    """
    Список документів законопроєкту
    """
    # TODO: Implement
    return {"documents": []}


@router.post("/bills/{billId}/documents")
async def upload_document(billId: str):
    """
    Завантажити документ до законопроєкту
    """
    # TODO: Implement
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/{documentId}/download")
async def download_document(documentId: str, format: str = "original"):
    """
    Скачати документ
    """
    # TODO: Implement with GCS signed URL
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{documentId}/url")
async def get_document_url(documentId: str, format: str = "original", expiresIn: int = 3600):
    """
    Отримати signed URL для документа
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Document not found")


@router.get("/{documentId}/preview")
async def preview_document(documentId: str):
    """
    Перегляд документа (Markdown версія)
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Document not found")


@router.delete("/{documentId}")
async def delete_document(documentId: str):
    """
    Видалити документ
    """
    # TODO: Implement
    raise HTTPException(status_code=404, detail="Document not found")
