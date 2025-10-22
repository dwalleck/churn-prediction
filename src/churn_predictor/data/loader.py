"""CSV data loading for customer churn prediction."""

from pathlib import Path
from typing import Any

import pandas as pd

from churn_predictor.exceptions import ValidationError


def load_csv(file_path: str | Path, validate: bool = True) -> pd.DataFrame:
    """
    Load customer data from CSV file.

    Args:
        file_path: Path to CSV file
        validate: Whether to validate file before loading (default: True)

    Returns:
        DataFrame with customer data

    Raises:
        ValidationError: If file doesn't exist, is too large, or has invalid format

    Example:
        >>> df = load_csv("data/raw/customers.csv")
        >>> print(f"Loaded {len(df)} customer records")
    """
    file_path = Path(file_path)

    # Check if file exists
    if not file_path.exists():
        raise ValidationError(
            f"File not found: {file_path}. "
            f"Please check the path and ensure the CSV file exists."
        )

    # Check file size (max 100MB)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 100:
        raise ValidationError(
            f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size of 100MB. "
            f"Please split the file into smaller chunks or remove unnecessary data."
        )

    # Try to load CSV
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValidationError(
            f"File is empty: {file_path}. "
            f"Expected a CSV file with customer data."
        )
    except pd.errors.ParserError as e:
        raise ValidationError(
            f"Failed to parse CSV file: {file_path}. "
            f"Error: {str(e)}. "
            f"Please ensure the file is a valid CSV format."
        )
    except Exception as e:
        raise ValidationError(
            f"Failed to load CSV file: {file_path}. "
            f"Error: {str(e)}. "
            f"Please check the file format and encoding (UTF-8 recommended)."
        )

    # Basic validation
    if len(df) == 0:
        raise ValidationError(
            f"CSV file contains no data rows: {file_path}. "
            f"Expected at least 1 row of customer data."
        )

    # Convert date columns
    if "month" in df.columns:
        try:
            df["month"] = pd.to_datetime(df["month"])
        except Exception:
            # Will be caught by schema validation
            pass

    if "last_touchbase_date" in df.columns:
        try:
            df["last_touchbase_date"] = pd.to_datetime(df["last_touchbase_date"])
        except Exception:
            # Will be caught by schema validation
            pass

    return df
