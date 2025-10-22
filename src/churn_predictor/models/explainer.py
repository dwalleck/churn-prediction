"""Model explainability using SHAP values."""

from typing import Any

import pandas as pd
import shap

from churn_predictor.exceptions import ModelError
from churn_predictor.models.trainer import TrainedModel


def explain_predictions(
    model: TrainedModel,
    df: pd.DataFrame,
    top_n: int = 3,
) -> pd.DataFrame:
    """
    Generate feature importance explanations for predictions using SHAP.

    Args:
        model: Trained model from train_model()
        df: Preprocessed DataFrame with features (must include predictions)
        top_n: Number of top risk factors to return per customer (default: 3)

    Returns:
        DataFrame with added column:
        - top_risk_factors: List of dicts with feature and importance

    Raises:
        ModelError: If explanation generation fails

    Example:
        >>> df_explained = explain_predictions(trained_model, df_predictions)
        >>> print(df_explained.iloc[0]['top_risk_factors'])
        [
            {"feature": "days_since_last_touchbase", "importance": 0.32},
            {"feature": "revenue_change_pct", "importance": 0.28},
            {"feature": "ticket_escalation_rate", "importance": 0.19}
        ]
    """
    df = df.copy()

    # Check for required features
    missing_features = set(model.feature_names) - set(df.columns)
    if missing_features:
        raise ModelError(
            f"Missing required features for explanation: {sorted(missing_features)}. "
            f"Ensure data has been preprocessed."
        )

    # Extract features and ensure numeric types
    X = df[model.feature_names].copy()

    # Convert all columns to numeric, replacing any non-numeric values
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors='coerce')

    # Fill any NaN values with 0
    X = X.fillna(0)

    try:
        # Create SHAP explainer
        explainer = shap.TreeExplainer(model.model)

        # Calculate SHAP values
        shap_values = explainer.shap_values(X)

        # For each customer, get top N features by absolute SHAP value
        top_risk_factors = []

        for i in range(len(X)):
            # Get absolute SHAP values for this customer
            customer_shap = shap_values[i]
            abs_shap = abs(customer_shap)

            # Get indices of top N features
            top_indices = abs_shap.argsort()[-top_n:][::-1]

            # Build list of risk factors
            factors = []
            total_abs_importance = abs_shap.sum()

            for idx in top_indices:
                feature_name = model.feature_names[idx]
                importance_value = abs_shap[idx]

                # Normalize importance as percentage of total
                normalized_importance = (
                    importance_value / total_abs_importance if total_abs_importance > 0 else 0
                )

                factors.append({
                    "feature": feature_name,
                    "importance": round(float(normalized_importance), 4),
                })

            top_risk_factors.append(factors)

        df["top_risk_factors"] = top_risk_factors

    except Exception as e:
        raise ModelError(f"SHAP explanation failed: {str(e)}")

    return df
