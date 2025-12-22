# Cloud Run Logs Viewer Script
# Usage: .\scripts\logs.ps1 [options]
# Examples:
#   .\scripts\logs.ps1                    # Get latest 50 logs
#   .\scripts\logs.ps1 -Limit 100         # Get latest 100 logs
#   .\scripts\logs.ps1 -Filter "bot"      # Filter logs containing "bot"
#   .\scripts\logs.ps1 -Errors            # Show only errors
#   .\scripts\logs.ps1 -Follow            # Follow logs in real-time

param(
    [int]$Limit = 50,
    [string]$Filter = "",
    [switch]$Errors,
    [switch]$Follow,
    [string]$Since = ""
)

$PROJECT_ID = "gen-lang-client-0955618410"
$SERVICE_NAME = "bills-analyzer"
$REGION = "europe-west3"

Write-Host "📋 Cloud Run Logs Viewer" -ForegroundColor Cyan
Write-Host "Service: $SERVICE_NAME" -ForegroundColor Yellow
Write-Host "Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Gray
Write-Host ""

# Build filter query
$filterQuery = "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME"

if ($Errors) {
    $filterQuery += " AND severity>=ERROR"
    Write-Host "🔴 Showing only ERRORS" -ForegroundColor Red
}

if ($Since) {
    $filterQuery += " AND timestamp>=`"$Since`""
    Write-Host "📅 Since: $Since" -ForegroundColor Yellow
}

Write-Host ""

if ($Follow) {
    Write-Host "👀 Following logs (Press Ctrl+C to stop)..." -ForegroundColor Green
    Write-Host ""
    
    # Follow logs in real-time
    gcloud logging tail "$filterQuery" --project=$PROJECT_ID --format=json | ForEach-Object {
        $log = $_ | ConvertFrom-Json
        $timestamp = if ($log.timestamp -is [string]) { 
            $log.timestamp.Substring(0, 19) 
        } else { 
            $log.timestamp.ToString("yyyy-MM-dd HH:mm:ss") 
        }
        $severity = $log.severity
        $text = $log.textPayload
        
        if ($text) {
            $color = switch ($severity) {
                "ERROR" { "Red" }
                "WARNING" { "Yellow" }
                "INFO" { "White" }
                default { "Gray" }
            }
            
            if ($Filter -eq "" -or $text -match $Filter) {
                Write-Host "$timestamp [$severity] " -ForegroundColor $color -NoNewline
                Write-Host $text
            }
        }
    }
} else {
    Write-Host "📜 Fetching latest $Limit logs..." -ForegroundColor Green
    Write-Host ""
    
    # Get logs
    $logs = gcloud logging read "$filterQuery" --limit=$Limit --project=$PROJECT_ID --format=json | ConvertFrom-Json
    
    if ($Filter) {
        $logs = $logs | Where-Object { $_.textPayload -match $Filter }
        Write-Host "🔍 Filtered by: $Filter" -ForegroundColor Cyan
        Write-Host ""
    }
    
    # Display logs
    $logs | ForEach-Object {
        $timestamp = if ($_.timestamp -is [string]) { 
            $_.timestamp.Substring(0, 19) 
        } else { 
            $_.timestamp.ToString("yyyy-MM-dd HH:mm:ss") 
        }
        $severity = $_.severity
        $text = $_.textPayload
        
        if ($text) {
            $color = switch ($severity) {
                "ERROR" { "Red" }
                "WARNING" { "Yellow" }
                "INFO" { "White" }
                default { "Gray" }
            }
            
            Write-Host "$timestamp [$severity] " -ForegroundColor $color -NoNewline
            Write-Host $text
        }
    }
    
    Write-Host ""
    Write-Host "=" * 80 -ForegroundColor Gray
    Write-Host "Total logs displayed: $($logs.Count)" -ForegroundColor Green
}

Write-Host ""
Write-Host "💡 Tip: Use -Follow to watch logs in real-time" -ForegroundColor Cyan
Write-Host "💡 Tip: Use -Filter `"keyword`" to search logs" -ForegroundColor Cyan
Write-Host "💡 Tip: Use -Errors to show only errors" -ForegroundColor Cyan
