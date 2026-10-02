# src/screener/period_utils.py
"""
Reuses Sprint-1's normalize_year() from src.etl.normaliser for canonical
year values, and adds month extraction (to exclude Jun/Sep TTM stubs).

CHANGE NOTE (Sprint 3, Day 16): get_latest_annual_snapshot() gained an
`offset` parameter (default 0, fully backward compatible) so callers can
also fetch the PREVIOUS annual snapshot per company — needed for the
Turnaround Watch preset's "D/E declining year-over-year" rule.
"""

import re
import pandas as pd
from src.etl.normaliser import normalize_year, NormalisationError

_MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
_MONTH_TOKEN_RE = re.compile(r"^\s*([A-Za-z]{3,9})[\s\-/]\d{2,4}\s*$")


def extract_period_month(raw: str) -> int | None:
    """'Mar 2024' -> 3, 'Dec-23' -> 12. Plain '2024' -> assumes March FY-close."""
    if raw is None:
        return None
    s = str(raw).strip()
    m = _MONTH_TOKEN_RE.match(s)
    if not m:
        if re.match(r"^\d{4}$", s):
            return 3
        return None
    return _MONTH_MAP.get(m.group(1)[:3].lower())


def _annualize(df: pd.DataFrame, year_col: str) -> pd.DataFrame:
    """Internal: parses year_col, tags fiscal_year/period_month, drops unparseable/TTM rows."""
    df = df.copy()
    fiscal_years, months, keep_mask = [], [], []
    for raw in df[year_col]:
        try:
            fy = normalize_year(raw)
        except NormalisationError:
            fiscal_years.append(None); months.append(None); keep_mask.append(False)
            continue
        fiscal_years.append(fy)
        months.append(extract_period_month(raw))
        keep_mask.append(True)

    df["_fiscal_year"] = fiscal_years
    df["_period_month"] = months
    dropped = int((~pd.Series(keep_mask, index=df.index)).sum())
    if dropped:
        print(f"[period_utils] WARNING: dropped {dropped} rows with unparseable year values")

    df = df[pd.Series(keep_mask, index=df.index)]
    return df[df["_period_month"].isin([3, 12])]  # annual closes only, TTM excluded


def get_latest_annual_snapshot(df: pd.DataFrame, year_col: str = "year", offset: int = 0) -> pd.DataFrame:
    """
    Per company_id, returns the annual (Mar/Dec) row at rank `offset`
    from the most recent (offset=0 = latest, offset=1 = previous year, ...).

    offset=0 preserves original Day-15 behavior exactly (backward compatible).
    Companies with fewer annual rows than `offset+1` are simply absent from
    the output (not an error) -- callers must handle missing company_ids.
    """
    annual = _annualize(df, year_col)
    ranked = (
        annual.sort_values(["company_id", "_fiscal_year"], ascending=[True, False])
        .groupby("company_id", as_index=False)
    )
    # nth(offset) within each company group, sorted descending by fiscal_year
    result = ranked.nth(offset)
    return result.reset_index(drop=True)
