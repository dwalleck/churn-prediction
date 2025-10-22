# Research: Customer Churn Prediction Dashboard

**Date**: 2025-10-22
**Feature**: 001-churn-prediction-dashboard

## 1. Churn Modeling Best Practices

### Decision: Gradient Boosting (XGBoost/LightGBM) with Class Weighting and Temporal Validation

### Rationale:
Churn prediction differs fundamentally from typical ML problems due to severe class imbalance (typically 5-20% churn rate), temporal dependencies in customer behavior, and asymmetric business costs (losing a customer is far more expensive than a retention campaign). Recent 2025 research consistently shows that gradient boosting algorithms with proper imbalance handling outperform other approaches for tabular churn data while remaining computationally efficient and interpretable.

### Key Practices:

**1. Algorithm Selection:**
- **Primary**: XGBoost or LightGBM - both excel with tabular data, handle class imbalance natively, provide feature importance, and are computationally efficient
- **Baseline**: Logistic Regression - simple, interpretable, fast to train, good for establishing baseline performance
- XGBoost has demonstrated high classification accuracy with built-in class imbalance handling in recent benchmarks

**2. Handling Class Imbalance:**
- **Class Weights**: Set `scale_pos_weight` parameter to ratio of negative/positive cases (e.g., 9:1 for 10% churn rate)
- **SMOTE (Synthetic Minority Over-sampling)**: Generates synthetic examples of minority class - proven effective in 2025 research when combined with ensemble methods
- **Threshold Tuning**: Adjust decision threshold based on business costs rather than default 0.5
- **Avoid aggressive undersampling**: Research shows you don't need 50/50 balance; class weights often work better

**3. Feature Engineering for Churn:**

**RFM Features (Time-Varying):**
- **Recency**: Days since last transaction/touchpoint
- **Frequency**: Transaction count over multiple time windows (7/30/90 days)
- **Monetary**: Revenue trends, average transaction value
- Research shows RFM features with temporal modeling (e.g., 3-month rolling windows) significantly improve prediction

**Behavioral Trends:**
- **Engagement trajectory**: Declining transaction counts month-over-month
- **Revenue velocity**: Rate of change in spending
- **Channel diversity**: Number of active communication channels
- **Self-service adoption**: Percentage of issues resolved without support

**Tenure & Lifecycle:**
- Customer age/tenure
- Contract type and renewal dates
- Product/feature adoption rate

**Support Interaction Patterns:**
- Support ticket frequency and escalation rates
- Average resolution time trends
- Time since last touchpoint
- Late payment patterns

**4. Evaluation Metrics:**
- **Primary**: **Precision-Recall AUC** (PR-AUC) - preferred over ROC-AUC for imbalanced datasets
- **Business Metric**: **F2 Score** - weights recall 2x higher than precision, reflecting that false negatives (missed churners) cost more than false positives
- **Targeting Efficiency**: **Lift** - how much better than random targeting in top deciles
- **Never use accuracy alone** - misleading with class imbalance (95% accuracy from predicting "no churn" for everyone)

**5. Time-Based Validation:**
- **Temporal Splits**: Train on months 1-6, validate on month 7, test on month 8+
- **Never use random train/test splits** - causes data leakage and overly optimistic metrics
- **Walk-forward validation**: Simulate real deployment by always predicting future from past
- Evaluate stability of lift/gain metrics across time periods

**6. Model Training Strategy:**
```python
# Pseudocode for recommended approach
- Use 3-6 months of historical data per customer
- Create features from months T-3 to T-1
- Predict churn in month T
- Apply class weights: scale_pos_weight = (# non-churners / # churners)
- Optimize threshold based on business costs
- Target precision >80% for retention campaigns
```

### Alternatives Considered:

**Deep Learning (LSTM/GRU):**
- **Why not chosen**: Requires significantly more data, longer training time, less interpretable
- **When to consider**: If you have >100k customers with rich sequential behavioral data
- Research shows classic RNNs can outperform transformers for time-varying RFM features, but only worthwhile at scale

**Survival Analysis:**
- **Why not chosen**: More complex to implement and explain to stakeholders
- **When to consider**: If you need time-to-churn predictions, not just binary churn/no-churn
- Excellent for understanding churn dynamics but harder to operationalize

**Pure SMOTE/Oversampling:**
- **Why not chosen**: Research shows class weights often perform as well or better with less complexity
- Can use SMOTE as enhancement, but start with simpler class weighting

---

## 2. Dashboard Framework

### Decision: Streamlit

### Rationale:
Streamlit aligns perfectly with the project constitution's emphasis on "ship it" and "developer experience is a feature." It enables building functional dashboards in under 5 minutes, has excellent data table support via `st.dataframe()`, built-in multi-page apps, strong AWS deployment options, and the lowest learning curve of all options. For a 10k customer dataset with 50 concurrent users, Streamlit's performance is more than adequate.

**Key Advantages for This Project:**
- **5-minute setup**: `pip install streamlit && streamlit run app.py` - literally nothing else needed
- **Multi-page support**: Native `pages/` directory structure introduced in 2023, perfect for dashboard views
- **Data tables**: `st.dataframe()` and `st.data_editor()` provide filtering, sorting, and interaction out of the box
- **Visualization**: Built-in Plotly integration for charts, supports Matplotlib, Altair
- **AWS deployment**: Works on EC2, ECS Fargate, or Streamlit Community Cloud
- **Iteration speed**: Hot reload, pure Python (no HTML/CSS/JavaScript), rapid prototyping

**Framework Comparison Summary:**

| Feature | Streamlit | Dash | Gradio |
|---------|-----------|------|--------|
| **Time to Hello World** | 5 min | 20 min | 10 min |
| **Multi-page apps** | Native `pages/` | Manual routing | Limited |
| **Data tables** | Excellent | Good (requires more code) | Basic |
| **Customization** | Good (components) | Excellent | Limited |
| **Dashboard use case** | Excellent | Excellent | Poor (ML demos) |
| **Learning curve** | Lowest | Moderate | Low |
| **Enterprise scale** | Good (up to mid-size) | Excellent | Limited |
| **AWS deployment** | Easy | Easy | Easy |

### Alternatives Considered:

**Dash (Plotly):**
- **Strengths**: More customizable, better for complex enterprise dashboards, production-grade at scale
- **Why not chosen**: 4x more code for same functionality, slower development, overkill for 10k customers/50 users
- **When to reconsider**: If you need >200 concurrent users or highly custom visualizations

**Gradio:**
- **Strengths**: Fastest for ML model demos, now backed by Hugging Face
- **Why not chosen**: Not designed for dashboards - optimized for "inputs → ML model → outputs" pattern, poor data table support
- **Wrong tool**: Gradio is for showcasing ML models, not building analytics dashboards

**Custom React/Vue + FastAPI:**
- **Why not chosen**: Violates "ship it" principle - weeks of development vs. days
- **When to consider**: Never for v1 - only if Streamlit proves insufficient after real usage

---

## 3. AWS Storage Architecture

### Decision: S3 + DynamoDB Hybrid Architecture

**Primary Storage:**
- **S3 Standard**: CSV uploads, model artifacts, historical data archives
- **DynamoDB**: Current customer churn scores, risk levels, dashboard query data

### Rationale:
This architecture optimizes for the specific access patterns of a churn prediction dashboard: batch writes (weekly ML pipeline updates all scores), fast point lookups (dashboard queries by customer ID or risk level), and cost-efficiency at 10k customer scale. S3 provides durable, cheap storage for raw data and models, while DynamoDB enables sub-10ms dashboard queries without managing database infrastructure.

### Architecture Flow:

```
1. CSV Upload → S3 bucket (s3://churn-data/uploads/)
2. Weekly ML Pipeline reads from S3
3. Pipeline generates predictions
4. Predictions written to:
   - S3 (s3://churn-data/predictions/YYYY-MM-DD.csv) - audit trail
   - DynamoDB (churn-scores table) - live dashboard queries
5. Model artifacts → S3 (s3://churn-models/model-v1.pkl)
6. Dashboard reads from DynamoDB for <10ms response
```

**DynamoDB Table Design:**

```python
Table: churn-scores
- Partition Key: customer_id (String)
- Sort Key: score_date (String, ISO format)
- Attributes:
  - churn_score (Number)
  - risk_level (String: "High", "Medium", "Low")
  - monthly_revenue (Number)
  - last_updated (String, timestamp)

# Global Secondary Index for risk-based queries
GSI: risk-level-index
- Partition Key: risk_level
- Sort Key: churn_score (descending)
# Enables "show me all high-risk customers sorted by score"
```

**S3 Bucket Structure:**

```
s3://churn-prediction-bucket/
├── uploads/
│   └── customer-data-YYYY-MM-DD.csv
├── predictions/
│   └── YYYY-MM-DD/
│       ├── scores.csv
│       └── metrics.json
└── models/
    └── model-v{version}.pkl
```

**Cost Analysis (10k customers, weekly updates):**

**DynamoDB:**
- Storage: 10k items × 1KB ≈ 10MB = $0.0025/month
- Reads: 50 users × 10 queries/day × 30 days = 15k reads/month
- On-demand pricing: 15k RCU ≈ $0.02/month
- **Total: ~$0.03/month**

**S3:**
- Storage: ~100MB historical data = $0.0023/month
- GET requests: ~1k/month = $0.0004
- **Total: ~$0.003/month**

**Total storage cost: <$0.05/month** (incredibly cheap at this scale)

### Alternatives Considered:

**RDS PostgreSQL:**
- **Strengths**: Familiar SQL, complex queries, ACID transactions
- **Why not chosen**:
  - Overkill for simple key-value lookups
  - Minimum cost ~$15/month (db.t3.micro), 300x more expensive
  - Requires managing connections, schema migrations, backups
  - Query patterns don't need relational joins
- **When to reconsider**: If you need complex analytics queries joining multiple tables

**S3 + Athena (Query-on-demand):**
- **Strengths**: No database to manage, SQL queries on S3 data
- **Why not chosen**:
  - Query latency 3-10 seconds (vs. <10ms for DynamoDB)
  - Not suitable for interactive dashboard
  - Better for batch analytics
- **When to use**: For ad-hoc analysis, not live dashboards

**DynamoDB Alternatives - Just S3 with Caching:**
- **Why not chosen**: Dashboard would need to load entire CSV on startup or parse S3 objects repeatedly
- Could work but more complex to implement than DynamoDB

**DocumentDB or MongoDB:**
- **Why not chosen**: MongoDB-compatible document store, minimum cost ~$200/month
- Massive overkill for 10k records

---

## 4. AWS Compute Services

### Decision:
- **ML Pipeline (Weekly Batch)**: AWS Lambda with S3 event trigger
- **Dashboard Hosting**: AWS Fargate (ECS with Fargate launch type)

### Rationale:

**Lambda for ML Pipeline:**
The weekly batch scoring pipeline is an ideal Lambda use case: infrequent execution (runs once/week), event-driven (triggered by CSV upload to S3), and sub-15-minute runtime (10k customers can be scored in ~5 minutes). Lambda pricing is 7.5x higher than Fargate per compute-hour, but since it runs <1% of the time, total cost is lowest. No server management, automatic scaling, pay only for execution time.

**Cost calculation:**
- Weekly runs: 4 runs/month × 10 minutes = 40 minutes/month
- Lambda with 3GB RAM: ~$0.10/month
- Fargate equivalent (always running): ~$30/month
- **Lambda wins: 300x cheaper for batch workload**

**Fargate for Dashboard:**
Streamlit dashboard needs to be always-available for 50 concurrent users. Lambda has cold start issues (3-5 second delays) that hurt user experience. Fargate provides consistent sub-second response times, runs containers 24/7, and is more cost-effective than EC2 for this scale since we can right-size resources (likely 0.5 vCPU, 1GB RAM).

**Cost calculation:**
- Fargate: 0.5 vCPU, 1GB RAM = ~$15/month (always on)
- EC2 t3.micro: ~$8.50/month but requires managing OS, security patches, scaling
- Lambda (if used for dashboard): Cold starts hurt UX, need provisioned concurrency (~$50/month)
- **Fargate wins: Best UX-to-cost ratio for always-on dashboard**

### Architecture:

```
┌─────────────────┐
│  CSV Upload     │
│  to S3 bucket   │
└────────┬────────┘
         │ (S3 event trigger)
         ▼
┌─────────────────────────────────┐
│  Lambda Function (ML Pipeline)  │
│  - Reads CSV from S3            │
│  - Loads model from S3          │
│  - Generates predictions        │
│  - Writes to DynamoDB + S3      │
│  Runtime: Python 3.11           │
│  Memory: 3GB, Timeout: 15min    │
└─────────────────────────────────┘

┌──────────────────────────────────┐
│  ECS Fargate (Dashboard)         │
│  - Streamlit app in container    │
│  - Reads from DynamoDB           │
│  - ALB for load balancing        │
│  Task: 0.5 vCPU, 1GB RAM         │
│  Auto-scaling: 1-3 tasks         │
└──────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│  Users (50)     │
│  via HTTPS      │
└─────────────────┘
```

### Implementation Details:

**Lambda Configuration:**
```python
# Lambda environment variables
ENVIRONMENT = "production"
S3_BUCKET = "churn-prediction-bucket"
DYNAMODB_TABLE = "churn-scores"
MODEL_KEY = "models/model-v1.pkl"

# Function settings
Memory: 3072 MB (3GB)
Timeout: 900 seconds (15 min)
Trigger: S3 PUT event on uploads/ prefix
Runtime: Python 3.11
```

**Fargate Task Definition:**
```yaml
# Minimal viable configuration
containerDefinitions:
  - name: streamlit-dashboard
    image: {account}.dkr.ecr.{region}.amazonaws.com/churn-dashboard:latest
    memory: 1024
    cpu: 512
    portMappings:
      - containerPort: 8501  # Streamlit default
    environment:
      - DYNAMODB_TABLE=churn-scores
      - AWS_REGION=us-east-1
```

### Scaling Considerations:

**Current Scale (10k customers, 50 users):**
- Lambda: No changes needed, auto-scales to 1000 concurrent executions
- Fargate: 1 task sufficient, can add target tracking auto-scaling

**Future Scale (100k customers, 500 users):**
- Lambda: May hit 15-min timeout, split into step functions or move to Fargate batch job
- Fargate dashboard: Scale to 3-5 tasks with ALB, still cost-effective

### Alternatives Considered:

**SageMaker for ML Pipeline:**
- **Strengths**: Purpose-built for ML, supports distributed training, model registry
- **Why not chosen**:
  - Minimum cost ~$50/month for inference endpoints
  - Overkill for simple batch scoring
  - Training a gradient boosting model on 10k rows doesn't need GPU/distributed compute
- **When to reconsider**: If model training takes >15 minutes or you need A/B testing infrastructure

**EC2 for Dashboard:**
- **Strengths**: Full control, potentially cheaper at high utilization
- **Why not chosen**:
  - Requires managing OS, security patches, monitoring
  - Violates "developer experience is a feature" - more operational burden
  - t3.micro ($8.50/month) is cheaper but needs manual scaling, health checks, backups
- **When to reconsider**: If cost optimization is critical and you have DevOps expertise

**Lambda for Dashboard:**
- **Why not chosen**:
  - Cold starts create 3-5 second delays for first request
  - Provisioned concurrency solves this but costs ~$50/month, 3x more than Fargate
  - Streamlit is designed for long-running processes, not serverless
- **When to use**: Never for Streamlit dashboard; only for REST APIs

**AWS Batch for ML Pipeline:**
- **Strengths**: Designed for batch processing, can use Fargate Spot for 70% cost savings
- **Why not chosen**: More complexity than Lambda for this workload, similar cost to Lambda
- **When to consider**: If pipeline needs >15 minutes or complex job dependencies

**EKS (Kubernetes):**
- **Why not chosen**: Massive overkill, $73/month for control plane alone, requires K8s expertise
- **Never use for this scale**: Only justified for >100 microservices

---

## 5. Data Generation Improvements

Based on analysis of `/home/dwalleck/repos/churn-prediction/sample-data.csv`, the current synthetic data includes good features but is missing critical temporal patterns and predictive signals that real churn data exhibits.

### Current Data Analysis:

**Existing Features (Good):**
- `account_id`: Customer identifier
- `month`: Temporal dimension
- `current_month_transactions`: Activity level
- `current_month_revenue`: Monetary value
- `total_tickets`, `escalated_tickets`: Support engagement
- `late_payments`: Payment behavior
- `enabled_channels`: Channel diversity
- `self_service_percentage`: Self-sufficiency
- `last_touchbase_date`: Engagement recency
- `average_resolution_time_hours`: Support experience
- `churned`: Target variable

**Issues Identified:**
1. No declining trends visible before churn events
2. Missing RFM-style features (recency, frequency, monetary trends)
3. No customer lifecycle/tenure information
4. No contract or subscription type
5. No seasonal patterns
6. No feature velocity (rate of change)

### Recommendations:

**1. Add Temporal Trend Features:**

Generate these as derived features showing behavior change:
```python
# Month-over-month changes
- transaction_change_pct: % change from previous month
- revenue_velocity: 3-month moving average slope
- ticket_trend: Are support tickets increasing?
- engagement_score_delta: Change in overall engagement
```

**Realistic churn pattern**: Customers typically show declining engagement 2-3 months before churn:
- Transactions drop 20-40% from baseline
- Revenue declines follow
- Support tickets may spike (frustration) OR drop to zero (already disengaged)
- Self-service percentage changes dramatically (very high = avoiding you, very low = needs hand-holding)

**2. Add RFM Features:**

```python
# Recency
- days_since_last_transaction: Critical predictor
- days_since_last_login: If you track login data
- months_of_inactivity: 0 for active, 1+ for dormant

# Frequency (already have current_month_transactions)
- transactions_last_30_days
- transactions_last_90_days
- avg_transactions_per_month: Lifetime average

# Monetary (already have current_month_revenue)
- revenue_last_90_days
- lifetime_value: Total revenue since signup
- avg_monthly_revenue: Lifetime average
```

**3. Add Customer Lifecycle Features:**

```python
- tenure_months: How long they've been a customer (critical!)
- contract_type: "month-to-month", "annual", "multi-year"
- months_until_renewal: Proximity to renewal is high-risk period
- is_trial: Boolean, trial customers churn at higher rates
- signup_channel: "organic", "paid", "referral"
```

**Realistic patterns**:
- Customers churn most in months 1-3 (poor onboarding) and at renewal time
- Month-to-month contracts have 3-5x higher churn than annual
- Trial users who don't convert within 14 days rarely convert later

**4. Add Product Engagement Features:**

```python
- active_features_count: How many features/products they use
- feature_adoption_rate: % of available features used
- daily_active_days: How many days active this month
- key_action_completion: Did they complete core workflow?
```

**5. Improve Churn Reasons Simulation:**

Real churn is not random - simulate distinct cohorts:

```python
# Cohort 1: Poor Onboarding (churn months 1-3)
- Low feature_adoption_rate
- High ticket count but poor resolution
- Low self_service_percentage (confused)
- Short tenure

# Cohort 2: Price Sensitive (churn at renewal)
- Declining revenue despite stable transactions
- months_until_renewal = 0 or -1
- Increased late_payments in months before churn

# Cohort 3: Better Alternative Found (gradual disengagement)
- Slow decline over 3-6 months
- Decreasing transactions and revenue
- Decreasing ticket submissions (already migrating)
- Still current on payments (clean exit)

# Cohort 4: Service Quality Issues
- Spike in escalated_tickets 1-2 months before churn
- Increasing average_resolution_time
- High late_payments (frustrated)
- Rapid drop in engagement

# Cohort 5: Feature Gap (stable then sudden)
- Stable usage for months, then sharp drop
- May correlate with competitor product launch
- Sudden channel reduction
```

**6. Add Temporal Patterns:**

```python
# Seasonality
- is_holiday_month: Nov/Dec often see changed behavior
- quarter: Q4 budgets, Q1 renewals
- fiscal_year_end: B2B customers may churn at fiscal year boundaries

# Weekly patterns (if you go to weekly granularity)
- weekend_activity_pct: Engaged users use product on weekends
- business_hours_usage: B2B vs. B2C patterns
```

**7. Add Noise and Realism:**

```python
# Not all features are perfectly predictive
- Add 10-20% random variation to features
- Some loyal customers have high ticket counts (power users)
- Some churners look perfect until the end (competitor stole them)
- Missing data: Occasional NULL in self_service_percentage or touchbase_date
- Outliers: A few customers with extreme values
```

### Recommended Synthetic Data Generation Approach:

```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_customer_history(account_id, churn_cohort, months=12):
    """
    Generate realistic temporal history for one customer.

    churn_cohort: "early", "renewal", "gradual", "service", "stable"
    """

    # Base characteristics
    tenure = np.random.randint(1, 36)  # 1-36 months
    contract_type = np.random.choice(["monthly", "annual"], p=[0.6, 0.4])
    baseline_transactions = np.random.randint(50, 200)
    baseline_revenue = baseline_transactions * np.random.uniform(100, 500)

    history = []
    for month_offset in range(months):
        # Apply cohort-specific patterns
        if churn_cohort == "gradual" and month_offset > months - 4:
            # Declining trend in last 3 months
            decline_factor = 1 - (0.15 * (months - month_offset))
            transactions = baseline_transactions * decline_factor
            revenue = baseline_revenue * decline_factor
            tickets = int(np.random.poisson(2) * (1.5 - decline_factor))  # Decreasing

        elif churn_cohort == "service" and month_offset > months - 3:
            # Service issues spike
            transactions = baseline_transactions * 0.8
            tickets = int(np.random.poisson(8))  # High tickets
            escalated = int(tickets * 0.4)  # Many escalations

        # ... implement other cohorts

        # Calculate derived features
        days_since_last_transaction = calculate_recency(month_offset)
        transaction_change_pct = calculate_mom_change(history)

        history.append({
            'account_id': account_id,
            'month': month_offset,
            'tenure_months': tenure + month_offset,
            'contract_type': contract_type,
            'transactions': transactions,
            'revenue': revenue,
            'tickets': tickets,
            # ... all features
            'churned': 1 if month_offset == months - 1 and churn_cohort != "stable" else 0
        })

    return pd.DataFrame(history)
```

### Additional Features to Generate:

**High-Impact Predictors (Add These First):**
1. **tenure_months**: Customer age - critical for lifecycle modeling
2. **contract_type**: Contract structure predicts churn propensity
3. **transaction_change_pct**: Month-over-month change - signals disengagement
4. **days_since_last_transaction**: Recency is one of strongest signals
5. **months_until_renewal**: Renewal proximity is high-risk
6. **revenue_velocity**: 3-month revenue trend line slope

**Medium-Impact (Add If Time Allows):**
7. **feature_adoption_rate**: % of available features used
8. **lifetime_value**: Total revenue to date
9. **active_days_this_month**: Activity frequency within month
10. **payment_failure_count**: Cumulative payment issues

**Nice-to-Have (For Realism):**
11. **signup_channel**: Acquisition source
12. **customer_segment**: "SMB", "Mid-Market", "Enterprise"
13. **primary_use_case**: Why they bought (if you have this in real data)
14. **nps_score**: Net Promoter Score (if you survey customers)

### Testing Data Quality:

Generate data, then validate:
```python
# Check temporal patterns
assert churned_customers.transaction_change_pct.mean() < -0.15  # Should decline
assert stable_customers.transaction_change_pct.mean() > -0.05  # Should be stable

# Check churn distribution by cohort
assert early_tenure_churn_rate > 0.20  # Months 1-3 should have high churn
assert renewal_month_churn_rate > 0.15  # Renewal time is risky

# Check feature correlations
assert correlation(days_since_last_transaction, churned) > 0.3  # Should be positive
assert correlation(tenure_months, churned) < -0.1  # Longer tenure = less churn
```

### Summary of Priority Improvements:

**Must Add (P0):**
- Tenure in months
- Month-over-month transaction/revenue changes
- Contract type
- Days since last transaction

**Should Add (P1):**
- Months until renewal
- Revenue velocity (3-month trend)
- Feature adoption rate
- Distinct churn cohorts with realistic patterns

**Nice to Have (P2):**
- Signup channel, customer segment
- NPS scores
- Seasonal/temporal effects

**Implementation Tip:**
Start with P0 features, train a model, evaluate feature importance. Then add P1 features and measure lift in model performance. Don't add P2 until you've proven P0 and P1 work.

---

## Summary & Next Steps

This research provides actionable recommendations for each component of the churn prediction dashboard:

1. **ML Model**: Use XGBoost with class weighting, optimize for F2 score and PR-AUC, validate temporally
2. **Dashboard**: Ship with Streamlit for fastest time-to-value, migrate to Dash only if proven necessary
3. **Storage**: S3 for data/models, DynamoDB for dashboard queries - costs <$0.05/month at 10k scale
4. **Compute**: Lambda for weekly batch ML, Fargate for always-on Streamlit dashboard
5. **Data**: Add tenure, contract type, temporal trends, and realistic churn cohorts to synthetic data

All recommendations align with project constitution principles: ship it fast, optimize developer experience, make it work before making it perfect, and base decisions on real usage data rather than theoretical optimization.

**Total Infrastructure Cost Estimate**: ~$15-20/month for 10k customers, 50 concurrent users, weekly model updates.

**Time to First Working Version**: 2-3 days for end-to-end prototype with recommended stack.
