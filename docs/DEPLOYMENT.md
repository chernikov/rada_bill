# Deployment Guide - Bills Analyzer

## Completed Steps

✅ **Firestore Database Created**
- Location: europe-west3
- Type: firestore-native
- Database: (default)
- Free tier enabled

✅ **Artifact Registry Repository Created**
- Name: cloud-run-source-deploy
- Location: europe-west3
- Format: docker

✅ **Docker Image Built and Pushed**
- Repository: europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:latest
- Base Image: python:3.11-slim
- Size: ~620MB

✅ **Cloud Run Service Created**
- Service Name: bills-analyzer
- Region: europe-west3
- URL: https://bills-analyzer-825745139734.europe-west3.run.app
- Status: Deployed (with errors - needs configuration)

✅ **Request Examples Created**
- requests/README.md - Full API documentation
- requests/api.http - VS Code REST Client format
- requests/examples.py - Python examples
- requests/powershell_examples.ps1 - PowerShell examples
- requests/curl_examples.sh - Bash/cURL examples

## Current Issue

The service is deployed but returning 404 errors. This is likely due to:
1. Missing environment variables (GEMINI_API_KEY, TELEGRAM_BOT_TOKEN)
2. Application startup issues

## Next Steps to Complete Deployment

### 1. Set Environment Variables via Secret Manager

```powershell
# Create secrets
gcloud secrets create GEMINI_API_KEY --data-file=- --replication-policy=automatic
# Enter your API key and press Ctrl+Z, then Enter on Windows

gcloud secrets create TELEGRAM_BOT_TOKEN --data-file=- --replication-policy=automatic
# Enter your bot token and press Ctrl+Z, then Enter on Windows

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding GEMINI_API_KEY `
    --member="serviceAccount:825745139734-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding TELEGRAM_BOT_TOKEN `
    --member="serviceAccount:825745139734-compute@developer.gserviceaccount.com" `
    --role="roles/secretmanager.secretAccessor"

# Update Cloud Run service to use secrets
gcloud run services update bills-analyzer `
    --region europe-west3 `
    --set-env-vars="DEBUG=false,GCP_PROJECT_ID=gen-lang-client-0955618410,FIRESTORE_DATABASE=(default)" `
    --update-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest"
```

### 2. Or Set Environment Variables Directly (Less Secure)

```powershell
gcloud run services update bills-analyzer `
    --region europe-west3 `
    --set-env-vars="DEBUG=false,GCP_PROJECT_ID=gen-lang-client-0955618410,FIRESTORE_DATABASE=(default),GEMINI_API_KEY=your-key-here,TELEGRAM_BOT_TOKEN=your-token-here"
```

### 3. Increase Memory and CPU (if needed)

```powershell
gcloud run services update bills-analyzer `
    --region europe-west3 `
    --memory 1Gi `
    --cpu 2
```

### 4. Check Logs

```powershell
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bills-analyzer" --limit 50

# Or in Cloud Console
# https://console.cloud.google.com/logs/query?project=gen-lang-client-0955618410
```

### 5. Test the Service

```powershell
# Health check
curl https://bills-analyzer-825745139734.europe-west3.run.app/health

# API docs
curl https://bills-analyzer-825745139734.europe-west3.run.app/docs

# Search bills
curl "https://bills-analyzer-825745139734.europe-west3.run.app/api/v1/bills?page=1&per_page=5"
```

## GCP Project Information

- **Project ID**: gen-lang-client-0955618410
- **Project Name**: Learn
- **Project Number**: 825745139734
- **Region**: europe-west3 (Frankfurt, Germany)

## Enabled APIs

- ✅ Cloud Run API
- ✅ Cloud Build API
- ✅ Artifact Registry API
- ✅ Firestore API

## Resources Created

1. **Firestore Database**: (default) in europe-west3
2. **Artifact Registry Repository**: cloud-run-source-deploy
3. **Docker Image**: bills-analyzer:latest
4. **Cloud Run Service**: bills-analyzer

## Service URL

🌐 **https://bills-analyzer-825745139734.europe-west3.run.app**

## Cost Estimation

- **Cloud Run**: Free tier includes 2M requests/month, 360K GB-seconds/month
- **Firestore**: Free tier includes 50K reads/day, 20K writes/day, 1GB storage
- **Artifact Registry**: Free 0.5GB storage/month
- **Expected Monthly Cost**: $0-5 for light usage within free tiers

## Troubleshooting

### Container failed to start

1. Check Dockerfile CMD is correct
2. Verify all dependencies in requirements.txt
3. Ensure PYTHONPATH is set correctly
4. Check application logs

### 404 Errors

1. Verify environment variables are set
2. Check application routing in backend/api/main.py
3. Verify health endpoint exists at /health

### Firestore Connection Issues

1. Verify Firestore API is enabled
2. Check service account permissions
3. Verify database exists: `gcloud firestore databases list`

## Local Testing

To test the Docker image locally:

```powershell
# Run container
docker run -p 8080:8080 `
    -e DEBUG=true `
    -e GCP_PROJECT_ID=gen-lang-client-0955618410 `
    -e FIRESTORE_DATABASE="(default)" `
    -e GEMINI_API_KEY=your-key `
    -e TELEGRAM_BOT_TOKEN=your-token `
    europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:latest

# Test
curl http://localhost:8080/health
```

## API Documentation

Once the service is running, visit:
- **Swagger UI**: https://bills-analyzer-825745139734.europe-west3.run.app/docs
- **ReDoc**: https://bills-analyzer-825745139734.europe-west3.run.app/redoc

## Telegram Bot Webhook Setup

### Quick Setup:

1. **Get your Bot Token** from [@BotFather](https://t.me/BotFather)
2. **Generate Secret Token**:
   ```powershell
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
   ```
3. **Set Environment Variables**:
   ```powershell
   gcloud run services update bills-analyzer `
       --region europe-west3 `
       --set-env-vars="TELEGRAM_BOT_TOKEN=your_token,TELEGRAM_WEBHOOK_URL=https://bills-analyzer-825745139734.europe-west3.run.app/api/telegram/webhook,TELEGRAM_SECRET_TOKEN=your_secret"
   ```
4. **Webhook auto-configures on service start** or call:
   ```bash
   curl -X POST https://bills-analyzer-825745139734.europe-west3.run.app/api/telegram/setup-webhook
   ```

### Test Telegram Bot:

1. Open your bot in Telegram
2. Send `/start`
3. Try `/bill 12414`

### Verify Webhook:

```bash
curl https://bills-analyzer-825745139734.europe-west3.run.app/api/telegram/webhook-info
```

## Next Development Steps

1. ✅ Complete environment variable configuration
2. ✅ Set up Telegram bot webhook
3. ⏳ Verify all API endpoints working
4. ⏳ Configure GCS bucket for document storage
5. ⏳ Set up Redis for Celery (optional)
6. ⏳ Configure monitoring and alerts
7. ⏳ Set up CI/CD pipeline

## Support

For issues or questions, check:
- Cloud Run Logs: https://console.cloud.google.com/run/detail/europe-west3/bills-analyzer/logs
- Cloud Console: https://console.cloud.google.com/home/dashboard?project=gen-lang-client-0955618410
- Firestore Console: https://console.cloud.google.com/firestore/databases?project=gen-lang-client-0955618410
