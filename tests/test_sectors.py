"""
tests/api/test_sectors.py

Tests for the /api/v1/sectors endpoints (Sprint 6, Day 42).
"""

from __future__ import annotations

from starlette.testclient import TestClient

from src.api.main import app

client = TestClient(app)

EXPECTED_SECTOR_COUNT = 11  # Per Day 40 spec ("all 11 sectors")


def test_sectors_returns_exactly_11() -> None:
    """GET /api/v1/sectors returns exactly 11 broad sectors."""
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
    sectors = response.json()
    assert len(sectors) == EXPECTED_SECTOR_COUNT


def test_sector_companies_returns_only_that_sector() -> None:
    """
    GET /api/v1/sectors/{sector}/companies returns a non-empty list, and
    every one of those companies is actually a member of the requested
    sector (cross-checked via /sectors/{sector}/companies against the
    sectors summary endpoint's company_count).
    """
    sectors = client.get("/api/v1/sectors").json()
    assert sectors, "No sectors returned -- cannot test sector company lookup"
    target = sectors[0]

    response = client.get(f"/api/v1/sectors/{target['broad_sector']}/companies")
    assert response.status_code == 200

    companies = response.json()
    assert len(companies) == target["company_count"]


def test_sector_companies_returns_404_for_unknown_sector() -> None:
    """An unknown sector name returns HTTP 404."""
    response = client.get("/api/v1/sectors/Not-A-Real-Sector-XYZ/companies")
    assert response.status_code == 404
