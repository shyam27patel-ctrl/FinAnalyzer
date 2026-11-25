
import pandas as pd
import numpy as np

from sec_data import (
    search_company,
    get_company_facts,
    get_company_filings,
    extract_financial_fact,
    financial_items,
    safe_divide
)


# ==========================================
# MAIN COMPANY ANALYSIS
# ==========================================

def analyze_company(company_query):

    # 1. Search for the company
    company_results = search_company(company_query)

    if company_results is None or company_results.empty:
        raise ValueError(
            f"No company found for '{company_query}'."
        )

    company = company_results.iloc[0]

    company_name = company["title"]
    ticker = company["ticker"]
    cik = str(int(company["cik_str"])).zfill(10)

    # 2. Retrieve SEC financial information
    financial_data = get_company_facts(cik)

    # 3. Retrieve filing history
    filings = get_company_filings(cik)

    # 4. Find latest annual 10-K
    annual_filings = filings[
        filings["form"] == "10-K"
    ].copy()

    if annual_filings.empty:
        raise ValueError("No annual 10-K filing found.")

    annual_filings["filingDate"] = pd.to_datetime(
        annual_filings["filingDate"]
    )

    annual_filings = annual_filings.sort_values(
        "filingDate",
        ascending=False
    )

    latest_filing = annual_filings.iloc[0]

    accession_number = latest_filing["accessionNumber"]
    report_date = latest_filing["reportDate"]

    filing_date = latest_filing["filingDate"].strftime(
        "%Y-%m-%d"
    )

    accession_clean = accession_number.replace("-", "")

    filing_url = (
        f"https://www.sec.gov/Archives/edgar/data/"
        f"{int(cik)}/{accession_clean}/"
        f"{latest_filing['primaryDocument']}"
    )

    # 5. Extract financial statement figures
    financials = {}

    for item, details in financial_items.items():

        result = extract_financial_fact(
            financial_data=financial_data,
            tag_candidates=details["tags"],
            accession_number=accession_number,
            report_date=report_date,
            period_type=details["period"]
        )

        financials[item] = result

    # 6. Retrieve individual financial figures
    def value(item):

        result = financials.get(item)

        if result is None:
            return None

        return result["value"]

    revenue = value("Revenue")
    cost_of_revenue = value("Cost of Revenue")
    gross_profit = value("Gross Profit")
    operating_income = value("Operating Income")
    net_income = value("Net Income")

    current_assets = value("Current Assets")
    current_liabilities = value("Current Liabilities")
    total_assets = value("Total Assets")
    total_liabilities = value("Total Liabilities")
    equity = value("Shareholders' Equity")

    cash = value("Cash and Equivalents")
    inventory = value("Inventory")

    # 7. Calculate the 12 financial ratios
    ratios = [

        ("Current Ratio",
         safe_divide(current_assets, current_liabilities),
         "Current Assets / Current Liabilities", "x"),

        ("Quick Ratio (Approx.)",
         safe_divide(
             current_assets - inventory
             if current_assets is not None and inventory is not None
             else None,
             current_liabilities
         ),
         "(Current Assets - Inventory) / Current Liabilities", "x"),

        ("Cash Ratio",
         safe_divide(cash, current_liabilities),
         "Cash / Current Liabilities", "x"),

        ("Debt-to-Assets Ratio",
         safe_divide(total_liabilities, total_assets),
         "Total Liabilities / Total Assets", "%"),

        ("Debt-to-Equity Ratio",
         safe_divide(total_liabilities, equity),
         "Total Liabilities / Equity", "x"),

        ("Gross Profit Margin",
         safe_divide(gross_profit, revenue),
         "Gross Profit / Revenue", "%"),

        ("Operating Profit Margin",
         safe_divide(operating_income, revenue),
         "Operating Income / Revenue", "%"),

        ("Net Profit Margin",
         safe_divide(net_income, revenue),
         "Net Income / Revenue", "%"),

        ("Return on Assets (ROA)",
         safe_divide(net_income, total_assets),
         "Net Income / Total Assets", "%"),

        ("Return on Equity (ROE)",
         safe_divide(net_income, equity),
         "Net Income / Equity", "%"),

        ("Asset Turnover",
         safe_divide(revenue, total_assets),
         "Revenue / Total Assets", "x"),

        ("Inventory Turnover",
         safe_divide(cost_of_revenue, inventory),
         "Cost of Revenue / Inventory", "x")
    ]

    ratios_df = pd.DataFrame(
        ratios,
        columns=["Ratio", "Result", "Formula", "Unit"]
    )

    # Convert percentage ratios into percentages
    percentage_rows = ratios_df["Unit"] == "%"

    ratios_df.loc[percentage_rows, "Result"] *= 100

    ratios_df["Result"] = ratios_df["Result"].round(2)

    # 8. Build financial statement table
    financial_rows = []

    for item, result in financials.items():

        financial_rows.append({
            "Financial Item": item,

            "Reported Value ($bn)": (
                result["value"] / 1_000_000_000
                if result is not None else np.nan
            ),

            "XBRL Tag": (
                result["tag"]
                if result is not None else "Not found"
            )
        })

    financial_statement = pd.DataFrame(financial_rows)

    financial_statement["Reported Value ($bn)"] = (
        financial_statement["Reported Value ($bn)"].round(2)
    )

    # 9. Return results for Streamlit
    return {
        "company_name": company_name,
        "ticker": ticker,
        "cik": cik,
        "report_date": report_date,
        "filing_date": filing_date,
        "filing_url": filing_url,
        "financials": financials,
        "financial_statement": financial_statement,
        "ratios": ratios_df
    }
