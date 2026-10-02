from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "db" / "nifty100.db"
CONFIG_PATH = ROOT / "src" / "screener" / "screener_config.yaml"
OUTPUT_DIR = ROOT / "output"
PEER_EXPORT_PATH = OUTPUT_DIR / "peer_comparison.xlsx"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from src.screener.engine import build_screener_universe, load_screener_config, run_all_presets, validate_preset_counts
from src.screener.peer import compute_peer_percentiles
from src.screener.peer_export import export_peer_comparison


def run_pytest_suite() -> int:
    """Run the project test suite and return the pytest exit code."""
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def validate_screener_presets(conn: sqlite3.Connection) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    universe = build_screener_universe(conn)
    config = load_screener_config(CONFIG_PATH)
    results = run_all_presets(universe, conn, config)
    summary = validate_preset_counts(results)

    print("\n=== Preset count summary ===")
    print(summary.to_string(index=False))

    qc = results["Quality Compounder"].copy()
    qc = qc[["company_id", "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr"]]
    qc = qc.sort_values("return_on_equity_pct", ascending=False)
    print("\n=== Quality Compounder top 5 ===")
    print(qc.head(5).to_string(index=False))

    assert not qc.empty, "Quality Compounder returned no companies"
    assert (qc["return_on_equity_pct"] > 15).all(), "Quality Compounder has ROE <= 15%"
    assert (qc["debt_to_equity"].fillna(np.inf) < 1.0).all(), "Quality Compounder has D/E >= 1.0"

    return summary, results


def validate_peer_ranking(conn: sqlite3.Connection, universe: pd.DataFrame) -> pd.DataFrame:
    peer_groups = pd.read_sql("SELECT * FROM peer_groups", conn)
    companies = pd.read_sql("SELECT * FROM companies", conn)
    peer_pct = compute_peer_percentiles(universe, peer_groups[["company_id", "peer_group_name"]])

    it_rows = peer_pct[
        (peer_pct["peer_group_name"] == "IT Services")
        & (peer_pct["metric"] == "return_on_equity_pct")
    ].copy()
    it_rows = it_rows.sort_values("percentile_rank", ascending=False)

    print("\n=== IT Services ROE percentile ranking ===")
    print(it_rows.head(10).to_string(index=False))

    assert not it_rows.empty, "IT Services peer group has no ROE percentile rows"

    it_companies = universe[universe["company_id"].isin(it_rows["company_id"])][["company_id", "return_on_equity_pct"]].copy()
    it_companies = it_companies.merge(it_rows[["company_id", "percentile_rank"]], on="company_id", how="inner")
    it_companies = it_companies.sort_values(["return_on_equity_pct", "percentile_rank"], ascending=[False, False])

    top_company_id = it_companies.iloc[0]["company_id"]
    top_company_rank = it_companies.iloc[0]["percentile_rank"]
    max_rank_company = it_rows.iloc[0]["company_id"]

    assert top_company_id == max_rank_company, (
        f"Highest ROE company ({top_company_id}) does not match highest percentile company ({max_rank_company})"
    )
    assert top_company_rank == it_rows.iloc[0]["percentile_rank"], "Percentile rank order is inconsistent"

    out_path = export_peer_comparison(peer_pct, companies, peer_groups, PEER_EXPORT_PATH)
    print(f"\nPeer comparison exported to: {out_path}")

    return it_companies


def main() -> None:
    print("Running Day 21 sprint review checks...\n")

    pytest_exit = run_pytest_suite()
    if pytest_exit != 0:
        raise SystemExit(f"Pytest failed with exit code {pytest_exit}")
    print("\nPytest: all tests passed.")

    conn = get_db_connection()
    try:
        universe = build_screener_universe(conn)
        summary, results = validate_screener_presets(conn)
        validate_peer_ranking(conn, universe)

        in_range = summary["in_range"].all()
        if not in_range:
            raise AssertionError(f"Preset counts out of range:\n{summary}")

        print("\nAll Day 21 validation checks passed.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
