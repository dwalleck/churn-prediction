# Dashboard API Contract

**Feature**: 001-churn-prediction-dashboard
**Type**: Streamlit Application Interface
**Date**: 2025-10-22

## Overview

This document defines the Streamlit dashboard interface components and data service APIs. The dashboard provides three main views corresponding to the prioritized user stories.

## Application Structure

```
dashboard/
├── app.py                    # Main entry point with navigation
├── pages/
│   ├── 1_High_Risk_Customers.py    # P1: View high-risk customers
│   ├── 2_Churn_Drivers.py          # P2: Variable importance
│   └── 3_Churn_Reasons.py          # P3: Historical churn analysis
└── services/
    └── data_service.py       # DynamoDB query layer
```

## Main Application

**File**: `dashboard/app.py`

### Entry Point

```python
import streamlit as st

st.set_page_config(
    page_title="Churn Prediction Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("Customer Churn Prediction Dashboard")
st.markdown("""
Welcome to the Churn Prediction Dashboard. Use the sidebar to navigate between views:

- **High Risk Customers**: Identify customers most likely to churn
- **Churn Drivers**: Understand which factors predict churn
- **Churn Reasons**: Analyze why customers have churned
""")

# Show summary metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Customers", "{:,}".format(total_customers))

with col2:
    st.metric("High Risk", "{:,}".format(high_risk_count),
              delta=f"{high_risk_pct}%")

with col3:
    st.metric("Average Score", f"{avg_score:.1f}")

with col4:
    st.metric("Last Updated", last_update_date)
```

**Features**:
- Welcome page with navigation instructions
- Summary metrics across all customers
- Automatic refresh every 5 minutes
- Error handling with user-friendly messages

---

## Page 1: High Risk Customers (P1)

**File**: `dashboard/pages/1_High_Risk_Customers.py`

**User Story**: Account managers identify customers most likely to churn in next 60-90 days

### Layout

```python
st.title("📈 High Risk Customers")

# Filters
col1, col2 = st.columns([1, 1])
with col1:
    min_score = st.slider(
        "Minimum Churn Score",
        min_value=0,
        max_value=100,
        value=70,
        help="Show customers with score >= this threshold"
    )

with col2:
    max_results = st.selectbox(
        "Results to Show",
        options=[20, 50, 100, 200],
        index=0,
        help="Number of customers to display"
    )

# Load data
with st.spinner("Loading high-risk customers..."):
    customers = data_service.get_high_risk_customers(
        min_probability=min_score,
        limit=max_results
    )

# Display results
st.subheader(f"Found {len(customers)} high-risk customers")

# Interactive data table
st.dataframe(
    customers[['account_id', 'churn_probability', 'risk_level',
               'days_since_contact', 'last_touchbase_date']],
    use_container_width=True,
    hide_index=True,
    column_config={
        "churn_probability": st.column_config.ProgressColumn(
            "Churn Score",
            min_value=0,
            max_value=100,
            format="%d%%"
        ),
        "risk_level": st.column_config.TextColumn(
            "Risk Level",
            help="Low (0-30), Medium (31-69), High (70-100)"
        )
    }
)

# Customer detail view
selected_customer = st.selectbox(
    "Select customer for details",
    options=customers['account_id'].tolist()
)

if selected_customer:
    display_customer_details(selected_customer)
```

### Customer Detail Component

```python
def display_customer_details(account_id: str):
    """Display detailed view for selected customer"""

    customer = data_service.get_customer_details(account_id)
    score = data_service.get_score(account_id)
    recommendations = data_service.get_recommendations(account_id)

    st.subheader(f"Customer: {account_id}")

    # Score and risk
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Churn Score", f"{score.churn_probability:.1f}%")
    with col2:
        st.metric("Risk Level", score.risk_level.upper())
    with col3:
        st.metric("Confidence", f"{score.confidence:.0%}")

    # Top risk factors
    st.subheader("Top Risk Factors")
    for factor in score.top_risk_factors:
        st.write(f"- **{factor['feature']}**: {factor['importance']:.0%} contribution")

    # Actionable recommendations
    st.subheader("Recommended Actions")
    for rec in recommendations:
        with st.expander(f"{rec.action_type.replace('_', ' ').title()} (Priority {rec.priority})"):
            st.write(f"**Action**: {rec.description}")
            st.write(f"**Why**: {rec.rationale}")
            st.write(f"**Expected Impact**: {rec.estimated_impact.capitalize()}")

    # Customer history
    st.subheader("Customer Data")
    st.json(customer.dict(), expanded=False)
```

**Success Criteria**:
- SC-001: Account managers can identify top 20 highest-risk customers in <30 seconds ✅

---

## Page 2: Churn Drivers (P2)

**File**: `dashboard/pages/2_Churn_Drivers.py`

**User Story**: Business leaders understand which factors most strongly predict churn

### Layout

```python
st.title("🔍 Churn Drivers Analysis")

# Load model metadata
model = data_service.get_active_model_metadata()

st.metric("Active Model Version", model.model_version)
st.metric("Model Performance (F2 Score)", f"{model.performance_metrics['f2_score']:.2f}")

# Feature importance chart
st.subheader("Top Predictive Features")

importance_df = pd.DataFrame([
    {"feature": k, "importance": v}
    for k, v in sorted(
        model.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]
])

fig = px.bar(
    importance_df,
    x="importance",
    y="feature",
    orientation='h',
    title="Feature Importance (Top 10)",
    labels={"importance": "Importance Score", "feature": "Feature"},
    color="importance",
    color_continuous_scale="Reds"
)
st.plotly_chart(fig, use_container_width=True)

# Feature direction analysis
st.subheader("How Features Impact Churn")

feature_select = st.selectbox(
    "Select feature to analyze",
    options=list(model.feature_importance.keys())[:10]
)

# Show distribution by churn status
feature_dist = data_service.get_feature_distribution(feature_select)
display_feature_distribution(feature_select, feature_dist)

# Segment analysis (optional)
st.subheader("Feature Importance by Customer Segment")

segment_by = st.radio(
    "Segment by",
    options=["All Customers", "Contract Type", "Tenure Bracket"],
    index=0
)

if segment_by != "All Customers":
    segment_importance = data_service.get_segment_importance(segment_by)
    display_segment_comparison(segment_importance)
```

### Feature Distribution Component

```python
def display_feature_distribution(feature: str, distribution: dict):
    """Show how feature values differ between churned/retained"""

    fig = px.box(
        distribution['data'],
        x="churn_status",
        y=feature,
        color="churn_status",
        title=f"{feature} Distribution by Churn Status",
        labels={"churn_status": "Customer Status"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Statistical summary
    st.write("**Insight**:")
    st.write(distribution['insight'])
    # Example: "Churned customers have 45% fewer transactions on average"
```

**Success Criteria**:
- SC-003: Users can understand which 5 variables most impact churn in <1 minute ✅
- SC-009: Variable importance analysis explains ≥70% of factors ✅

---

## Page 3: Churn Reasons (P3)

**File**: `dashboard/pages/3_Churn_Reasons.py`

**User Story**: Leadership analyzes why customers have churned to prioritize improvements

### Layout

```python
st.title("📊 Historical Churn Analysis")

# Time period filter
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime.now() - timedelta(days=365)
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime.now()
    )

# Load churn events
churn_events = data_service.get_churn_events(
    start_date=start_date,
    end_date=end_date
)

# Summary metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Churned", len(churn_events))
with col2:
    avg_tenure = churn_events['tenure_at_churn'].mean()
    st.metric("Avg Tenure at Churn", f"{avg_tenure:.1f} months")
with col3:
    total_revenue_lost = churn_events['final_revenue'].sum()
    st.metric("Revenue Lost", f"${total_revenue_lost:,.0f}")

# Churn reason breakdown
st.subheader("Churn Reasons")

reason_counts = churn_events['churn_reason_category'].value_counts()
reason_pcts = (reason_counts / len(churn_events) * 100).round(1)

fig = px.pie(
    values=reason_counts.values,
    names=reason_counts.index,
    title="Churn Reason Distribution",
    hole=0.4  # Donut chart
)
st.plotly_chart(fig, use_container_width=True)

# Top 3 reasons
st.subheader("Top 3 Churn Reasons")
for i, (reason, count) in enumerate(reason_counts.head(3).items(), 1):
    pct = reason_pcts[reason]
    st.write(f"{i}. **{reason.replace('_', ' ').title()}**: {count} customers ({pct}%)")

# Trend over time
st.subheader("Churn Reasons Over Time")

churn_by_month = churn_events.groupby([
    pd.Grouper(key='churn_date', freq='M'),
    'churn_reason_category'
]).size().reset_index(name='count')

fig = px.line(
    churn_by_month,
    x='churn_date',
    y='count',
    color='churn_reason_category',
    title="Churn Reason Trends",
    labels={"churn_date": "Month", "count": "Customer Count"}
)
st.plotly_chart(fig, use_container_width=True)

# Detailed table
st.subheader("Churn Event Details")
st.dataframe(
    churn_events[['account_id', 'churn_date', 'churn_reason_category',
                  'tenure_at_churn', 'final_revenue']],
    use_container_width=True,
    hide_index=True
)
```

**Success Criteria**:
- SC-002: Leadership can determine top 3 churn reasons in <2 minutes ✅
- SC-010: Churn reason categorization covers ≥90% of historical churned customers ✅

---

## Data Service API

**File**: `dashboard/services/data_service.py`

### DataService Class

```python
class DataService:
    """Service layer for dashboard data queries"""

    def __init__(
        self,
        score_repo: ChurnScoreRepository,
        event_repo: ChurnEventRepository,
        model_repo: ModelRepository
    ):
        self.score_repo = score_repo
        self.event_repo = event_repo
        self.model_repo = model_repo

    @st.cache_data(ttl=300)  # Cache for 5 minutes
    def get_high_risk_customers(
        self,
        min_probability: float = 70.0,
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Get high-risk customers sorted by churn probability.

        Returns DataFrame with columns:
        - account_id
        - churn_probability
        - risk_level
        - days_since_contact
        - last_touchbase_date
        """

    @st.cache_data(ttl=300)
    def get_customer_details(self, account_id: str) -> dict:
        """Get full customer data for detail view"""

    @st.cache_data(ttl=300)
    def get_score(self, account_id: str) -> ChurnScore:
        """Get latest churn score for customer"""

    @st.cache_data(ttl=300)
    def get_recommendations(
        self,
        account_id: str
    ) -> list[ActionableRecommendation]:
        """Get recommendations for customer"""

    @st.cache_data(ttl=3600)  # Cache for 1 hour
    def get_active_model_metadata(self) -> ModelMetadata:
        """Get metadata for currently active model"""

    @st.cache_data(ttl=3600)
    def get_feature_distribution(self, feature: str) -> dict:
        """
        Get feature value distribution by churn status.

        Returns:
        {
            'data': DataFrame with feature values and churn_status,
            'insight': str describing the pattern
        }
        """

    @st.cache_data(ttl=3600)
    def get_churn_events(
        self,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        Get historical churn events in date range.

        Returns DataFrame with all ChurnEvent fields.
        """

    def get_summary_metrics(self) -> dict:
        """
        Get dashboard summary metrics.

        Returns:
        {
            'total_customers': int,
            'high_risk_count': int,
            'high_risk_pct': float,
            'avg_score': float,
            'last_update_date': str
        }
        """
```

**Caching Strategy**:
- High-risk customer list: 5 minutes (semi-real-time for active monitoring)
- Model metadata: 1 hour (changes infrequently)
- Churn events: 1 hour (historical data, rarely changes)
- Summary metrics: 5 minutes (dashboard homepage)

---

## Error Handling

### User-Friendly Error Messages

```python
try:
    customers = data_service.get_high_risk_customers(min_score, max_results)
except StorageError as e:
    st.error("""
    ⚠️ Unable to load customer data from database.

    This might be a temporary connection issue. Please try:
    1. Refresh the page
    2. Check if the data pipeline has run this week
    3. Contact support if the issue persists

    Technical details: {error}
    """.format(error=str(e)))
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.info("Please contact support with the error message above.")
    st.stop()
```

### Empty State Handling

```python
if len(customers) == 0:
    st.info("""
    🎉 No high-risk customers found!

    This could mean:
    - All customers are low risk (great news!)
    - The churn score threshold is too high (try lowering the slider)
    - The scoring pipeline hasn't run yet this week
    """)
    st.stop()
```

---

## Performance Optimization

### Query Optimization

1. **Use DynamoDB GSI** for high-risk customer queries (not table scan)
2. **Limit results** to reasonable defaults (20, 50, 100)
3. **Lazy load** customer details (only when selected)
4. **Cache aggressively** using `@st.cache_data`

### Rendering Optimization

```python
# Good: Streamlit native components (fast)
st.dataframe(df, use_container_width=True)

# Good: Plotly charts (interactive, performant)
st.plotly_chart(fig, use_container_width=True)

# Avoid: Rendering 1000s of rows without pagination
if len(df) > 200:
    st.warning(f"Showing first 200 of {len(df)} results. Use filters to narrow down.")
    df = df.head(200)
```

### Memory Management

```python
# Clear cache periodically for long-running sessions
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
```

---

## Deployment Configuration

### Streamlit Config

**File**: `.streamlit/config.toml`

```toml
[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### Environment Variables

Required for AWS access:

```bash
AWS_REGION=us-east-1
DYNAMODB_SCORES_TABLE=churn-scores
DYNAMODB_EVENTS_TABLE=churn-events
S3_MODEL_BUCKET=churn-models
S3_DATA_BUCKET=churn-data
```

---

## Testing Strategy

### Dashboard Tests

**File**: `tests/integration/test_dashboard.py`

```python
def test_high_risk_page_loads():
    """Test that high-risk customer page renders without errors"""
    # Use Streamlit test framework
    pass

def test_filters_work():
    """Test that score threshold filter updates results"""
    pass

def test_empty_state_handling():
    """Test UI when no high-risk customers exist"""
    pass

def test_error_handling():
    """Test graceful degradation on data service errors"""
    pass
```

### Data Service Tests

```python
def test_get_high_risk_customers():
    """Test high-risk customer query"""
    service = DataService(mock_repos)
    result = service.get_high_risk_customers(min_probability=70)
    assert all(result['churn_probability'] >= 70)
    assert len(result) <= 100

def test_caching():
    """Test that repeated queries use cache"""
    # Verify cache hit on second call
    pass
```

---

## Accessibility

### Requirements

- ✅ Keyboard navigation support (Streamlit default)
- ✅ Screen reader friendly labels
- ✅ Color contrast meets WCAG AA standards
- ✅ Charts include text descriptions

### Implementation

```python
# Add helpful labels and descriptions
st.slider(
    "Minimum Churn Score",
    help="Show customers with churn score >= this threshold. "
         "High risk is 70-100, medium is 31-69, low is 0-30."
)

# Provide text alternatives for charts
st.write(f"The chart shows that {top_reason} is the #1 churn reason, "
         f"affecting {count} customers ({pct}% of total churned).")
```

---

## Success Metrics Validation

**Dashboard must meet these criteria**:

| Success Criterion | Target | Validation Method |
|------------------|--------|-------------------|
| SC-001: Identify top 20 in <30s | <30 seconds | Time from page load to view |
| SC-002: Top 3 reasons in <2 min | <2 minutes | Time to churn reasons page |
| SC-003: Understand top 5 variables in <1 min | <1 minute | Time to drivers page |
| SC-008: Support 50 concurrent users | 50 users | Load testing |
| Dashboard response time | <2 seconds | Query execution time |

**Load Testing** (using Locust or similar):
```python
# Simulate 50 concurrent users
# Measure: response times, error rates, resource usage
# Target: <2 second p95 latency, 0% error rate
```
