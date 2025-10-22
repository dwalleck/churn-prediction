"""Unit tests for data preprocessor."""

import pandas as pd
import pytest
from datetime import datetime, timedelta

from churn_predictor.data.preprocessor import preprocess


def test_preprocess_tenure_months():
    """Test that tenure_months is calculated correctly."""
    df = pd.DataFrame({
        "account_id": ["A001", "A001", "A001"],
        "month": ["2024-01-01", "2024-02-01", "2024-03-01"],
        "current_month_transactions": [100, 110, 120],
        "current_month_revenue": [1000, 1100, 1200],
        "total_tickets": [1, 2, 1],
        "escalated_tickets": [0, 1, 0],
        "last_touchbase_date": ["2024-01-15", "2024-02-15", "2024-03-15"],
    })

    result = preprocess(df)

    assert "tenure_months" in result.columns
    assert list(result["tenure_months"]) == [1, 2, 3]


def test_preprocess_transaction_change_pct():
    """Test month-over-month transaction change calculation."""
    df = pd.DataFrame({
        "account_id": ["A001", "A001"],
        "month": ["2024-01-01", "2024-02-01"],
        "current_month_transactions": [100, 120],
        "current_month_revenue": [1000, 1200],
        "total_tickets": [1, 1],
        "escalated_tickets": [0, 0],
        "last_touchbase_date": ["2024-01-15", "2024-02-15"],
    })

    result = preprocess(df)

    assert "transaction_change_pct" in result.columns
    # First month should be 0, second should be 20% increase
    assert result.iloc[0]["transaction_change_pct"] == 0
    assert abs(result.iloc[1]["transaction_change_pct"] - 20.0) < 0.1


def test_preprocess_ticket_escalation_rate():
    """Test ticket escalation rate calculation."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "month": ["2024-01-01"],
        "current_month_transactions": [100],
        "current_month_revenue": [1000],
        "total_tickets": [10],
        "escalated_tickets": [3],
        "last_touchbase_date": ["2024-01-15"],
    })

    result = preprocess(df)

    assert "ticket_escalation_rate" in result.columns
    assert abs(result.iloc[0]["ticket_escalation_rate"] - 30.0) < 0.1


def test_preprocess_revenue_per_transaction():
    """Test revenue per transaction calculation."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "month": ["2024-01-01"],
        "current_month_transactions": [100],
        "current_month_revenue": [5000],
        "total_tickets": [1],
        "escalated_tickets": [0],
        "last_touchbase_date": ["2024-01-15"],
    })

    result = preprocess(df)

    assert "revenue_per_transaction" in result.columns
    assert abs(result.iloc[0]["revenue_per_transaction"] - 50.0) < 0.1


def test_preprocess_handles_missing_values():
    """Test that preprocessor handles missing values gracefully."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "month": ["2024-01-01"],
        "current_month_transactions": [None],
        "current_month_revenue": [None],
        "total_tickets": [1],
        "escalated_tickets": [0],
        "last_touchbase_date": ["2024-01-15"],
    })

    result = preprocess(df)

    # Should not raise exception
    assert len(result) == 1
    # Missing values should be filled
    assert result["revenue_per_transaction"].notna().all()
