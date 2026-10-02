"""
tests/api/test_companies.py

Tests for the /api/v1/companies endpoints (Sprint 6, Day 42).

The original spec's example ("GET /companies/TCS returns correct data")
assumed a ticker column that doesn't exist in this schema. These tests
instead pull a real company_id from the live /companies list rather than
hard-coding one, so they don't depend on knowing the database's contents
in advance.
"""

from __future__ import annotations

from starlette.testclient import TestClient

from src.api.main import app

client = TestClient(app)

EXPECTED_COMPANY_COUNT = 92  # Per acceptance gate AC-01
NONEXISTENT_COMPANY_ID = 999_999_999


def test_list_companies_returns_all_92() -> None:
    """GET /api/v1/companies returns exactly 92 records (gate AC-01)."""
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert len(response.json()) == EXPECTED_COMPANY_COUNT


def test_get_company_returns_correct_data_for_valid_id() -> None:
    """
    GET /api/v1/companies/{company_id} returns a profile matching the
    summary row for the same company in the /companies list.
    """
    listing = client.get("/api/v1/companies").json()
    assert listing, "No companies returned -- cannot test detail lookup"
    sample = listing[0]

    response = client.get(f"/api/v1/companies/{sample['company_id']}")
    assert response.status_code == 200

    profile = response.json()
    assert profile["company_id"] == sample["company_id"]
    assert profile["company_name"] == sample["company_name"]
    assert "latest_ratios" in profile
    assert "sector_data" in profile


def test_get_company_returns_404_for_invalid_id() -> None:
    """GET /api/v1/companies/{invalid_id} returns HTTP 404."""
    response = client.get(f"/api/v1/companies/{NONEXISTENT_COMPANY_ID}")
    assert response.status_code == 404


def test_get_ratios_returns_404_for_invalid_id() -> None:
    """GET /api/v1/companies/{invalid_id}/ratios returns HTTP 404."""
    response = client.get(f"/api/v1/companies/{NONEXISTENT_COMPANY_ID}/ratios")
    assert response.status_code == 404


def test_get_pl_returns_404_for_invalid_id() -> None:
    """GET /api/v1/companies/{invalid_id}/pl returns HTTP 404."""
    response = client.get(f"/api/v1/companies/{NONEXISTENT_COMPANY_ID}/pl")
    assert response.status_code == 404
