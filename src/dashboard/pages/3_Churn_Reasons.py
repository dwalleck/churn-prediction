"""Churn reasons analysis page - historical churn patterns."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

from churn_predictor.storage.local_storage import LocalStorage

st.set_page_config(
    page_title="Churn Reasons",
    page_icon="📉",
    layout="wide",
)


@st.cache_resource
def get_storage():
    return LocalStorage(data_dir="data")


def categorize_churn_reason(row: pd.Series) -> str:
    """
    Categorize churn reason based on customer attributes.

    Categories:
    - price_cost: High revenue decline or late payments
    - product_quality: High ticket escalation
    - customer_service: High resolution times
    - competitor: Sudden drop in engagement with stable service
    - business_closed: Very low activity across all metrics
    """
    # Price/Cost issues
    if "revenue_change_pct" in row and row.get("revenue_change_pct", 0) < -30:
        return "price_cost"
    if "late_payments" in row and row.get("late_payments", 0) > 2:
        return "price_cost"

    # Product quality issues
    if "ticket_escalation_rate" in row and row.get("ticket_escalation_rate", 0) > 50:
        return "product_quality"

    # Customer service issues
    if "average_resolution_time_hours" in row and row.get("average_resolution_time_hours", 0) > 60:
        return "customer_service"

    # Business closed (very low activity)
    if "current_month_transactions" in row and row.get("current_month_transactions", 0) < 10:
        return "business_closed"

    # Competitor (moderate decline)
    if "transaction_change_pct" in row and row.get("transaction_change_pct", 0) < -15:
        return "competitor"

    return "other"


def plot_churn_reasons_pie(churn_df: pd.DataFrame, category_col: str = "churn_reason_category"):
    """Create pie chart of churn reasons."""
    if category_col not in churn_df.columns:
        return None

    reason_counts = churn_df[category_col].value_counts()

    fig = go.Figure(data=[go.Pie(
        labels=reason_counts.index,
        values=reason_counts.values,
        hole=.3,
        textinfo='label+percent',
        marker=dict(colors=px.colors.qualitative.Set2),
    )])

    fig.update_layout(
        title="Churn Reasons Distribution",
        height=400,
    )

    return fig


def plot_churn_trend(churn_df: pd.DataFrame, date_col: str = "month"):
    """Create line chart of churn over time."""
    if date_col not in churn_df.columns:
        return None

    # Ensure date column is datetime
    churn_df[date_col] = pd.to_datetime(churn_df[date_col])

    # Count churns by month
    churn_by_month = churn_df.groupby(churn_df[date_col].dt.to_period('M')).size()
    churn_by_month.index = churn_by_month.index.to_timestamp()

    fig = go.Figure(data=[go.Scatter(
        x=churn_by_month.index,
        y=churn_by_month.values,
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=8),
    )])

    fig.update_layout(
        title="Churn Events Over Time",
        xaxis_title="Month",
        yaxis_title="Number of Churned Customers",
        height=400,
    )

    return fig


def plot_reason_by_tenure(churn_df: pd.DataFrame, category_col: str = "churn_reason_category", tenure_col: str = "tenure_months"):
    """Create stacked bar chart of churn reasons by tenure bucket."""
    if category_col not in churn_df.columns or tenure_col not in churn_df.columns:
        return None

    # Create tenure buckets
    churn_df['tenure_bucket'] = pd.cut(
        churn_df[tenure_col],
        bins=[0, 3, 6, 12, 24, 100],
        labels=['0-3 months', '3-6 months', '6-12 months', '1-2 years', '2+ years']
    )

    # Count by tenure and reason
    reason_by_tenure = churn_df.groupby(['tenure_bucket', category_col]).size().unstack(fill_value=0)

    fig = go.Figure()

    for reason in reason_by_tenure.columns:
        fig.add_trace(go.Bar(
            name=reason,
            x=reason_by_tenure.index.astype(str),
            y=reason_by_tenure[reason],
        ))

    fig.update_layout(
        title="Churn Reasons by Customer Tenure",
        xaxis_title="Tenure",
        yaxis_title="Number of Churned Customers",
        barmode='stack',
        height=400,
    )

    return fig


def main():
    """Main churn reasons page."""
    st.title("📉 Churn Reasons Analysis")

    st.markdown("""
    Analyze historical churned customers to identify patterns and prioritize improvements.
    """)

    storage = get_storage()

    # Load scores
    try:
        df = storage.load_scores()

        # Filter to churned customers only
        if "churned" in df.columns:
            churn_df = df[df["churned"] == 1].copy()
        else:
            st.warning("No churn labels found in data. Using high-risk customers as proxy.")
            churn_df = df[df["churn_probability"] >= 70].copy()

        if len(churn_df) == 0:
            st.warning("No churned customers found in the dataset.")
            st.info("""
            This page analyzes historical churn patterns. Ensure your data includes:
            - A 'churned' column with 1 for churned customers
            - Historical customer records
            """)
            return

        # Add churn reason categorization
        churn_df["churn_reason_category"] = churn_df.apply(categorize_churn_reason, axis=1)

        # Date range filter
        st.sidebar.header("Filters")

        if "month" in churn_df.columns:
            churn_df["month"] = pd.to_datetime(churn_df["month"])

            min_date = churn_df["month"].min()
            max_date = churn_df["month"].max()

            date_range = st.sidebar.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

            if len(date_range) == 2:
                start_date, end_date = date_range
                churn_df = churn_df[
                    (churn_df["month"] >= pd.to_datetime(start_date)) &
                    (churn_df["month"] <= pd.to_datetime(end_date))
                ]

        # Summary metrics
        st.header("Summary Metrics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Churned", len(churn_df))

        with col2:
            avg_tenure = churn_df["tenure_months"].mean() if "tenure_months" in churn_df else 0
            st.metric("Avg Tenure (Months)", f"{avg_tenure:.1f}")

        with col3:
            total_revenue_lost = churn_df["current_month_revenue"].sum() if "current_month_revenue" in churn_df else 0
            st.metric("Revenue Lost", f"${total_revenue_lost:,.0f}")

        with col4:
            avg_revenue = churn_df["current_month_revenue"].mean() if "current_month_revenue" in churn_df else 0
            st.metric("Avg Customer Value", f"${avg_revenue:,.0f}")

        # Churn reasons breakdown
        st.header("Churn Reasons Breakdown")

        col1, col2 = st.columns(2)

        with col1:
            # Pie chart
            fig_pie = plot_churn_reasons_pie(churn_df)
            if fig_pie:
                st.plotly_chart(fig_pie, use_container_width=True)

        with col2:
            # Top reasons list
            st.subheader("Top 3 Reasons")

            reason_counts = churn_df["churn_reason_category"].value_counts()
            total_churned = len(churn_df)

            reason_labels = {
                "price_cost": "💰 Price/Cost",
                "product_quality": "📦 Product Quality",
                "customer_service": "🎧 Customer Service",
                "competitor": "🏢 Competitor",
                "business_closed": "🚫 Business Closed",
                "other": "❓ Other"
            }

            for i, (reason, count) in enumerate(reason_counts.head(3).items(), 1):
                pct = count / total_churned * 100
                label = reason_labels.get(reason, reason)
                st.markdown(f"**{i}. {label}**: {count} customers ({pct:.1f}%)")

            st.markdown("---")

            # Detailed breakdown
            st.subheader("All Reasons")
            reason_df = pd.DataFrame({
                "Reason": [reason_labels.get(r, r) for r in reason_counts.index],
                "Count": reason_counts.values,
                "Percentage": (reason_counts.values / total_churned * 100).round(1)
            })
            st.dataframe(reason_df, use_container_width=True, hide_index=True)

        # Trend over time
        if "month" in churn_df.columns:
            st.header("Churn Trend Over Time")
            fig_trend = plot_churn_trend(churn_df)
            if fig_trend:
                st.plotly_chart(fig_trend, use_container_width=True)

        # Churn by tenure
        if "tenure_months" in churn_df.columns:
            st.header("Churn Reasons by Tenure")
            fig_tenure = plot_reason_by_tenure(churn_df)
            if fig_tenure:
                st.plotly_chart(fig_tenure, use_container_width=True)

        # Detailed churn events table
        st.header("Detailed Churn Events")

        display_cols = ["account_id", "churn_reason_category"]
        optional_cols = ["month", "tenure_months", "current_month_revenue", "current_month_transactions", "churn_probability"]

        for col in optional_cols:
            if col in churn_df.columns:
                display_cols.append(col)

        st.dataframe(
            churn_df[display_cols].sort_values("churn_probability" if "churn_probability" in churn_df.columns else "month", ascending=False),
            use_container_width=True,
            hide_index=True,
        )

        # Insights
        st.header("Key Insights")

        top_reason = reason_counts.index[0]
        top_reason_count = reason_counts.values[0]
        top_reason_pct = top_reason_count / total_churned * 100

        st.info(f"""
        **Primary Churn Driver**: {reason_labels.get(top_reason, top_reason)}

        {top_reason_count} customers ({top_reason_pct:.1f}%) churned primarily due to {reason_labels.get(top_reason, top_reason).lower()}.

        **Recommended Actions**:
        - Focus retention efforts on this category
        - Analyze common patterns in this segment
        - Implement preventive measures for at-risk customers
        """)

    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("""
        **To view churn reasons:**
        1. Train a model: `python -m churn_predictor.cli train --data sample-data.csv --output data/models/model-v1.pkl`
        2. Generate scores: `python -m churn_predictor.cli score --data sample-data.csv --model data/models/model-v1.pkl`
        3. Refresh this page
        """)


if __name__ == "__main__":
    main()
