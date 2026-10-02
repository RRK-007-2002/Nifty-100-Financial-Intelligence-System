"""
src/api/routers/screener.py

Company screener endpoint (Sprint 6, Day 40).

Numeric filters are accepted as strings and parsed manually so that an
invalid value (e.g. min_roe=abc) can return HTTP 400, matching the spec --
FastAPI's default typed-query validation would otherwise return 422.

max_pe is matched against valuation."P/E" (a precomputed, already-latest
snapshot per company) rather than market_cap.pe_ratio, since the valuation
table appears purpose-built for screening/flagging. Ranking is by
return_on_equity_pct descending -- the spec asks for a "ranked" list but
does not say by what; change ORDER BY below if a different ranking is wanted.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

DB_PATH: str = "nifty100.db"

router = APIRouter(tags=["screener"])

_FLOAT_PARAMS = (
    "min_roe",
    "max_de",
    "min_fcf",
    "min_rev_cagr_5yr",
    "min_pat_cagr_5yr",
    "max_pe",
)


def _parse_float_params(raw_values: Dict[str, Optional[str]]) -> Dict[str, Optional[float]]:
    """
    Parse a dict of optional string query params into floats, raising
    HTTP 400 (not FastAPI's default 422) on the first invalid value.

    :param raw_values: Mapping of query param name -> raw string value (or None).
    :return: Mapping of the same names to parsed float values (or None).
    :raises HTTPException: 400 if any supplied value cannot be parsed as a float.
    """
    parsed: Dict[str, Optional[float]] = {}
    for name, raw in raw_values.items():
        if raw is None:
            parsed[name] = None
            continue
        try:
            parsed[name] = float(raw)
        except ValueError:
            raise HTTPException(
                status_code=400, detail=f"Invalid value for '{name}': '{raw}'"
            )
    return parsed


@router.get("/screener")
def run_screener(
    min_roe: Optional[str] = Query(default=None, description="Minimum ROE %"),
    max_de: Optional[str] = Query(default=None, description="Maximum debt-to-equity"),
    min_fcf: Optional[str] = Query(default=None, description="Minimum free cash flow (Cr)"),
    sector: Optional[str] = Query(default=None, description="Exact broad_sector match"),
    min_rev_cagr_5yr: Optional[str] = Query(default=None),
    min_pat_cagr_5yr: Optional[str] = Query(default=None),
    max_pe: Optional[str] = Query(default=None),
) -> List[Dict[str, Any]]:
    """
    Return companies matching all supplied filters, ranked by ROE descending.

    :param min_roe: Minimum return_on_equity_pct (latest year).
    :param max_de: Maximum debt_to_equity (latest year).
    :param min_fcf: Minimum free_cash_flow_cr (latest year).
    :param sector: Exact-match broad_sector filter.
    :param min_rev_cagr_5yr: Minimum revenue_cagr_5yr (latest year).
    :param min_pat_cagr_5yr: Minimum pat_cagr_5yr (latest year).
    :param max_pe: Maximum valuation."P/E".
    :return: List of company dicts with all filter metrics included.
    :raises HTTPException: 400 for an unparseable numeric filter value.
    """
    parsed = _parse_float_params(
        {
            "min_roe": min_roe,
            "max_de": max_de,
            "min_fcf": min_fcf,
            "min_rev_cagr_5yr": min_rev_cagr_5yr,
            "min_pat_cagr_5yr": min_pat_cagr_5yr,
            "max_pe": max_pe,
        }
    )

    query = """
        SELECT
            c.id AS company_id,
            c.company_name AS company_name,
            s.broad_sector AS broad_sector,
            fr.return_on_equity_pct AS roe_pct,
            fr.debt_to_equity AS debt_to_equity,
            fr.free_cash_flow_cr AS free_cash_flow_cr,
            fr.revenue_cagr_5yr AS revenue_cagr_5yr,
            fr.pat_cagr_5yr AS pat_cagr_5yr,
            v."P/E" AS pe_ratio
        FROM companies c
        JOIN sectors s ON s.company_id = c.id
        JOIN financial_ratios fr ON fr.company_id = c.id
            AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
        LEFT JOIN valuation v ON v.company_id = c.id
        WHERE 1 = 1
    """
    params: List[Any] = []

    if parsed["min_roe"] is not None:
        query += " AND fr.return_on_equity_pct >= ?"
        params.append(parsed["min_roe"])
    if parsed["max_de"] is not None:
        query += " AND fr.debt_to_equity <= ?"
        params.append(parsed["max_de"])
    if parsed["min_fcf"] is not None:
        query += " AND fr.free_cash_flow_cr >= ?"
        params.append(parsed["min_fcf"])
    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if parsed["min_rev_cagr_5yr"] is not None:
        query += " AND fr.revenue_cagr_5yr >= ?"
        params.append(parsed["min_rev_cagr_5yr"])
    if parsed["min_pat_cagr_5yr"] is not None:
        query += " AND fr.pat_cagr_5yr >= ?"
        params.append(parsed["min_pat_cagr_5yr"])
    if parsed["max_pe"] is not None:
        query += ' AND v."P/E" <= ?'
        params.append(parsed["max_pe"])

    query += " ORDER BY fr.return_on_equity_pct DESC"

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()

    return [dict(row) for row in rows]