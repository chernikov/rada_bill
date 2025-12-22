# Deployment Scripts

Цей каталог містить скрипти для розгортання Bills Analyzer.

## Файли

- **deploy.ps1** - PowerShell скрипт для Windows
- **deploy.sh** - Bash скрипт для Linux/Mac

## Використання

### Windows (PowerShell)
```powershell
.\scripts\deploy.ps1 local          # Локальний запуск
.\scripts\deploy.ps1 docker-hub     # Push в Docker Hub
.\scripts\deploy.ps1 gcr            # Push в Google Registry
.\scripts\deploy.ps1 cloud-run      # Deploy на Cloud Run
.\scripts\deploy.ps1 release        # Повний реліз
```

### Linux/Mac (Bash)
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh local           # Локальний запуск
./scripts/deploy.sh docker-hub      # Push в Docker Hub
./scripts/deploy.sh gcr             # Push в Google Registry
./scripts/deploy.sh cloud-run       # Deploy на Cloud Run
./scripts/deploy.sh release         # Повний реліз
```

## Детальна документація

Дивіться [docs/DOCKER_DEPLOYMENT.md](../docs/DOCKER_DEPLOYMENT.md) для детальної інформації.
