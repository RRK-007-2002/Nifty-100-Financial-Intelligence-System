import pandas as pd
import numpy as np

# Coulumns :    id, company_id,
#               year, sales,
#               expenses,   operating_profit,
#               opm_percentage, other_income,
#               interest,   depreciation,
#               profit_before_tax,  tax_percentage,
#               net_profit, eps, dividend_payout


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


# ====================================== Day 08 - Profitability Ratios ===================================

def net_profit_margin(net_profit: pd.Series, sales: pd.Series) -> pd.Series:
    """NPM = net_profit / sales x 100. Undefined if sales is 0."""
    index = _index_from(net_profit, sales)
    net_profit_s = _series(net_profit, index)
    sales_s = _series(sales, index)

    result = (net_profit_s / sales_s * 100).where(sales_s != 0).round(2)
    return _return_like_input(result, net_profit, sales)


def operating_profit_margin(
    operating_profit: pd.Series,
    sales: pd.Series,
    reported_opm: pd.Series | None = None,
    log_fn=None,
) -> pd.Series:
    """OPM = operating_profit / sales x 100, optionally checked with reported OPM."""
    index = _index_from(operating_profit, sales, reported_opm)
    operating_profit_s = _series(operating_profit, index)
    sales_s = _series(sales, index)

    computed = (operating_profit_s / sales_s * 100).where(sales_s != 0).round(2)

    if reported_opm is not None and log_fn:
        reported_opm_s = _series(reported_opm, index)
        mismatch = (computed - reported_opm_s).abs() > 1.0

        for idx in computed[mismatch].index:
            log_fn(
                f"OPM mismatch at index {idx}: "
                f"computed={computed.loc[idx]}, reported={reported_opm_s.loc[idx]}"
            )

    return _return_like_input(computed, operating_profit, sales, reported_opm)


def return_on_equity(
    net_profit: pd.Series,
    equity_capital: pd.Series,
    reserves: pd.Series,
) -> pd.Series:
    """ROE = net_profit / (equity + reserves) x 100. Undefined if base <= 0."""
    index = _index_from(net_profit, equity_capital, reserves)
    net_profit_s = _series(net_profit, index)
    base = _series(equity_capital, index) + _series(reserves, index)

    result = (net_profit_s / base * 100).where(base > 0).round(2)
    return _return_like_input(result, net_profit, equity_capital, reserves)


def return_on_capital_employed(
    operating_profit: pd.Series,
    depreciation: pd.Series,
    equity_capital: pd.Series,
    reserves: pd.Series,
    borrowings: pd.Series,
    is_financials: bool = False,
) -> pd.Series:
    """ROCE = EBIT / (equity + reserves + borrowings) x 100. Undefined if base <= 0."""
    index = _index_from(
        operating_profit,
        depreciation,
        equity_capital,
        reserves,
        borrowings,
    )
    ebit = _series(operating_profit, index) - _series(depreciation, index)
    base = (
        _series(equity_capital, index)
        + _series(reserves, index)
        + _series(borrowings, index)
    )

    result = (ebit / base * 100).where(base > 0).round(2)
    return _return_like_input(
        result,
        operating_profit,
        depreciation,
        equity_capital,
        reserves,
        borrowings,
    )


def return_on_assets(net_profit: pd.Series, total_assets: pd.Series) -> pd.Series:
    """ROA = net_profit / total_assets x 100. Undefined if total_assets is 0."""
    index = _index_from(net_profit, total_assets)
    net_profit_s = _series(net_profit, index)
    total_assets_s = _series(total_assets, index)

    result = (net_profit_s / total_assets_s * 100).where(total_assets_s != 0).round(2)
    return _return_like_input(result, net_profit, total_assets)

# ============= KPIs =======================
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

# =============== Day 9 - Leverage & Efficiency Ratios ===================================

# table: balancesheet
# Coulmns :         id,company_id,
#                   year,equity_capital,
#                   reserves,borrowings,
#                   other_liabilities,total_liabilities,
#                   fixed_assets,cwip,
#                   investments,other_asset,
#                   total_assets
def debt_to_equity(
    borrowings: pd.Series,
    equity_capital: pd.Series,
    reserves: pd.Series,
    is_financials: bool = False,
):
    """D/E = borrowings / (equity + reserves). Also returns high leverage flag."""
    index = _index_from(borrowings, equity_capital, reserves)
    borrowings_s = _series(borrowings, index)
    equity = _series(equity_capital, index) + _series(reserves, index)

    result = (borrowings_s / equity).where(equity > 0).round(2)
    result = result.mask(borrowings_s == 0, 0.0)
    return _return_like_input(result, borrowings, equity_capital, reserves)

def interest_coverage_ratio(
    operating_profit: pd.Series,
    other_income: pd.Series,
    interest: pd.Series,
):
    """ICR = (operating_profit + other_income) / interest."""
    index = _index_from(operating_profit, other_income, interest)
    numerator = _series(operating_profit, index) + _series(other_income, index)
    interest_s = _series(interest, index)

    icr = (numerator / interest_s).where(interest_s != 0).round(2)
    icr_label = pd.Series(np.where(interest_s == 0, "Debt Free", None), index=index)
    at_risk_flag = (icr < 1.5).fillna(False)

    return (
        _return_like_input(icr, operating_profit, other_income, interest),
        _return_like_input(icr_label, operating_profit, other_income, interest),
        _return_like_input(at_risk_flag, operating_profit, other_income, interest),
    )


def net_debt(borrowings: pd.Series, investments: pd.Series) -> pd.Series:
    """Net Debt = borrowings - investments."""
    # net_debt = borrowings - investments

    return borrowings - investments


def asset_turnover(sales: pd.Series, total_assets: pd.Series) -> pd.Series:
    """Asset Turnover = sales / total_assets. Undefined if total_assets is 0."""
    index = _index_from(sales, total_assets)
    sales_s = _series(sales, index)
    total_assets_s = _series(total_assets, index)

    result = (sales_s / total_assets_s).where(total_assets_s != 0).round(2)
    return _return_like_input(result, sales, total_assets)

# ======================= KPIs =====================
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



# ====================================== end ====================================

# df = pd.read_csv(r"C:\Users\bhrra\Desktop\nifty100\data\processed\profitandloss.csv")
# print(net_profit_margin(df["net_profit"],df["sales"]))
