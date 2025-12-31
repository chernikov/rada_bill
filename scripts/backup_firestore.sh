#!/bin/bash
# Firestore Database Backup Script (Bash)
# Creates a backup of Firestore database

set -e

# Configuration
PROJECT_ID="gen-lang-client-0955618410"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARCHIVE_DIR="$SCRIPT_DIR/../archive"

# Parse arguments
LOCAL_BACKUP=false
OUTPUT_BUCKET=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --local)
            LOCAL_BACKUP=true
            shift
            ;;
        --bucket)
            OUTPUT_BUCKET="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "Starting Firestore backup..."
echo "Project ID: $PROJECT_ID"
echo "Timestamp: $TIMESTAMP"
echo ""

# Create archive directory
mkdir -p "$ARCHIVE_DIR"

if [ "$LOCAL_BACKUP" = true ]; then
    # Local backup using Python script
    echo "Running local Python backup script..."
    
    # Activate virtual environment if it exists
    if [ -f "$SCRIPT_DIR/../.venv/bin/activate" ]; then
        source "$SCRIPT_DIR/../.venv/bin/activate"
    fi
    
    # Run Python backup script
    python "$SCRIPT_DIR/backup_firestore.py"
    
else
    # Cloud backup using gcloud
    echo "Using gcloud Firestore export..."
    
    if [ -z "$OUTPUT_BUCKET" ]; then
        OUTPUT_BUCKET="gs://$PROJECT_ID-firestore-backups/backup_$TIMESTAMP"
    fi
    
    echo "Backup destination: $OUTPUT_BUCKET"
    
    # Export Firestore data
    gcloud firestore export "$OUTPUT_BUCKET" \
        --project="$PROJECT_ID" \
        --async
    
    echo ""
    echo "Backup initiated successfully!"
    echo "Check status with: gcloud firestore operations list --project=$PROJECT_ID"
    echo ""
    echo "Note: Cloud Firestore export is asynchronous."
    echo "The backup will be available at: $OUTPUT_BUCKET"
fi

echo ""
echo "Backup process completed!"
