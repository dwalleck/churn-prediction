"""Unit tests for recommendation engine."""

import pandas as pd
import pytest

from churn_predictor.analytics.recommendations import generate_recommendations


def test_generate_recommendations_immediate_contact():
    """Test immediate contact recommendation for long gaps."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "churn_probability": [75.0],
        "days_since_last_touchbase": [90],
        "revenue_change_pct": [0],
        "ticket_escalation_rate": [0],
        "tenure_months": [12],
    })

    recs = generate_recommendations(df, min_risk_score=70)

    assert len(recs) > 0
    assert any(rec.action_type == "immediate_contact" for rec in recs)
    assert any("90 days" in rec.rationale for rec in recs)


def test_generate_recommendations_offer_discount():
    """Test discount recommendation for revenue decline."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "churn_probability": [80.0],
        "days_since_last_touchbase": [30],
        "revenue_change_pct": [-40],
        "ticket_escalation_rate": [0],
        "tenure_months": [12],
    })

    recs = generate_recommendations(df, min_risk_score=70)

    assert any(rec.action_type == "offer_discount" for rec in recs)
    assert any("revenue declined" in rec.rationale.lower() for rec in recs)


def test_generate_recommendations_service_review():
    """Test service review recommendation for high escalations."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "churn_probability": [85.0],
        "days_since_last_touchbase": [30],
        "revenue_change_pct": [0],
        "ticket_escalation_rate": [60],
        "tenure_months": [12],
    })

    recs = generate_recommendations(df, min_risk_score=70)

    assert any(rec.action_type == "review_service" for rec in recs)
    assert any("escalation" in rec.rationale.lower() for rec in recs)


def test_generate_recommendations_schedule_training():
    """Test training recommendation for new customers."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "churn_probability": [75.0],
        "days_since_last_touchbase": [30],
        "revenue_change_pct": [0],
        "ticket_escalation_rate": [0],
        "tenure_months": [2],
    })

    recs = generate_recommendations(df, min_risk_score=70)

    assert any(rec.action_type == "schedule_training" for rec in recs)
    assert any("new customer" in rec.rationale.lower() or "tenure" in rec.rationale.lower() for rec in recs)


def test_generate_recommendations_min_risk_filter():
    """Test that low-risk customers don't get recommendations."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "churn_probability": [30.0],
        "days_since_last_touchbase": [90],
        "revenue_change_pct": [-40],
        "ticket_escalation_rate": [60],
        "tenure_months": [2],
    })

    recs = generate_recommendations(df, min_risk_score=70)

    # Should return empty since below threshold
    assert len(recs) == 0


def test_generate_recommendations_priority_order():
    """Test that recommendations have proper priority."""
    df = pd.DataFrame({
        "account_id": ["A001"],
        "churn_probability": [85.0],
        "days_since_last_touchbase": [90],
        "revenue_change_pct": [-40],
        "ticket_escalation_rate": [60],
        "tenure_months": [2],
    })

    recs = generate_recommendations(df, min_risk_score=70)

    # All recommendations should have priority 1, 2, or 3
    assert all(rec.priority in [1, 2, 3] for rec in recs)

    # High priority actions should be present
    priority_1_recs = [rec for rec in recs if rec.priority == 1]
    assert len(priority_1_recs) > 0
