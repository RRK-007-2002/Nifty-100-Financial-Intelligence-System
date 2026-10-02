"""
src/api/routers/peers.py

Peer-group endpoints (Sprint 6, Day 40).

peer_percentiles(company_id, peer_group_name, metric, value, percentile_rank,
year, note) already stores precomputed percentile ranks in long format, so
/peers/{group_name} just pivots that table rather than recomputing ranks.

/companies/{company_id}/peers/compare needs a fixed set of "8 axis metrics"
that the spec does not name. These 8, all on financial_ratios, were chosen
as a broad profitability/leverage/growth spread -- change RADAR_METRICS
below if a different set is wanted:
    return_on_equity_pct, operating_profit_margin_pct, net_profit_margin_pct,
    debt_to_equity, interest_coverage, asset_turnover, revenue_cagr_5yr,
    pat_cagr_5yr
The "peer group average" includes every member of the group (target company
included); the benchmark company is whichever peer_groups row for that
group has is_benchmark = 1.
"""

from __future__ import annotations

import sqlite3
import statistics
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

DB_PATH: str = "nifty100.db"

RADAR_METRICS: List[str] = [
    "return_on_equity_pct",
    "operating_profit_margin_pct",
    "net_profit_margin_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]

router = APIRouter(tags=["peers"])


def _get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with row access by column name.

    :return: A sqlite3.Connection configured with sqlite3.Row row_factory.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@router.get("/peers/{group_name}")
def get_peer_group(group_name: str) -> List[Dict[str, Any]]:
    """
    Return every company in a peer group with its percentile rank for
    each metric present in peer_percentiles, pivoted wide (one row per
    company). Uses each company's latest available year within the group.

    :param group_name: Exact peer_group_name match.
    :return: List of company dicts, each with percentile_rank_<metric> keys.
    :raises HTTPException: 404 if the peer group has no rows.
    """
    query = """
        SELECT pp.company_id, c.company_name, pp.metric, pp.percentile_rank, pp.year
        FROM peer_percentiles pp
        JOIN companies c ON c.id = pp.company_id
        WHERE pp.peer_group_name = ?
          AND pp.year = (
              SELECT MAX(pp2.year) FROM peer_percentiles pp2
              WHERE pp2.company_id = pp.company_id AND pp2.peer_group_name = pp.peer_group_name
          )
    """
    with _get_connection() as conn:
        rows = conn.execute(query, (group_name,)).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found")

    companies: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        entry = companies.setdefault(
            row["company_id"],
            {"company_id": row["company_id"], "company_name": row["company_name"]},
        )
        entry[f"percentile_rank_{row['metric']}"] = row["percentile_rank"]

    return list(companies.values())


def _find_peer_group_for_company(conn: sqlite3.Connection, company_id: int) -> Optional[str]:
    """
    Look up the peer_group_name a company belongs to.

    :param conn: Open SQLite connection.
    :param company_id: The company's companies.id value.
    :return: The peer_group_name, or None if the company is in no group.
    """
    row = conn.execute(
        "SELECT peer_group_name FROM peer_groups WHERE company_id = ? LIMIT 1",
        (company_id,),
    ).fetchone()
    return row["peer_group_name"] if row else None


def _find_benchmark_company_id(conn: sqlite3.Connection, group_name: str) -> Optional[int]:
    """
    Look up the benchmark company for a peer group.

    :param conn: Open SQLite connection.
    :param group_name: The peer_group_name to search.
    :return: The benchmark company's company_id, or None if unset.
    """
    row = conn.execute(
        "SELECT company_id FROM peer_groups WHERE peer_group_name = ? AND is_benchmark = 1 LIMIT 1",
        (group_name,),
    ).fetchone()
    return row["company_id"] if row else None


def _latest_metric_values(conn: sqlite3.Connection, company_id: int) -> Dict[str, Optional[float]]:
    """
    Fetch the latest-year value of each RADAR_METRICS column for a company.

    :param conn: Open SQLite connection.
    :param company_id: The company's companies.id value.
    :return: Mapping of metric name -> latest value (or None if unavailable).
    """
    columns = ", ".join(RADAR_METRICS)
    row = conn.execute(
        f"""
        SELECT {columns} FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year DESC
        LIMIT 1
        """,
        (company_id,),
    ).fetchone()
    if row is None:
        return {metric: None for metric in RADAR_METRICS}
    return {metric: row[metric] for metric in RADAR_METRICS}


@router.get("/companies/{company_id}/peers/compare")
def compare_to_peers(company_id: int) -> Dict[str, Any]:
    """
    Return radar-chart data: this company's latest 8 axis metrics, the
    average of those metrics across its whole peer group, and the same
    metrics for the group's designated benchmark company.

    :param company_id: The company's companies.id value.
    :return: Dict with company, peer_group_average and benchmark sections.
    :raises HTTPException: 404 if the company or its peer group is not found.
    """
    with _get_connection() as conn:
        company_row = conn.execute(
            "SELECT id, company_name FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if company_row is None:
            raise HTTPException(status_code=404, detail=f"Company id {company_id} not found")

        group_name = _find_peer_group_for_company(conn, company_id)
        if group_name is None:
            raise HTTPException(
                status_code=404, detail=f"Company id {company_id} is not in any peer group"
            )

        member_ids = [
            row["company_id"]
            for row in conn.execute(
                "SELECT company_id FROM peer_groups WHERE peer_group_name = ?", (group_name,)
            ).fetchall()
        ]

        company_metrics = _latest_metric_values(conn, company_id)

        group_metrics: Dict[str, List[float]] = {metric: [] for metric in RADAR_METRICS}
        for member_id in member_ids:
            member_values = _latest_metric_values(conn, member_id)
            for metric, value in member_values.items():
                if value is not None:
                    group_metrics[metric].append(value)
        group_average = {
            metric: (statistics.mean(values) if values else None)
            for metric, values in group_metrics.items()
        }

        benchmark_id = _find_benchmark_company_id(conn, group_name)
        benchmark_metrics = _latest_metric_values(conn, benchmark_id) if benchmark_id else None
        benchmark_name = None
        if benchmark_id is not None:
            benchmark_row = conn.execute(
                "SELECT company_name FROM companies WHERE id = ?", (benchmark_id,)
            ).fetchone()
            benchmark_name = benchmark_row["company_name"] if benchmark_row else None

    return {
        "peer_group_name": group_name,
        "company": {
            "company_id": company_id,
            "company_name": company_row["company_name"],
            "metrics": company_metrics,
        },
        "peer_group_average": {"metrics": group_average},
        "benchmark": {
            "company_id": benchmark_id,
            "company_name": benchmark_name,
            "metrics": benchmark_metrics,
        },
    }