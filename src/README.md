# Ukrainian Parliament Bills Analysis System

FastAPI backend with Telegram bot for analyzing Ukrainian Parliament bills using AI.

## Features

- 🔍 **Bill Scraping**: Automatic download of bill cards from Parliament website
- 📄 **Document Processing**: PDF/DOCX to Markdown conversion
- 🤖 **AI Analysis**: Deep analysis using Google Gemini AI
- 💾 **Cloud Storage**: Google Cloud Storage integration
- 📱 **Telegram Bot**: User-friendly interface via Telegram
- 🗄️ **Firestore**: Bill and analysis data storage

## Quick Start

### 1. Install Dependencies

```bash
cd src/backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` file in project root:

```env
# Google AI
GEMINI_API_KEY=your-gemini-api-key

# Telegram
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_WEBHOOK_URL=  # Leave empty for polling mode

# API
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Run Telegram Bot

```bash
python run_bot.py
```

## Telegram Bot Commands

- `/start` - Welcome message
- `/help` - Detailed help
- `/bill <number>` - Analyze bill (e.g., `/bill 12414`)
- `/search <query>` - Search bills
- `/status` - System status

Or simply type bill number: `12414`

## Development

Run FastAPI server:
```bash
python run_api.py
```

API docs: http://localhost:8000/docs

## License

MIT
