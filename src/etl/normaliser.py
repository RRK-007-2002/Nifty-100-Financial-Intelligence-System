"""
normaliser.py
Day 02 deliverable: normalize_year() and normalize_ticker().

These functions turn messy, inconsistently-formatted source values
(from 12 different Excel files, each possibly exported at a different
time by a different person) into one canonical representation, so the
rest of the pipeline (validator, loader) can rely on a single format.
"""

import re
from typing import Optional


class NormalisationError(ValueError):
    """Raised when a value cannot be normalized and no safe default applies."""


# ---------------------------------------------------------------------------
# normalize_year
# ---------------------------------------------------------------------------
# Source files use a mix of:
#   2020            -> plain int/str year
#   "FY2020"        -> fiscal-year prefixed
#   "FY20"          -> 2-digit fiscal year
#   "2019-20"       -> Indian FY range, we take the ENDING year (2020)
#   "2019-2020"     -> same, full 4-digit range
#   "Mar-20"        -> month-year, fiscal year end -> 2020
#   "31-03-2020"    -> full date, take the year component
#   20.0            -> float leaking in from Excel numeric columns
#
# Convention adopted: Indian companies report fiscal year April-March,
# so "the year" = the calendar year the fiscal year ENDS in.

_YEAR_RANGE_RE = re.compile(r"^\s*(\d{4})\s*[-/]\s*(\d{2,4})\s*$")
_FY_PREFIX_RE = re.compile(r"^\s*FY\s*'?(\d{2,4})\s*$", re.IGNORECASE)
_MONTH_YEAR_RE = re.compile(
    r"^\s*[A-Za-z]{3,9}[\s\-/](\d{2,4})\s*$"
)
_FULL_DATE_RE = re.compile(r"^\s*\d{1,2}[\-/]\d{1,2}[\-/](\d{2,4})\s*$")
_PLAIN_YEAR_RE = re.compile(r"^\s*(\d{4})\s*$")

MIN_VALID_YEAR = 1995
MAX_VALID_YEAR = 2035


def _expand_2digit(yy: str) -> int:
    """'20' -> 2020, '99' -> 1999 (pivot at 2035 like most FY tooling)."""
    yy = int(yy)
    if yy >= 100:
        return yy
    return 2000 + yy if yy <= 35 else 1900 + yy


def normalize_year(raw) -> int:
    """
    Normalize any of the messy year formats above into a single 4-digit
    calendar year (int), using "fiscal year END" convention.

    Raises NormalisationError if the value can't be confidently parsed,
    or falls outside [MIN_VALID_YEAR, MAX_VALID_YEAR].
    """
    if raw is None:
        raise NormalisationError("year is None")

    # Excel sometimes gives floats like 2020.0
    if isinstance(raw, float):
        if raw.is_integer():
            raw = str(int(raw))
        else:
            raise NormalisationError(f"non-integer float year: {raw}")
    if isinstance(raw, int):
        raw = str(raw)

    s = str(raw).strip()
    if not s:
        raise NormalisationError("empty year string")

    year: Optional[int] = None

    if m := _PLAIN_YEAR_RE.match(s):
        year = int(m.group(1))

    elif m := _YEAR_RANGE_RE.match(s):
        # "2019-20" or "2019-2020" -> take ending year
        end = m.group(2)
        year = _expand_2digit(end) if len(end) <= 2 else int(end)

    elif m := _FY_PREFIX_RE.match(s):
        year = _expand_2digit(m.group(1))

    elif m := _FULL_DATE_RE.match(s):
        year = _expand_2digit(m.group(1))

    elif m := _MONTH_YEAR_RE.match(s):
        year = _expand_2digit(m.group(1))

    if year is None:
        raise NormalisationError(f"unrecognized year format: {raw!r}")

    if not (MIN_VALID_YEAR <= year <= MAX_VALID_YEAR):
        raise NormalisationError(f"year {year} out of plausible range: {raw!r}")

    return year


# ---------------------------------------------------------------------------
# normalize_ticker
# ---------------------------------------------------------------------------
# Source files mix:
#   "RELIANCE"          -> already clean
#   "reliance"          -> lowercase
#   "RELIANCE.NS"       -> NSE suffix
#   "RELIANCE.BO"       -> BSE suffix
#   " TCS "             -> stray whitespace
#   "TCS Ltd"           -> trailing company-type noise (rare, from a
#                          supplementary file) -- we only strip known
#                          exchange suffixes, NOT free text like "Ltd",
#                          since that risks corrupting real tickers.
#   "M&M"                -> ampersand is a legitimate ticker character
#                           (Mahindra & Mahindra), must be preserved

_EXCHANGE_SUFFIXES = (".NS", ".BO", ".NSE", ".BSE")
_VALID_TICKER_RE = re.compile(r"^[A-Z0-9&\-]+$")


def normalize_ticker(raw: str) -> str:
    """
    Normalize a ticker symbol: uppercase, strip whitespace, strip known
    exchange suffixes. Raises NormalisationError if empty or contains
    characters that don't belong in an NSE/BSE ticker.
    """
    if raw is None:
        raise NormalisationError("ticker is None")

    s = str(raw).strip().upper()
    if not s:
        raise NormalisationError("empty ticker string")

    for suffix in _EXCHANGE_SUFFIXES:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break

    s = s.strip()

    if not s:
        raise NormalisationError(f"ticker empty after stripping suffix: {raw!r}")

    if not _VALID_TICKER_RE.match(s):
        raise NormalisationError(f"ticker has invalid characters: {raw!r}")

    return s
