# src/analytics/peer.py
"""
Day 18: Peer percentile rankings.
Reuses period_utils.get_latest_annual_snapshot() for latest-year data.
"""

import numpy as np
import pandas as pd

# D/E is inverted: lower D/E = higher percentile rank.
PEER_METRICS = {
    "return_on_equity_pct": False,
    "net_profit_margin_pct": False,
    "debt_to_equity": True,      # invert
    "free_cash_flow_cr": False,
    "pat_cagr_5yr": False,
    "revenue_cagr_5yr": False,
    "eps_cagr_5yr": False,
    "interest_coverage": False,
    "asset_turnover": False,
    # ROCE excluded — same missing-column reason as Day 17 (documented, not fabricated)
}


def compute_peer_percentiles(universe: pd.DataFrame, peer_groups: pd.DataFrame) -> pd.DataFrame:
    """
    universe: latest-annual financial_ratios (+ any needed columns), one row/company.
    peer_groups: company_id, peer_group_name (raw peer_groups table).

    Returns long-format table: company_id, peer_group_name, metric, value,
    percentile_rank, matching the peer_percentiles SQLite schema from the spec.

    Companies with NO peer group get a row with metric='__no_group__',
    percentile_rank=NaN and a note — per spec: "No peer group assigned,
    do not raise an error."
    """
    merged = universe.copy()
    if "company_id" in merged.columns and merged["company_id"].duplicated().any():
        if "year" in merged.columns:
            merged = merged.sort_values(["company_id", "year"], ascending=[True, False]).drop_duplicates(subset=["company_id"], keep="first")
        else:
            merged = merged.drop_duplicates(subset=["company_id"], keep="last")

    merged = merged.merge(peer_groups[["company_id", "peer_group_name"]], on="company_id", how="left")

    no_group = merged[merged["peer_group_name"].isna()]["company_id"].unique()
    records = []
    for cid in no_group:
        records.append({
            "company_id": cid, "peer_group_name": None, "metric": "__no_group__",
            "value": None, "percentile_rank": None, "note": "No peer group assigned",
        })

    grouped = merged.dropna(subset=["peer_group_name"])
    for group_name, group_df in grouped.groupby("peer_group_name"):
        group_df = group_df.drop_duplicates(subset=["company_id"], keep="last")
        for metric, invert in PEER_METRICS.items():
            if metric not in group_df.columns:
                continue
            values = group_df[metric].astype(float)
            pct_rank = values.rank(pct=True, method="average")
            if invert:
                pct_rank = 1 - pct_rank
            for cid, val, pr in zip(group_df["company_id"], values, pct_rank):
                records.append({
                    "company_id": cid, "peer_group_name": group_name, "metric": metric,
                    "value": None if pd.isna(val) else val,
                    "percentile_rank": None if pd.isna(pr) else round(pr, 4),
                    "note": None,
                })

    return pd.DataFrame(records)


def save_peer_percentiles_to_db(peer_percentiles: pd.DataFrame, conn, year: int) -> None:
    """Writes to peer_percentiles table. Creates table if absent (non-destructive: CREATE IF NOT EXISTS)."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS peer_percentiles (
            company_id TEXT, peer_group_name TEXT, metric TEXT,
            value REAL, percentile_rank REAL, year INTEGER, note TEXT
        )
    """)
    out = peer_percentiles.copy()
    out["year"] = year
    out.to_sql("peer_percentiles", conn, if_exists="append", index=False)
    conn.commit()