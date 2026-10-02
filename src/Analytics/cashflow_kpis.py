import pandas as pd
import numpy as np
import math

# table : cashflow

# Columns : id,company_id,
    #       year,operating_activity,
    #       investing_activity,financing_activity,
    #       net_cash_flow


def _index_from(*values):
    for value in values:
        if isinstance(value, pd.Series):
            return value.index
    return pd.RangeIndex(1)


def _series(value, index):
    if isinstance(value, pd.Series):
        return value
    return pd.Series(value, index=index)


def _return_like_input(result, *original_inputs):
    if any(isinstance(value, pd.Series) for value in original_inputs):
        return result
    if isinstance(result, pd.Series):
        return result.iloc[0]
    return result


def free_cash_flow(operating_activity: float, investing_activity: float):
    """FCF = CFO + CFI. Negative FCF is a valid, real answer -- no guard."""
    index = _index_from(operating_activity, investing_activity)
    operating_activity_s = _series(operating_activity, index)
    investing_activity_s = _series(investing_activity, index)

    result = (operating_activity_s + investing_activity_s).round(2)
    return _return_like_input(result, operating_activity, investing_activity)


def cfo_quality_score(cfo_5yr_avg: float, pat_5yr_avg: float):
    """CFO/PAT averaged over 5yrs. None if PAT avg is 0 (undefined ratio)."""
    index = _index_from(cfo_5yr_avg, pat_5yr_avg)
    cfo_5yr_avg_s = _series(cfo_5yr_avg, index)
    pat_5yr_avg_s = _series(pat_5yr_avg, index)

    ratio = (cfo_5yr_avg_s / pat_5yr_avg_s).where(pat_5yr_avg_s != 0).round(2)
    label = pd.Series(
        np.select(
            [
                pat_5yr_avg_s == 0,
                ratio > 1.0,
                ratio >= 0.5,
            ],
            [
                "Undefined",
                "High Quality",
                "Moderate",
            ],
            default="Accrual Risk",
        ),
        index=index,
    )

    return (
        _return_like_input(ratio, cfo_5yr_avg, pat_5yr_avg),
        _return_like_input(label, cfo_5yr_avg, pat_5yr_avg),
    )


def capex_intensity(investing_activity: float, sales: float):
    """CapEx Intensity = |CFI| / sales x 100."""
    index = _index_from(investing_activity, sales)
    investing_activity_s = _series(investing_activity, index)
    sales_s = _series(sales, index)

    pct = (investing_activity_s.abs() / sales_s * 100).where(sales_s != 0).round(2)
    label = pd.Series(
        np.select(
            [
                sales_s == 0,
                pct < 3,
                pct <= 8,
            ],
            [
                None,
                "Asset Light",
                "Moderate",
            ],
            default="Capital Intensive",
        ),
        index=index,
    )

    return (
        _return_like_input(pct, investing_activity, sales),
        _return_like_input(label, investing_activity, sales),
    )


PATTERN_LABELS = {
    (1, -1, -1): "Reinvestor",          # default for (+,-,-); Shareholder
                                          # Returns is the SAME sign pattern,
                                          # distinguished by CFO/PAT, not sign
    (1, 1, -1): "Liquidating Assets",
    (-1, 1, 1): "Distress Signal",
    (-1, -1, 1): "Growth Funded by Debt",
    (1, 1, 1): "Cash Accumulator",
    (-1, -1, -1): "Pre-Revenue",
    (1, -1, 1): "Mixed",
}

def classify_capital_allocation(cfo: float, cfi: float, cff: float,
                                 cfo_quality_ratio: float = None):
    """Returns (cfo_sign, cfi_sign, cff_sign, pattern_label)."""
    index = _index_from(cfo, cfi, cff, cfo_quality_ratio)
    cfo_s = _series(cfo, index)
    cfi_s = _series(cfi, index)
    cff_s = _series(cff, index)
    cfo_quality_ratio_s = _series(cfo_quality_ratio, index)

    cfo_sign = pd.Series(np.where(cfo_s > 0, 1, -1), index=index)
    cfi_sign = pd.Series(np.where(cfi_s > 0, 1, -1), index=index)
    cff_sign = pd.Series(np.where(cff_s > 0, 1, -1), index=index)
    label = pd.Series(
        [
            PATTERN_LABELS.get(signs, "Unclassified")
            for signs in zip(cfo_sign, cfi_sign, cff_sign)
        ],
        index=index,
    )

    # (+,-,-) is ambiguous by sign alone -- CFO/PAT decides which sub-label
    shareholder_returns = (
        (cfo_sign == 1)
        & (cfi_sign == -1)
        & (cff_sign == -1)
        & (cfo_quality_ratio_s > 1.0)
    )
    label = label.mask(shareholder_returns, "Shareholder Returns")

    return (
        _return_like_input(cfo_sign, cfo, cfi, cff, cfo_quality_ratio),
        _return_like_input(cfi_sign, cfo, cfi, cff, cfo_quality_ratio),
        _return_like_input(cff_sign, cfo, cfi, cff, cfo_quality_ratio),
        _return_like_input(label, cfo, cfi, cff, cfo_quality_ratio),
    )

# ====================================== KPis =========================================
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