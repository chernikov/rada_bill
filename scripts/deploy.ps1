# Bills Analyzer - PowerShell Deployment Script
# Використання: .\deploy.ps1 <command>

param(
    [Parameter(Position=0)]
    [ValidateSet('local', 'docker-hub', 'gcr', 'cloud-run', 'release', 'help')]
    [string]$Command = 'help',
    
    [Parameter()]
    [string]$Version = $null,
    
    [Parameter()]
    [switch]$WithSecrets = $false
)

# Кольори
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Info($message) {
    Write-ColorOutput Cyan "ℹ️  $message"
}

function Write-Success($message) {
    Write-ColorOutput Green "✅ $message"
}

function Write-Warning($message) {
    Write-ColorOutput Yellow "⚠️  $message"
}

function Write-Error2($message) {
    Write-ColorOutput Red "❌ $message"
}

# Змінні
$APP_NAME = "bills-analyzer"
$DOCKER_USERNAME = "yourusername"
$GCP_PROJECT = "gen-lang-client-0955618410"
$GCP_REGION = "europe-west3"
$GCR_REGISTRY = "$GCP_REGION-docker.pkg.dev"
$GCR_REPO = "cloud-run-source-deploy"
$CLOUD_RUN_SERVICE = "bills-analyzer"

# Отримати версію
if (-not $Version) {
    try {
        $versionInfo = python -c "from src.backend.version import get_version; v = get_version(); print(f'{v[`"full_version`"]}')"
        $Version = $versionInfo
    } catch {
        $Version = "1.0.0"
        Write-Warning "Не вдалося отримати версію, використовую $Version"
    }
}

$DOCKER_IMAGE = "$DOCKER_USERNAME/$APP_NAME"
$GCR_IMAGE = "$GCR_REGISTRY/$GCP_PROJECT/$GCR_REPO/$APP_NAME"

# Функції деплою
function Deploy-Local {
    Write-Info "Локальний деплой..."
    
    # Збірка
    Write-Info "Збірка Docker image..."
    docker build -t "${APP_NAME}:latest" -t "${APP_NAME}:${Version}" .
    if ($LASTEXITCODE -ne 0) {
        Write-Error2 "Помилка збірки"
        exit 1
    }
    Write-Success "Image збудовано: ${APP_NAME}:${Version}"
    
    # Зупинити старий контейнер
    Write-Info "Зупинка старого контейнера..."
    docker stop $APP_NAME 2>$null
    docker rm $APP_NAME 2>$null
    
    # Запуск
    Write-Info "Запуск контейнера..."
    docker run -d `
        --name $APP_NAME `
        -p 8080:8080 `
        --env-file .env `
        "${APP_NAME}:latest"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Контейнер запущено: http://localhost:8080"
        Write-Info "Логи: docker logs -f $APP_NAME"
        
        # Показати логи
        Start-Sleep -Seconds 2
        docker logs $APP_NAME
    } else {
        Write-Error2 "Помилка запуску контейнера"
        exit 1
    }
}

function Deploy-DockerHub {
    Write-Info "Публікація в Docker Hub..."
    
    # Вхід
    Write-Info "Вхід в Docker Hub..."
    docker login
    if ($LASTEXITCODE -ne 0) {
        Write-Error2 "Помилка входу в Docker Hub"
        exit 1
    }
    
    # Збірка
    Write-Info "Збірка image..."
    docker build -t "${APP_NAME}:latest" .
    docker tag "${APP_NAME}:latest" "${DOCKER_IMAGE}:latest"
    docker tag "${APP_NAME}:latest" "${DOCKER_IMAGE}:${Version}"
    
    # Push
    Write-Info "Завантаження в Docker Hub..."
    docker push "${DOCKER_IMAGE}:latest"
    docker push "${DOCKER_IMAGE}:${Version}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Image завантажено: ${DOCKER_IMAGE}:${Version}"
    } else {
        Write-Error2 "Помилка завантаження"
        exit 1
    }
}

function Deploy-GCR {
    Write-Info "Публікація в Google Container Registry..."
    
    # Налаштування GCR
    Write-Info "Налаштування автентифікації..."
    gcloud auth configure-docker $GCR_REGISTRY
    
    # Збірка
    Write-Info "Збірка image для GCR..."
    docker build -t "${GCR_IMAGE}:latest" -t "${GCR_IMAGE}:${Version}" .
    if ($LASTEXITCODE -ne 0) {
        Write-Error2 "Помилка збірки"
        exit 1
    }
    
    # Push
    Write-Info "Завантаження в GCR..."
    docker push "${GCR_IMAGE}:latest"
    docker push "${GCR_IMAGE}:${Version}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Image завантажено: ${GCR_IMAGE}:${Version}"
    } else {
        Write-Error2 "Помилка завантаження"
        exit 1
    }
}

function Deploy-CloudRun {
    Write-Info "Розгортання на Cloud Run..."
    
    # Спочатку push в GCR
    Deploy-GCR
    
    # Базова команда деплою
    $deployCmd = @(
        "gcloud", "run", "deploy", $CLOUD_RUN_SERVICE,
        "--image", "${GCR_IMAGE}:${Version}",
        "--platform", "managed",
        "--region", $GCP_REGION,
        "--allow-unauthenticated",
        "--memory", "1Gi",
        "--cpu", "2",
        "--min-instances", "0",
        "--max-instances", "10",
        "--set-env-vars", "DEBUG=false,GCP_PROJECT_ID=$GCP_PROJECT,FIRESTORE_DATABASE=(default)"
    )
    
    # Додати секрети якщо потрібно
    if ($WithSecrets) {
        Write-Info "Додавання секретів..."
        $deployCmd += "--update-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest,TELEGRAM_BOT_TOKEN=TELEGRAM_BOT_TOKEN:latest"
    }
    
    # Виконати деплой
    Write-Info "Розгортання сервісу..."
    & $deployCmd[0] $deployCmd[1..($deployCmd.Length-1)]
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Сервіс розгорнуто на Cloud Run"
        
        # Отримати URL
        Write-Info "Отримання URL сервісу..."
        $url = gcloud run services describe $CLOUD_RUN_SERVICE `
            --region $GCP_REGION `
            --format="value(status.url)"
        Write-Success "URL: $url"
    } else {
        Write-Error2 "Помилка розгортання"
        exit 1
    }
}

function Bump-Version {
    Write-Info "Інкремент версії..."
    $newVersion = python -c "from src.backend.version import increment_build; print(increment_build())"
    Write-Success "Нова версія: $newVersion"
    return $newVersion
}

function Release {
    Write-Info "Повний реліз..."
    
    # Інкремент версії
    $script:Version = Bump-Version
    
    # Push в GCR
    Deploy-GCR
    
    # Deploy на Cloud Run
    Deploy-CloudRun
    
    Write-Success "Реліз завершено успішно!"
}

function Show-Help {
    Write-Host @"
Bills Analyzer - PowerShell Deployment Script

Використання:
  .\deploy.ps1 <command> [-Version <version>] [-WithSecrets]

Команди:
  local       - Збудувати та запустити локально (Docker)
  docker-hub  - Завантажити в Docker Hub
  gcr         - Завантажити в Google Container Registry
  cloud-run   - Розгорнути на Cloud Run
  release     - Повний реліз (інкремент версії + GCR + Cloud Run)
  help        - Показати цю допомогу

Параметри:
  -Version <version>  - Вказати версію (за замовчуванням з version.py)
  -WithSecrets        - Використати Secret Manager для Cloud Run

Приклади:
  .\deploy.ps1 local
  .\deploy.ps1 gcr -Version "1.0.1"
  .\deploy.ps1 cloud-run -WithSecrets
  .\deploy.ps1 release

Додаткові команди Docker:
  docker-compose up -d         - Запустити через docker-compose
  docker-compose logs -f       - Показати логи
  docker-compose down          - Зупинити
  
  docker logs -f bills-analyzer  - Логи контейнера
  docker stop bills-analyzer     - Зупинити контейнер
  docker rm bills-analyzer       - Видалити контейнер

"@
}

# Головна логіка
Write-Info "Bills Analyzer Deployment"
Write-Info "Версія: $Version"
Write-Host ""

switch ($Command) {
    'local' {
        Deploy-Local
    }
    'docker-hub' {
        Deploy-DockerHub
    }
    'gcr' {
        Deploy-GCR
    }
    'cloud-run' {
        Deploy-CloudRun
    }
    'release' {
        Release
    }
    'help' {
        Show-Help
    }
    default {
        Show-Help
    }
}
