"""
Configuration management for Learn Backend
Loads settings from environment variables and .env file
"""
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent  # Go up to project root
load_dotenv(PROJECT_ROOT / '.env')
load_dotenv(BASE_DIR / '.env')  # Also try backend dir
load_dotenv('.env')  # Also try current dir


class Config:
    """Base configuration"""
    
    # Application
    APP_NAME = "Learn Backend"
    VERSION = "1.0.0"
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', 'learn-documents-prod')
    
    # Google AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
    
    # Firebase
    FIREBASE_CREDENTIALS = os.getenv('FIREBASE_CREDENTIALS')
    FIRESTORE_DATABASE = os.getenv('FIRESTORE_DATABASE', '(default)')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_WEBHOOK_URL = os.getenv('TELEGRAM_WEBHOOK_URL')
    TELEGRAM_SECRET_TOKEN = os.getenv('TELEGRAM_SECRET_TOKEN')
    
    # API Settings
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    API_WORKERS = int(os.getenv('API_WORKERS', '4'))
    
    # Parliament Website
    RADA_SEARCH_URL = 'https://itd.rada.gov.ua/billinfo/Bills/searchResults'
    RADA_DOWNLOAD_URL = 'https://itd.rada.gov.ua/billinfo/api/file/download/'
    
    # Rate Limiting
    DOWNLOAD_DELAY = float(os.getenv('DOWNLOAD_DELAY', '0.5'))
    API_DELAY = float(os.getenv('API_DELAY', '2.0'))
    MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = 'json'  # or 'text'
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        # Only validate if not in test/dev mode
        if cls.DEBUG:
            return  # Skip validation in debug mode
        
        required = [
            'GEMINI_API_KEY',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_WEBHOOK_URL',
            'TELEGRAM_SECRET_TOKEN',
            'GOOGLE_CLOUD_PROJECT',
        ]
        missing = [key for key in required if not getattr(cls, key)]
        if missing:
            raise ValueError(f"Missing required config: {', '.join(missing)}")


config = Config()
