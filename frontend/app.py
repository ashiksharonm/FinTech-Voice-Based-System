import streamlit as st

st.set_page_config(
    page_title="FinBot Analytics",
    page_icon="💬",
    layout="wide"
)

st.title("FinBot Analytics: B2B Debt Discovery")

st.markdown("""
Welcome to the FinBot Analytics platform!

This application serves two main purposes:
1. **Chat Interface**: A conversational agent to help corporate borrowers discover debt products.
2. **Analytics Dashboard**: A telemetry dashboard for Conversational Analysts to monitor drop-off rates, intent resolution, and user sentiment.

Please select a page from the sidebar to continue.
""")
