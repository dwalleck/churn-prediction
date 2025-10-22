"""Enhanced synthetic data generation for churn prediction."""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


def generate_customer_data(
    num_customers: int = 1000,
    num_months: int = 12,
    churn_rate: float = 0.15,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Generate realistic synthetic customer data with temporal trends.

    Args:
        num_customers: Number of unique customers
        num_months: Number of months of history per customer
        churn_rate: Target churn rate (0-1)
        random_state: Random seed for reproducibility

    Returns:
        DataFrame with customer records
    """
    np.random.seed(random_state)

    records = []
    start_date = datetime(2024, 1, 1)

    # Determine which customers will churn
    num_churned = int(num_customers * churn_rate)
    churned_customers = set(np.random.choice(num_customers, num_churned, replace=False))

    for customer_id in range(num_customers):
        will_churn = customer_id in churned_customers

        # Customer baseline characteristics
        baseline_transactions = np.random.randint(50, 300)
        baseline_revenue = baseline_transactions * np.random.uniform(50, 500)
        baseline_tickets = np.random.poisson(2)
        contract_type = np.random.choice(["monthly", "annual"], p=[0.7, 0.3])

        # Churn cohort assignment
        if will_churn:
            churn_cohort = np.random.choice([
                "early_churn",  # Month 1-3
                "renewal_churn",  # At 11-13 months
                "gradual_disengagement",  # Slow decline
                "service_issues",  # Spike in tickets
                "price_sensitive",  # Revenue decline
            ])
            churn_month = _get_churn_month(churn_cohort, num_months)
        else:
            churn_cohort = "stable"
            churn_month = None

        # Generate monthly records
        for month_offset in range(num_months):
            month_date = start_date + timedelta(days=30 * month_offset)
            is_churn_month = (churn_month == month_offset)

            # Apply cohort-specific patterns
            metrics = _generate_month_metrics(
                baseline_transactions=baseline_transactions,
                baseline_revenue=baseline_revenue,
                baseline_tickets=baseline_tickets,
                month_offset=month_offset,
                churn_cohort=churn_cohort,
                churn_month=churn_month,
                contract_type=contract_type,
            )

            record = {
                "account_id": f"ACC-{customer_id:04d}",
                "month": month_date.strftime("%Y-%m-%d"),
                "current_month_transactions": metrics["transactions"],
                "current_month_revenue": metrics["revenue"],
                "total_tickets": metrics["tickets"],
                "escalated_tickets": metrics["escalated_tickets"],
                "late_payments": metrics["late_payments"],
                "enabled_channels": metrics["enabled_channels"],
                "self_service_percentage": metrics["self_service_pct"],
                "last_touchbase_date": (month_date - timedelta(days=metrics["days_since_contact"])).isoformat(),
                "average_resolution_time_hours": metrics["resolution_time"],
                "churned": 1 if is_churn_month else 0,
            }

            records.append(record)

            # Stop generating records after churn
            if is_churn_month:
                break

    return pd.DataFrame(records)


def _get_churn_month(cohort: str, num_months: int) -> int:
    """Determine churn month based on cohort."""
    if cohort == "early_churn":
        return np.random.randint(1, 4)  # Month 1-3
    elif cohort == "renewal_churn":
        return np.random.randint(11, min(14, num_months))  # Month 11-13
    elif cohort in ["gradual_disengagement", "service_issues", "price_sensitive"]:
        return np.random.randint(6, num_months)  # Later months
    else:
        return num_months  # Never churns


def _generate_month_metrics(
    baseline_transactions: int,
    baseline_revenue: float,
    baseline_tickets: int,
    month_offset: int,
    churn_cohort: str,
    churn_month: Optional[int],
    contract_type: str,
) -> dict:
    """Generate realistic monthly metrics based on churn cohort."""
    metrics = {}

    # Base values with some randomness
    transactions = baseline_transactions * np.random.uniform(0.9, 1.1)
    revenue = baseline_revenue * np.random.uniform(0.9, 1.1)
    tickets = max(0, baseline_tickets + np.random.randint(-1, 2))
    days_since_contact = np.random.randint(1, 30)
    resolution_time = np.random.uniform(20, 60)
    enabled_channels = np.random.randint(1, 7)
    self_service_pct = np.random.uniform(30, 80)

    # Apply cohort-specific patterns
    if churn_month is not None and month_offset >= churn_month - 3:
        months_until_churn = churn_month - month_offset

        if churn_cohort == "gradual_disengagement":
            # Gradual decline over 3 months
            decline_factor = 1 - (0.15 * (3 - months_until_churn))
            transactions *= decline_factor
            revenue *= decline_factor
            tickets = max(0, int(tickets * (1 - 0.2 * (3 - months_until_churn))))
            days_since_contact += int(10 * (3 - months_until_churn))

        elif churn_cohort == "service_issues":
            # Spike in tickets and escalations
            tickets = int(tickets * 3)
            resolution_time *= 1.5
            days_since_contact = min(90, days_since_contact + 20 * (3 - months_until_churn))

        elif churn_cohort == "price_sensitive":
            # Revenue decline but transactions stable
            revenue *= (0.7 + 0.1 * months_until_churn)
            # More late payments
            pass

        elif churn_cohort == "early_churn":
            # Poor onboarding - high tickets, low adoption
            tickets = int(tickets * 2)
            self_service_pct = max(10, self_service_pct * 0.5)
            enabled_channels = max(1, int(enabled_channels * 0.5))

    metrics["transactions"] = int(max(0, transactions))
    metrics["revenue"] = max(0, revenue)
    metrics["tickets"] = int(max(0, tickets))
    metrics["escalated_tickets"] = int(min(metrics["tickets"], np.random.binomial(metrics["tickets"], 0.2)))
    metrics["late_payments"] = np.random.binomial(3, 0.1) if churn_cohort != "price_sensitive" else np.random.binomial(3, 0.4)
    metrics["enabled_channels"] = enabled_channels
    metrics["self_service_pct"] = min(100, max(0, self_service_pct))
    metrics["days_since_contact"] = min(365, max(0, int(days_since_contact)))
    metrics["resolution_time"] = max(0, resolution_time)

    return metrics
