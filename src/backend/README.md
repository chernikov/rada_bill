# Learn Backend

AI-powered Ukrainian Parliament Bill Analysis System

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Cloud Project
- Firebase Project
- Telegram Bot Token
- Redis (for Celery)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd rada_bill
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. Run the application:
```bash
python -m backend.api.main
```

The API will be available at: http://localhost:8000

### Docker

```bash
docker build -t learn-backend .
docker run -p 8000:8000 --env-file .env learn-backend
```

## 📁 Project Structure

```
backend/
├── api/              # FastAPI routes and middleware
├── services/         # Business logic services
├── workers/          # Celery background workers
├── telegram_bot/     # Telegram bot handlers
├── models/           # Pydantic models
├── utils/            # Utilities
├── config.py         # Configuration
└── requirements.txt  # Dependencies
```

## 🔧 Configuration

See `.env.example` for all configuration options.

Required:
- `GOOGLE_API_KEY` - Google Gemini API key
- `TELEGRAM_BOT_TOKEN` - Telegram bot token
- `GOOGLE_CLOUD_PROJECT` - GCP project ID

## 📚 API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🧪 Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black backend/
flake8 backend/
```

## 📄 License

MIT
