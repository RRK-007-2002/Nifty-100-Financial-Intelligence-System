import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src" / "etl"))
from normaliser import normalize_year, normalize_ticker, NormalisationError


# ---------------------------------------------------------------------------
# normalize_year — 20 tests
# ---------------------------------------------------------------------------

def test_year_plain_int():
    assert normalize_year(2020) == 2020

def test_year_plain_str():
    assert normalize_year("2020") == 2020

def test_year_plain_str_padded():
    assert normalize_year("  2020  ") == 2020

def test_year_float_whole():
    assert normalize_year(2020.0) == 2020

def test_year_float_nonwhole_raises():
    with pytest.raises(NormalisationError):
        normalize_year(2020.5)

def test_year_fy_prefix_4digit():
    assert normalize_year("FY2020") == 2020

def test_year_fy_prefix_2digit():
    assert normalize_year("FY20") == 2020

def test_year_fy_lowercase():
    assert normalize_year("fy20") == 2020

def test_year_fy_apostrophe():
    assert normalize_year("FY'20") == 2020

def test_year_range_4digit_end():
    assert normalize_year("2019-2020") == 2020

def test_year_range_2digit_end():
    assert normalize_year("2019-20") == 2020

def test_year_range_slash():
    assert normalize_year("2019/20") == 2020

def test_year_month_year_short():
    assert normalize_year("Mar-20") == 2020

def test_year_month_year_full():
    assert normalize_year("March-2020") == 2020

def test_year_full_date_dash():
    assert normalize_year("31-03-2020") == 2020

def test_year_full_date_slash():
    assert normalize_year("31/03/2020") == 2020

def test_year_none_raises():
    with pytest.raises(NormalisationError):
        normalize_year(None)

def test_year_empty_string_raises():
    with pytest.raises(NormalisationError):
        normalize_year("")

def test_year_garbage_raises():
    with pytest.raises(NormalisationError):
        normalize_year("not-a-year")

def test_year_out_of_range_raises():
    with pytest.raises(NormalisationError):
        normalize_year("1899")

def test_year_two_digit_pivot_high():
    # '99' should resolve to 1999, not 2099
    assert normalize_year("FY99") == 1999


# ---------------------------------------------------------------------------
# normalize_ticker — 15 tests
# ---------------------------------------------------------------------------

def test_ticker_already_clean():
    assert normalize_ticker("RELIANCE") == "RELIANCE"

def test_ticker_lowercase():
    assert normalize_ticker("reliance") == "RELIANCE"

def test_ticker_mixed_case():
    assert normalize_ticker("ReLiAnCe") == "RELIANCE"

def test_ticker_ns_suffix():
    assert normalize_ticker("RELIANCE.NS") == "RELIANCE"

def test_ticker_bo_suffix():
    assert normalize_ticker("RELIANCE.BO") == "RELIANCE"

def test_ticker_nse_suffix():
    assert normalize_ticker("TCS.NSE") == "TCS"

def test_ticker_bse_suffix():
    assert normalize_ticker("TCS.BSE") == "TCS"

def test_ticker_leading_trailing_whitespace():
    assert normalize_ticker("  TCS  ") == "TCS"

def test_ticker_ampersand_preserved():
    assert normalize_ticker("M&M") == "M&M"

def test_ticker_ampersand_with_suffix():
    assert normalize_ticker("m&m.ns") == "M&M"

def test_ticker_hyphenated():
    assert normalize_ticker("BAJAJ-AUTO") == "BAJAJ-AUTO"

def test_ticker_none_raises():
    with pytest.raises(NormalisationError):
        normalize_ticker(None)

def test_ticker_empty_raises():
    with pytest.raises(NormalisationError):
        normalize_ticker("")

def test_ticker_whitespace_only_raises():
    with pytest.raises(NormalisationError):
        normalize_ticker("   ")

def test_ticker_invalid_chars_raises():
    with pytest.raises(NormalisationError):
        normalize_ticker("TCS Ltd!")
