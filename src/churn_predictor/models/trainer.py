"""Model training for churn prediction using XGBoost."""

import pickle
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import fbeta_score, precision_recall_curve, precision_score, recall_score
from sklearn.model_selection import train_test_split

from churn_predictor.exceptions import ModelError


@dataclass
class TrainedModel:
    """Container for trained model and metadata."""

    model: xgb.XGBClassifier
    version: str
    trained_at: datetime
    feature_names: list[str]
    performance_metrics: dict[str, float]
    feature_importance: dict[str, float]
    optimal_threshold: float

    def save(self, path: str | Path) -> None:
        """Save model to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, path: str | Path) -> "TrainedModel":
        """Load model from disk."""
        path = Path(path)
        if not path.exists():
            raise ModelError(f"Model file not found: {path}")

        try:
            with open(path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            raise ModelError(f"Failed to load model from {path}: {str(e)}")


# Features used for training
TRAINING_FEATURES = [
    "current_month_transactions",
    "current_month_revenue",
    "total_tickets",
    "escalated_tickets",
    "late_payments",
    "enabled_channels",
    "self_service_percentage",
    "average_resolution_time_hours",
    "tenure_months",
    "transaction_change_pct",
    "revenue_change_pct",
    "days_since_last_touchbase",
    "ticket_escalation_rate",
    "revenue_per_transaction",
]


def train_model(
    df: pd.DataFrame,
    test_size: float = 0.2,
    model_version: str | None = None,
    random_state: int = 42,
) -> TrainedModel:
    """
    Train XGBoost churn prediction model.

    Args:
        df: Preprocessed DataFrame with features and 'churned' target
        test_size: Proportion of data for test set (default: 0.2)
        model_version: Semantic version string (default: auto-generated)
        random_state: Random seed for reproducibility

    Returns:
        TrainedModel with model, metrics, and metadata

    Raises:
        ModelError: If training fails

    Example:
        >>> df_processed = preprocess(df_raw)
        >>> trained_model = train_model(df_processed, test_size=0.2)
        >>> print(f"F2 Score: {trained_model.performance_metrics['f2_score']:.3f}")
    """
    if "churned" not in df.columns:
        raise ModelError(
            "Target column 'churned' not found in DataFrame. "
            "Ensure the data includes churn labels."
        )

    # Check for required features
    missing_features = set(TRAINING_FEATURES) - set(df.columns)
    if missing_features:
        raise ModelError(
            f"Missing required features: {sorted(missing_features)}. "
            f"Run preprocess() before training."
        )

    # Prepare features and target
    X = df[TRAINING_FEATURES].copy()
    y = df["churned"].copy()

    # Check class balance
    churn_rate = y.mean()
    if churn_rate < 0.01:
        raise ModelError(
            f"Churn rate is {churn_rate:.1%}, which is too low for training. "
            "Need at least 1% positive examples."
        )

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Calculate class weight for imbalance
    scale_pos_weight = (y_train == 0).sum() / (y_train == 1).sum()

    # Train XGBoost model
    try:
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            scale_pos_weight=scale_pos_weight,
            random_state=random_state,
            eval_metric="logloss",
            use_label_encoder=False,
        )

        model.fit(X_train, y_train)

    except Exception as e:
        raise ModelError(f"Model training failed: {str(e)}")

    # Get predictions on test set
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    # Find optimal threshold to maximize F2 score
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)
    f2_scores = (5 * precision * recall) / (4 * precision + recall + 1e-10)
    optimal_idx = np.argmax(f2_scores)
    optimal_threshold = thresholds[optimal_idx] if optimal_idx < len(thresholds) else 0.5

    # Get predictions with optimal threshold
    y_pred = (y_pred_proba >= optimal_threshold).astype(int)

    # Calculate metrics
    f2_score_value = fbeta_score(y_test, y_pred, beta=2)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall_value = recall_score(y_test, y_pred, zero_division=0)

    # Calculate PR-AUC manually
    precision_curve, recall_curve, _ = precision_recall_curve(y_test, y_pred_proba)
    pr_auc = np.trapz(precision_curve, recall_curve)

    performance_metrics = {
        "f2_score": float(f2_score_value),
        "precision": float(precision),
        "recall": float(recall_value),
        "pr_auc": float(pr_auc),
        "optimal_threshold": float(optimal_threshold),
        "test_size": len(X_test),
        "train_size": len(X_train),
        "churn_rate": float(churn_rate),
    }

    # Get feature importance
    feature_importance_values = model.feature_importances_
    feature_importance = dict(zip(TRAINING_FEATURES, feature_importance_values.tolist()))

    # Generate version
    if model_version is None:
        model_version = f"1.0.0-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    return TrainedModel(
        model=model,
        version=model_version,
        trained_at=datetime.now(),
        feature_names=TRAINING_FEATURES,
        performance_metrics=performance_metrics,
        feature_importance=feature_importance,
        optimal_threshold=optimal_threshold,
    )
