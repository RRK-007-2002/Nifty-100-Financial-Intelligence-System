# src/screener/engine.py
"""
Day 15-16 deliverable: config-driven screener engine.
Reuses src.screener.period_utils for all date/latest-snapshot logic.
"""

from pathlib import Path
from typing import Any
import operator as op
import logging

import numpy as np
import pandas as pd
import yaml

from period_utils import get_latest_annual_snapshot

logger = logging.getLogger(__name__)

OPERATORS = {
    ">": op.gt,
    "<": op.lt,
    ">=": op.ge,
    "<=": op.le,
    "==": None,  # handled specially (float-safe via np.isclose)
}

FLOAT_EQ_ATOL = 1e-6


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------
def load_screener_config(config_path: str | Path) -> dict:
    config_path = Path(config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"screener_config.yaml not found at {config_path}")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    if "presets" not in config:
        raise ValueError("screener_config.yaml missing required top-level key: 'presets'")
    return config


# ---------------------------------------------------------------------------
# Universe assembly — merges the 3 source tables into one screener input
# ---------------------------------------------------------------------------
def build_screener_universe(conn) -> pd.DataFrame:
    """
    Assembles the screener's input DataFrame from financial_ratios,
    sectors, market_cap, and profitandloss — using each company's
    LATEST annual (Mar/Dec) snapshot only. Does not average or use
    stale data.

    Raises explicitly (does not silently drop) if a required source
    table/column is missing.
    """
    required_tables = {"financial_ratios", "sectors", "market_cap", "profitandloss"}
    existing = {
        row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    missing_tables = required_tables - existing
    if missing_tables:
        raise RuntimeError(
            f"Cannot build screener universe — missing tables: {missing_tables}. "
            "These must exist from Sprint 1/2; not fabricated here."
        )

    fr_all = pd.read_sql("SELECT * FROM financial_ratios", conn)
    mc_all = pd.read_sql("SELECT * FROM market_cap", conn)
    pnl_all = pd.read_sql("SELECT * FROM profitandloss", conn)
    sectors = pd.read_sql("SELECT company_id, broad_sector FROM sectors", conn)

    fr_latest = get_latest_annual_snapshot(fr_all, offset=0)
    mc_latest = get_latest_annual_snapshot(mc_all, offset=0)
    pnl_latest = get_latest_annual_snapshot(pnl_all, offset=0)

    keep_fr = [c for c in fr_latest.columns if not c.startswith("_")]
    keep_mc = ["company_id", "pe_ratio", "pb_ratio", "dividend_yield_pct", "market_cap_crore"]
    keep_pnl = ["company_id", "sales", "net_profit"]

    universe = (
        fr_latest[keep_fr]
        .merge(sectors, on="company_id", how="left")
        .merge(mc_latest[keep_mc], on="company_id", how="left")
        .merge(pnl_latest[keep_pnl], on="company_id", how="left")
    )

    missing_sector = universe["broad_sector"].isna().sum()
    if missing_sector:
        logger.warning(f"{missing_sector} companies have no sector mapping — D/E carve-out cannot apply to them.")

    return universe


# ---------------------------------------------------------------------------
# Special metric preprocessing
# ---------------------------------------------------------------------------
def preprocess_special_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """ICR: icr_label == 'Debt Free' -> ICR_effective = infinity, never 0/NaN."""
    df = df.copy()
    if "icr_label" not in df.columns:
        raise KeyError(f"'icr_label' column missing. Available: {df.columns.tolist()}")
    if "interest_coverage" not in df.columns:
        raise KeyError(f"'interest_coverage' column missing. Available: {df.columns.tolist()}")

    is_debt_free = df["icr_label"].astype(str).str.strip().str.lower() == "debt free"
    df["ICR_effective"] = np.where(is_debt_free, np.inf, df["interest_coverage"])
    return df


# ---------------------------------------------------------------------------
# Generic operator-driven filter engine
# ---------------------------------------------------------------------------
def apply_custom_filters(df: pd.DataFrame, filters: list[dict[str, Any]]) -> pd.DataFrame:
    """
    filters: list of {"metric": <schema column>, "operator": one of
    OPERATORS, "value": <threshold>}.

    Special rules applied automatically, not per-filter config:
      - metric == 'debt_to_equity' -> Financials-sector rows exempted
      - metric == 'interest_coverage' -> uses ICR_effective (infinity-aware)
    """
    df = preprocess_special_metrics(df)
    mask = pd.Series(True, index=df.index)

    for f in filters:
        metric, operator_str, value = f["metric"], f["operator"], f["value"]

        if operator_str not in OPERATORS:
            raise ValueError(f"Unsupported operator '{operator_str}' for metric '{metric}'.")

        # ICR uses the infinity-aware effective column
        col = "ICR_effective" if metric == "interest_coverage" else metric
        if col not in df.columns:
            raise KeyError(f"Filter metric '{metric}' -> column '{col}' not found in DataFrame.")

        series = df[col]

        if operator_str == "==":
            cond = np.isclose(series.astype(float), value, atol=FLOAT_EQ_ATOL, equal_nan=False)
        else:
            cond = OPERATORS[operator_str](series, value)

        # Sector-aware D/E carve-out (Financials exempt from ANY D/E filter)
        if metric == "debt_to_equity":
            if "broad_sector" not in df.columns:
                raise KeyError("'broad_sector' required for D/E sector carve-out but missing.")
            is_financials = df["broad_sector"].astype(str).str.strip().str.lower() == "financials"
            cond = np.where(is_financials, True, cond)

        mask &= pd.Series(cond, index=df.index).fillna(False)

    return df[mask].copy()


# ---------------------------------------------------------------------------
# Turnaround Watch — trend-based, not expressible as static operator/value
# ---------------------------------------------------------------------------
def compute_revenue_cagr_3yr(conn) -> pd.DataFrame:
    """
    profitandloss se: latest annual sales vs sales 3 fiscal years earlier.
    Explicit NaN for companies without a valid 3-years-back match (missing
    data is never silently treated as 0% growth).
    """
    pnl_all = pd.read_sql("SELECT company_id, year, sales FROM profitandloss", conn)
    from period_utils import _annualize  # internal reuse, same module

    annual = _annualize(pnl_all.copy(), "year")
    latest = annual.sort_values(["company_id", "_fiscal_year"]).groupby("company_id", as_index=False).tail(1)
    latest = latest[["company_id", "_fiscal_year", "sales"]].rename(
        columns={"_fiscal_year": "end_year", "sales": "sales_end"}
    )

    rows = []
    for _, r in latest.iterrows():
        target = r["end_year"] - 3
        match = annual[(annual["company_id"] == r["company_id"]) & (annual["_fiscal_year"] == target)]
        sales_start = match["sales"].iloc[0] if len(match) else np.nan
        rows.append({"company_id": r["company_id"], "sales_end": r["sales_end"], "sales_start": sales_start})

    out = pd.DataFrame(rows)
    valid = (out["sales_start"] > 0) & (out["sales_end"] > 0)
    out["revenue_cagr_3yr"] = np.nan
    out.loc[valid, "revenue_cagr_3yr"] = ((out.loc[valid, "sales_end"] / out.loc[valid, "sales_start"]) ** (1 / 3) - 1) * 100
    return out[["company_id", "revenue_cagr_3yr"]]


def compute_turnaround_watch(universe: pd.DataFrame, conn, config: dict) -> pd.DataFrame:
    """
    Revenue CAGR 3yr > threshold AND FCF > 0 in latest year (from `universe`,
    already latest-snapshot) AND D/E strictly declining YoY (current < previous,
    from financial_ratios history — NOT from a fixed threshold).
    """
    tw_config = config["presets"].get("turnaround_watch", {})
    cagr_min = tw_config.get("revenue_cagr_3yr_min", 10)

    fr_all = pd.read_sql("SELECT * FROM financial_ratios", conn)
    de_curr = get_latest_annual_snapshot(fr_all, offset=0)[["company_id", "debt_to_equity"]].rename(
        columns={"debt_to_equity": "de_current_year"}
    )
    de_prev = get_latest_annual_snapshot(fr_all, offset=1)[["company_id", "debt_to_equity"]].rename(
        columns={"debt_to_equity": "de_previous_year"}
    )
    revenue_cagr_3yr = compute_revenue_cagr_3yr(conn)

    df = (
        universe
        .merge(revenue_cagr_3yr, on="company_id", how="left")
        .merge(de_curr, on="company_id", how="left")
        .merge(de_prev, on="company_id", how="left")
    )

    mask = (
        (df["revenue_cagr_3yr"] > cagr_min)
        & (df["free_cash_flow_cr"] > 0)
        & (df["de_current_year"] < df["de_previous_year"])  # strict YoY decline
    )
    mask = mask.fillna(False)  # companies missing prev-year D/E cannot show "decline" -> excluded, not errored

    return df[mask].copy()


# ---------------------------------------------------------------------------
# Day-17 interface stub (placeholder only — do not implement Day 17 logic)
# ---------------------------------------------------------------------------
def add_composite_score_placeholder(df: pd.DataFrame) -> pd.DataFrame:
    """
    Establishes the composite_quality_score column and the sort contract
    for Day 17. Day 17 will replace ONLY the score-computation step; this
    function signature and the sort_screener_results() call below remain
    unchanged, so nothing downstream needs to be rewritten later.
    """
    df = df.copy()
    df["composite_quality_score"] = np.nan
    return df


def sort_screener_results(df: pd.DataFrame) -> pd.DataFrame:
    """Sort contract for Day 17: descending composite score, NaN (unscored) last."""
    return df.sort_values("composite_quality_score", ascending=False, na_position="last")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------
def run_preset(universe: pd.DataFrame, conn, config: dict, preset_name: str) -> pd.DataFrame:
    if preset_name == "Turnaround Watch":
        result = compute_turnaround_watch(universe, conn, config)
    else:
        preset_filters = config["presets"].get(preset_name)
        if preset_filters is None:
            raise KeyError(f"Preset '{preset_name}' not found in screener_config.yaml")
        result = apply_custom_filters(universe, preset_filters)

    result = add_composite_score_placeholder(result)
    return sort_screener_results(result)


def run_all_presets(universe: pd.DataFrame, conn, config: dict) -> dict[str, pd.DataFrame]:
    preset_names = [k for k in config["presets"].keys() if k != "turnaround_watch"] + ["Turnaround Watch"]
    return {name: run_preset(universe, conn, config, name) for name in preset_names}


def validate_preset_counts(results: dict[str, pd.DataFrame], min_count=5, max_count=50) -> pd.DataFrame:
    rows = [
        {"preset": name, "count": len(df), "in_range": min_count <= len(df) <= max_count}
        for name, df in results.items()
    ]
    return pd.DataFrame(rows)