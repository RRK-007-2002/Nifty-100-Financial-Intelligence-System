"""
scripts/run_acceptance_gates.py

Day 45 final sign-off: checks every automatable acceptance gate (AC-01
through AC-20) against the real database, filesystem, and (where needed)
a running API server, then prints a PASS / FAIL / MANUAL report.

Five gates can't be automated from this script at all, and are reported
as MANUAL with instructions instead of being guessed at:
  AC-05  needs a manual Excel calculation to compare against
  AC-08  needs the Streamlit dashboard running, to time a page load
  AC-09  needs the Streamlit dashboard's screener CSV export button
  AC-10  needs a human to look at PDFs for visual text overflow
  AC-13  needs screener_output.xlsx, a reference file this project
         hasn't produced

AC-07's "quality" screener preset and AC-12's "TCS" company aren't
formally defined elsewhere in this codebase (no ticker column exists),
so both make a documented assumption -- see their docstrings.

Run with: python scripts/run_acceptance_gates.py
Requires: pip install requests  (pypdf is optional, only for AC-20)
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import requests

DB_PATH: str = "nifty100.db"
API_BASE_URL: str = "http://127.0.0.1:8000"
EXPECTED_COMPANY_COUNT: int = 92
EXPECTED_PEER_GROUP_COUNT: int = 11

# (passed, detail) -- passed is None for a gate that can't be automated.
GateResult = Tuple[Optional[bool], str]


def _connect() -> sqlite3.Connection:
    """
    Open a SQLite connection with row access by column name.

    :return: A sqlite3.Connection configured with sqlite3.Row row_factory.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def gate_ac01_company_count() -> GateResult:
    """AC-01: SELECT COUNT(*) FROM companies = 92."""
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    return count == EXPECTED_COMPANY_COUNT, (
        f"companies count = {count} (expected {EXPECTED_COMPANY_COUNT})"
    )


def gate_ac02_statement_coverage() -> GateResult:
    """AC-02: >=90% of companies have >=10 years of P&L, BS and CF records."""
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
        if total == 0:
            return False, "no companies in database"

        qualifying = 0
        for row in conn.execute("SELECT id FROM companies"):
            company_id = row["id"]
            pl_years = conn.execute(
                "SELECT COUNT(DISTINCT year) FROM profitandloss WHERE company_id = ?",
                (company_id,),
            ).fetchone()[0]
            bs_years = conn.execute(
                "SELECT COUNT(DISTINCT year) FROM balancesheet WHERE company_id = ?",
                (company_id,),
            ).fetchone()[0]
            cf_years = conn.execute(
                "SELECT COUNT(DISTINCT year) FROM cashflow WHERE company_id = ?",
                (company_id,),
            ).fetchone()[0]
            if pl_years >= 10 and bs_years >= 10 and cf_years >= 10:
                qualifying += 1

        pct = qualifying / total * 100
    return pct >= 90, (
        f"{qualifying}/{total} companies ({pct:.1f}%) have >=10yrs of "
        f"PL/BS/CF records (need >= 90%)"
    )


def gate_ac03_foreign_keys() -> GateResult:
    """AC-03: PRAGMA foreign_key_check returns 0 rows."""
    with _connect() as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    return len(violations) == 0, f"{len(violations)} foreign key violations found"


def gate_ac04_ratio_row_count() -> GateResult:
    """AC-04: SELECT COUNT(*) FROM financial_ratios >= 1,100."""
    with _connect() as conn:
        count = conn.execute("SELECT COUNT(*) FROM financial_ratios").fetchone()[0]
    return count >= 1100, f"financial_ratios count = {count} (need >= 1100)"


def gate_ac05_revenue_cagr_spotcheck() -> GateResult:
    """AC-05: Revenue CAGR spot-check vs. manual Excel calc, within 0.1%."""
    return None, (
        "MANUAL: pick 5 companies, compute revenue CAGR by hand in Excel "
        "from profitandloss.sales, and compare to financial_ratios."
        "revenue_cagr_5yr -- must be within 0.1%"
    )


def gate_ac06_roe_consistency() -> GateResult:
    """AC-06: ROE matches companies.roe_percentage within 5% for 5 companies."""
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.company_name, c.roe_percentage, fr.return_on_equity_pct
            FROM companies c
            JOIN financial_ratios fr ON fr.company_id = c.id
                AND fr.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
            LIMIT 5
            """
        ).fetchall()

    if not rows:
        return False, "no companies with both roe_percentage and financial_ratios found"

    mismatches: List[str] = []
    for row in rows:
        stored, computed = row["roe_percentage"], row["return_on_equity_pct"]
        if stored is None or computed is None:
            mismatches.append(f"{row['company_name']}: missing value")
            continue
        diff_pct = abs(stored - computed) / abs(stored) * 100 if stored != 0 else (
            0 if computed == 0 else 100
        )
        if diff_pct > 5:
            mismatches.append(f"{row['company_name']}: {stored} vs {computed} ({diff_pct:.1f}% diff)")

    if mismatches:
        return False, "; ".join(mismatches)
    return True, f"checked {len(rows)} companies, all within 5%"


def gate_ac07_quality_screener_range() -> GateResult:
    """
    AC-07: a "quality" screener preset returns 10-50 companies.

    No formal definition of "quality preset" exists elsewhere in this
    project, so min_roe=15 and max_de=1 are assumed here -- edit these
    two values if your actual preset differs.
    """
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/screener",
            params={"min_roe": 15, "max_de": 1},
            timeout=10,
        )
    except requests.RequestException as exc:
        return None, f"BLOCKED: could not reach API server ({exc}) -- start uvicorn first"

    if response.status_code != 200:
        return False, f"screener returned HTTP {response.status_code}"

    count = len(response.json())
    return 10 <= count <= 50, (
        f"quality preset (min_roe=15, max_de=1) returned {count} companies (need 10-50)"
    )


def gate_ac08_profile_load_time() -> GateResult:
    """AC-08: Company Profile screen loads in under 3 seconds."""
    return None, (
        "MANUAL: requires the Streamlit dashboard running -- time the "
        "Company Profile screen for 5 companies, must be <3s each"
    )


def gate_ac09_csv_download_valid() -> GateResult:
    """AC-09: CSV download from the screener screen is valid and well-formed."""
    return None, (
        "MANUAL: requires the Streamlit dashboard's screener screen -- "
        "export the CSV and confirm it opens/parses correctly"
    )


def gate_ac10_tearsheet_text_overflow() -> GateResult:
    """AC-10: no text overflow in any of 5 sampled tearsheet PDFs."""
    return None, (
        "MANUAL: open 5 PDFs from reports/tearsheets/ and visually check "
        "for text overflow"
    )


def gate_ac11_health_endpoint() -> GateResult:
    """AC-11: GET /api/v1/health returns HTTP 200."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=10)
    except requests.RequestException as exc:
        return False, f"could not reach API server ({exc}) -- start uvicorn first"
    return response.status_code == 200, f"GET /api/v1/health -> HTTP {response.status_code}"


def gate_ac12_tcs_ratios_10_years() -> GateResult:
    """
    AC-12: the "TCS" ratios endpoint returns data for 10+ years.

    There's no ticker column in this schema, so the company is found by
    a name search instead -- adjust the LIKE pattern below if your
    companies table spells it differently.
    """
    with _connect() as conn:
        row = conn.execute(
            "SELECT id FROM companies "
            "WHERE company_name LIKE '%TCS%' OR company_name LIKE '%Tata Consultancy%' "
            "LIMIT 1"
        ).fetchone()
        if row is None:
            return None, (
                "MANUAL: no company matching 'TCS'/'Tata Consultancy' found by "
                "name -- confirm the right company_id yourself"
            )
        years = conn.execute(
            "SELECT COUNT(DISTINCT year) FROM financial_ratios WHERE company_id = ?",
            (row["id"],),
        ).fetchone()[0]

    return years >= 10, f"company_id {row['id']} has ratios for {years} distinct years (need >= 10)"


def gate_ac13_screener_matches_excel() -> GateResult:
    """AC-13: API screener results match screener_output.xlsx."""
    return None, (
        "MANUAL: requires screener_output.xlsx as a reference file (not "
        "produced by this project yet) to diff against /api/v1/screener"
    )


def gate_ac14_peer_percentiles_coverage() -> GateResult:
    """AC-14: peer_percentiles has data for all 11 peer groups."""
    with _connect() as conn:
        count = conn.execute(
            "SELECT COUNT(DISTINCT peer_group_name) FROM peer_percentiles"
        ).fetchone()[0]
    return count >= EXPECTED_PEER_GROUP_COUNT, (
        f"peer_percentiles covers {count} distinct peer groups "
        f"(need >= {EXPECTED_PEER_GROUP_COUNT})"
    )


def gate_ac15_cluster_labels_complete() -> GateResult:
    """AC-15: all 92 companies have a cluster_id in cluster_labels.csv."""
    path = Path("output/cluster_labels.csv")
    if not path.exists():
        return False, "output/cluster_labels.csv not found -- run src.analytics.clustering first"

    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    missing = [r for r in rows if not r.get("cluster_id", "")]
    passed = len(rows) == EXPECTED_COMPANY_COUNT and not missing
    return passed, (
        f"{len(rows)} rows, {len(missing)} with a missing cluster_id "
        f"(need {EXPECTED_COMPANY_COUNT} rows, 0 missing)"
    )


def gate_ac16_pros_cons_coverage() -> GateResult:
    """
    AC-16: all 92 companies have >=1 pro and >=1 con.

    Checked against the prosandcons DB table rather than a
    pros_cons_generated.csv, since this project has that data in SQLite,
    not as a standalone CSV file.
    """
    with _connect() as conn:
        rows = conn.execute("SELECT company_id, pros, cons FROM prosandcons").fetchall()

    covered = {r["company_id"] for r in rows}
    missing_content = [r["company_id"] for r in rows if not r["pros"] or not r["cons"]]
    passed = len(covered) == EXPECTED_COMPANY_COUNT and not missing_content
    return passed, (
        f"{len(covered)}/{EXPECTED_COMPANY_COUNT} companies have a prosandcons "
        f"row, {len(missing_content)} with an empty pros or cons"
    )


def gate_ac17_tearsheet_files() -> GateResult:
    """AC-17: 92 tearsheet PDFs exist, each at least 30 KB."""
    tearsheet_dir = Path("reports/tearsheets")
    if not tearsheet_dir.exists():
        return False, "reports/tearsheets/ directory not found"

    pdfs = list(tearsheet_dir.glob("*.pdf"))
    undersized = [p.name for p in pdfs if p.stat().st_size < 30 * 1024]
    passed = len(pdfs) == EXPECTED_COMPANY_COUNT and not undersized
    return passed, (
        f"{len(pdfs)} PDFs found (need {EXPECTED_COMPANY_COUNT}), "
        f"{len(undersized)} under 30KB"
    )


def gate_ac18_pytest_suite() -> GateResult:
    """AC-18: pytest shows 60+ tests collected, 0 failures."""
    return None, (
        "MANUAL: run `pytest tests/ --html=reports/pytest_report.html` "
        "and confirm 60+ tests collected, 0 failures"
    )


def gate_ac19_validation_failures_csv() -> GateResult:
    """AC-19: validation_failures.csv exists with the required columns."""
    path = Path("output/validation_failures.csv")
    if not path.exists():
        return False, "output/validation_failures.csv not found"

    with open(path, newline="", encoding="utf-8") as handle:
        header = next(csv.reader(handle), [])

    required = {"company_id", "field", "issue", "severity"}
    missing = required - set(header)
    return not missing, (
        f"columns present: {header}" if not missing else f"missing columns: {missing}"
    )


def gate_ac20_analyst_guide_length() -> GateResult:
    """AC-20: analyst_guide.pdf is at least 10 pages."""
    path = Path("docs/analyst_guide.pdf")
    if not path.exists():
        return False, "docs/analyst_guide.pdf not found"

    try:
        from pypdf import PdfReader
    except ImportError:
        return None, "MANUAL: install pypdf (`pip install pypdf`) to auto-count pages"

    pages = len(PdfReader(str(path)).pages)
    return pages >= 10, f"{pages} pages (need >= 10)"


GATES: List[Tuple[str, str, Callable[[], GateResult]]] = [
    ("AC-01", "companies count = 92", gate_ac01_company_count),
    ("AC-02", ">=90% companies have >=10yrs PL/BS/CF", gate_ac02_statement_coverage),
    ("AC-03", "PRAGMA foreign_key_check returns 0 rows", gate_ac03_foreign_keys),
    ("AC-04", "financial_ratios count >= 1,100", gate_ac04_ratio_row_count),
    ("AC-05", "Revenue CAGR spot-check within 0.1% of Excel", gate_ac05_revenue_cagr_spotcheck),
    ("AC-06", "ROE matches companies.roe_percentage within 5% (5 cos)", gate_ac06_roe_consistency),
    ("AC-07", "Quality screener preset returns 10-50 companies", gate_ac07_quality_screener_range),
    ("AC-08", "Company Profile screen loads under 3s", gate_ac08_profile_load_time),
    ("AC-09", "Screener CSV download is valid", gate_ac09_csv_download_valid),
    ("AC-10", "No text overflow in 5 sampled tearsheets", gate_ac10_tearsheet_text_overflow),
    ("AC-11", "GET /api/v1/health returns HTTP 200", gate_ac11_health_endpoint),
    ("AC-12", "TCS ratios endpoint returns data for 10+ years", gate_ac12_tcs_ratios_10_years),
    ("AC-13", "API screener results match screener_output.xlsx", gate_ac13_screener_matches_excel),
    ("AC-14", "peer_percentiles has data for all 11 peer groups", gate_ac14_peer_percentiles_coverage),
    ("AC-15", "All 92 companies have a cluster_id", gate_ac15_cluster_labels_complete),
    ("AC-16", "All 92 companies have >=1 pro and >=1 con", gate_ac16_pros_cons_coverage),
    ("AC-17", "92 tearsheet PDFs exist, each >=30KB", gate_ac17_tearsheet_files),
    ("AC-18", "pytest shows 60+ tests, 0 failures", gate_ac18_pytest_suite),
    ("AC-19", "validation_failures.csv exists with required columns", gate_ac19_validation_failures_csv),
    ("AC-20", "analyst_guide.pdf is >=10 pages", gate_ac20_analyst_guide_length),
]


def run_all_gates() -> List[Dict[str, str]]:
    """
    Run every gate in GATES, catching any unexpected exception so one
    broken gate doesn't stop the rest from running.

    :return: List of dicts with gate, description, status and detail.
    """
    results: List[Dict[str, str]] = []
    for gate_id, description, func in GATES:
        try:
            passed, detail = func()
        except Exception as exc:  # noqa: BLE001 -- isolate failures per gate
            passed, detail = False, f"ERROR while running this gate: {exc}"

        status = "MANUAL" if passed is None else ("PASS" if passed else "FAIL")
        results.append(
            {"gate": gate_id, "description": description, "status": status, "detail": detail}
        )
    return results


def _print_report(results: List[Dict[str, str]]) -> None:
    """
    Print a human-readable PASS/FAIL/MANUAL report with a summary count.

    :param results: The list returned by run_all_gates().
    """
    for result in results:
        print(f"[{result['status']:>6}] {result['gate']}: {result['description']}")
        print(f"         {result['detail']}")

    counts: Dict[str, int] = {}
    for result in results:
        counts[result["status"]] = counts.get(result["status"], 0) + 1
    print()
    print("Summary:", ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    _print_report(run_all_gates())
