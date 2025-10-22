"""Unit tests for data validator."""

import pandas as pd
import pytest

from churn_predictor.data.validator import validate_schema, REQUIRED_COLUMNS


def test_validate_schema_valid_data():
    """Test validation with valid data."""
    df = pd.DataFrame({
        "account_id": ["A001", "A002"],
        "month": ["2024-01", "2024-01"],
        "current_month_transactions": [100, 150],
        "current_month_revenue": [1000.0, 1500.0],
        "total_tickets": [2, 3],
        "escalated_tickets": [1, 0],
        "late_payments": [0, 1],
        "enabled_channels": [3, 4],
        "self_service_percentage": [50.0, 60.0],
        "last_touchbase_date": ["2024-01-15", "2024-01-20"],
        "average_resolution_time_hours": [24.0, 36.0],
        "churned": [0, 1],
    })

    result = validate_schema(df)
    assert result.is_valid
    assert len(result.errors) == 0


def test_validate_schema_missing_columns():
    """Test validation with missing required columns."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "month": ["2024-01"],
    })

    result = validate_schema(df)
    assert not result.is_valid
    assert len(result.errors) > 0
    assert any("Missing required columns" in error for error in result.errors)


def test_validate_schema_negative_values():
    """Test validation with negative values in numeric columns."""
    df = pd.DataFrame({
        **{col: [0] for col in REQUIRED_COLUMNS},
        "current_month_transactions": [-10],
    })

    result = validate_schema(df)
    assert not result.is_valid
    assert any("negative values" in error.lower() for error in result.errors)


def test_validate_schema_churned_invalid_values():
    """Test validation with invalid churned column values."""
    df = pd.DataFrame({
        **{col: [0] if col != "churned" else [5] for col in REQUIRED_COLUMNS},
        "account_id": ["A001"],
        "month": ["2024-01"],
    })

    result = validate_schema(df)
    assert not result.is_valid
    assert any("churned" in error.lower() for error in result.errors)


def test_validate_schema_low_churn_rate_warning():
    """Test that low churn rate generates a warning."""
    data = {col: [0] * 100 for col in REQUIRED_COLUMNS}
    data["account_id"] = [f"A{i:03d}" for i in range(100)]
    data["month"] = ["2024-01"] * 100
    data["churned"] = [0] * 98 + [1] * 2  # 2% churn rate

    df = pd.DataFrame(data)

    result = validate_schema(df)
    assert any("churn rate" in warning.lower() for warning in result.warnings)
