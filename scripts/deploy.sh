#!/bin/bash
# Bills Analyzer - Bash Deployment Script
# Використання: ./deploy.sh <command>

set -e

# Кольори
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функції виводу
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Змінні
APP_NAME="bills-analyzer"
DOCKER_USERNAME="yourusername"
GCP_PROJECT="gen-lang-client-0955618410"
GCP_REGION="europe-west3"
GCR_REGISTRY="${GCP_REGION}-docker.pkg.dev"
GCR_REPO="cloud-run-source-deploy"
CLOUD_RUN_SERVICE="bills-analyzer"

# Отримати версію
if [ -z "$VERSION" ]; then
    VERSION=$(python -c "from src.backend.version import get_version; v = get_version(); print(v['full_version'])" 2>/dev/null || echo "1.0.0")
fi

DOCKER_IMAGE="${DOCKER_USERNAME}/${APP_NAME}"
GCR_IMAGE="${GCR_REGISTRY}/${GCP_PROJECT}/${GCR_REPO}/${APP_NAME}"

# Функції деплою
deploy_local() {
    info "Локальний деплой..."
    
    # Збірка
    info "Збірка Docker image..."
    docker build -t "${APP_NAME}:latest" -t "${APP_NAME}:${VERSION}" . || error "Помилка збірки"
    success "Image збудовано: ${APP_NAME}:${VERSION}"
    
    # Зупинити старий контейнер
    info "Зупинка старого контейнера..."
    docker stop $APP_NAME 2>/dev/null || true
    docker rm $APP_NAME 2>/dev/null || true
    
    # Запуск
    info "Запуск контейнера..."
    docker run -d \
        --name $APP_NAME \
        -p 8080:8080 \
        --env-file .env \
        "${APP_NAME}:latest" || error "Помилка запуску контейнера"
    
    success "Контейнер запущено: http://localhost:8080"
    info "Логи: docker logs -f $APP_NAME"
    
    # Показати логи
    sleep 2
    docker logs $APP_NAME
}

deploy_docker_hub() {
    info "Публікація в Docker Hub..."
    
    # Вхід
    info "Вхід в Docker Hub..."
    docker login || error "Помилка входу в Docker Hub"
    
    # Збірка
    info "Збірка image..."
    docker build -t "${APP_NAME}:latest" .
    docker tag "${APP_NAME}:latest" "${DOCKER_IMAGE}:latest"
    docker tag "${APP_NAME}:latest" "${DOCKER_IMAGE}:${VERSION}"
    
    # Push
    info "Завантаження в Docker Hub..."
    docker push "${DOCKER_IMAGE}:latest"
    docker push "${DOCKER_IMAGE}:${VERSION}"
    
    success "Image завантажено: ${DOCKER_IMAGE}:${VERSION}"
}

deploy_gcr() {
    info "Публікація в Google Container Registry..."
    
    # Налаштування GCR
    info "Налаштування автентифікації..."
    gcloud auth configure-docker $GCR_REGISTRY || error "Помилка налаштування GCR"
    
    # Збірка
    info "Збірка image для GCR..."
    docker build -t "${GCR_IMAGE}:latest" -t "${GCR_IMAGE}:${VERSION}" . || error "Помилка збірки"
    
    # Push
    info "Завантаження в GCR..."
    docker push "${GCR_IMAGE}:latest"
    docker push "${GCR_IMAGE}:${VERSION}"
    
    success "Image завантажено: ${GCR_IMAGE}:${VERSION}"
}

deploy_cloud_run() {
    info "Розгортання на Cloud Run..."
    
    # Спочатку push в GCR
    deploy_gcr
    
    # Деплой
    info "Розгортання сервісу..."
    
    if [ "$WITH_SECRETS" = "true" ]; then
        info "Додавання секретів..."
        gcloud run deploy $CLOUD_RUN_SERVICE \
            --image "${GCR_IMAGE}:${VERSION}" \
            --platform managed \
            --region $GCP_REGION \
            --allow-unauthenticated \
            --memory 1Gi \
            --cpu 2 \
            --min-instances 0 \
            --max-instances 10 \
            --set-env-vars "DEBUG=false,GCP_PROJECT_ID=$GCP_PROJECT,FIRESTORE_DATABASE=(default)" \
            --update-secrets="GEMINI_API_KEY=GEMINI_API_KEY:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest" \
            || error "Помилка розгортання"
    else
        gcloud run deploy $CLOUD_RUN_SERVICE \
            --image "${GCR_IMAGE}:${VERSION}" \
            --platform managed \
            --region $GCP_REGION \
            --allow-unauthenticated \
            --memory 1Gi \
            --cpu 2 \
            --min-instances 0 \
            --max-instances 10 \
            --set-env-vars "DEBUG=false,GCP_PROJECT_ID=$GCP_PROJECT,FIRESTORE_DATABASE=(default)" \
            || error "Помилка розгортання"
    fi
    
    success "Сервіс розгорнуто на Cloud Run"
    
    # Отримати URL
    info "Отримання URL сервісу..."
    URL=$(gcloud run services describe $CLOUD_RUN_SERVICE \
        --region $GCP_REGION \
        --format="value(status.url)")
    success "URL: $URL"
}

bump_version() {
    info "Інкремент версії..."
    NEW_VERSION=$(python -c "from src.backend.version import increment_build; print(increment_build())")
    success "Нова версія: $NEW_VERSION"
    VERSION=$NEW_VERSION
}

release() {
    info "Повний реліз..."
    
    # Інкремент версії
    bump_version
    
    # Push в GCR
    deploy_gcr
    
    # Deploy на Cloud Run
    deploy_cloud_run
    
    success "Реліз завершено успішно!"
}

show_help() {
    cat << EOF
Bills Analyzer - Bash Deployment Script

Використання:
  ./deploy.sh <command> [options]

Команди:
  local       - Збудувати та запустити локально (Docker)
  docker-hub  - Завантажити в Docker Hub
  gcr         - Завантажити в Google Container Registry
  cloud-run   - Розгорнути на Cloud Run
  release     - Повний реліз (інкремент версії + GCR + Cloud Run)
  help        - Показати цю допомогу

Змінні середовища:
  VERSION         - Вказати версію (за замовчуванням з version.py)
  WITH_SECRETS    - Використати Secret Manager (true/false)

Приклади:
  ./deploy.sh local
  VERSION=1.0.1 ./deploy.sh gcr
  WITH_SECRETS=true ./deploy.sh cloud-run
  ./deploy.sh release

Додаткові команди Docker:
  docker-compose up -d         - Запустити через docker-compose
  docker-compose logs -f       - Показати логи
  docker-compose down          - Зупинити
  
  docker logs -f bills-analyzer  - Логи контейнера
  docker stop bills-analyzer     - Зупинити контейнер
  docker rm bills-analyzer       - Видалити контейнер

EOF
}

# Головна логіка
info "Bills Analyzer Deployment"
info "Версія: $VERSION"
echo ""

case "${1:-help}" in
    local)
        deploy_local
        ;;
    docker-hub)
        deploy_docker_hub
        ;;
    gcr)
        deploy_gcr
        ;;
    cloud-run)
        deploy_cloud_run
        ;;
    release)
        release
        ;;
    help|*)
        show_help
        ;;
esac
