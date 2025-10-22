"""Data entities for churn prediction system."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ChurnScore:
    """Customer churn score entity."""

    account_id: str
    score_date: str  # ISO format date
    churn_probability: float  # 0-100
    risk_level: str  # "low", "medium", "high"
    confidence: float  # 0-1
    model_version: str
    top_risk_factors: list[dict[str, Any]]  # [{"feature": str, "importance": float}]
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "account_id": self.account_id,
            "score_date": self.score_date,
            "churn_probability": float(self.churn_probability),
            "risk_level": self.risk_level,
            "confidence": float(self.confidence),
            "model_version": self.model_version,
            "top_risk_factors": self.top_risk_factors,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ActionableRecommendation:
    """Retention recommendation for high-risk customer."""

    account_id: str
    recommendation_id: str
    action_type: str  # "immediate_contact", "offer_discount", etc.
    priority: int  # 1, 2, or 3
    description: str
    rationale: str
    estimated_impact: str  # "high", "medium", "low"
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "account_id": self.account_id,
            "recommendation_id": self.recommendation_id,
            "action_type": self.action_type,
            "priority": self.priority,
            "description": self.description,
            "rationale": self.rationale,
            "estimated_impact": self.estimated_impact,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ChurnEvent:
    """Historical churn event record."""

    event_id: str
    account_id: str
    churn_date: str  # ISO format date
    churn_reason_category: str  # "price_cost", "product_quality", etc.
    churn_reason_detail: str | None
    final_revenue: float
    final_transactions: int
    tenure_at_churn: int
    created_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "event_id": self.event_id,
            "account_id": self.account_id,
            "churn_date": self.churn_date,
            "churn_reason_category": self.churn_reason_category,
            "churn_reason_detail": self.churn_reason_detail,
            "final_revenue": float(self.final_revenue),
            "final_transactions": int(self.final_transactions),
            "tenure_at_churn": int(self.tenure_at_churn),
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class ModelMetadata:
    """ML model metadata and performance metrics."""

    model_version: str
    trained_at: datetime
    training_data_path: str
    model_artifact_path: str
    algorithm: str
    hyperparameters: dict[str, Any]
    performance_metrics: dict[str, float]
    feature_importance: dict[str, float]
    is_active: bool

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "model_version": self.model_version,
            "trained_at": self.trained_at.isoformat(),
            "training_data_path": self.training_data_path,
            "model_artifact_path": self.model_artifact_path,
            "algorithm": self.algorithm,
            "hyperparameters": self.hyperparameters,
            "performance_metrics": self.performance_metrics,
            "feature_importance": self.feature_importance,
            "is_active": self.is_active,
        }
