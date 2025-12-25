"""
Firestore Database Backup Script
Creates a JSON dump of all Firestore collections to the archive folder.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from google.cloud import firestore


def backup_firestore():
    """Export all Firestore collections to JSON files."""
    
    # Initialize Firestore client
    db = firestore.Client()
    
    # Create archive directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_dir = Path(__file__).parent.parent / "archive" / f"firestore_backup_{timestamp}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Starting Firestore backup to: {archive_dir}")
    
    # Get all collections
    collections = ['bills', 'documents', 'analyses', 'telegramUsers']
    
    total_docs = 0
    
    for collection_name in collections:
        print(f"\nBacking up collection: {collection_name}")
        
        try:
            collection_ref = db.collection(collection_name)
            docs = collection_ref.stream()
            
            collection_data = []
            doc_count = 0
            
            for doc in docs:
                doc_dict = doc.to_dict()
                doc_dict['_id'] = doc.id  # Include document ID
                collection_data.append(doc_dict)
                doc_count += 1
            
            # Save to JSON file
            output_file = archive_dir / f"{collection_name}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(collection_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"  ✓ Exported {doc_count} documents to {output_file.name}")
            total_docs += doc_count
            
        except Exception as e:
            print(f"  ✗ Error backing up {collection_name}: {e}")
    
    # Create backup metadata
    metadata = {
        'backup_timestamp': timestamp,
        'backup_date': datetime.now().isoformat(),
        'total_documents': total_docs,
        'collections': collections,
        'project_id': os.getenv('GCP_PROJECT_ID', 'gen-lang-client-0955618410')
    }
    
    metadata_file = archive_dir / "backup_metadata.json"
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Backup completed successfully!")
    print(f"Total documents backed up: {total_docs}")
    print(f"Backup location: {archive_dir}")
    print(f"{'='*60}")
    
    return archive_dir


if __name__ == "__main__":
    try:
        backup_firestore()
    except Exception as e:
        print(f"Backup failed: {e}")
        exit(1)
