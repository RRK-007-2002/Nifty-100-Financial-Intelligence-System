# tests/kpi/test_ratio_formulas.py
import sys
from pathlib import Path
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "Analytics"))

from ratio import (net_profit_margin, operating_profit_margin,
                    return_on_equity, debt_to_equity,
                    interest_coverage_ratio, asset_turnover)
from cagr import compute_cagr
from cashflow_kpis import (free_cash_flow, cfo_quality_score,
                            capex_intensity, classify_capital_allocation)


# ── Day 08 — Profitability (5 tests) ────────────────────────────────────

def test_npm_normal():
    result = net_profit_margin(pd.Series([100]), pd.Series([500]))
    assert result.iloc[0] == 20.0

def test_npm_zero_sales_returns_none():
    result = net_profit_margin(pd.Series([100]), pd.Series([0]))
    assert pd.isna(result.iloc[0])

def test_roe_normal():
    result = return_on_equity(pd.Series([100]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] == 20.0

def test_roe_negative_equity_returns_none():
    result = return_on_equity(pd.Series([100]), pd.Series([-50]), pd.Series([-100]))
    assert pd.isna(result.iloc[0])

def test_opm_mismatch_triggers_log():
    logged = []
    operating_profit_margin(
        pd.Series([100]), pd.Series([500]),
        reported_opm=pd.Series([15.0]),  # computed will be 20.0 -- >1% mismatch
        log_fn=lambda msg: logged.append(msg)
    )
    assert len(logged) == 1


# ── Day 09 — Leverage & Efficiency (5 tests) ─────────────────────────────

def test_de_debtfree_returns_zero():
    result = debt_to_equity(pd.Series([0]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] == 0.0

def test_de_normal():
    result = debt_to_equity(pd.Series([200]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] == 0.4

def test_icr_interest_zero_label_debt_free():
    icr, label, risk = interest_coverage_ratio(
        pd.Series([500]), pd.Series([50]), pd.Series([0]))
    assert pd.isna(icr.iloc[0])
    assert label.iloc[0] == "Debt Free"

def test_icr_at_risk_flag_below_threshold():
    icr, label, risk = interest_coverage_ratio(
        pd.Series([100]), pd.Series([0]), pd.Series([100]))  # ICR = 1.0
    assert risk.iloc[0] == True

def test_asset_turnover_zero_assets_returns_none():
    result = asset_turnover(pd.Series([500]), pd.Series([0]))
    assert pd.isna(result.iloc[0])


# ── Day 10 — CAGR Engine (6 tests, scalar-style) ─────────────────────────

def test_cagr_normal():
    value, flag = compute_cagr(100, 161, 5, years_available=6)
    assert flag is None and abs(value - 10.0) < 0.1

def test_cagr_decline_to_loss():
    value, flag = compute_cagr(100, -50, 5, years_available=6)
    assert value is None and flag == "DECLINE_TO_LOSS"

def test_cagr_turnaround():
    value, flag = compute_cagr(-100, 200, 5, years_available=6)
    assert value is None and flag == "TURNAROUND"

def test_cagr_both_negative():
    value, flag = compute_cagr(-100, -50, 5, years_available=6)
    assert value is None and flag == "BOTH_NEGATIVE"

def test_cagr_zero_base():
    value, flag = compute_cagr(0, 100, 5, years_available=6)
    assert value is None and flag == "ZERO_BASE"

def test_cagr_insufficient_data():
    value, flag = compute_cagr(100, 150, 5, years_available=3)
    assert value is None and flag == "INSUFFICIENT"


# ── Day 11 — Cash Flow KPIs (4 tests) ─────────────────────────────────────

def test_fcf_negative_allowed():
    result = free_cash_flow(pd.Series([500]), pd.Series([-800]))
    assert result.iloc[0] == -300

def test_cfo_quality_high_quality_label():
    ratio, label = cfo_quality_score(pd.Series([1200]), pd.Series([1000]))
    assert ratio.iloc[0] == 1.2 and label.iloc[0] == "High Quality"

def test_capex_intensity_asset_light():
    pct, label = capex_intensity(pd.Series([-1000]), pd.Series([50000]))
    assert pct.iloc[0] == 2.0 and label.iloc[0] == "Asset Light"

def test_capital_allocation_distress_signal():
    cfo_sign, cfi_sign, cff_sign, label = classify_capital_allocation(
        pd.Series([-500]), pd.Series([800]), pd.Series([600]))
    assert label.iloc[0] == "Distress Signal"