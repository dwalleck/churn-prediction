"""Actionable recommendation engine for high-risk customers."""

import uuid
from datetime import datetime
from typing import Any

import pandas as pd

from churn_predictor.models.entities import ActionableRecommendation


def generate_recommendations(
    df: pd.DataFrame,
    min_risk_score: float = 70.0,
) -> list[ActionableRecommendation]:
    """
    Generate actionable retention recommendations for high-risk customers.

    Rule-based logic:
    - days_since_last_touchbase > 60 → immediate_contact
    - revenue_change_pct < -30% → offer_discount
    - ticket_escalation_rate > 50% → review_service
    - tenure_months < 3 → schedule_training

    Args:
        df: DataFrame with customer data and predictions
        min_risk_score: Minimum churn probability to generate recommendations

    Returns:
        List of ActionableRecommendation objects

    Example:
        >>> recommendations = generate_recommendations(df_predictions, min_risk_score=70)
        >>> for rec in recommendations[:3]:
        ...     print(f"{rec.account_id}: {rec.action_type} - {rec.description}")
    """
    # Filter to high-risk customers
    if "churn_probability" in df.columns:
        high_risk_df = df[df["churn_probability"] >= min_risk_score].copy()
    else:
        high_risk_df = df.copy()

    recommendations = []

    for _, row in high_risk_df.iterrows():
        account_id = row.get("account_id", "UNKNOWN")

        # Rule 1: Immediate contact for long gaps
        if row.get("days_since_last_touchbase", 0) > 60:
            recommendations.append(ActionableRecommendation(
                account_id=account_id,
                recommendation_id=str(uuid.uuid4()),
                action_type="immediate_contact",
                priority=1,
                description="Contact customer within 24-48 hours",
                rationale=f"No contact in {int(row.get('days_since_last_touchbase', 0))} days - high disengagement risk",
                estimated_impact="high",
                created_at=datetime.now(),
            ))

        # Rule 2: Offer discount for revenue decline
        if row.get("revenue_change_pct", 0) < -30:
            recommendations.append(ActionableRecommendation(
                account_id=account_id,
                recommendation_id=str(uuid.uuid4()),
                action_type="offer_discount",
                priority=2,
                description="Offer retention discount or value-add services",
                rationale=f"Revenue declined by {abs(row.get('revenue_change_pct', 0)):.0f}% - price sensitivity indicated",
                estimated_impact="high",
                created_at=datetime.now(),
            ))

        # Rule 3: Service quality review for escalations
        if row.get("ticket_escalation_rate", 0) > 50:
            recommendations.append(ActionableRecommendation(
                account_id=account_id,
                recommendation_id=str(uuid.uuid4()),
                action_type="review_service",
                priority=1,
                description="Schedule service quality review call",
                rationale=f"High ticket escalation rate ({row.get('ticket_escalation_rate', 0):.0f}%) - service issues",
                estimated_impact="high",
                created_at=datetime.now(),
            ))

        # Rule 4: Training for new customers
        if row.get("tenure_months", 99) < 3:
            recommendations.append(ActionableRecommendation(
                account_id=account_id,
                recommendation_id=str(uuid.uuid4()),
                action_type="schedule_training",
                priority=2,
                description="Schedule product training or onboarding check-in",
                rationale=f"New customer (tenure: {int(row.get('tenure_months', 0))} months) - onboarding support needed",
                estimated_impact="medium",
                created_at=datetime.now(),
            ))

        # Rule 5: Contract renewal discussion
        if row.get("tenure_months", 0) >= 11 and row.get("tenure_months", 0) <= 13:
            recommendations.append(ActionableRecommendation(
                account_id=account_id,
                recommendation_id=str(uuid.uuid4()),
                action_type="contract_renewal",
                priority=2,
                description="Proactive contract renewal discussion",
                rationale="Approaching 1-year tenure - renewal opportunity",
                estimated_impact="medium",
                created_at=datetime.now(),
            ))

        # Rule 6: General engagement for moderate risk
        if 50 < row.get("churn_probability", 0) < 70 and len([r for r in recommendations if r.account_id == account_id]) == 0:
            recommendations.append(ActionableRecommendation(
                account_id=account_id,
                recommendation_id=str(uuid.uuid4()),
                action_type="immediate_contact",
                priority=3,
                description="Schedule check-in call to gauge satisfaction",
                rationale=f"Moderate churn risk ({row.get('churn_probability', 0):.0f}%) - preventive outreach",
                estimated_impact="medium",
                created_at=datetime.now(),
            ))

    return recommendations


def get_recommendations_for_customer(
    account_id: str,
    df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """
    Get formatted recommendations for a specific customer.

    Args:
        account_id: Customer account ID
        df: DataFrame with customer data

    Returns:
        List of recommendation dictionaries
    """
    customer_df = df[df["account_id"] == account_id]

    if len(customer_df) == 0:
        return []

    recommendations = generate_recommendations(customer_df, min_risk_score=0)

    # Convert to dictionaries and sort by priority
    rec_dicts = [rec.to_dict() for rec in recommendations]
    rec_dicts.sort(key=lambda x: x["priority"])

    return rec_dicts
