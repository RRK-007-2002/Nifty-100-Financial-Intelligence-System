"""
scripts/performance/load_test_screener.py

Day 43 load test: fire 10 concurrent GET /api/v1/screener requests against
a running FastAPI server using Python's threading module, and check that
all 10 complete within 10 seconds (combined wall-clock time, not per-request).

Requires the API server to already be running (uvicorn src.api.main:app),
since this exercises real network I/O and concurrency -- unlike the
in-process Starlette TestClient used in tests/api/.
"""

from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional

import requests

API_BASE_URL: str = "http://127.0.0.1:8000"
SCREENER_ENDPOINT: str = f"{API_BASE_URL}/api/v1/screener"
NUM_CONCURRENT_REQUESTS: int = 10
TARGET_TOTAL_SECONDS: float = 10.0
PER_REQUEST_TIMEOUT_SECONDS: float = TARGET_TOTAL_SECONDS


def _fire_request(results: List[Optional[Dict[str, Any]]], index: int) -> None:
    """
    Make one GET request to the screener endpoint and record its outcome
    into results[index]. Runs inside a worker thread.

    :param results: Shared list that each thread writes its own slot of.
    :param index: This thread's slot in results.
    """
    start = time.perf_counter()
    try:
        response = requests.get(
            SCREENER_ENDPOINT,
            params={"min_roe": 10},
            timeout=PER_REQUEST_TIMEOUT_SECONDS,
        )
        elapsed = time.perf_counter() - start
        results[index] = {
            "status_code": response.status_code,
            "elapsed_seconds": elapsed,
            "error": None,
        }
    except requests.RequestException as exc:
        elapsed = time.perf_counter() - start
        results[index] = {
            "status_code": None,
            "elapsed_seconds": elapsed,
            "error": str(exc),
        }


def run_load_test() -> Dict[str, Any]:
    """
    Launch NUM_CONCURRENT_REQUESTS threads against the screener endpoint
    simultaneously, wait for all of them, and summarise the result.

    :return: Dict with overall_elapsed_seconds, passed (bool), and the
        per-request results list.
    """
    results: List[Optional[Dict[str, Any]]] = [None] * NUM_CONCURRENT_REQUESTS
    threads = [
        threading.Thread(target=_fire_request, args=(results, i))
        for i in range(NUM_CONCURRENT_REQUESTS)
    ]

    overall_start = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    overall_elapsed = time.perf_counter() - overall_start

    passed = overall_elapsed <= TARGET_TOTAL_SECONDS and all(
        r is not None and r["error"] is None and r["status_code"] == 200 for r in results
    )

    return {
        "overall_elapsed_seconds": overall_elapsed,
        "passed": passed,
        "results": results,
    }


def _print_report(summary: Dict[str, Any]) -> None:
    """
    Print a human-readable report of a run_load_test() summary.

    :param summary: The dict returned by run_load_test().
    """
    print(
        f"All {NUM_CONCURRENT_REQUESTS} requests completed in "
        f"{summary['overall_elapsed_seconds']:.2f}s "
        f"(target: <= {TARGET_TOTAL_SECONDS:.0f}s)"
    )
    for i, result in enumerate(summary["results"]):
        print(
            f"  Request {i}: status={result['status_code']} "
            f"elapsed={result['elapsed_seconds']:.3f}s error={result['error']}"
        )
    print("PASS" if summary["passed"] else "FAIL")


if __name__ == "__main__":
    _print_report(run_load_test())
