"""
src/api/routers/documents.py

Company annual-report documents endpoint (Sprint 6, Day 40).

documents(id, company_id, Year, Annual_Report) has no is_url_valid column,
so it's computed here with a live HTTP HEAD request per link (short timeout,
any exception or non-2xx/3xx status counts as invalid). This makes the
endpoint's latency depend on the annual-report host's response time --
acceptable for a handful of documents per company, but worth caching if
this list grows or gets called often.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List

import requests
from fastapi import APIRouter, HTTPException

DB_PATH: str = "nifty100.db"
URL_CHECK_TIMEOUT_SECONDS: float = 4.0

router = APIRouter(tags=["documents"])


def _is_url_valid(url: str) -> bool:
    """
    Check whether a URL responds successfully to an HTTP HEAD request.

    :param url: The URL to check.
    :return: True if the response status is in the 200-399 range, else False.
    """
    if not url:
        return False
    try:
        response = requests.head(url, timeout=URL_CHECK_TIMEOUT_SECONDS, allow_redirects=True)
        return 200 <= response.status_code < 400
    except requests.RequestException:
        return False


@router.get("/companies/{company_id}/documents")
def get_company_documents(company_id: int) -> List[Dict[str, Any]]:
    """
    Return every annual report link on file for a company, each tagged
    with a live is_url_valid check.

    :param company_id: The company's companies.id value.
    :return: List of dicts with year, annual_report_url and is_url_valid.
    :raises HTTPException: 404 if the company_id is not found.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        company_row = conn.execute(
            "SELECT 1 FROM companies WHERE id = ?", (company_id,)
        ).fetchone()
        if company_row is None:
            raise HTTPException(status_code=404, detail=f"Company id {company_id} not found")

        rows = conn.execute(
            'SELECT Year AS year, Annual_Report AS annual_report_url '
            "FROM documents WHERE company_id = ? ORDER BY Year ASC",
            (company_id,),
        ).fetchall()

    return [
        {
            "year": row["year"],
            "annual_report_url": row["annual_report_url"],
            "is_url_valid": _is_url_valid(row["annual_report_url"]),
        }
        for row in rows
    ]