# Performance Notes — Sprint 6, Day 43

## 1. Load test — GET /api/v1/screener (10 concurrent requests)

Run (with `uvicorn src.api.main:app --port 8000` already running):

```
python scripts/performance/load_test_screener.py
```

- Target: all 10 requests complete within 10 seconds combined.
- Result: _paste the script's PASS/FAIL output and overall_elapsed_seconds here_

## 2. SQLite indexing

Run once:

```
python scripts/add_sqlite_indexes.py
```

Adds a composite `(company_id, year)` index on every table that has both
columns, and a single-column `company_id` index on tables that only have
that one. Safe to re-run.

- Indexes created: _paste the script's output list here_
- Re-ran the load test after indexing — before/after comparison: _fill in_

## 3. Dashboard performance (Company Profile screen, 5 companies)

**Blocked** — needs the Streamlit app's source/entry-point file, not yet
shared. Target per spec: under 3 seconds per company.

## 4. End-to-end test (Streamlit :8501 + FastAPI :8000 simultaneously)

**Blocked** — same reason as above. Target: both start without a port
conflict and the dashboard loads data correctly from the API.

## 5. Bottlenecks found

_Fill in after running items 1–2 above. If the screener's `JOIN` against_
_`sectors` and `financial_ratios` with a per-row correlated subquery for_
_"latest year" shows up slow at scale, that subquery is the first place_
_to look — the new composite index should help it directly._
