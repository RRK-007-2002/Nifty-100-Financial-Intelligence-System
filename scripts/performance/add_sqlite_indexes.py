"""
scripts/add_sqlite_indexes.py

Day 43 SQLite optimisation: add indexes on company_id and year across
every table in nifty100.db where those columns exist.

Tables with both company_id and year (balancesheet, cashflow,
financial_ratios, market_cap, profitandloss, peer_percentiles) get a
single composite index on (company_id, year), since nearly every query
in src/api/ and src/analytics/ filters by company_id and then picks the
latest/matching year -- a composite index serves that pattern better
than two separate single-column indexes. Tables with only company_id
(sectors, documents, peer_groups, prosandcons, analysis) get a
single-column index instead.

Uses CREATE INDEX IF EXISTS, so safe to re-run at any time.
"""

from __future__ import annotations

import sqlite3
from typing import List

DB_PATH: str = r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db"


def _table_names(conn: sqlite3.Connection) -> List[str]:
    """
    List every user table in the database (excluding sqlite's internal tables).

    :param conn: Open SQLite connection.
    :return: List of table names.
    """
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [row[0] for row in rows]


def _column_names(conn: sqlite3.Connection, table: str) -> List[str]:
    """
    List column names for a table via PRAGMA table_info.

    :param conn: Open SQLite connection.
    :param table: Table name.
    :return: List of column names.
    """
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def add_indexes(db_path: str = DB_PATH) -> List[str]:
    """
    Create a composite (company_id, year) index on any table that has
    both columns, and a single-column company_id index on any table
    that has only that one. Idempotent.

    :param db_path: Path to the SQLite database.
    :return: List of index names created or already present.
    """
    created: List[str] = []
    with sqlite3.connect(db_path) as conn:
        for table in _table_names(conn):
            columns = _column_names(conn, table)
            has_company_id = "company_id" in columns
            has_year = "year" in columns

            if has_company_id and has_year:
                index_name = f"idx_{table}_company_year"
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {index_name} "
                    f"ON {table} (company_id, year)"
                )
                created.append(index_name)
            elif has_company_id:
                index_name = f"idx_{table}_company_id"
                conn.execute(
                    f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} (company_id)"
                )
                created.append(index_name)

        conn.commit()
    return created


if __name__ == "__main__":
    index_names = add_indexes()
    print(f"Ensured {len(index_names)} indexes exist:")
    for name in index_names:
        print(f"  {name}")
