"""Churn drivers analysis page - feature importance and model insights."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from churn_predictor.storage.local_storage import LocalStorage
from churn_predictor.models.trainer import TrainedModel

st.set_page_config(
    page_title="Churn Drivers",
    page_icon="📊",
    layout="wide",
)


@st.cache_resource
def get_storage():
    return LocalStorage(data_dir="data")


@st.cache_resource
def load_model(model_path: str):
    """Load trained model for feature importance."""
    try:
        return TrainedModel.load(model_path)
    except Exception as e:
        return None


def plot_feature_importance(feature_importance: dict, top_n: int = 10):
    """Create horizontal bar chart of feature importance."""
    # Sort by importance
    sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    top_features = sorted_features[:top_n]

    features = [f[0] for f in top_features]
    importance = [f[1] for f in top_features]

    # Create horizontal bar chart
    fig = go.Figure(go.Bar(
        x=importance,
        y=features,
        orientation='h',
        marker=dict(
            color=importance,
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Importance")
        ),
        text=[f"{v:.3f}" for v in importance],
        textposition='auto',
    ))

    fig.update_layout(
        title=f"Top {top_n} Predictive Features",
        xaxis_title="Feature Importance",
        yaxis_title="Feature",
        height=500,
        yaxis={'categoryorder': 'total ascending'},
    )

    return fig


def plot_feature_distribution(df: pd.DataFrame, feature: str, risk_level_col: str = "risk_level"):
    """Create box plot showing feature distribution by risk level."""
    if feature not in df.columns:
        return None

    fig = px.box(
        df,
        x=risk_level_col,
        y=feature,
        color=risk_level_col,
        color_discrete_map={"low": "green", "medium": "orange", "high": "red"},
        title=f"Distribution of {feature} by Risk Level",
        category_orders={risk_level_col: ["low", "medium", "high"]},
    )

    fig.update_layout(
        xaxis_title="Risk Level",
        yaxis_title=feature.replace('_', ' ').title(),
        height=400,
        showlegend=False,
    )

    return fig


def get_feature_insight(df: pd.DataFrame, feature: str, risk_level_col: str = "risk_level"):
    """Generate statistical insight about feature."""
    if feature not in df.columns or risk_level_col not in df.columns:
        return "Insufficient data for analysis."

    high_risk = df[df[risk_level_col] == "high"][feature]
    low_risk = df[df[risk_level_col] == "low"][feature]

    if len(high_risk) == 0 or len(low_risk) == 0:
        return "Not enough data for comparison."

    high_median = high_risk.median()
    low_median = low_risk.median()

    diff_pct = ((high_median - low_median) / low_median * 100) if low_median != 0 else 0

    if diff_pct > 20:
        direction = "higher"
        insight = f"High-risk customers have **{abs(diff_pct):.1f}% {direction}** {feature.replace('_', ' ')} than low-risk customers (median: {high_median:.2f} vs {low_median:.2f})."
    elif diff_pct < -20:
        direction = "lower"
        insight = f"High-risk customers have **{abs(diff_pct):.1f}% {direction}** {feature.replace('_', ' ')} than low-risk customers (median: {high_median:.2f} vs {low_median:.2f})."
    else:
        insight = f"Similar {feature.replace('_', ' ')} across risk levels (high-risk median: {high_median:.2f}, low-risk median: {low_median:.2f})."

    return insight


def main():
    """Main churn drivers page."""
    st.title("📊 Churn Drivers Analysis")

    st.markdown("""
    Understand which factors most strongly predict customer churn.
    This analysis helps identify strategic areas for improvement.
    """)

    storage = get_storage()

    # Try to load model
    model_path = st.sidebar.text_input(
        "Model Path",
        value="data/models/model-v1.pkl",
        help="Path to trained model file"
    )

    model = load_model(model_path)

    if model is None:
        st.error(f"Could not load model from {model_path}")
        st.info("""
        **To view churn drivers:**
        1. Train a model: `python -m churn_predictor.cli train --data sample-data.csv --output data/models/model-v1.pkl`
        2. Refresh this page
        """)
        return

    # Model metadata
    st.header("Model Information")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Model Version", model.version)
    with col2:
        st.metric("F2 Score", f"{model.performance_metrics['f2_score']:.3f}")
    with col3:
        st.metric("Precision", f"{model.performance_metrics['precision']:.3f}")
    with col4:
        st.metric("Recall", f"{model.performance_metrics['recall']:.3f}")

    # Feature importance
    st.header("Feature Importance")

    top_n = st.slider(
        "Number of features to display",
        min_value=5,
        max_value=len(model.feature_importance),
        value=10,
        step=1,
    )

    fig = plot_feature_importance(model.feature_importance, top_n=top_n)
    st.plotly_chart(fig, use_container_width=True)

    # Feature analysis
    st.header("Feature Analysis")

    # Load scores for distribution analysis
    try:
        df = storage.load_scores()

        # Select feature to analyze
        available_features = [f for f in model.feature_names if f in df.columns]

        if available_features:
            selected_feature = st.selectbox(
                "Select feature to analyze",
                options=available_features,
                index=0,
            )

            col1, col2 = st.columns([2, 1])

            with col1:
                # Distribution plot
                fig_dist = plot_feature_distribution(df, selected_feature)
                if fig_dist:
                    st.plotly_chart(fig_dist, use_container_width=True)

            with col2:
                st.subheader("Statistical Insight")
                insight = get_feature_insight(df, selected_feature)
                st.info(insight)

                # Feature statistics
                st.subheader("Summary Statistics")
                feature_stats = df.groupby("risk_level")[selected_feature].describe()[["mean", "median", "std"]]
                st.dataframe(feature_stats, use_container_width=True)

        else:
            st.warning("No feature data available in scores. Run scoring pipeline first.")

    except Exception as e:
        st.warning(f"Could not load score data: {e}")
        st.info("Run the scoring pipeline to enable feature distribution analysis.")

    # Top predictive factors explanation
    st.header("Key Insights")

    # Get top 5 features
    top_5_features = sorted(
        model.feature_importance.items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]

    st.markdown("**Top 5 Predictive Factors:**")
    for i, (feature, importance) in enumerate(top_5_features, 1):
        feature_name = feature.replace('_', ' ').title()
        st.markdown(f"{i}. **{feature_name}**: {importance:.1%} importance")

    st.markdown("""
    ---
    ### How to Use This Information

    **High Importance Features** indicate areas where changes in customer behavior
    most strongly predict churn. Focus retention efforts on:

    1. **Engagement Metrics** (e.g., days since last touchbase, transaction changes)
    2. **Service Quality** (e.g., ticket escalation rate, resolution time)
    3. **Financial Indicators** (e.g., revenue changes, late payments)
    4. **Customer Lifecycle** (e.g., tenure, contract type)
    """)


if __name__ == "__main__":
    main()
