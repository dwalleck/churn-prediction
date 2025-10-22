"""Local file-based storage for development."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from churn_predictor.exceptions import StorageError


class LocalStorage:
    """Local file storage for churn scores and predictions."""

    def __init__(self, data_dir: str | Path = "data"):
        self.data_dir = Path(data_dir)
        self.scores_dir = self.data_dir / "scores"
        self.models_dir = self.data_dir / "models"

        # Create directories
        self.scores_dir.mkdir(parents=True, exist_ok=True)
        self.models_dir.mkdir(parents=True, exist_ok=True)

    def save_scores(self, df: pd.DataFrame, filename: str = "latest.csv") -> Path:
        """Save churn scores to CSV file."""
        try:
            filepath = self.scores_dir / filename
            df.to_csv(filepath, index=False)
            return filepath
        except Exception as e:
            raise StorageError(f"Failed to save scores: {str(e)}", resource=str(filepath))

    def load_scores(self, filename: str = "latest.csv") -> pd.DataFrame:
        """Load churn scores from CSV file."""
        try:
            filepath = self.scores_dir / filename
            if not filepath.exists():
                raise StorageError(
                    f"Scores file not found: {filepath}. "
                    f"Run scoring first to generate predictions.",
                    resource=str(filepath),
                )
            return pd.read_csv(filepath)
        except StorageError:
            raise
        except Exception as e:
            raise StorageError(f"Failed to load scores: {str(e)}", resource=str(filepath))

    def get_high_risk_customers(self, threshold: int = 70, limit: int = 100) -> pd.DataFrame:
        """Get high-risk customers from latest scores."""
        df = self.load_scores()

        if "churn_probability" not in df.columns:
            raise StorageError(
                "Scores file missing 'churn_probability' column. "
                "Ensure predictions have been generated."
            )

        high_risk = df[df["churn_probability"] >= threshold]
        high_risk = high_risk.sort_values("churn_probability", ascending=False)
        return high_risk.head(limit)
