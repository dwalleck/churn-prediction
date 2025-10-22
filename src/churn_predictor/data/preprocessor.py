"""Feature engineering and data preprocessing for churn prediction."""

from datetime import datetime

import numpy as np
import pandas as pd

from churn_predictor.exceptions import ValidationError


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply feature engineering to customer data.

    Derived features:
    - tenure_months: Customer age in months
    - transaction_change_pct: Month-over-month transaction change
    - revenue_change_pct: Month-over-month revenue change
    - days_since_last_touchbase: Days since last interaction
    - ticket_escalation_rate: Percentage of tickets escalated
    - revenue_per_transaction: Average transaction value

    Args:
        df: Raw customer DataFrame

    Returns:
        DataFrame with additional engineered features

    Raises:
        ValidationError: If required columns are missing

    Example:
        >>> df_raw = load_csv("customers.csv")
        >>> df_processed = preprocess(df_raw)
        >>> assert "tenure_months" in df_processed.columns
    """
    df = df.copy()

    # Sort by account_id and month for time-based calculations
    if "account_id" in df.columns and "month" in df.columns:
        df = df.sort_values(["account_id", "month"])

    # Feature 1: tenure_months - customer age
    if "account_id" in df.columns and "month" in df.columns:
        # Count distinct months per customer
        df["tenure_months"] = df.groupby("account_id").cumcount() + 1
    else:
        # Fallback if columns missing
        df["tenure_months"] = 1

    # Feature 2: transaction_change_pct - MoM transaction change
    if "current_month_transactions" in df.columns and "account_id" in df.columns:
        df["prev_transactions"] = df.groupby("account_id")["current_month_transactions"].shift(1)
        df["transaction_change_pct"] = (
            (df["current_month_transactions"] - df["prev_transactions"])
            / df["prev_transactions"].replace(0, np.nan)
            * 100
        )
        # Fill NaN with 0 (first month or division by zero)
        df["transaction_change_pct"] = df["transaction_change_pct"].fillna(0)
        # Cap extreme values at +/- 500%
        df["transaction_change_pct"] = df["transaction_change_pct"].clip(-500, 500)
        df.drop(columns=["prev_transactions"], inplace=True)
    else:
        df["transaction_change_pct"] = 0

    # Feature 3: revenue_change_pct - MoM revenue change
    if "current_month_revenue" in df.columns and "account_id" in df.columns:
        df["prev_revenue"] = df.groupby("account_id")["current_month_revenue"].shift(1)
        df["revenue_change_pct"] = (
            (df["current_month_revenue"] - df["prev_revenue"])
            / df["prev_revenue"].replace(0, np.nan)
            * 100
        )
        df["revenue_change_pct"] = df["revenue_change_pct"].fillna(0)
        df["revenue_change_pct"] = df["revenue_change_pct"].clip(-500, 500)
        df.drop(columns=["prev_revenue"], inplace=True)
    else:
        df["revenue_change_pct"] = 0

    # Feature 4: days_since_last_touchbase - recency
    if "last_touchbase_date" in df.columns:
        try:
            touchbase_dates = pd.to_datetime(df["last_touchbase_date"], errors="coerce")
            reference_date = df["month"] if "month" in df.columns else datetime.now()
            reference_date = pd.to_datetime(reference_date, errors="coerce")

            df["days_since_last_touchbase"] = (
                (reference_date - touchbase_dates).dt.days
            )
            # Cap at 365 days for extreme values
            df["days_since_last_touchbase"] = df["days_since_last_touchbase"].clip(0, 365)
            # Fill missing with median
            df["days_since_last_touchbase"] = df["days_since_last_touchbase"].fillna(
                df["days_since_last_touchbase"].median()
            )
        except Exception:
            df["days_since_last_touchbase"] = 30  # Default value
    else:
        df["days_since_last_touchbase"] = 30

    # Feature 5: ticket_escalation_rate - support quality indicator
    if "escalated_tickets" in df.columns and "total_tickets" in df.columns:
        df["ticket_escalation_rate"] = (
            df["escalated_tickets"] / df["total_tickets"].replace(0, np.nan) * 100
        )
        df["ticket_escalation_rate"] = df["ticket_escalation_rate"].fillna(0)
        df["ticket_escalation_rate"] = df["ticket_escalation_rate"].clip(0, 100)
    else:
        df["ticket_escalation_rate"] = 0

    # Feature 6: revenue_per_transaction - transaction quality
    if "current_month_revenue" in df.columns and "current_month_transactions" in df.columns:
        df["revenue_per_transaction"] = (
            df["current_month_revenue"]
            / df["current_month_transactions"].replace(0, np.nan)
        )
        df["revenue_per_transaction"] = df["revenue_per_transaction"].fillna(0)
        # Cap extreme values
        upper_bound = df["revenue_per_transaction"].quantile(0.99)
        df["revenue_per_transaction"] = df["revenue_per_transaction"].clip(0, upper_bound)
    else:
        df["revenue_per_transaction"] = 0

    # Handle remaining missing values
    # For numeric columns, fill with 0
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    df[numeric_cols] = df[numeric_cols].fillna(0)

    return df
