"""
Helper utilities
"""
from datetime import datetime
from typing import Optional


def generate_analysis_filename(
    prefix: str = "analysis",
    extension: str = "json"
) -> str:
    """
    Generate filename for analysis with timestamp
    
    Args:
        prefix: Filename prefix (analysis, summary)
        extension: File extension (json, md)
        
    Returns:
        Filename like: analysis_20251216_143022.json
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def format_bill_number(bill_number: str) -> str:
    """
    Format bill number with leading zeros
    
    Args:
        bill_number: Bill number
        
    Returns:
        Formatted bill number (e.g., "0012414")
    """
    try:
        num = int(bill_number)
        return f"{num:07d}"
    except ValueError:
        return bill_number


def parse_document_filename(filename: str) -> Optional[dict]:
    """
    Parse document filename to extract metadata
    
    Args:
        filename: Document filename (e.g., "12414_2725589_1.pdf")
        
    Returns:
        Dictionary with billNumber, documentId, sequenceNumber, extension
    """
    try:
        name_without_ext = filename.rsplit('.', 1)[0]
        extension = filename.rsplit('.', 1)[1] if '.' in filename else ''
        
        parts = name_without_ext.split('_')
        
        if len(parts) >= 3:
            return {
                'billNumber': parts[0],
                'documentId': parts[1],
                'sequenceNumber': int(parts[2]),
                'extension': extension
            }
    except Exception:
        pass
    
    return None
