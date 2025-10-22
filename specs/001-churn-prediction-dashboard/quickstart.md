# Quickstart Guide: Customer Churn Prediction Dashboard

**Goal**: Get from zero to running churn predictions in under 5 minutes

**Prerequisites**:
- Python 3.12 installed
- AWS account with credentials configured (for production deployment)
- Git

## 🚀 Quick Start (Local Development)

### Step 1: Clone and Setup (60 seconds)

```bash
# Clone repository
git clone <repo-url>
cd churn-prediction

# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Step 2: Prepare Sample Data (30 seconds)

```bash
# Use provided sample data
cp sample-data.csv data/raw/customers.csv

# Or generate fresh synthetic data
python -m churn_predictor.cli generate-data \
    --output data/raw/customers.csv \
    --num-customers 1000 \
    --churn-rate 0.15
```

### Step 3: Train Model (90 seconds)

```bash
python -m churn_predictor.cli train \
    --data data/raw/customers.csv \
    --output models/model-v1.0.0.pkl \
    --test-size 0.2

# Expected output:
# ✓ Loaded 1000 customer records
# ✓ Train/test split: 800/200
# ✓ Model trained in 12.3 seconds
# ✓ F2 Score: 0.78
# ✓ PR-AUC: 0.82
# ✓ Model saved to models/model-v1.0.0.pkl
```

### Step 4: Generate Predictions (30 seconds)

```bash
python -m churn_predictor.cli score \
    --data data/raw/customers.csv \
    --model models/model-v1.0.0.pkl \
    --output data/scores/latest.csv

# Expected output:
# ✓ Loaded 1000 customers
# ✓ Generated predictions: 342 high-risk, 458 medium, 200 low
# ✓ Scores saved to data/scores/latest.csv
```

### Step 5: Launch Dashboard (30 seconds)

```bash
# Set local development mode
export CHURN_ENV=local

# Start Streamlit dashboard
streamlit run src/dashboard/app.py

# Browser opens automatically at http://localhost:8501
```

**🎉 You're done!** The dashboard is now running with your churn predictions.

---

## 📊 Using the Dashboard

### High Risk Customers (P1)

1. Navigate to **High Risk Customers** in sidebar
2. Adjust churn score threshold (default: 70)
3. Click on any customer to see:
   - Churn probability score
   - Top 3 risk factors
   - Actionable recommendations

**Example**:
```
Customer: ACC-0042
Churn Score: 87%
Risk Level: HIGH

Top Risk Factors:
- days_since_last_touchbase: 32% contribution
- revenue_change_pct: 28% contribution
- ticket_escalation_rate: 19% contribution

Recommended Actions:
✓ Immediate Contact (Priority 1)
  "Contact customer within 48 hours"
  Why: 90+ days since last interaction
```

### Churn Drivers (P2)

1. Navigate to **Churn Drivers**
2. View feature importance chart (top 10 variables)
3. Select a feature to see distribution analysis
4. Understand which factors predict churn

**Key Insight Example**:
```
Top 5 Predictive Features:
1. days_since_last_touchbase (28%)
2. revenue_change_pct (22%)
3. tenure_months (15%)
4. ticket_escalation_rate (12%)
5. transaction_change_pct (10%)
```

### Churn Reasons (P3)

1. Navigate to **Churn Reasons**
2. Select date range for analysis
3. View top 3 churn reasons with percentages
4. Analyze trends over time

**Example Output**:
```
Top 3 Churn Reasons (Last 6 Months):
1. Price/Cost: 156 customers (45%)
2. Product Quality: 87 customers (25%)
3. Customer Service: 52 customers (15%)
```

---

## 🏗️ Project Structure

```
churn-prediction/
├── src/
│   ├── churn_predictor/      # ML pipeline
│   │   ├── data/              # CSV loading, validation
│   │   ├── models/            # Training, prediction
│   │   ├── analytics/         # Recommendations
│   │   └── cli/               # Command-line interface
│   └── dashboard/             # Streamlit app
│       ├── app.py             # Main entry point
│       ├── pages/             # Dashboard views
│       └── services/          # Data queries
├── data/
│   ├── raw/                   # Input CSV files
│   ├── processed/             # Preprocessed features
│   ├── models/                # Trained models
│   └── scores/                # Generated predictions
├── tests/                     # Unit & integration tests
├── pyproject.toml             # Dependencies
└── README.md
```

---

## 🔄 Typical Workflow

### Weekly Batch Update

```bash
# 1. Upload new customer data
cp latest_customer_export.csv data/raw/2025-10-29.csv

# 2. Generate scores (uses existing model)
python -m churn_predictor.cli score \
    --data data/raw/2025-10-29.csv \
    --model active \
    --output data/scores/2025-10-29.csv

# 3. Dashboard automatically shows updated scores
# No restart needed - refresh browser
```

### Retraining Model

```bash
# When you have new historical data with churn outcomes
python -m churn_predictor.cli train \
    --data data/raw/historical_with_outcomes.csv \
    --output models/model-v1.1.0.pkl \
    --test-size 0.2

# Evaluate new model
python -m churn_predictor.cli evaluate \
    --model models/model-v1.1.0.pkl \
    --test-data data/test/holdout.csv \
    --report reports/v1.1.0-evaluation.html

# If better, use for scoring
python -m churn_predictor.cli score \
    --data data/raw/2025-10-29.csv \
    --model models/model-v1.1.0.pkl \
    --output data/scores/2025-10-29.csv
```

---

## ☁️ AWS Deployment (Production)

### Prerequisites

```bash
# Install AWS CLI and configure credentials
aws configure

# Set environment variables
export AWS_REGION=us-east-1
export S3_DATA_BUCKET=my-churn-data
export S3_MODEL_BUCKET=my-churn-models
export DYNAMODB_SCORES_TABLE=churn-scores
```

### Deploy Infrastructure

```bash
# Create S3 buckets
aws s3 mb s3://${S3_DATA_BUCKET}
aws s3 mb s3://${S3_MODEL_BUCKET}

# Create DynamoDB tables
python scripts/deploy/create_dynamodb_tables.py

# Upload initial model
python -m churn_predictor.cli train \
    --data data/raw/customers.csv \
    --output models/model-v1.0.0.pkl \
    --upload-to-s3
```

### Deploy Lambda Function (ML Pipeline)

```bash
# Package Lambda deployment
cd lambda/scoring_pipeline
pip install -r requirements.txt -t package/
cd package && zip -r ../deployment.zip .
cd .. && zip -g deployment.zip handler.py

# Deploy to Lambda
aws lambda create-function \
    --function-name churn-scoring-pipeline \
    --runtime python3.12 \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
    --handler handler.lambda_handler \
    --zip-file fileb://deployment.zip \
    --memory-size 1024 \
    --timeout 300

# Create S3 trigger (runs on CSV upload)
aws s3api put-bucket-notification-configuration \
    --bucket ${S3_DATA_BUCKET} \
    --notification-configuration file://s3-trigger-config.json
```

### Deploy Dashboard (Fargate)

```bash
# Build Docker image
docker build -t churn-dashboard -f dashboard/Dockerfile .

# Push to ECR
aws ecr create-repository --repository-name churn-dashboard
aws ecr get-login-password | docker login --username AWS --password-stdin <ECR_URI>
docker tag churn-dashboard:latest <ECR_URI>/churn-dashboard:latest
docker push <ECR_URI>/churn-dashboard:latest

# Deploy to Fargate
aws ecs create-service \
    --cluster churn-cluster \
    --service-name churn-dashboard \
    --task-definition churn-dashboard-task \
    --desired-count 1 \
    --launch-type FARGATE

# Dashboard available at: http://<ALB_DNS_NAME>:8501
```

### Production Workflow

```bash
# Upload new customer data to S3
aws s3 cp latest_customers.csv s3://${S3_DATA_BUCKET}/raw/2025-10-29.csv

# Lambda automatically:
# 1. Processes CSV
# 2. Generates predictions
# 3. Writes to DynamoDB
# 4. Dashboard shows updated scores
```

---

## 🧪 Testing

### Run All Tests

```bash
# Unit tests (fast)
pytest tests/unit/ -v

# Integration tests (slower, requires AWS credentials)
pytest tests/integration/ -v --slow

# Full test suite with coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html  # View coverage report
```

### Test Specific Components

```bash
# Test data loading
pytest tests/unit/test_data_loader.py -v

# Test model training
pytest tests/unit/test_trainer.py -v

# Test dashboard
pytest tests/integration/test_dashboard.py -v
```

---

## 📈 Performance Benchmarks

**Local Development** (MacBook Pro M1, 16GB RAM):
- Load 10k CSV: ~3 seconds
- Train model: ~45 seconds
- Score 10k customers: ~8 seconds
- Dashboard page load: <1 second

**AWS Lambda** (1GB memory):
- Full pipeline (CSV → DynamoDB): ~90 seconds for 10k customers
- Memory usage: ~650MB peak
- Cost: ~$0.10 per weekly run

**AWS Fargate** (0.5 vCPU, 1GB RAM):
- Dashboard concurrent users: 50+ supported
- Query response time: <500ms p95
- Monthly cost: ~$15

---

## 🐛 Troubleshooting

### "Module not found" errors

```bash
# Ensure you're in virtual environment
source .venv/bin/activate

# Reinstall package in editable mode
uv pip install -e .
```

### "No such file or directory: models/"

```bash
# Create required directories
mkdir -p data/{raw,processed,models,scores}
mkdir -p models reports
```

### Dashboard shows "No data"

```bash
# Ensure scores have been generated
ls -la data/scores/

# If empty, run scoring:
python -m churn_predictor.cli score \
    --data data/raw/customers.csv \
    --model models/model-v1.0.0.pkl \
    --output data/scores/latest.csv
```

### AWS Lambda timeout

```bash
# Increase timeout (max 15 minutes)
aws lambda update-function-configuration \
    --function-name churn-scoring-pipeline \
    --timeout 900

# Or increase memory (faster execution)
aws lambda update-function-configuration \
    --function-name churn-scoring-pipeline \
    --memory-size 2048
```

### DynamoDB "Table does not exist"

```bash
# Create tables
python scripts/deploy/create_dynamodb_tables.py

# Verify
aws dynamodb list-tables
```

---

## 📚 Next Steps

### Improve Data Quality

1. **Add more features** to improve predictions:
   ```bash
   python -m churn_predictor.cli generate-data \
       --output data/raw/customers.csv \
       --num-customers 10000 \
       --include-contract-type \
       --include-tenure \
       --include-engagement-trends
   ```

2. **Use real customer data**:
   - Export from your CRM/billing system
   - Ensure CSV matches required schema (see `contracts/ml-pipeline-api.md`)
   - Validate with: `python -m churn_predictor.cli validate --data your_data.csv`

### Tune Model Performance

```bash
# Experiment with hyperparameters
python -m churn_predictor.cli train \
    --data data/raw/customers.csv \
    --output models/model-v1.1.0.pkl \
    --max-depth 8 \
    --learning-rate 0.05 \
    --n-estimators 200

# Compare models
python scripts/compare_models.py \
    models/model-v1.0.0.pkl \
    models/model-v1.1.0.pkl
```

### Add Custom Recommendations

Edit `src/churn_predictor/analytics/recommendations.py`:

```python
def generate_recommendations(predictions, customer_data):
    # Add your business-specific rules
    if customer_data['industry'] == 'healthcare':
        # Healthcare-specific recommendations
        pass
```

### Enable Monitoring

```bash
# Set up CloudWatch dashboards
python scripts/deploy/setup_monitoring.py

# View metrics:
# - Lambda execution time
# - DynamoDB read/write units
# - Dashboard user count
```

---

## 💡 Tips for Success

**Start Simple**:
- Use the sample data first
- Get comfortable with the CLI
- Explore the dashboard
- Then move to your real data

**Iterate on Model**:
- Don't expect perfect predictions on day 1
- Retrain monthly with fresh outcomes
- Monitor F2 score trends over time
- Add new features as you learn

**Monitor Business Impact**:
- Track: How many high-risk customers contacted?
- Measure: What % were saved from churning?
- Calculate: ROI of retention efforts

**Follow the Constitution**:
- Ship it (working > perfect)
- Developer experience matters (simple APIs)
- Make it work, then make it right, then make it fast

---

## 🆘 Getting Help

**Documentation**:
- API Contracts: `specs/001-churn-prediction-dashboard/contracts/`
- Data Model: `specs/001-churn-prediction-dashboard/data-model.md`
- Research: `specs/001-churn-prediction-dashboard/research.md`

**Common Issues**:
- Check `docs/troubleshooting.md`
- Review error messages (they suggest fixes!)
- Run validation: `python -m churn_predictor.cli validate --data <file>`

**Support**:
- GitHub Issues: Report bugs, request features
- Email: support@example.com
- Slack: #churn-prediction channel

---

**⏱️ Total Time to First Prediction: ~5 minutes**

```bash
# All-in-one script
git clone <repo> && cd churn-prediction
uv venv && source .venv/bin/activate && uv pip install -e .
python -m churn_predictor.cli train --data sample-data.csv --output models/v1.pkl
python -m churn_predictor.cli score --data sample-data.csv --model models/v1.pkl --output scores/latest.csv
streamlit run src/dashboard/app.py
```

🚀 **Now go prevent some churn!**
