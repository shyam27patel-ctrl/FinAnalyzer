
import os
import requests
import pandas as pd
import numpy as np
from functools import lru_cache


# ==========================================
# SEC CONNECTION
# ==========================================

def get_sec_headers():
    """Create a private SEC User-Agent using your contact email."""

    email = os.getenv("SEC_EMAIL", "")

    try:
        import streamlit as st
        email = st.secrets.get("SEC_EMAIL", email)
    except Exception:
        pass

    if not email:
        raise ValueError(
            "SEC contact email is missing. "
            "Please configure SEC_EMAIL in Streamlit Secrets."
        )

    return {
        "User-Agent": f"FinAnalyzer/0.1 ({email})",
        "Accept-Encoding": "gzip, deflate"
    }


SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"


# ==========================================
# DOWNLOAD SEC COMPANY DATABASE
# ==========================================

@lru_cache(maxsize=1)
def get_companies():

    response = requests.get(
        SEC_TICKERS_URL,
        headers=get_sec_headers(),
        timeout=30
    )

    response.raise_for_status()

    ticker_data = response.json()

    companies = pd.DataFrame.from_dict(
        ticker_data,
        orient="index"
    )

    return companies


# ==========================================
# COMPANY SEARCH
# ==========================================

def search_company(query):

    companies = get_companies()

    query = str(query).strip().upper()

    if query.isdigit():

        results = companies[
            companies["cik_str"].astype(str) == str(int(query))
        ]

    else:

        exact_ticker = companies[
            companies["ticker"].str.upper() == query
        ]

        if not exact_ticker.empty:
            results = exact_ticker

        else:
            results = companies[
                companies["title"].str.upper().str.contains(
                    query,
                    na=False,
                    regex=False
                )
            ]

    if results.empty:
        return None

    return results[
        ["title", "ticker", "cik_str"]
    ].head(10)


# ==========================================
# RETRIEVE COMPANY FACTS
# ==========================================

def get_company_facts(cik):

    cik = str(int(cik)).zfill(10)

    url = (
        f"https://data.sec.gov/api/xbrl/companyfacts/"
        f"CIK{cik}.json"
    )

    response = requests.get(
        url,
        headers=get_sec_headers(),
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ==========================================
# RETRIEVE COMPANY FILINGS
# ==========================================

def get_company_filings(cik):

    cik = str(int(cik)).zfill(10)

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    response = requests.get(
        url,
        headers=get_sec_headers(),
        timeout=30
    )

    response.raise_for_status()

    submissions = response.json()

    return pd.DataFrame(
        submissions["filings"]["recent"]
    )


# ==========================================
# EXTRACT FINANCIAL FIGURES
# ==========================================

def extract_financial_fact(
    financial_data,
    tag_candidates,
    accession_number,
    report_date,
    period_type
):

    us_gaap = financial_data["facts"]["us-gaap"]

    for tag in tag_candidates:

        if tag not in us_gaap:
            continue

        concept = us_gaap[tag]

        if "USD" not in concept["units"]:
            continue

        observations = pd.DataFrame(
            concept["units"]["USD"]
        )

        if "start" not in observations.columns:
            observations["start"] = pd.NA

        if "end" not in observations.columns:
            observations["end"] = pd.NA

        observations = observations[
            (observations["accn"] == accession_number) &
            (observations["end"] == report_date)
        ].copy()

        if period_type == "instant":

            observations = observations[
                observations["start"].isna()
            ]

        elif period_type == "duration":

            observations = observations[
                observations["start"].notna()
            ].copy()

            observations["start"] = pd.to_datetime(
                observations["start"]
            )

            observations["end"] = pd.to_datetime(
                observations["end"]
            )

            observations["days"] = (
                observations["end"] -
                observations["start"]
            ).dt.days

            observations = observations[
                observations["days"].between(330, 400)
            ]

        else:
            raise ValueError("Invalid period_type")

        if not observations.empty:

            result = observations.sort_values(
                "filed"
            ).iloc[-1]

            return {
                "tag": tag,
                "value": result["val"],
                "unit": "USD",
                "start": result["start"],
                "end": result["end"],
                "filed": result["filed"],
                "accession": result["accn"]
            }

    return None


# ==========================================
# FINANCIAL STATEMENT ITEMS
# ==========================================

financial_items = {

    "Revenue": {
        "tags": [
            "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet",
            "Revenues"
        ],
        "period": "duration"
    },

    "Cost of Revenue": {
        "tags": [
            "CostOfGoodsAndServicesSold",
            "CostOfRevenue"
        ],
        "period": "duration"
    },

    "Gross Profit": {
        "tags": ["GrossProfit"],
        "period": "duration"
    },

    "Operating Income": {
        "tags": ["OperatingIncomeLoss"],
        "period": "duration"
    },

    "Net Income": {
        "tags": ["NetIncomeLoss"],
        "period": "duration"
    },

    "Current Assets": {
        "tags": ["AssetsCurrent"],
        "period": "instant"
    },

    "Current Liabilities": {
        "tags": ["LiabilitiesCurrent"],
        "period": "instant"
    },

    "Total Assets": {
        "tags": ["Assets"],
        "period": "instant"
    },

    "Total Liabilities": {
        "tags": ["Liabilities"],
        "period": "instant"
    },

    "Shareholders' Equity": {
        "tags": ["StockholdersEquity"],
        "period": "instant"
    },

    "Cash and Equivalents": {
        "tags": ["CashAndCashEquivalentsAtCarryingValue"],
        "period": "instant"
    },

    "Inventory": {
        "tags": ["InventoryNet"],
        "period": "instant"
    }
}


# ==========================================
# HELPER: SAFE DIVISION
# ==========================================

def safe_divide(numerator, denominator):

    if (
        numerator is None or
        denominator is None or
        denominator == 0
    ):
        return np.nan

    return numerator / denominator
