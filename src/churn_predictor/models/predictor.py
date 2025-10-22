"""Churn prediction and risk level mapping."""

from typing import Any

import pandas as pd

from churn_predictor.exceptions import ModelError
from churn_predictor.models.trainer import TrainedModel


def predict_churn(
    model: TrainedModel,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Generate churn probability scores and risk levels.

    Risk level mapping:
    - Low: 0-30
    - Medium: 31-69
    - High: 70-100

    Args:
        model: Trained model from train_model()
        df: Preprocessed DataFrame with features

    Returns:
        DataFrame with added columns:
        - churn_probability: Score 0-100
        - risk_level: "low", "medium", or "high"
        - confidence: Model confidence 0-1

    Raises:
        ModelError: If prediction fails

    Example:
        >>> predictions = predict_churn(trained_model, df_processed)
        >>> high_risk = predictions[predictions['risk_level'] == 'high']
        >>> print(f"Found {len(high_risk)} high-risk customers")
    """
    df = df.copy()

    # Check for required features
    missing_features = set(model.feature_names) - set(df.columns)
    if missing_features:
        raise ModelError(
            f"Missing required features for prediction: {sorted(missing_features)}. "
            f"Ensure data has been preprocessed with preprocess()."
        )

    # Extract features
    X = df[model.feature_names]

    # Get predictions
    try:
        # Probability of churning (class 1)
        probabilities = model.model.predict_proba(X)[:, 1]
    except Exception as e:
        raise ModelError(f"Prediction failed: {str(e)}")

    # Convert to 0-100 scale
    df["churn_probability"] = (probabilities * 100).round(2)

    # Map to risk levels
    df["risk_level"] = df["churn_probability"].apply(_map_risk_level)

    # Confidence is max probability
    df["confidence"] = probabilities.round(4)

    return df


def _map_risk_level(score: float) -> str:
    """Map churn probability to risk level."""
    if score < 31:
        return "low"
    elif score < 70:
        return "medium"
    else:
        return "high"
