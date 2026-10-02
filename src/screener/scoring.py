# src/screener/scoring.py
"""
Day 17: Composite Quality Score (0-100).
Populates the composite_quality_score column that Day 15 established
as a placeholder — sort_screener_results() in engine.py is untouched.
"""

import numpy as np
import pandas as pd

# Weight spec per project PDF Section 25.1.
# NOTE (documented substitution, not fabrication):
#   - ROCE (10%) is NOT available as a Ratio-Engine-computed column in
#     financial_ratios (only companies.roce_percentage exists, and the
#     PDF itself says that field is "display only"). Its weight is
#     redistributed within Profitability: ROE 15% -> effectively 25%,
#     NPM 10% -> stays 10% (proportional to original 15:10 ratio).
#   - FCF CAGR 5yr (15%) is NOT pre-computed in financial_ratios (only
#     revenue/pat/eps CAGR exist). Its weight is redistributed within
#     Cash Quality: CFO/PAT 10% -> ~14.3%, FCF-positive-flag 5% -> ~7.1%
#     (proportional to original 10:5 ratio), i.e. the FCF-CAGR slice is
#     dropped and the remaining two are scaled up to still sum to 30%.
DIMENSION_WEIGHTS = {"profitability": 0.35, "cash_quality": 0.30, "growth": 0.20, "leverage": 0.15}

PROFITABILITY_SUBWEIGHTS = {"return_on_equity_pct": 15 / 25, "net_profit_margin_pct": 10 / 25}
CASH_QUALITY_SUBWEIGHTS = {"cfo_pat_ratio": 10 / 15, "fcf_positive_flag": 5 / 15}
GROWTH_SUBWEIGHTS = {"revenue_cagr_5yr": 0.5, "pat_cagr_5yr": 0.5}
LEVERAGE_SUBWEIGHTS = {"de_score": 10 / 15, "icr_score": 5 / 15}


def _winsorize_scale(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """P10/P90 winsorise, then linearly scale to 0-100. NaN stays NaN (not silently 0)."""
    s = series.astype(float)
    valid = s.dropna()
    if len(valid) < 2:
        return pd.Series(np.nan, index=series.index)
    p10, p90 = valid.quantile(0.10), valid.quantile(0.90)
    if p90 == p10:
        return pd.Series(50.0, index=series.index).where(s.notna())
    clipped = s.clip(lower=p10, upper=p90)
    scaled = (clipped - p10) / (p90 - p10) * 100
    return scaled if higher_is_better else (100 - scaled)


def compute_composite_score(universe: pd.DataFrame) -> pd.DataFrame:
    """
    Adds composite_quality_score (0-100) to universe. Requires
    ICR_effective (from preprocess_special_metrics) — caller must run
    that first, same as apply_custom_filters() does.
    """
    df = universe.copy()
    required = ["return_on_equity_pct", "net_profit_margin_pct", "cash_from_operations_cr",
                "free_cash_flow_cr", "revenue_cagr_5yr", "pat_cagr_5yr", "debt_to_equity", "net_profit"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"compute_composite_score missing required columns: {missing}")

    # --- Profitability ---
    roe_score = _winsorize_scale(df["return_on_equity_pct"])
    npm_score = _winsorize_scale(df["net_profit_margin_pct"])
    profitability = (
        roe_score * PROFITABILITY_SUBWEIGHTS["return_on_equity_pct"]
        + npm_score * PROFITABILITY_SUBWEIGHTS["net_profit_margin_pct"]
    )

    # --- Cash Quality ---
    with np.errstate(divide="ignore", invalid="ignore"):
        cfo_pat = np.where(df["net_profit"] != 0, df["cash_from_operations_cr"] / df["net_profit"], np.nan)
    cfo_pat_score = _winsorize_scale(pd.Series(cfo_pat, index=df.index))
    fcf_flag_score = np.where(df["free_cash_flow_cr"] > 0, 100.0, 0.0)
    cash_quality = (
        cfo_pat_score * CASH_QUALITY_SUBWEIGHTS["cfo_pat_ratio"]
        + fcf_flag_score * CASH_QUALITY_SUBWEIGHTS["fcf_positive_flag"]
    )

    # --- Growth (turnaround/negative-base CAGR already None/NaN upstream -> excluded, not 0) ---
    rev_cagr_score = _winsorize_scale(df["revenue_cagr_5yr"])
    pat_cagr_score = _winsorize_scale(df["pat_cagr_5yr"])
    growth = (
        rev_cagr_score * GROWTH_SUBWEIGHTS["revenue_cagr_5yr"]
        + pat_cagr_score * GROWTH_SUBWEIGHTS["pat_cagr_5yr"]
    )

    # --- Leverage --- (D/E: lower=better -> higher_is_better=False; ICR: needs ICR_effective from preprocessing)
    de_score = _winsorize_scale(df["debt_to_equity"], higher_is_better=False)
    if "ICR_effective" in df.columns:
        icr_finite = df["ICR_effective"].replace(np.inf, np.nan)  # winsorise on finite values only
        icr_score = _winsorize_scale(icr_finite)
        icr_score = np.where(df["ICR_effective"] == np.inf, 100.0, icr_score)  # debt-free -> best score
    else:
        icr_score = np.nan
    leverage = (
        de_score * LEVERAGE_SUBWEIGHTS["de_score"]
        + pd.Series(icr_score, index=df.index) * LEVERAGE_SUBWEIGHTS["icr_score"]
    )

    composite = (
        profitability * DIMENSION_WEIGHTS["profitability"]
        + cash_quality * DIMENSION_WEIGHTS["cash_quality"]
        + growth * DIMENSION_WEIGHTS["growth"]
        + leverage * DIMENSION_WEIGHTS["leverage"]
    )

    df["composite_quality_score"] = composite.round(2)
    return df