# Firestore Database Backup Script (PowerShell)
# Creates a backup of Firestore database using gcloud CLI

param(
    [string]$OutputBucket = "",
    [switch]$LocalBackup = $false
)

$ErrorActionPreference = "Stop"

# Get project configuration
$ProjectId = "gen-lang-client-0955618410"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchiveDir = Join-Path $PSScriptRoot ".." "archive"

Write-Host "Starting Firestore backup..." -ForegroundColor Cyan
Write-Host "Project ID: $ProjectId"
Write-Host "Timestamp: $Timestamp"
Write-Host ""

# Create archive directory
if (-not (Test-Path $ArchiveDir)) {
    New-Item -ItemType Directory -Path $ArchiveDir | Out-Null
}

if ($LocalBackup) {
    # Local backup using Python script
    Write-Host "Running local Python backup script..." -ForegroundColor Yellow
    
    # Activate virtual environment if it exists
    $VenvPath = Join-Path $PSScriptRoot ".." ".venv" "Scripts" "Activate.ps1"
    if (Test-Path $VenvPath) {
        & $VenvPath
    }
    
    # Run Python backup script
    $BackupScript = Join-Path $PSScriptRoot "backup_firestore.py"
    python $BackupScript
    
} else {
    # Cloud backup using gcloud
    Write-Host "Using gcloud Firestore export..." -ForegroundColor Yellow
    
    if ($OutputBucket -eq "") {
        $OutputBucket = "gs://$ProjectId-firestore-backups/backup_$Timestamp"
    }
    
    Write-Host "Backup destination: $OutputBucket" -ForegroundColor Green
    
    try {
        # Export Firestore data
        gcloud firestore export $OutputBucket `
            --project=$ProjectId `
            --async
        
        Write-Host ""
        Write-Host "Backup initiated successfully!" -ForegroundColor Green
        Write-Host "Check status with: gcloud firestore operations list --project=$ProjectId" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Note: Cloud Firestore export is asynchronous."
        Write-Host "The backup will be available at: $OutputBucket"
        
    } catch {
        Write-Host "Error during backup: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "Tip: Use -LocalBackup flag for local JSON export" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""
Write-Host "Backup process completed!" -ForegroundColor Green
