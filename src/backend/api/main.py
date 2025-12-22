"""
Main FastAPI application entry point
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path

from backend.config import config
from backend.api.routes import bills, documents, analyses, telegram, admin
from backend.api.middleware.logging import LoggingMiddleware
from backend.api.middleware.error_handler import ErrorHandlerMiddleware

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    config.validate()
    print(f"🚀 Starting {config.APP_NAME} v{config.VERSION}")
    print(f"🔧 Environment: {'Development' if config.DEBUG else 'Production'}")
    
    # Initialize and start Telegram bot
    if config.TELEGRAM_BOT_TOKEN:
        try:
            from backend.telegram_bot.bot import bot
            
            # Debug: print all telegram config to check for newlines
            print(f"🔍 Debug: TELEGRAM_BOT_TOKEN = '{config.TELEGRAM_BOT_TOKEN[:20]}...'")
            print(f"🔍 Debug: TELEGRAM_BOT_TOKEN length = {len(config.TELEGRAM_BOT_TOKEN)}")
            print(f"🔍 Debug: TELEGRAM_BOT_TOKEN repr = {repr(config.TELEGRAM_BOT_TOKEN)}")
            print(f"🔍 Debug: TELEGRAM_WEBHOOK_URL = '{config.TELEGRAM_WEBHOOK_URL}'")
            print(f"🔍 Debug: TELEGRAM_WEBHOOK_URL length = {len(config.TELEGRAM_WEBHOOK_URL) if config.TELEGRAM_WEBHOOK_URL else 0}")
            print(f"🔍 Debug: TELEGRAM_WEBHOOK_URL repr = {repr(config.TELEGRAM_WEBHOOK_URL)}")
            print(f"🔍 Debug: TELEGRAM_SECRET_TOKEN length = {len(config.TELEGRAM_SECRET_TOKEN) if config.TELEGRAM_SECRET_TOKEN else 0}")
            print(f"🔍 Debug: TELEGRAM_SECRET_TOKEN repr = {repr(config.TELEGRAM_SECRET_TOKEN)}")
            
            bot.setup()
            await bot.start()
            print(f"🤖 Telegram bot initialized")
            
            # Auto-setup webhook if URL is configured
            if config.TELEGRAM_WEBHOOK_URL:
                try:
                    success = await bot.set_webhook(webhook_url=config.TELEGRAM_WEBHOOK_URL)
                    if success:
                        print(f"✅ Webhook налаштовано: {config.TELEGRAM_WEBHOOK_URL}")
                    else:
                        print(f"⚠️ Не вдалося налаштувати webhook")
                except Exception as e:
                    print(f"⚠️ Webhook setup error: {e}")
        except Exception as e:
            print(f"⚠️ Telegram bot initialization failed: {e}")
            print("⚠️ Continuing without Telegram bot...")
    else:
        print("⚠️ TELEGRAM_BOT_TOKEN not configured - bot disabled")
    
    yield
    
    # Shutdown
    print("👋 Shutting down gracefully...")
    
    # Stop Telegram bot
    if config.TELEGRAM_BOT_TOKEN:
        try:
            from backend.telegram_bot.bot import bot
            await bot.stop()
            print("🤖 Telegram bot stopped")
        except Exception as e:
            print(f"⚠️ Error stopping bot: {e}")


# Create FastAPI app
app = FastAPI(
    title="Learn Backend API",
    description="AI-powered Ukrainian Parliament Bill Analysis System",
    version=config.VERSION,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlerMiddleware)

# Include routers
app.include_router(bills.router, prefix="/api/bills", tags=["Bills"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(analyses.router, prefix="/api/analyses", tags=["Analyses"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["Telegram"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Welcome page"""
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "version": config.VERSION
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": config.VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.api.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=config.DEBUG,
        workers=1 if config.DEBUG else config.API_WORKERS,
    )
