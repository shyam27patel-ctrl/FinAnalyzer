
import streamlit as st
from financial_analysis import analyze_company

st.set_page_config(
    page_title="FinAnalyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 FinAnalyzer")
st.write("SEC 10-K Financial Analysis Platform")

st.divider()

st.subheader("Company Analysis")

company = st.text_input(
    "Enter a company name or ticker",
    placeholder="e.g. Apple, AAPL, Microsoft"
)

if st.button("Analyse Company"):

    if not company.strip():

        st.warning("Please enter a company name or ticker.")

    else:

        with st.spinner("Retrieving SEC data and analysing company..."):

            try:
                results = analyze_company(company)

                st.success("Analysis completed successfully!")

                st.subheader(
                    f"{results['company_name']} ({results['ticker']})"
                )

                st.write(
                    f"Financial reporting date: {results['report_date']}"
                )

                st.markdown(
                    f"[View SEC 10-K Filing]({results['filing_url']})"
                )

                st.divider()

                st.subheader("Financial Statements")

                st.dataframe(
                    results["financial_statement"],
                    use_container_width=True
                )

                st.divider()

                st.subheader("Financial Ratios")

                st.dataframe(
                    results["ratios"],
                    use_container_width=True
                )

            except Exception as e:

                st.error(f"Analysis failed: {e}")
