import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide")

st.title("📊 Conversational Analytics Dashboard")
st.markdown("Monitor key metrics, user drop-off rates, and intent resolution for the FinBot Debt Discovery Agent.")

# Fetch analytics from backend
@st.cache_data(ttl=5) # Cache for 5 seconds to prevent spamming the backend
def fetch_analytics():
    try:
        response = requests.get(f"{BACKEND_URL}/analytics")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Failed to fetch analytics: {e}")
        return None

analytics = fetch_analytics()

if analytics:
    # High-level metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sessions", analytics["total_sessions"])
    with col2:
        st.metric("Completed Sessions", analytics["completed_sessions"])
    with col3:
        st.metric("Drop-off Rate", f"{analytics['drop_off_rate']}%")
    with col4:
        st.metric("Avg Sentiment Score", analytics["average_sentiment"])

    st.markdown("---")

    # Intent Distribution
    st.subheader("User Intent Distribution")
    intents = analytics.get("intent_distribution", {})
    if intents:
        df_intents = pd.DataFrame(list(intents.items()), columns=["Intent", "Count"])
        fig1 = px.pie(df_intents, names="Intent", values="Count", hole=0.4, title="Detected Intents")
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("No intent data available yet.")

    # Product Recommendations
    st.subheader("Final Product Recommendations")
    products = analytics.get("product_recommendations", {})
    if products:
        df_products = pd.DataFrame(list(products.items()), columns=["Product", "Count"])
        fig2 = px.bar(df_products, x="Product", y="Count", color="Product", title="Recommended Debt Products")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No product recommendations made yet.")
        
    # Refresh button
    if st.button("Refresh Data"):
        st.rerun()

else:
    st.warning("Ensure the FastAPI backend is running on http://localhost:8000")
