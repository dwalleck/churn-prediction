# Customer Churn Prediction Dashboard

A complete machine learning system that predicts customer churn probability and provides actionable insights through an interactive dashboard with AWS deployment support.

## Features

### ML Pipeline
- **XGBoost Models**: Train models with class weighting and F2 score optimization
- **Churn Scoring**: Generate 0-100 churn probability scores
- **Risk Levels**: Automatic classification (low/medium/high)
- **Explainability**: SHAP-based feature importance for each prediction
- **Feature Engineering**: 6 derived features (tenure, MoM changes, recency, escalation rate, etc.)

### Interactive Dashboard (Streamlit)
- **Home**: Summary metrics and risk distribution
- **High-Risk Customers**: Interactive filtering, customer details, actionable recommendations
- **Churn Drivers**: Feature importance visualization and distribution analysis
- **Churn Reasons**: Historical churn patterns and trend analysis

### Recommendation Engine
- Rule-based actionable recommendations for high-risk customers
- Priority-based action plans
- 5 recommendation types: immediate contact, discount offers, service review, training, contract renewal

### AWS Deployment
- **Lambda**: Serverless ML pipeline triggered by S3 uploads
- **Fargate**: Containerized dashboard with auto-scaling
- **DynamoDB**: Fast customer score lookups with GSI
- **S3**: Model artifacts and data storage

## Quick Start (< 5 minutes)

### 1. Install Dependencies

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### 2. Train Model

```bash
python -m churn_predictor.cli train \
    --data sample-data.csv \
    --output data/models/model-v1.pkl
```

Expected output:
```
Loading data from sample-data.csv...
✓ Loaded 1000 customer records
Validating data...
✓ Validation passed
Preprocessing data...
✓ Preprocessed data with 20 features
Training model...
✓ Model trained successfully
  F2 Score: 0.XXX
  Precision: 0.XXX
  Recall: 0.XXX
  PR-AUC: 0.XXX
Saving model to data/models/model-v1.pkl...
✓ Model saved successfully
```

### 3. Generate Predictions

```bash
python -m churn_predictor.cli score \
    --data sample-data.csv \
    --model data/models/model-v1.pkl \
    --output data/scores/latest.csv
```

### 4. Launch Dashboard

```bash
streamlit run src/dashboard/app.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`

## Project Structure

```
churn-prediction/
├── src/
│   ├── churn_predictor/      # ML pipeline
│   │   ├── data/              # Data loading and preprocessing
│   │   ├── models/            # Model training and prediction
│   │   ├── storage/           # Data storage layer
│   │   └── cli/               # Command-line interface
│   └── dashboard/             # Streamlit dashboard
│       ├── app.py             # Main dashboard page
│       └── pages/             # Multi-page views
├── data/
│   ├── raw/                   # Input CSV files
│   ├── models/                # Trained models
│   └── scores/                # Generated predictions
├── tests/                     # Test suite
├── sample-data.csv            # Sample customer data
├── pyproject.toml             # Dependencies
└── README.md                  # This file
```

## CLI Commands

### Generate Synthetic Data

```bash
python -m churn_predictor.cli generate-data --output data.csv --customers 1000 --churn-rate 0.15
```

### Train a Model

```bash
python -m churn_predictor.cli train --data <csv_file> --output <model_file>
```

### Generate Scores

```bash
python -m churn_predictor.cli score --data <csv_file> --model <model_file> --output <scores_file>
```

### Validate Data

```bash
python -m churn_predictor.cli validate --data <csv_file>
```

### Compare Models

```bash
python scripts/compare_models.py model1.pkl model2.pkl model3.pkl
```

## Dashboard Pages

### 1. Home
- Summary metrics (total customers, risk distribution)
- Risk level breakdown
- Quick statistics

### 2. High Risk Customers
- Score threshold slider (default: 70)
- Max results selector (20/50/100/200)
- Interactive customer list with sortable columns
- Detailed customer view with:
  - Churn probability and confidence
  - Tenure and revenue metrics
  - Top risk factors (SHAP-based)
  - Actionable recommendations with priority levels

### 3. Churn Drivers
- Model performance metrics (F2, Precision, Recall, PR-AUC)
- Top N feature importance visualization (interactive)
- Feature distribution analysis by risk level
- Statistical insights and comparisons
- Strategic recommendations

### 4. Churn Reasons
- Historical churn event analysis
- Churn reason categorization (6 categories)
- Date range filtering
- Summary metrics (total churned, avg tenure, revenue lost)
- Visualizations:
  - Pie chart of reason distribution
  - Trend line over time
  - Reasons by customer tenure
- Top 3 reasons with percentages
- Detailed event table

## Data Format

The system expects CSV files with the following columns:

**Required Columns:**
- `account_id`: Customer identifier
- `month`: Data snapshot month (YYYY-MM)
- `current_month_transactions`: Transaction count
- `current_month_revenue`: Revenue ($)
- `total_tickets`: Support tickets
- `escalated_tickets`: Escalated tickets
- `late_payments`: Late payment count
- `enabled_channels`: Active channels
- `self_service_percentage`: Self-service usage (%)
- `last_touchbase_date`: Last interaction timestamp
- `average_resolution_time_hours`: Avg support resolution time
- `churned`: Churn label (0=active, 1=churned)

**Derived Features** (automatically calculated):
- `tenure_months`: Customer age
- `transaction_change_pct`: MoM transaction change
- `revenue_change_pct`: MoM revenue change
- `days_since_last_touchbase`: Days since last contact
- `ticket_escalation_rate`: Escalation percentage
- `revenue_per_transaction`: Average transaction value

## Model Details

- **Algorithm**: XGBoost with class weighting
- **Optimization Metric**: F2 score (prioritizes recall)
- **Evaluation**: PR-AUC on hold-out test set
- **Explainability**: SHAP TreeExplainer for feature importance

## Development

### Run Tests

```bash
# Unit tests
pytest tests/unit/ -v

# All tests
pytest tests/ -v --cov=src
```

### Code Quality

```bash
# Linting
ruff check .

# Type checking
mypy src/
```

## AWS Deployment

### Prerequisites

1. **AWS Account** with configured credentials
2. **Create S3 Buckets**:
   ```bash
   aws s3 mb s3://your-churn-data-bucket
   aws s3 mb s3://your-churn-models-bucket
   ```

3. **Create DynamoDB Tables**:
   ```bash
   python scripts/deploy/create_dynamodb_tables.py
   ```

4. **Configure Environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your AWS configuration
   ```

### Deploy Lambda Function

```bash
# Build and deploy ML scoring pipeline
./scripts/deploy/deploy_lambda.sh
```

### Deploy Dashboard to Fargate

```bash
# Build Docker image and deploy to ECS
./scripts/deploy/deploy_fargate.sh
```

### Production Workflow

1. Upload CSV to S3: `s3://bucket/uploads/customers.csv`
2. Lambda automatically processes and scores
3. Results written to DynamoDB
4. Dashboard displays updated scores

## Recommendation Engine

The system generates actionable recommendations based on customer risk factors:

### Action Types

1. **Immediate Contact** (Priority 1)
   - Triggered by: >60 days since last touchbase
   - Action: Reach out within 24-48 hours

2. **Offer Discount** (Priority 2)
   - Triggered by: >30% revenue decline
   - Action: Retention discount or value-add services

3. **Review Service** (Priority 1)
   - Triggered by: >50% ticket escalation rate
   - Action: Service quality review call

4. **Schedule Training** (Priority 2)
   - Triggered by: <3 months tenure
   - Action: Product training or onboarding check-in

5. **Contract Renewal** (Priority 2)
   - Triggered by: 11-13 months tenure
   - Action: Proactive renewal discussion

## Testing

### Run Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_validator.py -v

# Run with coverage
pytest tests/unit/ --cov=src --cov-report=html
```

### Test Files

- `test_validator.py`: Data validation logic
- `test_preprocessor.py`: Feature engineering
- `test_recommendations.py`: Recommendation engine

## Troubleshooting

### "No prediction data found"

Run the scoring pipeline first:
```bash
python -m churn_predictor.cli score --data sample-data.csv --model data/models/model-v1.pkl
```

### "Module not found"

Ensure you're in the virtual environment and have installed the package:
```bash
source .venv/bin/activate
uv pip install -e .
```

### "File not found: data/models/..."

Create the directory structure:
```bash
mkdir -p data/{raw,processed,models,scores}
```

## Next Steps

- See `specs/001-churn-prediction-dashboard/quickstart.md` for more detailed usage
- Check `specs/001-churn-prediction-dashboard/contracts/` for API documentation
- Review `specs/001-churn-prediction-dashboard/research.md` for technical decisions

## License

[Your License Here]
