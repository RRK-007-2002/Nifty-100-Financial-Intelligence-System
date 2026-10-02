"""
src/api/routers/portfolio.py

Portfolio-wide percentile statistics endpoint (Sprint 6, Day 40).

Rather than recomputing P10-P90 across all companies a second time, this
reads output/portfolio_stats.csv, which src/analytics/profiling.py
(Day 37) already generates from the same 10 core KPIs.
"""

from __future__ import annotations

import csv
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

PORTFOLIO_STATS_CSV: str = "output/portfolio_stats.csv"

router = APIRouter(tags=["portfolio"])


@router.get("/portfolio/stats")
def get_portfolio_stats() -> List[Dict[str, Any]]:
    """
    Return the P10-P90 percentile table for the 10 core KPIs across all
    companies, as previously computed by
    src.analytics.profiling.generate_profiles_and_reports().

    :return: List of per-metric stat rows (metric, P10, P25, P50, P75, P90, Mean, Std).
    :raises HTTPException: 404 if portfolio_stats.csv has not been generated yet.
    """
    try:
        with open(PORTFOLIO_STATS_CSV, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=(
                f"{PORTFOLIO_STATS_CSV} not found -- run "
                "src.analytics.profiling.generate_profiles_and_reports() first"
            ),
        )

    numeric_fields = {"P10", "P25", "P50", "P75", "P90", "Mean", "Std"}
    parsed_rows: List[Dict[str, Any]] = []
    for row in rows:
        parsed = dict(row)
        for field in numeric_fields:
            if field in parsed and parsed[field] != "":
                parsed[field] = float(parsed[field])
        parsed_rows.append(parsed)

    return parsed_rows