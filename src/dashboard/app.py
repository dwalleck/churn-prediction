"""Main Streamlit dashboard for churn prediction."""

import streamlit as st
import pandas as pd
from pathlib import Path

from churn_predictor.storage.local_storage import LocalStorage


# Page configuration
st.set_page_config(
    page_title="Churn Prediction Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize storage
@st.cache_resource
def get_storage():
    return LocalStorage(data_dir="data")


def main():
    """Main dashboard page."""
    st.title("📊 Customer Churn Prediction Dashboard")

    storage = get_storage()

    # Try to load scores
    try:
        df = storage.load_scores()

        # Summary metrics
        st.header("Summary Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_customers = len(df)
            st.metric("Total Customers", f"{total_customers:,}")

        with col2:
            high_risk = len(df[df["risk_level"] == "high"])
            st.metric("High Risk", f"{high_risk:,}", delta=None)

        with col3:
            medium_risk = len(df[df["risk_level"] == "medium"])
            st.metric("Medium Risk", f"{medium_risk:,}")

        with col4:
            low_risk = len(df[df["risk_level"] == "low"])
            st.metric("Low Risk", f"{low_risk:,}")

        # Risk distribution
        st.header("Risk Distribution")

        risk_counts = df["risk_level"].value_counts()
        st.bar_chart(risk_counts)

        # Quick stats
        st.header("Quick Statistics")
        st.write(f"**Average Churn Probability**: {df['churn_probability'].mean():.2f}%")
        st.write(f"**Median Churn Probability**: {df['churn_probability'].median():.2f}%")
        st.write(f"**Max Churn Probability**: {df['churn_probability'].max():.2f}%")

    except Exception as e:
        st.error("No prediction data found. Please run scoring first.")
        st.info(
            """
            To generate predictions:
            1. Train a model: `python -m churn_predictor.cli train --data sample-data.csv --output data/models/model-v1.pkl`
            2. Generate scores: `python -m churn_predictor.cli score --data sample-data.csv --model data/models/model-v1.pkl`
            3. Refresh this dashboard
            """
        )

    # Sidebar
    st.sidebar.title("Navigation")
    st.sidebar.info(
        """
        **Available Pages:**
        - Home (this page)
        - High Risk Customers

        More pages coming soon:
        - Churn Drivers
        - Churn Reasons
        """
    )


if __name__ == "__main__":
    main()
