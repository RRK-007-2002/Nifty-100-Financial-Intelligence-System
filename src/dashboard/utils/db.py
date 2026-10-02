import sqlite3
# from pathlib import Path
import streamlit as st
import pandas as pd
from pathlib import Path
DB_PATH = Path(r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db")

print(f"[db.py] Using DB_PATH: {DB_PATH}, exists: {DB_PATH.exists()}")
def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(sql, conn, params=params)


@st.cache_data(ttl=600)
def get_companies() -> pd.DataFrame:
    return _query("""
        SELECT c.id AS company_id, c.company_name, c.about_company, c.website,
               c.face_value, c.book_value, c.roce_percentage, c.roe_percentage,
               s.broad_sector AS sector, s.sub_sector, s.market_cap_category
        FROM companies c
        LEFT JOIN (
            SELECT company_id, broad_sector, sub_sector, market_cap_category
            FROM sectors GROUP BY company_id
        ) s ON s.company_id = c.id
    """)


@st.cache_data(ttl=600)
def get_ratios(company_id: str, year: str | None = None) -> pd.DataFrame:
    company_id = company_id.upper().strip()
    if year is None:
        return _query("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year", (company_id,))
    return _query("SELECT * FROM financial_ratios WHERE company_id = ? AND year = ?", (company_id, year))


@st.cache_data(ttl=600)
def get_all_latest_ratios() -> pd.DataFrame:
    """Bulk fetch — latest-year ratios for all companies in ONE query, avoids 92 separate calls."""
    all_r = _query("SELECT * FROM financial_ratios ORDER BY year")
    return all_r.groupby("company_id").tail(1).reset_index(drop=True)


@st.cache_data(ttl=600)
def get_ratios_for_year(year: str) -> pd.DataFrame:
    return _query("SELECT * FROM financial_ratios WHERE year = ?", (year,))


@st.cache_data(ttl=600)
def get_pl(company_id: str) -> pd.DataFrame:
    return _query("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", (company_id.upper().strip(),))


@st.cache_data(ttl=600)
def get_bs(company_id: str) -> pd.DataFrame:
    return _query("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", (company_id.upper().strip(),))


@st.cache_data(ttl=600)
def get_cf(company_id: str) -> pd.DataFrame:
    return _query("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", (company_id.upper().strip(),))


@st.cache_data(ttl=600)
def get_sectors() -> pd.DataFrame:
    return _query("""
        SELECT broad_sector AS sector_name, COUNT(DISTINCT company_id) AS company_count
        FROM sectors GROUP BY broad_sector
    """)


@st.cache_data(ttl=600)
def get_peer_group_names() -> pd.DataFrame:
    return _query("SELECT DISTINCT peer_group_name FROM peer_groups")


@st.cache_data(ttl=600)
def get_peers(group_name: str) -> pd.DataFrame:
    return _query("""
        SELECT pg.company_id, pg.is_benchmark, c.company_name
        FROM peer_groups pg LEFT JOIN companies c ON c.id = pg.company_id
        WHERE pg.peer_group_name = ?
    """, (group_name,))


@st.cache_data(ttl=600)
def get_all_valuation() -> pd.DataFrame:
    return _query("SELECT * FROM valuation")


@st.cache_data(ttl=600)
def get_valuation(company_id: str) -> pd.DataFrame:
    return _query("SELECT * FROM valuation WHERE company_id = ?", (company_id.upper().strip(),))


@st.cache_data(ttl=600)
def get_composite_scores() -> pd.DataFrame:
    """No composite score exists in the schema — DERIVED metric, placeholder weights.
    Still pending your confirmation on the formula."""
    latest = get_all_latest_ratios()
    score = (
        latest["return_on_equity_pct"].fillna(0) * 0.4
        + latest["revenue_cagr_5yr"].fillna(0) * 0.3
        + latest["interest_coverage"].fillna(0) * 0.15
        - latest["debt_to_equity"].fillna(0) * 15 * 0.15
    )
    return pd.DataFrame({"company_id": latest["company_id"], "composite_score": score})


@st.cache_data(ttl=600)
def get_pros_cons(company_id: str) -> pd.DataFrame:
    """pros/cons are single TEXT blobs per company — caller splits on newlines."""
    return _query("SELECT pros, cons FROM prosandcons WHERE company_id = ?", (company_id.upper().strip(),))


@st.cache_data(ttl=600)
def get_capital_patterns() -> pd.DataFrame:
    all_r = _query("SELECT company_id, year, capital_allocation_label FROM financial_ratios ORDER BY year")
    return all_r.groupby("company_id").tail(1).reset_index(drop=True)


@st.cache_data(ttl=600)
def get_documents(company_id: str) -> pd.DataFrame:
    return _query(
        'SELECT company_id, Year AS year, Annual_Report AS pdf_url FROM documents WHERE company_id = ?',
        (company_id.upper().strip(),)
    )
@st.cache_data(ttl=600)
def get_all_latest_market_cap() -> pd.DataFrame:
    """Latest-year market cap + valuation multiples, straight from the market_cap table."""
    all_m = _query("SELECT * FROM market_cap ORDER BY year")
    return all_m.groupby("company_id").tail(1).reset_index(drop=True)


@st.cache_data(ttl=600)
def get_market_cap(company_id: str, year: str | None = None) -> pd.DataFrame:
    company_id = company_id.upper().strip()
    if year is None:
        return _query("SELECT * FROM market_cap WHERE company_id = ? ORDER BY year", (company_id,))
    return _query("SELECT * FROM market_cap WHERE company_id = ? AND year = ?", (company_id, year))