"""
Global error handler middleware
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
import traceback


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Handle uncaught exceptions globally"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as exc:
            # Log error
            print(f"❌ Unhandled error: {exc}")
            traceback.print_exc()
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": str(exc),
                }
            )
