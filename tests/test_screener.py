"""
tests/api/test_screener.py

Tests for GET /api/v1/screener (Sprint 6, Day 42).
"""

from __future__ import annotations

from starlette.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_screener_min_roe_filters_correctly() -> None:
    """Every row returned for min_roe=15 has roe_pct >= 15."""
    response = client.get("/api/v1/screener", params={"min_roe": 15})
    assert response.status_code == 200

    results = response.json()
    assert results, "Expected at least one company with ROE >= 15"
    for company in results:
        assert company["roe_pct"] is not None
        assert company["roe_pct"] >= 15


def test_screener_invalid_numeric_param_returns_400() -> None:
    """A non-numeric value for a numeric filter returns HTTP 400."""
    response = client.get("/api/v1/screener", params={"min_roe": "not-a-number"})
    assert response.status_code == 400


def test_screener_max_de_filters_correctly() -> None:
    """Every row returned for max_de=1 has debt_to_equity <= 1."""
    response = client.get("/api/v1/screener", params={"max_de": 1})
    assert response.status_code == 200

    for company in response.json():
        assert company["debt_to_equity"] is not None
        assert company["debt_to_equity"] <= 1


def test_screener_sector_filter() -> None:
    """Filtering by sector only returns companies in that sector."""
    sectors_response = client.get("/api/v1/sectors")
    assert sectors_response.status_code == 200
    sectors = sectors_response.json()
    assert sectors, "No sectors returned -- cannot test the sector filter"
    target_sector = sectors[0]["broad_sector"]

    response = client.get("/api/v1/screener", params={"sector": target_sector})
    assert response.status_code == 200
    for company in response.json():
        assert company["broad_sector"] == target_sector


def test_screener_no_filters_returns_all_companies() -> None:
    """With no query params, the screener returns every company."""
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    all_companies = client.get("/api/v1/companies").json()
    assert len(response.json()) == len(all_companies)
