# Bills Analyzer - System Architecture

## Executive Summary

**Bills Analyzer** is a cloud-native document processing and AI analysis system for Ukrainian Parliament bills. It orchestrates web scraping, document conversion, AI-powered analysis, and multi-channel delivery (REST API + Telegram Bot).

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    BILLS ANALYZER SYSTEM                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌────────────────┐      ┌──────────────┐      ┌─────────────┐     │
│  │   Web Scraper  │ ───> │  Converter   │ ───> │ AI Analyzer │     │
│  │  (Parliament)  │      │ (DOCX/PDF→MD)│      │   (Gemini)  │     │
│  └────────────────┘      └──────────────┘      └─────────────┘     │
│          │                       │                      │            │
│          ▼                       ▼                      ▼            │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              Cloud Storage (GCS + Firestore)               │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                   │                                  │
│                                   ▼                                  │
│         ┌──────────────────────────────────────┐                    │
│         │  API Layer (FastAPI + Telegram Bot)  │                    │
│         └──────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Core Process Flows

### 1️⃣ BILL SCRAPING FLOW

```
INPUT: Bill ID / ID Range / Search Query
  │
  ├─> HTTP Request → Parliament Website (itd.rada.gov.ua)
  ├─> Parse HTML Search Results
  ├─> Extract Bill Metadata (number, title, author, files)
  ├─> Apply Rate Limiting (0.5-2s delays)
  ├─> Download HTML Cards
  │
OUTPUT: HTML files → GCS (data/TTTT-TTTT/HHH-HHH/NNNN/NNNN.html)
        Metadata → Firestore (bills collection)
```

**Entry Points:**
- `src/backend/services/scraper.py` - Scrapes search result pages
- `src/backend/services/document_downloader.py` - Downloads bill documents

**Folder Structure:**
```
data/
  0000-0999/
    000-099/
      0010/
        0010.html       # Bill card
```

---

### 2️⃣ DOCUMENT DOWNLOAD FLOW

```
INPUT: HTML Bill Card
  │
  ├─> Parse Card HTML
  ├─> Extract File IDs (x-file-id headers)
  ├─> Identify File Types (.pdf, .docx)
  ├─> Download Files via API (with custom headers)
  ├─> Validate File Integrity
  ├─> Store in Hierarchical Structure
  │
OUTPUT: Documents → GCS (data/.../NNNN/*.pdf, *.docx)
```

**Key Service:** `DocumentDownloader` in `src/backend/services/document_downloader.py`

**API Endpoint:**
```
https://itd.rada.gov.ua/billinfo/api/file/download/
```

---

### 3️⃣ DOCUMENT CONVERSION FLOW

```
INPUT: PDF/DOCX Files
  │
  ├─> Detect File Type
  │
  ├─> PDF Branch:
  │   ├─> pdfplumber → Extract Text with Layout
  │   ├─> Apply Markdown Formatting
  │   └─> Clean Whitespace
  │
  ├─> DOCX Branch:
  │   ├─> python-docx → Parse Document Structure
  │   ├─> Map Styles to Markdown Headers
  │   ├─> Process Tables/Lists
  │   └─> Format Paragraphs
  │
  ├─> Save as .md File (same directory)
  │
OUTPUT: Markdown Files → GCS (data/.../NNNN/*.md)
```

**Converters:**
- `src/backend/services/converters/pdf_converter.py`
- `src/backend/services/converters/docx_converter.py`

**Style Mapping:**
```python
Heading 1 → #
Heading 2 → ##
Heading 3 → ###
Lists → -, 1.
Tables → Markdown tables
```

---

### 4️⃣ AI ANALYSIS FLOW

```
INPUT: Markdown Document Text
  │
  ├─> Text Truncation (30,000 chars max)
  ├─> Build Analysis Prompt (structured template)
  │
  ├─> Call Gemini API:
  │   ├─> Model: gemini-2.5-flash
  │   ├─> Prompt: Deep analysis (5-point structure)
  │   └─> Response: Analysis text
  │
  ├─> Generate Filename:
  │   ├─> Extract key concepts from analysis
  │   ├─> Transliterate to uppercase
  │   └─> Format: VISNOVOK_CONCEPT.txt
  │
  ├─> Save Analysis → GCS (same directory as source)
  ├─> Store Metadata → Firestore (analyses collection)
  │
  ├─> Optional: Send to Telegram
  │   ├─> Split into 4096-char chunks
  │   └─> POST to Telegram Bot API
  │
OUTPUT: Analysis Files → GCS (VISNOVOK_*.txt)
        Metadata → Firestore
        Notification → Telegram (optional)
```

**Analysis Structure:**
1. **Суть** - Bill purpose and goal
2. **Автор та Репутація** - Author's reputation
3. **Корупційні ризики** - Corruption risks
4. **Вплив на Україну** - Country impact assessment
5. **Плюси та Мінуси** - Pros and Cons

**Key Service:** `AIService` in `src/backend/services/ai_service.py`

**Key Functions:**
- `analyze_document()` - Main analysis function
- `analyze_bill()` - Wrapper for bills
- `_build_analysis_prompt()` - Creates structured prompt
- `_build_naming_prompt()` - Generates filename

---

### 5️⃣ TELEGRAM BOT FLOW

```
INPUT: Telegram Message/Command
  │
  ├─> Parse Command:
  │   ├─> /start → Welcome message
  │   ├─> /bill NNNN → Analyze specific bill
  │   ├─> /search KEYWORD → Search bills
  │   ├─> /status → System status
  │   └─> /help → Help text
  │
  ├─> Validate Bill Number (4 digits)
  ├─> Check Firestore for Existing Analysis
  │
  ├─> If Not Exists:
  │   ├─> Trigger Scraping Pipeline
  │   ├─> Download Documents
  │   ├─> Convert to Markdown
  │   ├─> Run AI Analysis
  │   └─> Store Results
  │
  ├─> Fetch Analysis from Firestore
  ├─> Format Response (Markdown)
  ├─> Handle Long Messages (split/pagination)
  │
OUTPUT: Telegram Reply with Analysis
```

**Bot Implementation:** `src/backend/telegram_bot/bot.py`

**Webhook URL:**
```
https://bills-analyzer-825745139734.europe-west3.run.app/api/telegram/webhook
```

---

### 6️⃣ REST API FLOW

```
INPUT: HTTP Request to /api/*
  │
  ├─> Route to Controller:
  │   ├─> GET /api/bills → List bills
  │   ├─> GET /api/bills/{id} → Get bill details
  │   ├─> POST /api/bills → Create bill analysis job
  │   ├─> GET /api/documents/{id} → Get document
  │   └─> GET /api/telegram/webhook → Telegram webhook
  │
  ├─> Validate Request Parameters
  ├─> Query Firestore Database
  ├─> Optional: Trigger Background Job
  ├─> Fetch Data from GCS (if needed)
  ├─> Format JSON Response
  │
OUTPUT: JSON Response with Data/Status
```

**API Routes:**
- `src/backend/api/routes/bills.py`
- `src/backend/api/routes/documents.py`
- `src/backend/api/routes/telegram.py`
- `src/backend/api/routes/admin.py`

**Documentation:**
- Swagger UI: `/docs`
- ReDoc: `/redoc`

---

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        DATA SOURCES                              │
├─────────────────────────────────────────────────────────────────┤
│  Parliament Website  │  User Input (Telegram/API)  │  .env File │
└──────────┬───────────┴─────────────┬──────────────┴────┬────────┘
           │                         │                    │
           ▼                         ▼                    ▼
    ┌──────────┐            ┌──────────────┐     ┌──────────┐
    │ Scraper  │            │  Bot/API     │     │  Config  │
    │ Service  │            │  Handlers    │     │  Loader  │
    └─────┬────┘            └──────┬───────┘     └────┬─────┘
          │                        │                   │
          └────────────┬───────────┴───────────────────┘
                       ▼
            ┌─────────────────────┐
            │   Business Logic    │
            │  (Services Layer)   │
            └──────────┬──────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌─────────┐  ┌─────────┐  ┌─────────┐
    │   GCS   │  │Firestore│  │ Gemini  │
    │ Storage │  │   DB    │  │   AI    │
    └─────────┘  └─────────┘  └─────────┘
          │            │            │
          └────────────┼────────────┘
                       ▼
            ┌─────────────────────┐
            │   Response Layer    │
            └──────────┬──────────┘
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
    ┌──────────┐ ┌──────────┐ ┌──────────┐
    │Telegram  │ │REST API  │ │  Files   │
    │ Message  │ │ Response │ │  (GCS)   │
    └──────────┘ └──────────┘ └──────────┘
```

---

## Deployment Architecture

### Cloud Run Service

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud Run                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌───────────────────────────────────────────────┐      │
│  │  Container: bills-analyzer:latest             │      │
│  │  Base: python:3.11-slim                       │      │
│  │  Port: 8080                                   │      │
│  │  Memory: 1Gi                                  │      │
│  │  Region: europe-west3                         │      │
│  └───────────────────────────────────────────────┘      │
│                                                           │
│  ┌───────────────────────────────────────────────┐      │
│  │  Environment Variables:                       │      │
│  │  - GEMINI_API_KEY (Secret Manager)           │      │
│  │  - TELEGRAM_BOT_TOKEN (Secret Manager)       │      │
│  │  - GCP_PROJECT_ID                            │      │
│  │  - FIRESTORE_DATABASE                        │      │
│  │  - GCS_BUCKET_NAME                           │      │
│  └───────────────────────────────────────────────┘      │
│                                                           │
│  ┌───────────────────────────────────────────────┐      │
│  │  Exposed Endpoints:                           │      │
│  │  - /health                                    │      │
│  │  - /api/*                                     │      │
│  │  - /api/telegram/webhook                      │      │
│  │  - /docs (Swagger)                            │      │
│  └───────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
```

**Service URL:**
```
https://bills-analyzer-825745139734.europe-west3.run.app
```

### Docker Image Build Process

```
INPUT: Source Code
  │
  ├─> Copy requirements.txt
  ├─> Install Python Dependencies
  ├─> Copy src/ Directory
  ├─> Copy .env.production → .env
  ├─> Set Environment Variables:
  │   ├─> PYTHONUNBUFFERED=1
  │   ├─> PORT=8080
  │   └─> PYTHONPATH=/app/src
  ├─> Expose Port 8080
  │
OUTPUT: Docker Image → Artifact Registry
        europe-west3-docker.pkg.dev/gen-lang-client-0955618410/
        cloud-run-source-deploy/bills-analyzer:latest
```

**Build Script:** `scripts/deploy.ps1`, `scripts/deploy.sh`

---

## External Dependencies

### ☁️ Cloud Services

| Service | Purpose | Endpoint/Location |
|---------|---------|-------------------|
| **Google Cloud Storage** | Document/analysis file storage | `gs://learn-documents-prod/` |
| **Google Firestore** | Bills/analyses metadata database | `(default)` database, `europe-west3` |
| **Google Cloud Run** | Container hosting | `europe-west3` region |
| **Google Artifact Registry** | Docker image storage | `europe-west3-docker.pkg.dev` |
| **Google Secret Manager** | API keys/tokens storage | Secrets: `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN` |

### 🤖 External APIs

| API | Purpose | Rate Limits |
|-----|---------|-------------|
| **Google Gemini AI** | Document analysis | Model: `gemini-2.5-flash`, 30K chars/request |
| **Telegram Bot API** | User interface | Standard Bot API limits, 4096 chars/message |
| **Parliament Website** | Bill data source | 0.5-2s delays between requests |

**Parliament Endpoints:**
```
https://itd.rada.gov.ua/billinfo/Bills/searchResults
https://itd.rada.gov.ua/billinfo/api/file/download/
```

### 📦 Python Libraries

#### Core Framework
- **FastAPI** - REST API framework
- **uvicorn** - ASGI server
- **python-telegram-bot** - Telegram integration

#### Document Processing
- **pdfplumber** - PDF text extraction
- **python-docx** - DOCX processing
- **PyPDF2** - PDF reading (legacy)
- **markdownify** - HTML→Markdown conversion

#### AI & Cloud
- **google-genai** - Gemini AI client
- **google-cloud-storage** - GCS client
- **google-cloud-firestore** - Firestore client

#### Utilities
- **requests** - HTTP client
- **BeautifulSoup4** - HTML parsing
- **python-dotenv** - Environment variable loading
- **pydantic** - Data validation
- **structlog** - Structured logging

---

## Storage Structure

### Google Cloud Storage (GCS)

```
gs://learn-documents-prod/
├── data/
│   └── TTTT-TTTT/               # Thousands range (0000-0999)
│       └── HHH-HHH/             # Hundreds range (000-099)
│           └── NNNN/            # Bill number (0010)
│               ├── NNNN.html    # Bill card HTML
│               ├── doc1.pdf     # Original documents
│               ├── doc1.md      # Converted markdown
│               ├── doc2.docx
│               └── doc2.md
│
└── archives/
    └── YYYYMMDD_HHMMSS/
        └── firestore_backup.json
```

### Firestore Collections

```
bills/
  {billId}/
    billNumber: "0010"
    billTitle: "Про..."
    status: "downloaded"
    documentsCount: 3
    gcsPath: "gs://..."
    createdAt: timestamp
    updatedAt: timestamp
    
documents/
  {documentId}/
    billNumber: "0010"
    originalName: "document.pdf"
    format: "pdf"
    gcsPath: "gs://..."
    convertedToMd: true
    createdAt: timestamp
    
analyses/
  {analysisId}/
    billNumber: "0010"
    analysisText: "..."
    generatedFilename: "VISNOVOK_*.txt"
    gcsPath: "gs://..."
    model: "gemini-2.5-flash"
    createdAt: timestamp
```

---

## Configuration

### Environment Variables

```env
# Google AI
GEMINI_API_KEY=AIza...

# Telegram
TELEGRAM_BOT_TOKEN=1234567890:ABC...
TELEGRAM_CHAT_ID=123456789
TELEGRAM_WEBHOOK_URL=https://bills-analyzer-....run.app/api/telegram/webhook
TELEGRAM_SECRET_TOKEN=...

# GCP
GOOGLE_CLOUD_PROJECT=gen-lang-client-0955618410
GCS_BUCKET_NAME=learn-documents-prod
FIRESTORE_DATABASE=(default)

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Processing
MAX_TEXT_LENGTH=30000
```

**Config Files:**
- `.env.example` - Template
- `.env.production` - Production config
- `src/backend/config.py` - Config loader

---

## Monitoring & Logging

### Health Check Endpoint

```
GET /health

Response:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "firestore": "connected",
    "gcs": "connected",
    "gemini": "configured"
  }
}
```

### Logging

- **Console Logs**: Structured logging with structlog
- **Application Logs**: All services use logger
- **Cloud Logging**: Automatic on Cloud Run

**View Logs:**
```powershell
# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit 50

# Local logs
python -m backend.api.main  # Console output
```

---

## Security

### Secrets Management

- **Secret Manager**: Stores `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`
- **IAM Permissions**: Service account has `roles/secretmanager.secretAccessor`

### Access Control

- **Cloud Run**: Public access (unauthenticated)
- **Firestore**: IAM-based access control
- **GCS**: Bucket-level permissions
- **Telegram**: Webhook secret token validation

---

## Cost Estimation

| Service | Free Tier | Expected Usage | Cost/Month |
|---------|-----------|----------------|------------|
| **Cloud Run** | 2M requests, 360K GB-seconds | ~10K requests | $0-2 |
| **Firestore** | 50K reads/day, 20K writes/day | ~1K operations/day | $0 |
| **GCS** | 5GB storage | ~2GB | $0 |
| **Artifact Registry** | 0.5GB | <500MB | $0 |
| **Secret Manager** | 6 secrets | 2 secrets | $0 |
| **Gemini API** | Free tier varies | ~100 requests/month | $0-5 |

**Total Estimated Cost:** $0-7/month (within free tiers)

---

## Key Technical Decisions

### Why Gemini AI?
- **Free tier** for moderate usage
- **30K character context** window
- **Fast inference** (2.5-flash model)
- **Structured output** support
- **Ukrainian language** support

### Why Cloud Run?
- **Serverless** (no infrastructure management)
- **Auto-scaling** (0 → N instances)
- **Pay-per-use** pricing
- **Built-in HTTPS** and load balancing

### Why Firestore?
- **NoSQL flexibility** for evolving schema
- **Real-time updates** (optional)
- **Free tier** sufficient for MVP
- **Native GCP integration**

### Why Markdown Conversion?
- **Lightweight** text format
- **AI-friendly** (better than PDF)
- **Human-readable** for debugging
- **Version controllable** with Git

### Why Telegram Bot?
- **Simple user interface**
- **No frontend needed**
- **Real-time notifications**
- **Wide adoption** in Ukraine

---

## Project Structure

```
rada_bill/
├── src/
│   └── backend/
│       ├── api/                    # FastAPI application
│       │   ├── main.py            # App entry point
│       │   ├── middleware/        # Custom middleware
│       │   └── routes/            # API endpoints
│       ├── models/                # Data models
│       ├── services/              # Business logic
│       │   ├── ai_service.py      # Gemini AI integration
│       │   ├── scraper.py         # Bill scraping
│       │   ├── document_downloader.py
│       │   ├── firestore_service.py
│       │   ├── storage_service.py  # GCS operations
│       │   └── converters/        # Document converters
│       ├── telegram_bot/          # Telegram bot
│       │   └── bot.py
│       ├── utils/                 # Utilities
│       ├── config.py              # Configuration
│       └── version.py             # Version info
├── scripts/                       # Deployment scripts
│   ├── deploy.ps1
│   ├── deploy.sh
│   └── backup_firestore.py
├── docs/                          # Documentation
├── architecture/                  # Architecture docs
├── Dockerfile                     # Container definition
├── docker-compose.yml            # Local development
├── requirements.txt              # Python dependencies
└── .env.production               # Production config
```

---

## Development Workflow

### Local Development

```bash
# 1. Setup virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 4. Run locally
cd src
python -m uvicorn backend.api.main:app --reload --port 8000
```

### Testing Telegram Bot

```bash
# Set webhook
curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" \
  -d "url=https://your-domain.run.app/api/telegram/webhook"

# Test commands
/start
/bill 0010
/status
```

### Deployment

```powershell
# Deploy to Cloud Run
.\scripts\deploy.ps1

# Or manually
gcloud run deploy bills-analyzer \
  --source . \
  --region europe-west3 \
  --allow-unauthenticated
```

---

## Troubleshooting

### Common Issues

**1. Telegram webhook not receiving updates**
- Check webhook URL is set correctly
- Verify Cloud Run service is deployed and accessible
- Check secret token matches

**2. AI analysis fails**
- Verify `GEMINI_API_KEY` is set
- Check API quota limits
- Ensure text length < 30K chars

**3. Document download fails**
- Verify Parliament website is accessible
- Check rate limiting delays
- Validate file IDs in HTML cards

**4. Firestore connection issues**
- Verify service account permissions
- Check project ID is correct
- Ensure Firestore is enabled

---

## Future Improvements

### Performance
- ✅ Redis caching for Firestore queries
- ✅ Celery for background job processing
- ✅ Connection pooling for HTTP requests

### Features
- ✅ User authentication (OAuth2)
- ✅ Bill comparison tool
- ✅ Trend analysis dashboard
- ✅ Email notifications
- ✅ PDF report generation
- ✅ Multi-language support

### Infrastructure
- ✅ CI/CD pipeline (GitHub Actions)
- ✅ Automated testing (pytest)
- ✅ Multi-region deployment
- ✅ Disaster recovery plan
- ✅ Monitoring dashboard (Grafana)

---

## Support & Documentation

### Links
- **API Docs**: https://bills-analyzer-825745139734.europe-west3.run.app/docs
- **Cloud Console**: https://console.cloud.google.com/home/dashboard?project=gen-lang-client-0955618410
- **Firestore Console**: https://console.cloud.google.com/firestore/databases

### Additional Documentation
- `docs/DEPLOYMENT.md` - Full deployment guide
- `docs/DOCKER_DEPLOYMENT.md` - Docker workflow
- `src/backend/README.md` - Backend architecture

---

## Version Information

- **Version**: 1.0.0
- **Build Date**: 2025-12-25
- **Source**: `src/backend/version.py`

---

**Last Updated**: 2025-12-25  
**Maintained By**: Development Team  
**Project**: Bills Analyzer  
**Status**: Production Ready ✅
