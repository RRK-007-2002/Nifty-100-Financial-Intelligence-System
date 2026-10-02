# src/analytics/build_ratios.py
import pandas as pd
import sqlite3

from ratio import (net_profit_margin, operating_profit_margin,
                     return_on_equity, return_on_capital_employed,
                     debt_to_equity, interest_coverage_ratio,
                     asset_turnover)
from cagr import revenue_cagr, pat_cagr, eps_cagr
from cashflow_kpis import free_cash_flow, cfo_quality_score, capex_intensity


def _deduplicate_company_year(df):
    """Keep one statement row per company-year before year indexing."""
    return df.sort_values("id").drop_duplicates(["company_id", "year"], keep="first")


def build_ratio_row(company_id, year, pl_row, bs_row, cf_row,
                     sales_series, pat_series, eps_series, is_financials):
    """One company-year -> one dict matching financial_ratios columns."""
    npm = net_profit_margin(pl_row["net_profit"], pl_row["sales"])
    opm = operating_profit_margin(pl_row["operating_profit"], pl_row["sales"],
                                   pl_row.get("opm_percentage"))
    roe = return_on_equity(pl_row["net_profit"], bs_row["equity_capital"], bs_row["reserves"])
    de = debt_to_equity(bs_row["borrowings"], bs_row["equity_capital"],
                         bs_row["reserves"], is_financials)
    icr, icr_label, _ = interest_coverage_ratio(pl_row["operating_profit"],
                                                  pl_row.get("other_income", 0),
                                                  pl_row["interest"])
    at = asset_turnover(pl_row["sales"], bs_row["total_assets"])
    fcf = free_cash_flow(cf_row["operating_activity"], cf_row["investing_activity"])

    rev_cagr_5, rev_flag = revenue_cagr(sales_series, 5)
    pat_cagr_5, pat_flag = pat_cagr(pat_series, 5)
    eps_cagr_5, eps_flag = eps_cagr(eps_series, 5)

    return {
        "company_id": company_id, "year": year,
        "net_profit_margin_pct": npm,
        "operating_profit_margin_pct": opm,
        "return_on_equity_pct": roe,
        "debt_to_equity": de,
        "interest_coverage": icr,
        "asset_turnover": at,
        "free_cash_flow_cr": fcf,
        "capex_cr": abs(cf_row["investing_activity"]),
        "earnings_per_share": pl_row.get("eps"),
        "book_value_per_share": (bs_row["equity_capital"] + bs_row["reserves"])
                                  / (bs_row["equity_capital"] / pl_row.get("face_value", 1)),
        "dividend_payout_ratio_pct": pl_row.get("dividend_payout"),
        "total_debt_cr": bs_row["borrowings"],
        "cash_from_operations_cr": cf_row["operating_activity"],
        "revenue_cagr_5yr": rev_cagr_5,
        "pat_cagr_5yr": pat_cagr_5,
        "eps_cagr_5yr": eps_cagr_5,
    }


def build_all_ratios(companies_df, pl_df, bs_df, cf_df, sectors_df):
    pl_df = _deduplicate_company_year(pl_df)
    bs_df = _deduplicate_company_year(bs_df)
    cf_df = _deduplicate_company_year(cf_df)

    financials_ids = set(sectors_df[sectors_df.broad_sector == "Financials"].company_id)
    rows = []

    for company_id in companies_df["id"]:
        company_pl = pl_df[pl_df.company_id == company_id].sort_values("year")
        company_bs = bs_df[bs_df.company_id == company_id].set_index("year")
        company_cf = cf_df[cf_df.company_id == company_id].set_index("year")

        sales_series = dict(zip(company_pl.year, company_pl.sales))
        pat_series = dict(zip(company_pl.year, company_pl.net_profit))
        eps_series = dict(zip(company_pl.year, company_pl.eps))

        for _, pl_row in company_pl.iterrows():
            year = pl_row["year"]
            if year not in company_bs.index or year not in company_cf.index:
                continue  # skip years missing BS or CF data
            rows.append(build_ratio_row(
                company_id, year, pl_row, company_bs.loc[year], company_cf.loc[year],
                sales_series, pat_series, eps_series,
                is_financials=company_id in financials_ids
            ))

    return pd.DataFrame(rows)


def load_to_db(df, db_path="nifty100.db"):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    df.to_sql("financial_ratios", conn, if_exists="append", index=False)
    count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    print(f"financial_ratios row count: {count}")
    conn.close()


	
