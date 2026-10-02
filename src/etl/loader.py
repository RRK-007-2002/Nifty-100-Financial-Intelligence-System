"""
loader.py
Day 02 deliverable (skeleton). Full 12-file / 10-table load happens Day 05,
once schema.sql (Day 04) and validator.py (Day 03) exist. Today this module
is responsible for:
  1. Reading a raw Excel source file into a DataFrame
  2. Applying normalize_year() / normalize_ticker() to the relevant columns
  3. Basic shape/dtype logging so problems surface early

This intentionally does NOT touch SQLite yet -- that's Day 04/05.
"""

import re
import pandas as pd

def normalize_ticker(raw: str) -> str:
    """
    convert lower case into uppercase
    """   

    t = str(raw).strip().upper()
    for suffix in (".NS", ".BO", ".NSE", ".BSE"):
        if t.endswith(suffix):
            t = t[: -len(suffix)]
    if not t:
        raise ValueError(f"empty ticker: {raw!r}")
    return t



def normalize_year(raw: str) -> str:
    """
    normalize year into mon year format.
    """
    if raw == 'TTM':
        raw = 'Dec 2024'

    s = str(raw).split(" ")

    if len(s) > 2:
        return " ".join(s[:-1])
    else:
        return " ".join(s)
    


