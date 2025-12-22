"""
Authentication middleware
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Authentication middleware
    TODO: Implement Firebase Auth verification
    """
    
    async def dispatch(self, request: Request, call_next):
        # TODO: Verify JWT token
        # TODO: Check user permissions
        
        response = await call_next(request)
        return response
