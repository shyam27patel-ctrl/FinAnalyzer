
import pandas as pd
import numpy as np

from sec_data import (
    get_company_facts,
    get_company_filings,
    extract_financial_fact,
    financial_items
)


def get_historical_filings(cik, years=5):

    filings = get_company_filings(cik)

    annual_filings = filings[
        filings["form"] == "10-K"
    ].copy()

    if annual_filings.empty:
        raise ValueError("No historical 10-K filings found.")

    annual_filings["filingDate"] = pd.to_datetime(
        annual_filings["filingDate"]
    )

    annual_filings = annual_filings.sort_values(
        "filingDate",
        ascending=False
    )

    historical = annual_filings.head(years).copy()

    return historical[
        [
            "form",
            "filingDate",
            "reportDate",
            "accessionNumber",
            "primaryDocument"
        ]
    ].reset_index(drop=True)


def extract_historical_financials(cik, years=5):

    financial_data = get_company_facts(cik)

    historical_filings = get_historical_filings(
        cik,
        years=years
    )

    historical_results = []

    for _, filing in historical_filings.iterrows():

        accession_number = filing["accessionNumber"]
        report_date = filing["reportDate"]

        annual_data = {
            "Reporting Date": report_date
        }

        for item, details in financial_items.items():

            result = extract_financial_fact(
                financial_data=financial_data,
                tag_candidates=details["tags"],
                accession_number=accession_number,
                report_date=report_date,
                period_type=details["period"]
            )

            annual_data[item] = (
                result["value"]
                if result is not None
                else np.nan
            )

        historical_results.append(annual_data)

    historical_df = pd.DataFrame(historical_results)

    historical_df["Reporting Date"] = pd.to_datetime(
        historical_df["Reporting Date"]
    )

    historical_df = historical_df.sort_values(
        "Reporting Date"
    ).reset_index(drop=True)

    return historical_df


def calculate_historical_ratios(historical_df):

    historical = historical_df.copy()

    def divide(numerator, denominator):

        result = numerator / denominator

        return result.replace(
            [np.inf, -np.inf],
            np.nan
        )

    historical["Current Ratio"] = divide(
        historical["Current Assets"],
        historical["Current Liabilities"]
    )

    historical["Quick Ratio"] = divide(
        historical["Current Assets"] - historical["Inventory"],
        historical["Current Liabilities"]
    )

    historical["Cash Ratio"] = divide(
        historical["Cash and Equivalents"],
        historical["Current Liabilities"]
    )

    historical["Debt-to-Assets"] = divide(
        historical["Total Liabilities"],
        historical["Total Assets"]
    ) * 100

    historical["Debt-to-Equity"] = divide(
        historical["Total Liabilities"],
        historical["Shareholders' Equity"]
    )

    historical["Gross Profit Margin"] = divide(
        historical["Gross Profit"],
        historical["Revenue"]
    ) * 100

    historical["Operating Profit Margin"] = divide(
        historical["Operating Income"],
        historical["Revenue"]
    ) * 100

    historical["Net Profit Margin"] = divide(
        historical["Net Income"],
        historical["Revenue"]
    ) * 100

    historical["ROA"] = divide(
        historical["Net Income"],
        historical["Total Assets"]
    ) * 100

    historical["ROE"] = divide(
        historical["Net Income"],
        historical["Shareholders' Equity"]
    ) * 100

    historical["Asset Turnover"] = divide(
        historical["Revenue"],
        historical["Total Assets"]
    )

    historical["Inventory Turnover"] = divide(
        historical["Cost of Revenue"],
        historical["Inventory"]
    )

    return historical.replace(
        [np.inf, -np.inf],
        np.nan
    )
