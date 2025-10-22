"""Data validation for customer CSV files."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import pandas as pd

from churn_predictor.exceptions import ValidationError


@dataclass
class ValidationResult:
    """Result of data validation with status and messages."""

    is_valid: bool
    errors: list[str]
    warnings: list[str]
    row_count: int
    column_count: int

    def __str__(self) -> str:
        """Human-readable validation summary."""
        status = "✓ VALID" if self.is_valid else "✗ INVALID"
        msg = [f"{status} - {self.row_count} rows, {self.column_count} columns"]

        if self.errors:
            msg.append(f"\nErrors ({len(self.errors)}):")
            msg.extend(f"  - {error}" for error in self.errors)

        if self.warnings:
            msg.append(f"\nWarnings ({len(self.warnings)}):")
            msg.extend(f"  - {warning}" for warning in self.warnings)

        return "\n".join(msg)


REQUIRED_COLUMNS = [
    "account_id",
    "month",
    "current_month_transactions",
    "current_month_revenue",
    "total_tickets",
    "escalated_tickets",
    "late_payments",
    "enabled_channels",
    "self_service_percentage",
    "last_touchbase_date",
    "average_resolution_time_hours",
    "churned",
]


def validate_schema(df: pd.DataFrame) -> ValidationResult:
    """
    Validate CSV schema and data quality.

    Args:
        df: DataFrame to validate

    Returns:
        ValidationResult with validation status and messages

    Raises:
        ValidationError: If critical validation failures occur
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Check required columns
    missing_columns = set(REQUIRED_COLUMNS) - set(df.columns)
    if missing_columns:
        errors.append(
            f"Missing required columns: {sorted(missing_columns)}. "
            f"Expected {len(REQUIRED_COLUMNS)} columns, found {len(df.columns)}."
        )

    # Check for empty DataFrame
    if len(df) == 0:
        errors.append("DataFrame is empty. Expected at least 100 customer records.")

    # Check minimum rows
    if len(df) < 100:
        warnings.append(
            f"Only {len(df)} rows found. Recommend at least 100 customers for robust training."
        )

    # Check for duplicates
    if "account_id" in df.columns and "month" in df.columns:
        duplicates = df.duplicated(subset=["account_id", "month"], keep=False)
        if duplicates.any():
            dup_count = duplicates.sum()
            errors.append(
                f"Found {dup_count} duplicate (account_id, month) pairs. "
                "Each customer-month combination must be unique."
            )

    # Validate numeric columns
    numeric_columns = [
        "current_month_transactions",
        "current_month_revenue",
        "total_tickets",
        "escalated_tickets",
        "late_payments",
        "enabled_channels",
        "self_service_percentage",
        "average_resolution_time_hours",
        "churned",
    ]

    for col in numeric_columns:
        if col not in df.columns:
            continue

        # Check for non-numeric values
        try:
            pd.to_numeric(df[col], errors="raise")
        except (ValueError, TypeError):
            errors.append(
                f"Column '{col}' contains non-numeric values. All values must be numbers."
            )

        # Check for negative values where inappropriate
        if col in ["current_month_transactions", "current_month_revenue", "total_tickets"]:
            if (df[col] < 0).any():
                errors.append(
                    f"Column '{col}' contains negative values. "
                    f"Expected values >= 0."
                )

        # Check escalated_tickets <= total_tickets
        if col == "escalated_tickets" and "total_tickets" in df.columns:
            if (df["escalated_tickets"] > df["total_tickets"]).any():
                errors.append(
                    "Column 'escalated_tickets' has values greater than 'total_tickets'. "
                    "Escalated tickets cannot exceed total tickets."
                )

        # Check self_service_percentage range
        if col == "self_service_percentage":
            if ((df[col] < 0) | (df[col] > 100)).any():
                errors.append(
                    "Column 'self_service_percentage' has values outside 0-100 range."
                )

        # Check churned values
        if col == "churned":
            unique_values = df[col].unique()
            if not set(unique_values).issubset({0, 1}):
                errors.append(
                    f"Column 'churned' contains invalid values: {unique_values}. "
                    "Expected only 0 (active) or 1 (churned)."
                )

    # Check class balance for churn
    if "churned" in df.columns and len(df) > 0:
        churn_rate = df["churned"].mean()
        if churn_rate < 0.05:
            warnings.append(
                f"Churn rate is {churn_rate:.1%}, which is very low. "
                "Recommend at least 5% positive examples for model training."
            )
        if churn_rate > 0.50:
            warnings.append(
                f"Churn rate is {churn_rate:.1%}, which is very high. "
                "This may indicate data quality issues or unusual business conditions."
            )

    # Check for missing values
    missing_counts = df.isnull().sum()
    high_missing = missing_counts[missing_counts > len(df) * 0.10]
    if len(high_missing) > 0:
        for col, count in high_missing.items():
            pct = count / len(df) * 100
            warnings.append(
                f"Column '{col}' has {count} missing values ({pct:.1f}%). "
                "More than 10% missing may impact model quality."
            )

    # Check date columns
    if "month" in df.columns:
        try:
            pd.to_datetime(df["month"], errors="raise")
        except (ValueError, TypeError):
            errors.append(
                "Column 'month' contains invalid dates. "
                "Expected format: YYYY-MM or valid datetime."
            )

    if "last_touchbase_date" in df.columns:
        try:
            touchbase_dates = pd.to_datetime(df["last_touchbase_date"], errors="coerce")
            future_dates = touchbase_dates > datetime.now()
            if future_dates.any():
                errors.append(
                    "Column 'last_touchbase_date' contains future dates. "
                    "Dates must be in the past."
                )
        except (ValueError, TypeError):
            errors.append(
                "Column 'last_touchbase_date' contains invalid dates. "
                "Expected valid datetime format."
            )

    is_valid = len(errors) == 0
    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        row_count=len(df),
        column_count=len(df.columns),
    )
