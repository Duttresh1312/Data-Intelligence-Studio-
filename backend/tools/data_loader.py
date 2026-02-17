"""
Deterministic data loading utilities.

Handles loading of CSV, Excel, and HTML table files.
No LLM usage - pure pandas operations.
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


def load_file(file_path: Path) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Load a file into a pandas DataFrame.
    
    Args:
        file_path: Path to the file
        
    Returns:
        (dataframe, error_message)
        If successful: (DataFrame, None)
        If failed: (None, error_message)
    """
    try:
        suffix = file_path.suffix.lower()
        
        if suffix == ".csv":
            df = pd.read_csv(file_path)
        elif suffix in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
        elif suffix == ".html":
            # Try to read HTML table
            tables = pd.read_html(file_path)
            if not tables:
                return None, "No HTML tables found in file"
            df = tables[0]  # Use first table
        else:
            return None, f"Unsupported file type: {suffix}"
        
        logger.info(f"Successfully loaded file: {file_path.name}, shape: {df.shape}")
        return df, None
        
    except Exception as e:
        error_msg = f"Error loading file {file_path.name}: {str(e)}"
        logger.error(error_msg)
        return None, error_msg


def validate_dataframe(df: pd.DataFrame) -> tuple[bool, Optional[str]]:
    """
    Validate that dataframe is usable for analysis.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        (is_valid, error_message)
    """
    if df is None:
        return False, "DataFrame is None"
    
    if df.empty:
        return False, "DataFrame is empty"
    
    if len(df.columns) == 0:
        return False, "DataFrame has no columns"
    
    # Check for reasonable size (prevent memory issues)
    max_rows = 10_000_000  # 10M rows max
    if len(df) > max_rows:
        return False, f"DataFrame too large: {len(df)} rows (max: {max_rows})"
    
    return True, None


def get_file_info(file_path: Path) -> Dict[str, Any]:
    """
    Get file metadata.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file info
    """
    return {
        "name": file_path.name,
        "size_bytes": file_path.stat().st_size,
        "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2),
        "extension": file_path.suffix.lower(),
    }
