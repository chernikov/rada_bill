#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Запуск FastAPI застосунку в venv
.DESCRIPTION
    Цей скрипт активує віртуальне оточення та запускає FastAPI застосунок через uvicorn
#>

# Перехід до кореневої директорії проекту
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-Host "🔧 Активація віртуального оточення..." -ForegroundColor Cyan
& "$ProjectRoot\.venv\Scripts\Activate.ps1"

Write-Host "🚀 Запуск FastAPI застосунку на http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "📝 Натисніть Ctrl+C для зупинки сервера" -ForegroundColor Yellow
Write-Host ""

# Перехід до src і запуск uvicorn
Set-Location "$ProjectRoot\src"
python -m uvicorn backend.api.main:app --reload --port 8000
