"""
src/api/routers/sectors.py

Sector-level endpoints (Sprint 6, Day 40).

SQLite has no built-in MEDIAN() aggregate, so medians are computed in
Python via the statistics module after fetching each sector's raw rows.
"""

from __future__ import annotations

import sqlite3
import statistics
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

DB_PATH: str = "nifty100.db"

router = APIRouter(tags=["sectors"])


def _get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with row access by column name.

    :return: A sqlite3.Connection configured with sqlite3.Row row_factory.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _safe_median(values: List[Any]) -> float | None:
    """
    Compute the median of the non-null values in a list.

    :param values: Raw values, possibly containing None.
    :return: The median, or None if no non-null values are present.
    """
    clean = [v for v in values if v is not None]
    return statistics.median(clean) if clean else None


@router.get("/sectors")
def list_sectors() -> List[Dict[str, Any]]:
    """
    Return every broad_sector with its company count and median ROE,
    P/E and debt-to-equity (each computed from the latest fiscal year
    per company).

    :return: List of sector summary dicts.
    """
    query = """
        SELECT
            s.broad_sector AS broad_sector,
            c.id AS company_id,
            fr.return_on_equity_pct AS roe_pct,
            fr.debt_to_equity AS debt_to_equity,
            v."P/E" AS pe_ratio
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        LEFT JOIN financial_ratios fr ON fr.company_id = c.id
            AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        LEFT JOIN valuation v ON v.company_id = c.id
    """
    with _get_connection() as conn:
        rows = conn.execute(query).fetchall()

    by_sector: Dict[str, Dict[str, List[Any]]] = {}
    for row in rows:
        bucket = by_sector.setdefault(
            row["broad_sector"], {"roe": [], "pe": [], "de": [], "company_ids": set()}
        )
        bucket["company_ids"].add(row["company_id"])
        bucket["roe"].append(row["roe_pct"])
        bucket["pe"].append(row["pe_ratio"])
        bucket["de"].append(row["debt_to_equity"])

    return [
        {
            "broad_sector": sector,
            "company_count": len(bucket["company_ids"]),
            "median_roe": _safe_median(bucket["roe"]),
            "median_pe": _safe_median(bucket["pe"]),
            "median_de": _safe_median(bucket["de"]),
        }
        for sector, bucket in sorted(by_sector.items())
    ]


@router.get("/sectors/{sector}/companies")
def get_sector_companies(sector: str) -> List[Dict[str, Any]]:
    """
    Return all companies in a broad_sector with their latest-year KPIs.

    :param sector: Exact broad_sector name.
    :return: List of company dicts.
    :raises HTTPException: 404 if the sector name matches no rows.
    """
    query = """
        SELECT
            c.id AS company_id,
            c.company_name AS company_name,
            s.sub_sector AS sub_sector,
            fr.return_on_equity_pct AS roe_pct,
            fr.debt_to_equity AS debt_to_equity,
            fr.operating_profit_margin_pct AS operating_profit_margin_pct,
            fr.revenue_cagr_5yr AS revenue_cagr_5yr
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        LEFT JOIN financial_ratios fr ON fr.company_id = c.id
            AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        WHERE s.broad_sector = ?
    """
    with _get_connection() as conn:
        rows = conn.execute(query, (sector,)).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Sector '{sector}' not found")

    return [dict(row) for row in rows]