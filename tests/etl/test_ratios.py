"""
tests/kpi/test_ratios.py

Unit tests for the ratio functions in src/kpi/ratio.py (Sprint 6, Day 41).

Update the import path below if your module is at a different location --
the uploaded file was named ratio.py (singular).

NOTE: The Day 41 spec also calls for tests covering "CAGR turnaround flag,
CAGR decline-to-loss, normal CAGR calculation" and "CFO quality score
calculation". Those functions are not present in the uploaded ratio.py
(only profitability, leverage and efficiency ratios exist there), so they
are not tested here. Send that code over when it's ready and I'll add
matching tests.

Similarly, debt_to_equity() returns only the raw ratio, not a boolean
"D/E > 5" flag -- test_de_high_leverage_exceeds_five below checks the
numeric threshold directly rather than a flag that doesn't exist.
"""

from __future__ import annotations

import pandas as pd

from src.Analytics.ratio import (
    asset_turnover,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    net_profit_margin,
    operating_profit_margin,
    return_on_assets,
    return_on_capital_employed,
    return_on_equity,
)

# --- Net Profit Margin ----------------------------------------------------


def test_npm_normal() -> None:
    """NPM = net_profit / sales * 100 for a straightforward case."""
    result = net_profit_margin(pd.Series([100]), pd.Series([500]))
    assert result.iloc[0] == 20.0


def test_npm_zero_sales_returns_none() -> None:
    """NPM is undefined (NaN) when sales is 0."""
    result = net_profit_margin(pd.Series([100]), pd.Series([0]))
    assert pd.isna(result.iloc[0])


def test_npm_negative_profit() -> None:
    """A net loss produces a negative NPM, not an error."""
    result = net_profit_margin(pd.Series([-50]), pd.Series([500]))
    assert result.iloc[0] == -10.0


# --- Operating Profit Margin -----------------------------------------------


def test_opm_computed_normal() -> None:
    """OPM = operating_profit / sales * 100 with no reported_opm supplied."""
    result = operating_profit_margin(pd.Series([100]), pd.Series([500]))
    assert result.iloc[0] == 20.0


def test_opm_mismatch_triggers_log() -> None:
    """A >1% divergence from reported_opm calls log_fn exactly once."""
    logged = []
    operating_profit_margin(
        pd.Series([100]),
        pd.Series([500]),
        reported_opm=pd.Series([15.0]),  # computed = 20.0, >1% mismatch
        log_fn=lambda msg: logged.append(msg),
    )
    assert len(logged) == 1


def test_opm_no_mismatch_does_not_log() -> None:
    """A reported_opm within 1% of the computed value logs nothing."""
    logged = []
    operating_profit_margin(
        pd.Series([100]),
        pd.Series([500]),
        reported_opm=pd.Series([20.0]),  # matches computed exactly
        log_fn=lambda msg: logged.append(msg),
    )
    assert len(logged) == 0


# --- Return on Equity -------------------------------------------------------


def test_roe_normal() -> None:
    """ROE = net_profit / (equity + reserves) * 100."""
    result = return_on_equity(pd.Series([100]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] == 20.0


def test_roe_negative_equity_returns_none() -> None:
    """A negative equity base (equity + reserves <= 0) makes ROE undefined."""
    result = return_on_equity(pd.Series([100]), pd.Series([-50]), pd.Series([-100]))
    assert pd.isna(result.iloc[0])


def test_roe_zero_base_returns_none() -> None:
    """A zero equity base is also undefined, same as a negative one."""
    result = return_on_equity(pd.Series([100]), pd.Series([0]), pd.Series([0]))
    assert pd.isna(result.iloc[0])


# --- Return on Capital Employed ---------------------------------------------


def test_roce_normal() -> None:
    """ROCE = (operating_profit - depreciation) / (equity+reserves+borrowings) * 100."""
    result = return_on_capital_employed(
        pd.Series([200]), pd.Series([50]), pd.Series([400]),
        pd.Series([100]), pd.Series([100]),
    )
    # ebit = 200-50 = 150; base = 400+100+100 = 600; 150/600*100 = 25.0
    assert result.iloc[0] == 25.0


def test_roce_negative_base_returns_none() -> None:
    """ROCE is undefined when the capital-employed base is <= 0."""
    result = return_on_capital_employed(
        pd.Series([200]), pd.Series([50]), pd.Series([-400]),
        pd.Series([-100]), pd.Series([0]),
    )
    assert pd.isna(result.iloc[0])


# --- Return on Assets --------------------------------------------------------


def test_roa_normal() -> None:
    """ROA = net_profit / total_assets * 100."""
    result = return_on_assets(pd.Series([100]), pd.Series([1000]))
    assert result.iloc[0] == 10.0


def test_roa_zero_assets_returns_none() -> None:
    """ROA is undefined when total_assets is 0."""
    result = return_on_assets(pd.Series([100]), pd.Series([0]))
    assert pd.isna(result.iloc[0])


# --- Debt to Equity -----------------------------------------------------------


def test_de_debtfree_returns_zero() -> None:
    """A company with zero borrowings gets D/E = 0.0, not NaN."""
    result = debt_to_equity(pd.Series([0]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] == 0.0


def test_de_normal() -> None:
    """D/E = borrowings / (equity + reserves) for a normal case."""
    result = debt_to_equity(pd.Series([200]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] == 0.4


def test_de_high_leverage_exceeds_five() -> None:
    """
    A heavily-levered company's raw D/E exceeds 5 (no dedicated boolean
    flag exists in the current implementation -- see module docstring).
    """
    result = debt_to_equity(pd.Series([3000]), pd.Series([400]), pd.Series([100]))
    assert result.iloc[0] > 5


# --- Interest Coverage Ratio ---------------------------------------------------


def test_icr_interest_zero_label_debt_free() -> None:
    """Zero interest expense makes ICR undefined and labels 'Debt Free'."""
    icr, label, risk = interest_coverage_ratio(
        pd.Series([500]), pd.Series([50]), pd.Series([0])
    )
    assert pd.isna(icr.iloc[0])
    assert label.iloc[0] == "Debt Free"


def test_icr_at_risk_flag_below_threshold() -> None:
    """An ICR below 1.5 sets the at-risk flag True."""
    icr, label, risk = interest_coverage_ratio(
        pd.Series([100]), pd.Series([0]), pd.Series([100])
    )  # ICR = 1.0
    assert bool(risk.iloc[0]) is True


def test_icr_normal_above_threshold_not_at_risk() -> None:
    """A healthy ICR (>=1.5) leaves the at-risk flag False."""
    icr, label, risk = interest_coverage_ratio(
        pd.Series([500]), pd.Series([0]), pd.Series([100])
    )  # ICR = 5.0
    assert icr.iloc[0] == 5.0
    assert bool(risk.iloc[0]) is False


# --- Net Debt -------------------------------------------------------------------


def test_net_debt_positive() -> None:
    """More borrowings than investments gives a positive net debt."""
    result = net_debt(pd.Series([500]), pd.Series([200]))
    assert result.iloc[0] == 300


def test_net_debt_negative_net_cash_position() -> None:
    """More investments than borrowings gives a negative net debt (net cash)."""
    result = net_debt(pd.Series([200]), pd.Series([500]))
    assert result.iloc[0] == -300


# --- Asset Turnover --------------------------------------------------------------


def test_asset_turnover_normal() -> None:
    """Asset turnover = sales / total_assets."""
    result = asset_turnover(pd.Series([500]), pd.Series([250]))
    assert result.iloc[0] == 2.0


def test_asset_turnover_zero_assets_returns_none() -> None:
    """Asset turnover is undefined when total_assets is 0."""
    result = asset_turnover(pd.Series([500]), pd.Series([0]))
    assert pd.isna(result.iloc[0])
