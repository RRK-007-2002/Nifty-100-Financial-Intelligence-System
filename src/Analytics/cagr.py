import pandas as pd

# ========================================= Day 10: CAGR Engine ============================
# table: profitann
def compute_cagr(start_value: float, end_value: float, n_years: int,
                  years_available: int):
    """
    Returns (cagr_value, flag).
    cagr_value is None whenever the flag is not None -- the two are
    mutually exclusive by design, so downstream code can check
    'if flag: handle_special_case()' without also checking the value.
    """
    if years_available < n_years:
        return None, "INSUFFICIENT"

    if start_value == 0:
        return None, "ZERO_BASE"

    if start_value > 0 and end_value < 0:
        return None, "DECLINE_TO_LOSS"

    if start_value < 0 and end_value > 0:
        return None, "TURNAROUND"

    if start_value < 0 and end_value < 0:
        return None, "BOTH_NEGATIVE"

    # Only remaining case: both positive -- safe to compute
    cagr = ((end_value / start_value) ** (1 / n_years) - 1) * 100
    return round(cagr, 2), None


def revenue_cagr(sales_series: dict, n_years: int):
    """sales_series: {year: sales_value}, sorted chronologically.
    Picks the earliest and latest year within the n_years window."""
    years = sorted(sales_series.keys())
    if len(years) < n_years + 1:
        return compute_cagr(0, 0, n_years, len(years))  # forces INSUFFICIENT
    start_year, end_year = years[-(n_years + 1)], years[-1]
    return compute_cagr(sales_series[start_year], sales_series[end_year],
                         n_years, len(years))

def pat_cagr(net_profit_series: dict, n_years: int):
    """PAT (net profit) CAGR -- same logic as revenue_cagr, different source."""
    years = sorted(net_profit_series.keys())
    if len(years) < n_years + 1:
        return compute_cagr(0, 0, n_years, len(years))  # forces INSUFFICIENT
    start_year, end_year = years[-(n_years + 1)], years[-1]
    return compute_cagr(net_profit_series[start_year], net_profit_series[end_year],
                         n_years, len(years))


def eps_cagr(eps_series: dict, n_years: int):
    """EPS CAGR -- same logic as revenue_cagr, different source."""
    years = sorted(eps_series.keys())
    if len(years) < n_years + 1:
        return compute_cagr(0, 0, n_years, len(years))
    start_year, end_year = years[-(n_years + 1)], years[-1]
    return compute_cagr(eps_series[start_year], eps_series[end_year],
                         n_years, len(years))

# ==========  KPis ===============
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


