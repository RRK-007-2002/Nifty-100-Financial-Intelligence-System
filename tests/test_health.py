"""
tests/api/test_health.py

Tests for GET /api/v1/health (Sprint 6, Day 42).
"""

from __future__ import annotations

from starlette.testclient import TestClient

from src.api.main import SCHEMA_TABLES, app

client = TestClient(app)


def test_health_returns_200_and_status_ok() -> None:
    """GET /api/v1/health responds with HTTP 200 and status == 'ok'."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_reports_all_schema_tables() -> None:
    """db_row_counts includes a key for every table in SCHEMA_TABLES."""
    response = client.get("/api/v1/health")
    row_counts = response.json()["db_row_counts"]
    for table in SCHEMA_TABLES:
        assert table in row_counts, f"'{table}' missing from db_row_counts"


def test_health_row_counts_are_non_negative_for_existing_tables() -> None:
    """
    Every table in SCHEMA_TABLES exists in the real schema, so none of the
    reported counts should be -1 (the sentinel main.py uses for a missing
    table).
    """
    response = client.get("/api/v1/health")
    row_counts = response.json()["db_row_counts"]
    for table, count in row_counts.items():
        assert count != -1, f"Table '{table}' not found in the database"


def test_health_includes_version_and_uptime() -> None:
    """Response includes a version string and a non-negative uptime."""
    response = client.get("/api/v1/health")
    body = response.json()
    assert body["version"] == "1.0.0"
    assert body["uptime_seconds"] >= 0
