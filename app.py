
import streamlit as st
import pandas as pd

from financial_analysis import analyze_company

from historical_analysis import (
    extract_historical_financials,
    calculate_historical_ratios
)


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

years = st.selectbox(
    "Historical reporting years",
    [3, 5, 7, 10],
    index=1
)


if st.button("Analyse Company"):

    if not company.strip():

        st.warning("Please enter a company name or ticker.")

    else:

        with st.spinner("Retrieving SEC data and analysing company..."):

            try:

                results = analyze_company(company)

                st.success("Company analysis completed!")

                st.subheader(
                    f"{results['company_name']} ({results['ticker']})"
                )

                st.write(
                    f"Latest reporting date: {results['report_date']}"
                )

                st.markdown(
                    f"[View SEC 10-K Filing]({results['filing_url']})"
                )

                st.divider()

                # CURRENT YEAR ANALYSIS

                st.header("Current Financial Analysis")

                st.subheader("Financial Statements")

                st.dataframe(
                    results["financial_statement"],
                    use_container_width=True
                )

                st.subheader("Financial Ratios")

                st.dataframe(
                    results["ratios"],
                    use_container_width=True
                )

                st.divider()

                # HISTORICAL ANALYSIS

                st.header("Historical Financial Analysis")

                with st.spinner("Retrieving historical financial information..."):

                    historical = extract_historical_financials(
                        results["cik"],
                        years=years
                    )

                    historical_ratios = calculate_historical_ratios(
                        historical
                    )

                st.subheader("Historical Financial Statements")

                display_financials = historical.copy()

                display_financials["Reporting Date"] = (
                    display_financials["Reporting Date"].dt.strftime("%Y-%m-%d")
                )

                st.dataframe(
                    display_financials,
                    use_container_width=True
                )

                st.subheader("Historical Financial Ratios")

                ratio_columns = [
                    "Reporting Date",
                    "Current Ratio",
                    "Quick Ratio",
                    "Cash Ratio",
                    "Debt-to-Assets",
                    "Debt-to-Equity",
                    "Gross Profit Margin",
                    "Operating Profit Margin",
                    "Net Profit Margin",
                    "ROA",
                    "ROE",
                    "Asset Turnover",
                    "Inventory Turnover"
                ]

                st.dataframe(
                    historical_ratios[ratio_columns].round(2),
                    use_container_width=True
                )

                st.divider()

                # HISTORICAL GRAPHS

                st.header("Financial Performance Trends")

                chart_data = historical_ratios.copy()

                chart_data["Year"] = (
                    chart_data["Reporting Date"].dt.year.astype(str)
                )

                chart_data = chart_data.set_index("Year")

                st.subheader("1. Revenue Trend")

                st.line_chart(
                    chart_data[["Revenue"]] / 1_000_000_000,
                    y_label="Revenue ($ billions)"
                )

                st.subheader("2. Net Income Trend")

                st.line_chart(
                    chart_data[["Net Income"]] / 1_000_000_000,
                    y_label="Net Income ($ billions)"
                )

                st.subheader("3. Profitability Trends")

                st.line_chart(
                    chart_data[
                        [
                            "Gross Profit Margin",
                            "Operating Profit Margin",
                            "Net Profit Margin"
                        ]
                    ],
                    y_label="Profitability (%)"
                )

                st.subheader("4. Liquidity Trends")

                st.line_chart(
                    chart_data[
                        [
                            "Current Ratio",
                            "Quick Ratio",
                            "Cash Ratio"
                        ]
                    ],
                    y_label="Liquidity ratio (x)"
                )

                st.subheader("5. Financial Leverage Trends")

                st.line_chart(
                    chart_data[
                        [
                            "Debt-to-Assets",
                            "Debt-to-Equity"
                        ]
                    ],
                    y_label="Leverage ratios"
                )

                st.success("Historical analysis and graphs completed!")

            except Exception as e:

                st.error(f"Analysis failed: {e}")
