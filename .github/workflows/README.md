# GitHub Actions Workflows

## Deploy to Cloud Run

Автоматичний деплой додатку на Google Cloud Run при push в гілки `main` або `feature/deployment`.

### Необхідні GitHub Secrets

Перед використанням workflow потрібно налаштувати наступні секрети в репозиторії:

#### 1. GCP_SA_KEY
Service Account Key для Google Cloud Platform у форматі JSON.

**Як створити:**
```bash
# Створити service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deploy"

# Надати необхідні права
gcloud projects add-iam-policy-binding gen-lang-client-0955618410 \
  --member="serviceAccount:github-actions@gen-lang-client-0955618410.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0955618410 \
  --member="serviceAccount:github-actions@gen-lang-client-0955618410.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0955618410 \
  --member="serviceAccount:github-actions@gen-lang-client-0955618410.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0955618410 \
  --member="serviceAccount:github-actions@gen-lang-client-0955618410.iam.gserviceaccount.com" \
  --role="roles/secretmanager.admin"

gcloud projects add-iam-policy-binding gen-lang-client-0955618410 \
  --member="serviceAccount:github-actions@gen-lang-client-0955618410.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Створити ключ
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@gen-lang-client-0955618410.iam.gserviceaccount.com

# Скопіювати вміст файлу та додати як GCP_SA_KEY секрет
cat github-actions-key.json
```

#### 2. GOOGLE_API_KEY
API ключ для Google Gemini AI (вже налаштовано ✅)

#### 3. TELEGRAM_BOT_TOKEN
Токен бота з @BotFather (вже налаштовано ✅)

#### 4. TELEGRAM_CHAT_ID (опціонально)
ID чату для нотифікацій (вже налаштовано ✅)

### Як додати секрет в GitHub:

```bash
# Через GitHub CLI
gh secret set GCP_SA_KEY < github-actions-key.json
gh secret set GOOGLE_API_KEY
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID

# Або вручну:
# 1. Відкрити Settings > Secrets and variables > Actions
# 2. Натиснути "New repository secret"
# 3. Ввести ім'я та значення
```

### Workflow Тригери

- **Push в main/feature/deployment**: Автоматичний деплой
- **Manual trigger**: Можна запустити вручну через GitHub UI

### Що робить workflow:

1. ✅ Checkout коду
2. ✅ Налаштування Google Cloud SDK
3. ✅ Аутентифікація в GCP
4. ✅ Створення .env.production файлу
5. ✅ Збірка Docker образу
6. ✅ Push в Artifact Registry
7. ✅ Створення/оновлення секретів в Secret Manager
8. ✅ Деплой на Cloud Run
9. ✅ Перевірка health check
10. ✅ Виведення summary з посиланнями

### Моніторинг деплою

Переглянути статус деплою можна:
- На вкладці "Actions" в GitHub
- В логах Cloud Run: https://console.cloud.google.com/run/detail/europe-west3/bills-analyzer/logs

### Швидкий запуск

1. Переконайтесь, що всі секрети налаштовані
2. Push код в гілку `main` або `feature/deployment`
3. Перейдіть на вкладку Actions та спостерігайте за деплоєм
4. Після завершення отримаєте URL сервісу

### Troubleshooting

**Помилка: "Permission denied"**
- Перевірте, що Service Account має всі необхідні ролі

**Помилка: "Secret not found"**
- Перевірте, що всі секрети створені в GitHub

**Деплой успішний, але сервіс не працює**
- Перевірте логи: `gcloud logging read "resource.type=cloud_run_revision"`
- Перевірте змінні середовища в Cloud Run Console
