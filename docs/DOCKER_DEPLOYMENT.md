# Docker Deployment Guide

## Швидкий старт

### Windows (PowerShell)
```powershell
# Локально
.\scripts\deploy.ps1 local

# Docker Hub
.\scripts\deploy.ps1 docker-hub

# Google Cloud Run
.\scripts\deploy.ps1 cloud-run -WithSecrets

# Повний реліз
.\scripts\deploy.ps1 release
```

### Linux/Mac (Bash)
```bash
chmod +x scripts/deploy.sh

# Локально
./scripts/deploy.sh local

# Docker Hub
./scripts/deploy.sh docker-hub

# Google Cloud Run
WITH_SECRETS=true ./scripts/deploy.sh cloud-run

# Повний реліз
./scripts/deploy.sh release
```

## Детальна інструкція

### 1. Локальний деплой

#### Docker Run
```powershell
# Збудувати image
docker build -t bills-analyzer:latest .

# Запустити контейнер
docker run -d `
    --name bills-analyzer `
    -p 8080:8080 `
    --env-file .env `
    bills-analyzer:latest

# Перевірити логи
docker logs -f bills-analyzer

# Зупинити
docker stop bills-analyzer
docker rm bills-analyzer
```

#### Docker Compose
```powershell
# Запустити
docker-compose up -d

# Логи
docker-compose logs -f

# Зупинити
docker-compose down
```

### 2. Docker Hub

#### Налаштування
```powershell
# Змінити в Makefile або deploy.ps1
$DOCKER_USERNAME = "ваш-username"
```

#### Деплой
```powershell
# Увійти
docker login

# Збудувати та завантажити
docker build -t bills-analyzer:latest .
docker tag bills-analyzer:latest yourusername/bills-analyzer:latest
docker tag bills-analyzer:latest yourusername/bills-analyzer:1.0.0
docker push yourusername/bills-analyzer:latest
docker push yourusername/bills-analyzer:1.0.0
```

#### Запустити з Docker Hub
```powershell
# На будь-якому сервері
docker pull yourusername/bills-analyzer:latest
docker run -d `
    --name bills-analyzer `
    -p 8080:8080 `
    -e GEMINI_API_KEY="your-key" `
    -e TELEGRAM_BOT_TOKEN="your-token" `
    yourusername/bills-analyzer:latest
```

### 3. Google Container Registry

#### Налаштування
```powershell
# Увійти в GCP
gcloud auth login
gcloud config set project gen-lang-client-0955618410

# Налаштувати Docker для GCR
gcloud auth configure-docker europe-west3-docker.pkg.dev

# Створити репозиторій (якщо не існує)
gcloud artifacts repositories create cloud-run-source-deploy `
    --repository-format=docker `
    --location=europe-west3 `
    --description="Bills Analyzer Docker repository"
```

#### Деплой
```powershell
# Збудувати та завантажити
$IMAGE = "europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer"

docker build -t "${IMAGE}:latest" -t "${IMAGE}:1.0.0" .
docker push "${IMAGE}:latest"
docker push "${IMAGE}:1.0.0"
```

### 4. Google Cloud Run

#### Налаштування секретів
```powershell
# Створити секрети
echo "your-gemini-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo "your-bot-token" | gcloud secrets create TELEGRAM_BOT_TOKEN --data-file=-

# Надати доступ Cloud Run
$SERVICE_ACCOUNT = "825745139734-compute@developer.gserviceaccount.com"

gcloud secrets add-iam-policy-binding GEMINI_API_KEY `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding TELEGRAM_BOT_TOKEN `
    --member="serviceAccount:$SERVICE_ACCOUNT" `
    --role="roles/secretmanager.secretAccessor"
```

#### Деплой
```powershell
# Базовий деплой
gcloud run deploy bills-analyzer `
    --image europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:latest `
    --platform managed `
    --region europe-west3 `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 2 `
    --set-env-vars "DEBUG=false,GCP_PROJECT_ID=gen-lang-client-0955618410,FIRESTORE_DATABASE=(default)"

# З секретами
gcloud run deploy bills-analyzer `
    --image europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:latest `
    --platform managed `
    --region europe-west3 `
    --allow-unauthenticated `
    --memory 1Gi `
    --cpu 2 `
    --update-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest"

# Отримати URL
gcloud run services describe bills-analyzer `
    --region europe-west3 `
    --format="value(status.url)"
```

## Workflow для релізів

### Автоматичний реліз
```powershell
# 1. Інкремент версії
python -c "from src.backend.version import increment_build; print(increment_build())"

# 2. Збудувати та завантажити в GCR
make push-gcr

# 3. Розгорнути на Cloud Run
make deploy-cloudrun

# АБО все разом
make release
# або
.\deploy.ps1 release
```

### Ручний workflow
```powershell
# 1. Оновити версію в src/backend/version.py
# VERSION = "1.1.0"

# 2. Збудувати локально та протестувати
docker build -t bills-analyzer:1.1.0 .
docker run -d --name test -p 8080:8080 --env-file .env bills-analyzer:1.1.0
# Тестування...
docker stop test && docker rm test

# 3. Завантажити в GCR
docker tag bills-analyzer:1.1.0 europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:1.1.0
docker push europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:1.1.0

# 4. Розгорнути
gcloud run deploy bills-analyzer --image europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:1.1.0 --region europe-west3
```

## Моніторинг та логи

### Локальний Docker
```powershell
# Логи
docker logs -f bills-analyzer

# Статус
docker ps
docker inspect bills-analyzer

# Зайти всередину контейнера
docker exec -it bills-analyzer /bin/bash
```

### Cloud Run
```powershell
# Логи
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=bills-analyzer" --limit 50

# Метрики
gcloud run services describe bills-analyzer --region europe-west3

# Логи в реальному часі
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=bills-analyzer"
```

## Troubleshooting

### Контейнер не запускається
```powershell
# Перевірити логи
docker logs bills-analyzer

# Перевірити healthcheck
docker inspect bills-analyzer | grep -A 10 Health

# Зайти всередину та діагностувати
docker run -it --entrypoint /bin/bash bills-analyzer:latest
```

### Cloud Run помилки
```powershell
# Детальні логи
gcloud logging read "resource.type=cloud_run_revision" --limit 100 --format json

# Перевірити змінні середовища
gcloud run services describe bills-analyzer --region europe-west3 --format yaml

# Перевірити доступ до секретів
gcloud secrets versions access latest --secret="GEMINI_API_KEY"
```

### Image надто великий
```powershell
# Аналіз розміру
docker images bills-analyzer
docker history bills-analyzer:latest

# Оптимізація: використати multi-stage build в Dockerfile
# Очистити build cache
docker builder prune
```

## Додаткові команди

### Очищення
```powershell
# Локальні images
docker rmi bills-analyzer:latest
docker system prune -a

# GCR images
gcloud artifacts docker images delete europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer:old-version

# Cloud Run revisions
gcloud run revisions delete old-revision --region europe-west3
```

### Версіонування
```powershell
# Переглянути поточну версію
python -m backend.version

# Інкремент
python -c "from src.backend.version import increment_build; increment_build()"

# Показати всі версії в GCR
gcloud artifacts docker images list europe-west3-docker.pkg.dev/gen-lang-client-0955618410/cloud-run-source-deploy/bills-analyzer
```

## Корисні посилання

- [Docker Documentation](https://docs.docker.com/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
