# ML Pipeline API Contract

**Feature**: 001-churn-prediction-dashboard
**Type**: Python Module API (Internal)
**Date**: 2025-10-22

## Overview

This document defines the Python API contracts for the ML pipeline components. These are internal APIs used by the Lambda function and local CLI, not HTTP endpoints.

## 1. Data Loader API

**Module**: `churn_predictor.data.loader`

### load_csv()

```python
def load_csv(
    file_path: str | Path,
    validate: bool = True
) -> pd.DataFrame:
    """
    Load customer data from CSV file.

    Args:
        file_path: Path to CSV file (local or s3://)
        validate: Run validation checks (default True)

    Returns:
        DataFrame with customer records

    Raises:
        FileNotFoundError: If file doesn't exist
        ValidationError: If validation fails (when validate=True)
        ValueError: If CSV format invalid

    Example:
        >>> df = load_csv("data/raw/customers.csv")
        >>> df.shape
        (10000, 12)
    """
```

**Validation Performed** (when `validate=True`):
- File size < 100MB
- Required columns present
- No duplicate (account_id, month) pairs
- Numeric fields parseable
- At least 100 records

**Error Messages**:
- `"CSV file too large: {size}MB. Maximum 100MB allowed."`
- `"Missing required columns: {missing_cols}"`
- `"Duplicate records found for account_id={id}, month={month}"`
- `"Invalid numeric value in column {col}, row {row}"`

---

## 2. Data Validator API

**Module**: `churn_predictor.data.validator`

### validate_schema()

```python
def validate_schema(df: pd.DataFrame) -> ValidationResult:
    """
    Validate DataFrame schema and data quality.

    Args:
        df: Customer data DataFrame

    Returns:
        ValidationResult with is_valid, errors, warnings

    Example:
        >>> result = validate_schema(df)
        >>> if not result.is_valid:
        ...     print(result.errors)
    """
```

### ValidationResult (dataclass)

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]           # Blocking issues
    warnings: list[str]          # Non-blocking concerns
    row_count: int
    column_count: int
    churn_rate: float           # % of churned records
```

**Validation Checks**:

| Check | Type | Message |
|-------|------|---------|
| Required columns | Error | "Missing columns: {cols}" |
| Numeric ranges | Error | "{col} has values outside valid range" |
| Class balance | Warning | "Churn rate {rate}% is below 5% threshold" |
| Missing values | Warning | "{col} has {pct}% missing values" |
| Date format | Error | "Invalid date format in {col}" |

---

## 3. Preprocessor API

**Module**: `churn_predictor.data.preprocessor`

### preprocess()

```python
def preprocess(
    df: pd.DataFrame,
    include_target: bool = True
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """
    Engineer features and prepare data for modeling.

    Args:
        df: Raw customer DataFrame
        include_target: Include 'churned' column (False for scoring)

    Returns:
        Tuple of (processed_df, metadata)
        metadata contains: feature_names, preprocessing_steps, stats

    Example:
        >>> processed_df, metadata = preprocess(raw_df)
        >>> metadata['feature_names']
        ['tenure_months', 'transaction_change_pct', ...]
    """
```

**Derived Features Created**:
- `tenure_months`: Count distinct months per account
- `transaction_change_pct`: MoM change
- `revenue_change_pct`: MoM change
- `days_since_last_touchbase`: Recency
- `ticket_escalation_rate`: escalated / total
- `revenue_per_transaction`: revenue / transactions

**Preprocessing Steps**:
1. Sort by (account_id, month) for temporal features
2. Calculate derived features
3. Fill missing values (median for numeric, mode for categorical)
4. Cap outliers at 1st and 99th percentiles
5. Drop original date columns (keep derived recency)

---

## 4. Model Trainer API

**Module**: `churn_predictor.models.trainer`

### train_model()

```python
def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    hyperparameters: dict[str, Any] | None = None,
    use_class_weights: bool = True
) -> TrainedModel:
    """
    Train XGBoost churn prediction model.

    Args:
        X_train: Training features
        y_train: Training labels (0=active, 1=churned)
        hyperparameters: XGBoost params (None = use defaults)
        use_class_weights: Auto-calculate scale_pos_weight

    Returns:
        TrainedModel with model, metrics, feature_importance

    Example:
        >>> model = train_model(X_train, y_train)
        >>> model.metrics['f2_score']
        0.78
    """
```

### TrainedModel (dataclass)

```python
@dataclass
class TrainedModel:
    model: xgb.Booster              # Trained XGBoost model
    model_version: str               # Semver version
    trained_at: datetime
    hyperparameters: dict[str, Any]
    metrics: dict[str, float]        # f2_score, pr_auc, etc.
    feature_importance: dict[str, float]  # Feature -> importance
    optimal_threshold: float         # Tuned decision threshold

    def save(self, path: str | Path) -> None:
        """Save model and metadata to file"""

    @classmethod
    def load(cls, path: str | Path) -> "TrainedModel":
        """Load model from file"""
```

**Default Hyperparameters**:
```python
{
    'objective': 'binary:logistic',
    'eval_metric': 'aucpr',
    'max_depth': 6,
    'learning_rate': 0.1,
    'n_estimators': 100,
    'scale_pos_weight': <calculated from class ratio>,
    'subsample': 0.8,
    'colsample_bytree': 0.8
}
```

**Metrics Calculated**:
- `f2_score`: F-beta score (beta=2, weights recall higher)
- `precision`: Positive predictive value
- `recall`: True positive rate (critical for churn)
- `pr_auc`: Precision-recall AUC (not ROC-AUC)
- `lift_at_10pct`: Lift in top 10% scored customers
- `optimal_threshold`: Threshold maximizing F2 score

---

## 5. Predictor API

**Module**: `churn_predictor.models.predictor`

### predict_churn()

```python
def predict_churn(
    model: TrainedModel,
    X: pd.DataFrame,
    include_explanations: bool = True
) -> pd.DataFrame:
    """
    Generate churn predictions for customers.

    Args:
        model: Trained model from train_model()
        X: Customer features (same schema as training)
        include_explanations: Include top risk factors (SHAP)

    Returns:
        DataFrame with columns:
        - account_id
        - churn_probability (0-100)
        - risk_level ("low", "medium", "high")
        - confidence (0-1)
        - top_risk_factors (if include_explanations=True)

    Example:
        >>> predictions = predict_churn(model, X_new)
        >>> high_risk = predictions[predictions['risk_level'] == 'high']
        >>> len(high_risk)
        342
    """
```

**Risk Level Mapping**:
- `churn_probability 0-30` → `risk_level = "low"`
- `churn_probability 31-69` → `risk_level = "medium"`
- `churn_probability 70-100` → `risk_level = "high"`

**top_risk_factors Format**:
```python
[
    {"feature": "days_since_last_touchbase", "importance": 0.32},
    {"feature": "revenue_change_pct", "importance": 0.28},
    {"feature": "ticket_escalation_rate", "importance": 0.19}
]
```

---

## 6. Explainer API

**Module**: `churn_predictor.models.explainer`

### explain_predictions()

```python
def explain_predictions(
    model: xgb.Booster,
    X: pd.DataFrame,
    top_n: int = 3
) -> dict[str, list[dict]]:
    """
    Calculate SHAP values for predictions.

    Args:
        model: Trained XGBoost model
        X: Features to explain
        top_n: Number of top features per prediction

    Returns:
        Dict mapping account_id -> top risk factors

    Example:
        >>> explanations = explain_predictions(model.model, X)
        >>> explanations['ACC-0001']
        [{'feature': 'tenure_months', 'importance': 0.25}, ...]
    """
```

**Implementation Notes**:
- Uses TreeExplainer (fast for tree models)
- Returns absolute SHAP values (magnitude of impact)
- Normalizes to sum to 1.0 for top_n features

---

## 7. Recommendation Engine API

**Module**: `churn_predictor.analytics.recommendations`

### generate_recommendations()

```python
def generate_recommendations(
    predictions: pd.DataFrame,
    customer_data: pd.DataFrame,
    max_recommendations: int = 3
) -> pd.DataFrame:
    """
    Generate actionable recommendations for high-risk customers.

    Args:
        predictions: Output from predict_churn()
        customer_data: Original customer features
        max_recommendations: Max recommendations per customer

    Returns:
        DataFrame with columns:
        - account_id
        - action_type
        - priority (1-3)
        - description
        - rationale
        - estimated_impact

    Example:
        >>> recs = generate_recommendations(predictions, customer_data)
        >>> recs[recs['priority'] == 1]  # Highest priority
    """
```

**Recommendation Rules**:

| Condition | Action Type | Description |
|-----------|-------------|-------------|
| days_since_last_touchbase > 60 | immediate_contact | "Contact customer within 48 hours" |
| revenue_change_pct < -30% | offer_discount | "Consider retention pricing offer" |
| ticket_escalation_rate > 50% | review_service | "Schedule service quality review" |
| tenure_months < 3 | schedule_training | "Provide onboarding support" |
| Default (high risk) | immediate_contact | "Proactive outreach recommended" |

---

## 8. Storage Repository API

**Module**: `churn_predictor.storage.repositories`

### ChurnScoreRepository

```python
class ChurnScoreRepository:
    """DynamoDB repository for churn scores"""

    def save_scores(
        self,
        scores: pd.DataFrame,
        model_version: str
    ) -> int:
        """
        Save batch of churn scores to DynamoDB.

        Returns: Number of records saved
        """

    def get_score(
        self,
        account_id: str,
        score_date: date | None = None
    ) -> ChurnScore | None:
        """
        Get churn score for customer.

        If score_date is None, returns latest score.
        """

    def get_high_risk_customers(
        self,
        min_probability: float = 70.0,
        limit: int = 100
    ) -> list[ChurnScore]:
        """
        Query high-risk customers using GSI.

        Returns customers sorted by probability DESC.
        """
```

### ModelRepository

```python
class ModelRepository:
    """S3 repository for ML models"""

    def save_model(
        self,
        model: TrainedModel,
        is_active: bool = False
    ) -> str:
        """
        Save model to S3 and update metadata.

        Returns: S3 URI of saved model
        """

    def get_active_model(self) -> TrainedModel:
        """
        Load currently active model.

        Raises: ValueError if no active model exists
        """

    def list_models(
        self,
        limit: int = 10
    ) -> list[str]:
        """List model versions (newest first)"""
```

---

## Error Handling Patterns

### Exception Hierarchy

```python
class ChurnPredictorError(Exception):
    """Base exception for churn predictor"""

class ValidationError(ChurnPredictorError):
    """Data validation failed"""

class ModelError(ChurnPredictorError):
    """Model training/prediction error"""

class StorageError(ChurnPredictorError):
    """AWS storage operation failed"""
```

### Error Response Format

All functions return detailed error messages following this pattern:

```python
# Good error message
raise ValidationError(
    "CSV validation failed: Missing required columns ['account_id', 'month']. "
    "Expected 12 columns, found 10. "
    "See documentation: https://docs.example.com/csv-schema"
)

# Bad error message
raise ValidationError("Invalid CSV")
```

**Error Message Requirements**:
1. What went wrong
2. Why it's wrong
3. How to fix it (when possible)
4. Link to docs (for complex issues)

---

## CLI Interface

**Module**: `churn_predictor.cli.commands`

### Command: train

```bash
python -m churn_predictor.cli train \
    --data data/raw/customers.csv \
    --output models/model-v1.0.0.pkl \
    --test-size 0.2 \
    --upload-to-s3
```

**Options**:
- `--data`: Path to training CSV
- `--output`: Local save path
- `--test-size`: Train/test split ratio
- `--upload-to-s3`: Upload to S3 and mark active

### Command: score

```bash
python -m churn_predictor.cli score \
    --data data/raw/customers-new.csv \
    --model models/model-v1.0.0.pkl \
    --output scores/2025-10-22.csv \
    --write-to-dynamodb
```

**Options**:
- `--data`: Path to customer CSV
- `--model`: Model path (or "active" for latest)
- `--output`: Save predictions to CSV
- `--write-to-dynamodb`: Write to DynamoDB table

### Command: evaluate

```bash
python -m churn_predictor.cli evaluate \
    --model models/model-v1.0.0.pkl \
    --test-data data/test/holdout.csv \
    --report reports/evaluation.html
```

**Options**:
- `--model`: Model to evaluate
- `--test-data`: Holdout test set
- `--report`: Output HTML report

---

## Testing Contract

### Unit Test Coverage Requirements

**Minimum 80% line coverage** for:
- `data.loader`
- `data.validator`
- `data.preprocessor`
- `models.predictor`
- `analytics.recommendations`

**Minimum 60% line coverage** for:
- `models.trainer` (harder to test ML training)

### Integration Test Requirements

1. **End-to-end pipeline test**: CSV → trained model → predictions → DynamoDB
2. **AWS integration test**: S3 upload/download, DynamoDB read/write
3. **Error path tests**: Invalid CSV, missing columns, model load failure

### Test Fixtures

Location: `tests/fixtures/`

Required fixtures:
- `sample_data.csv`: 100 customer records (10% churned)
- `invalid_data.csv`: CSV with validation errors
- `trained_model.pkl`: Pre-trained model for testing

---

## Performance Benchmarks

**Target Execution Times** (on Lambda 1GB memory):

| Operation | Target | Measurement |
|-----------|--------|-------------|
| Load 10k CSV | <5 sec | Time to DataFrame |
| Preprocess 10k | <10 sec | Feature engineering |
| Train model (10k) | <60 sec | Full training loop |
| Score 10k customers | <15 sec | Prediction + SHAP |
| Write to DynamoDB | <30 sec | Batch write 10k records |
| **Total pipeline** | **<120 sec** | CSV to DynamoDB |

**Memory Constraints**:
- Peak memory < 800MB (for 1GB Lambda)
- Process in chunks if >50k customers

---

## Versioning Strategy

**Semantic Versioning** for models:
- **Major** (1.0.0 → 2.0.0): Breaking changes to features or data schema
- **Minor** (1.0.0 → 1.1.0): New features added, backward compatible
- **Patch** (1.0.0 → 1.0.1): Hyperparameter tuning, bug fixes

**Example**:
- v1.0.0: Initial model with 12 features
- v1.1.0: Added derived features (tenure, changes)
- v2.0.0: Changed churn window from 90 days to 60 days (breaking)

**Model metadata** stored in DynamoDB tracks full lineage.
