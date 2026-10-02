"""
tests/etl/test_normalise.py

20 unit tests for normalize_year(), covering every branch of its actual
implementation (Sprint 6, Day 41).

normalize_year lives in src/etl/loader.py in this codebase, not a separate
normalize.py -- update the import below if it moves. Every expected value
here was verified by running the real function, not guessed from the spec.

Behaviour as implemented:
  - 'TTM' (exact match only, case-sensitive) becomes 'Dec 2024' first.
  - The (possibly-substituted) string is split on literal single spaces.
  - 2 tokens or fewer: re-joined unchanged.
  - More than 2 tokens: the LAST token is dropped, remaining tokens re-joined.
  - Non-string input is coerced via str() before splitting.

A short bonus section for normalize_ticker() (the other function in the
same module) follows the 20 required normalize_year tests -- not counted
against that 20, just extra coverage since the function was otherwise
untested.
"""

from __future__ import annotations

import pytest

from src.etl.loader import normalize_ticker, normalize_year

# --- normalize_year: TTM substitution -----------------------------------


def test_ttm_becomes_dec_2024() -> None:
    """Exact 'TTM' is substituted with 'Dec 2024' before splitting."""
    assert normalize_year("TTM") == "Dec 2024"


def test_lowercase_ttm_is_not_substituted() -> None:
    """The TTM check is case-sensitive; 'ttm' passes through unchanged."""
    assert normalize_year("ttm") == "ttm"


def test_ttm_embedded_in_longer_string_is_not_substituted() -> None:
    """Only an exact 'TTM' match triggers substitution, not a substring."""
    assert normalize_year("Q4 TTM") == "Q4 TTM"


# --- normalize_year: 2-token (month year) inputs pass through unchanged -


def test_standard_month_year_unchanged() -> None:
    """A normal 'Mon YYYY' string (2 tokens) is returned unchanged."""
    assert normalize_year("Mar 2024") == "Mar 2024"


def test_different_month_year_unchanged() -> None:
    """A second 'Mon YYYY' example confirms this isn't a one-off."""
    assert normalize_year("Sep 2023") == "Sep 2023"


def test_dec_2024_unchanged() -> None:
    """'Dec 2024' (the literal TTM substitution target) passes through as-is."""
    assert normalize_year("Dec 2024") == "Dec 2024"


# --- normalize_year: single-token inputs ---------------------------------


def test_single_token_year_only() -> None:
    """A bare year with no month (1 token) is returned unchanged."""
    assert normalize_year("2024") == "2024"


def test_single_token_month_only() -> None:
    """A bare month with no year (1 token) is returned unchanged."""
    assert normalize_year("Mar") == "Mar"


def test_empty_string_returns_empty_string() -> None:
    """An empty string splits to [''] (1 token) and is returned unchanged."""
    assert normalize_year("") == ""


# --- normalize_year: 3+ token inputs drop the last token -----------------


def test_three_tokens_drops_last() -> None:
    """With 3 tokens, the last one is dropped and the rest re-joined."""
    assert normalize_year("Sales Mar 2024") == "Sales Mar"


def test_three_tokens_different_prefix_drops_last() -> None:
    """A second 3-token example confirms the drop-last behaviour generally."""
    assert normalize_year("Q1 Mar 2024") == "Q1 Mar"


def test_four_tokens_drops_only_the_last() -> None:
    """With 4 tokens, only the final one is dropped, not all extras."""
    assert normalize_year("A B C D") == "A B C"


# --- normalize_year: whitespace edge cases --------------------------------


def test_single_space_string() -> None:
    """A lone space splits into ['',''] (2 tokens) and rejoins to ' '."""
    assert normalize_year(" ") == " "


def test_double_space_between_tokens_creates_extra_empty_token() -> None:
    """
    A double space inserts an empty token, pushing the token count to 3
    and triggering the drop-last behaviour, which drops '2024' here.
    """
    assert normalize_year("Mar  2024") == "Mar "


def test_trailing_space_creates_extra_empty_token() -> None:
    """A trailing space adds an empty 3rd token, which then gets dropped."""
    assert normalize_year("Dec 2024 ") == "Dec 2024"


def test_leading_space_creates_extra_empty_token() -> None:
    """A leading space adds an empty 1st token; the last token is dropped."""
    assert normalize_year(" Mar 2024") == " Mar"


def test_tab_is_not_treated_as_a_separator() -> None:
    """Only literal spaces are split on -- a tab keeps the string as 1 token."""
    assert normalize_year("Mar\t2024") == "Mar\t2024"


# --- normalize_year: non-string input --------------------------------------


def test_integer_input_is_coerced_to_string() -> None:
    """A non-string input is coerced via str() before splitting."""
    assert normalize_year(2024) == "2024"


def test_none_input_is_coerced_to_the_string_none() -> None:
    """None coerces to the literal string 'None' via str(), not an error."""
    assert normalize_year(None) == "None"


# --- normalize_year: idempotency ------------------------------------------


def test_normalizing_twice_is_idempotent() -> None:
    """Running normalize_year on its own output a second time is a no-op."""
    once = normalize_year("Sales Mar 2024")
    twice = normalize_year(once)
    assert once == twice == "Sales Mar"


# =========================================================================
# Bonus: normalize_ticker (same module, not part of the required 20 above)
# =========================================================================


def test_ticker_uppercased() -> None:
    """A lowercase ticker is converted to uppercase."""
    assert normalize_ticker("tcs") == "TCS"


def test_ticker_strips_ns_suffix() -> None:
    """The .NS exchange suffix is stripped."""
    assert normalize_ticker("INFY.NS") == "INFY"


def test_ticker_strips_bo_suffix() -> None:
    """The .BO exchange suffix is stripped."""
    assert normalize_ticker("reliance.bo") == "RELIANCE"


def test_ticker_strips_nse_suffix() -> None:
    """The longer .NSE suffix is also stripped."""
    assert normalize_ticker("TCS.NSE") == "TCS"


def test_ticker_strips_surrounding_whitespace() -> None:
    """Leading/trailing whitespace is stripped before suffix handling."""
    assert normalize_ticker("  tcs  ") == "TCS"


def test_ticker_without_suffix_unchanged_besides_case() -> None:
    """A ticker with no recognised suffix is only uppercased."""
    assert normalize_ticker("wipro") == "WIPRO"


def test_empty_ticker_raises_value_error() -> None:
    """An empty string (after stripping) raises ValueError."""
    with pytest.raises(ValueError):
        normalize_ticker("")


def test_whitespace_only_ticker_raises_value_error() -> None:
    """A whitespace-only string strips to empty and also raises ValueError."""
    with pytest.raises(ValueError):
        normalize_ticker("   ")
