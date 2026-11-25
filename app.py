
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="FinAnalyzer",
    page_icon="📊",
    layout="wide"
)

# Website heading
st.title("📊 FinAnalyzer")

st.write(
    "Your financial analysis platform."
)

st.divider()

# Company search
st.subheader("Company Analysis")

company = st.text_input(
    "Enter a company name or ticker",
    placeholder="e.g. Apple, AAPL, Microsoft"
)

if st.button("Analyse Company"):

    if company:
        st.success(f"Ready to analyse: {company}")

    else:
        st.warning(
            "Please enter a company name or ticker."
        )
