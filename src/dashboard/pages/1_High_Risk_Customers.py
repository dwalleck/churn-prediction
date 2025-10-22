"""High risk customers page for the dashboard."""

import streamlit as st
import pandas as pd
import json

from churn_predictor.storage.local_storage import LocalStorage


st.set_page_config(
    page_title="High Risk Customers",
    page_icon="⚠️",
    layout="wide",
)

# Initialize storage
@st.cache_resource
def get_storage():
    return LocalStorage(data_dir="data")


def format_risk_factors(risk_factors_str):
    """Format risk factors for display."""
    try:
        if pd.isna(risk_factors_str):
            return "No risk factors available"

        # Try to parse as JSON
        if isinstance(risk_factors_str, str):
            risk_factors = json.loads(risk_factors_str.replace("'", '"'))
        else:
            risk_factors = risk_factors_str

        if not risk_factors:
            return "No risk factors available"

        formatted = []
        for factor in risk_factors:
            feature = factor.get("feature", "Unknown")
            importance = factor.get("importance", 0)
            formatted.append(f"- **{feature}**: {importance:.1%} contribution")

        return "\n".join(formatted)
    except Exception as e:
        return f"Error formatting risk factors: {str(e)}"


def main():
    """Main high risk customers page."""
    st.title("⚠️ High Risk Customers")

    storage = get_storage()

    # Controls
    col1, col2 = st.columns(2)

    with col1:
        threshold = st.slider(
            "Churn Score Threshold",
            min_value=0,
            max_value=100,
            value=70,
            step=5,
            help="Show customers with churn probability above this threshold",
        )

    with col2:
        max_results = st.selectbox(
            "Max Results",
            options=[20, 50, 100, 200],
            index=0,
            help="Maximum number of customers to display",
        )

    # Load and filter data
    try:
        df = storage.load_scores()

        # Filter by threshold
        high_risk_df = df[df["churn_probability"] >= threshold].copy()
        high_risk_df = high_risk_df.sort_values("churn_probability", ascending=False)
        high_risk_df = high_risk_df.head(max_results)

        if len(high_risk_df) == 0:
            st.warning(f"No customers found with churn probability >= {threshold}%")
            return

        st.success(f"Found {len(high_risk_df)} customers with churn probability >= {threshold}%")

        # Display table
        st.header("Customer List")

        # Select columns to display
        display_columns = ["account_id", "churn_probability", "risk_level"]

        # Add other available columns if they exist
        optional_columns = [
            "current_month_revenue",
            "current_month_transactions",
            "tenure_months",
            "days_since_last_touchbase",
        ]
        for col in optional_columns:
            if col in high_risk_df.columns:
                display_columns.append(col)

        # Display dataframe
        st.dataframe(
            high_risk_df[display_columns],
            use_container_width=True,
            hide_index=True,
        )

        # Customer details
        st.header("Customer Details")

        # Select customer
        if "account_id" in high_risk_df.columns:
            selected_account = st.selectbox(
                "Select a customer to view details",
                options=high_risk_df["account_id"].tolist(),
                index=0,
            )

            # Get customer data
            customer = high_risk_df[high_risk_df["account_id"] == selected_account].iloc[0]

            # Display details in columns
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Churn Probability", f"{customer['churn_probability']:.1f}%")
                st.metric("Risk Level", customer["risk_level"].upper())

            with col2:
                if "confidence" in customer:
                    st.metric("Confidence", f"{customer['confidence']:.2%}")
                if "tenure_months" in customer:
                    st.metric("Tenure (Months)", int(customer["tenure_months"]))

            with col3:
                if "current_month_revenue" in customer:
                    st.metric("Current Month Revenue", f"${customer['current_month_revenue']:,.2f}")
                if "current_month_transactions" in customer:
                    st.metric("Current Month Transactions", int(customer["current_month_transactions"]))

            # Risk factors
            if "top_risk_factors" in customer and not pd.isna(customer["top_risk_factors"]):
                st.subheader("Top Risk Factors")
                st.markdown(format_risk_factors(customer["top_risk_factors"]))

            # Recommendations
            st.subheader("Recommended Actions")

            try:
                from churn_predictor.analytics.recommendations import get_recommendations_for_customer

                recommendations = get_recommendations_for_customer(selected_account, high_risk_df)

                if recommendations:
                    action_icons = {
                        "immediate_contact": "📞",
                        "offer_discount": "💰",
                        "review_service": "🎧",
                        "schedule_training": "📚",
                        "contract_renewal": "📝",
                    }

                    for i, rec in enumerate(recommendations, 1):
                        icon = action_icons.get(rec["action_type"], "•")
                        priority_label = {1: "HIGH", 2: "MEDIUM", 3: "LOW"}.get(rec["priority"], "")

                        st.markdown(f"""
                        **{i}. {icon} {rec['description']}** `{priority_label} PRIORITY`

                        *{rec['rationale']}*

                        Expected Impact: {rec['estimated_impact'].upper()}
                        """)
                else:
                    st.info("No specific recommendations generated. Monitor customer engagement.")

            except Exception as e:
                st.info(
                    """
                    **Suggested actions based on churn probability:**

                    1. **Immediate Contact**: Reach out within 24-48 hours
                    2. **Account Review**: Schedule check-in call with account manager
                    3. **Retention Offer**: Consider discount or additional services
                    4. **Monitor**: Track engagement metrics closely
                    """
                )

    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        st.info(
            """
            To generate predictions:
            1. Train a model: `python -m churn_predictor.cli train --data sample-data.csv --output data/models/model-v1.pkl`
            2. Generate scores: `python -m churn_predictor.cli score --data sample-data.csv --model data/models/model-v1.pkl`
            3. Refresh this dashboard
            """
        )


if __name__ == "__main__":
    main()
