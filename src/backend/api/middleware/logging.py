"""
Logging middleware for request/response tracking
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import json


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        print(f"→ {request.method} {request.url.path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response
        duration = time.time() - start_time
        print(f"← {response.status_code} ({duration:.3f}s)")
        
        return response
