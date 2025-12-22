"""
Firestore database service wrapper
"""
from google.cloud import firestore
from typing import Optional, Dict, List, Any
from datetime import datetime

from backend.config import config


class FirestoreService:
    """
    Service for Firebase Firestore database operations
    """
    
    def __init__(self):
        # Use ADC (Application Default Credentials)
        self.db = firestore.Client(
            database=config.FIRESTORE_DATABASE or "(default)"
        )
    
    # Bills Collection
    
    async def create_bill(self, bill_data: Dict) -> str:
        """Create a new bill document"""
        bill_ref = self.db.collection('bills').document()
        
        bill_data.update({
            'id': bill_ref.id,
            'createdAt': firestore.SERVER_TIMESTAMP,
            'updatedAt': firestore.SERVER_TIMESTAMP,
        })
        
        bill_ref.set(bill_data)
        
        return bill_ref.id
    
    async def get_bill(self, bill_id: str) -> Optional[Dict]:
        """Get bill by ID"""
        doc = self.db.collection('bills').document(bill_id).get()
        
        if doc.exists:
            return doc.to_dict()
        
        return None
    
    async def get_bill_by_number(self, bill_number: str) -> Optional[Dict]:
        """Get bill by bill number"""
        docs = self.db.collection('bills').where('billNumber', '==', bill_number).limit(1).stream()
        
        for doc in docs:
            return doc.to_dict()
        
        return None
    
    async def update_bill(self, bill_id: str, updates: Dict) -> bool:
        """Update bill document"""
        updates['updatedAt'] = firestore.SERVER_TIMESTAMP
        
        self.db.collection('bills').document(bill_id).update(updates)
        
        return True
    
    async def list_bills(
        self,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """List bills with filters"""
        query = self.db.collection('bills')
        
        if user_id:
            query = query.where('userId', '==', user_id)
        
        if status:
            query = query.where('status', '==', status)
        
        query = query.order_by('createdAt', direction=firestore.Query.DESCENDING)
        query = query.limit(limit).offset(offset)
        
        docs = query.stream()
        
        return [doc.to_dict() for doc in docs]
    
    # Documents Collection
    
    async def create_document(self, document_data: Dict) -> str:
        """Create a new document"""
        doc_ref = self.db.collection('documents').document()
        
        document_data.update({
            'id': doc_ref.id,
            'uploadedAt': firestore.SERVER_TIMESTAMP,
        })
        
        doc_ref.set(document_data)
        
        return doc_ref.id
    
    async def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document by ID"""
        doc = self.db.collection('documents').document(document_id).get()
        
        if doc.exists:
            return doc.to_dict()
        
        return None
    
    # Analyses Collection
    
    async def create_analysis(self, analysis_data: Dict) -> str:
        """Create a new analysis"""
        analysis_ref = self.db.collection('analyses').document()
        
        analysis_data.update({
            'id': analysis_ref.id,
            'createdAt': firestore.SERVER_TIMESTAMP,
        })
        
        analysis_ref.set(analysis_data)
        
        return analysis_ref.id
    
    async def get_analysis(self, analysis_id: str) -> Optional[Dict]:
        """Get analysis by ID"""
        doc = self.db.collection('analyses').document(analysis_id).get()
        
        if doc.exists:
            return doc.to_dict()
        
        return None
    
    # Telegram Users Collection
    
    async def create_telegram_user(self, user_data: Dict) -> str:
        """Create or update Telegram user"""
        chat_id = str(user_data.get('chatId'))
        user_ref = self.db.collection('telegramUsers').document(chat_id)
        
        user_data['lastInteraction'] = firestore.SERVER_TIMESTAMP
        
        user_ref.set(user_data, merge=True)
        
        return chat_id
    
    async def get_telegram_user(self, chat_id: int) -> Optional[Dict]:
        """Get Telegram user by chat ID"""
        doc = self.db.collection('telegramUsers').document(str(chat_id)).get()
        
        if doc.exists:
            return doc.to_dict()
        
        return None
    
    async def log_user_request(self, user_id: int, request_data: Dict) -> str:
        """Log user request to Firestore"""
        request_ref = self.db.collection('telegramUsers').document(str(user_id)).collection('requests').document()
        
        request_data.update({
            'id': request_ref.id,
            'timestamp': firestore.SERVER_TIMESTAMP,
            'userId': user_id
        })
        
        request_ref.set(request_data)
        
        # Update user stats
        user_ref = self.db.collection('telegramUsers').document(str(user_id))
        user_ref.set({
            'lastRequestAt': firestore.SERVER_TIMESTAMP,
            'totalRequests': firestore.Increment(1)
        }, merge=True)
        
        return request_ref.id
