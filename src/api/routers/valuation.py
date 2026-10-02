"""
src/api/routers/valuation.py

Historical valuation multiples endpoint (Sprint 6, Day 40).

Sourced from market_cap(company_id, year, market_cap_crore,
enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct),
which carries a full year-by-year time series -- unlike the `valuation`
table, which appears to hold only a single latest snapshot per company.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

DB_PATH: str = "nifty100.db"
DEFAULT_FROM_YEAR: int = 2019
DEFAULT_TO_YEAR: int = 2024

router = APIRouter(tags=["valuation"])


@router.get("/market-cap/{company_id}")
def get_valuation_history(company_id: int) -> List[Dict[str, Any]]:
    """
    Return historical valuation multiples (P/E, P/B, EV/EBITDA, dividend
    yield) for a company from 2019 to 2024.

    :param company_id: The company's companies.id value.
    :return: List of yearly valuation rows as dicts, ordered by year ascending.
    :raises HTTPException: 404 if the company_id is not found.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        company_row = conn.execute(
            "SELECT 1 FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if company_row is None:
            raise HTTPException(status_code=404, detail=f"Company id {company_id} not found")

        rows = conn.execute(
            """
            SELECT year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct,
                   market_cap_crore, enterprise_value_crore
            FROM market_cap
            WHERE company_id = ? AND year BETWEEN ? AND ?
            ORDER BY year ASC
            """,
            (company_id, DEFAULT_FROM_YEAR, DEFAULT_TO_YEAR),
        ).fetchall()

    return [dict(row) for row in rows]