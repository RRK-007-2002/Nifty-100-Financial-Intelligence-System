
"""
src/api/routers/companies.py

Company-data endpoints for the Financial Analytics API
(Nifty 100 Financial Intelligence Platform, Sprint 6, Day 39).

Actual database schema:

companies(
    id,
    company_logo,
    company_name,
    chart_link,
    about_company,
    website,
    nse_profile,
    bse_profile,
    face_value,
    book_value,
    roce_percentage,
    roe_percentage
)

sectors(
    company_id,
    broad_sector,
    sub_sector,
    index_weight_pct,
    market_cap_category
)

financial_ratios(
    company_id,
    year,
    ...
)

profitandloss(
    company_id,
    year,
    ...
)

balancesheet(
    company_id,
    year,
    ...
)

cashflow(
    company_id,
    year,
    ...
)

Tearsheets:
reports/tearsheets/<company_id>_tearsheet.pdf
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse


# ============================================================
# PROJECT PATHS
# ============================================================

# File:
# nifty100/src/api/routers/companies.py
#
# parents[0] = routers
# parents[1] = api
# parents[2] = src
# parents[3] = nifty100

BASE_DIR = Path(__file__).resolve().parents[3]

DB_PATH = BASE_DIR / "db" / "nifty100.db"

TEARSHEET_DIR = BASE_DIR / "reports" / "tearsheets"


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(tags=["companies"])


# ============================================================
# DATABASE CONNECTION
# ============================================================

def _get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection with sqlite3.Row access.
    """

    if not DB_PATH.exists():
        raise RuntimeError(
            f"Database not found: {DB_PATH}"
        )

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row

    return conn


# ============================================================
# HELPERS
# ============================================================

def _rows_to_dicts(
    rows: List[sqlite3.Row],
) -> List[Dict[str, Any]]:
    """
    Convert sqlite3.Row objects to normal dictionaries.
    """

    return [dict(row) for row in rows]


def _company_exists(
    conn: sqlite3.Connection,
    company_id: str,
) -> bool:
    """
    Check whether a company exists.

    company_id is TEXT in the actual database.
    """

    row = conn.execute(
        """
        SELECT 1
        FROM companies
        WHERE id = ?
        LIMIT 1
        """,
        (company_id,),
    ).fetchone()

    return row is not None


def _year_expression(column: str = "year") -> str:
    """
    Convert year values such as:

        Mar 2016
        Mar 2024
        2019

    into an integer year inside SQLite.

    The database stores year as TEXT.
    """

    return f"""
        CAST(
            CASE
                WHEN {column} GLOB '*[0-9][0-9][0-9][0-9]*'
                THEN substr(
                    {column},
                    instr(
                        {column},
                        substr(
                            {column},
                            instr({column}, '20'),
                            4
                        )
                    ),
                    4
                )
                ELSE NULL
            END
            AS INTEGER
        )
    """


def _build_year_filter(
    from_year: Optional[int],
    to_year: Optional[int],
) -> tuple[str, List[int]]:
    """
    Build a year filter for TEXT year values such as 'Mar 2016'.
    """

    clauses: List[str] = []
    params: List[int] = []

    year_expr = _year_expression("year")

    if from_year is not None:
        clauses.append(
            f"{year_expr} >= ?"
        )
        params.append(from_year)

    if to_year is not None:
        clauses.append(
            f"{year_expr} <= ?"
        )
        params.append(to_year)

    if not clauses:
        return "", params

    return (
        " AND " + " AND ".join(clauses),
        params,
    )


# ============================================================
# COMPANY LIST
# ============================================================

@router.get("/companies")
def list_companies(
    sector: Optional[str] = Query(
        default=None,
        description="Filter by broad sector",
    ),
    market_cap_category: Optional[str] = Query(
        default=None,
        description="Filter by market-cap category",
    ),
    search: Optional[str] = Query(
        default=None,
        description="Partial match on company name",
    ),
) -> List[Dict[str, Any]]:
    """
    Return companies with sector information and basic ROE/ROCE.

    Optional filters:
        - sector
        - market_cap_category
        - search
    """

    query = """
        SELECT
            c.id AS company_id,
            c.company_name AS company_name,
            s.broad_sector AS broad_sector,
            s.sub_sector AS sub_sector,
            s.market_cap_category AS market_cap_category,
            s.index_weight_pct AS index_weight_pct,
            c.roe_percentage AS roe_pct,
            c.roce_percentage AS roce_pct
        FROM companies c
        JOIN sectors s
            ON s.company_id = c.id
        WHERE 1 = 1
    """

    params: List[Any] = []

    if sector:
        query += """
            AND s.broad_sector = ?
        """
        params.append(sector)

    if market_cap_category:
        query += """
            AND s.market_cap_category = ?
        """
        params.append(market_cap_category)

    if search:
        query += """
            AND LOWER(c.company_name) LIKE LOWER(?)
        """
        params.append(f"%{search}%")

    query += """
        ORDER BY c.company_name ASC
    """

    with _get_connection() as conn:
        rows = conn.execute(
            query,
            params,
        ).fetchall()

    return _rows_to_dicts(rows)


# ============================================================
# COMPANY PROFILE
# ============================================================

@router.get("/companies/{company_id}")
def get_company(
    company_id: str,
) -> Dict[str, Any]:
    """
    Return the complete company profile.

    Includes:
        - base company information
        - latest financial ratios
        - sector information
    """

    with _get_connection() as conn:

        company_row = conn.execute(
            """
            SELECT *
            FROM companies
            WHERE id = ?
            """,
            (company_id,),
        ).fetchone()

        if company_row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Company id '{company_id}' not found",
            )

        # ----------------------------------------------------
        # Latest financial ratios
        # ----------------------------------------------------

        latest_ratios_row = conn.execute(
            f"""
            SELECT *
            FROM financial_ratios
            WHERE company_id = ?

            ORDER BY
                {_year_expression("year")} DESC

            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

        # ----------------------------------------------------
        # Sector information
        # ----------------------------------------------------

        sector_row = conn.execute(
            """
            SELECT *
            FROM sectors
            WHERE company_id = ?
            LIMIT 1
            """,
            (company_id,),
        ).fetchone()

    profile: Dict[str, Any] = dict(company_row)

    # Rename database id -> company_id
    profile["company_id"] = profile.pop("id")

    profile["latest_ratios"] = (
        dict(latest_ratios_row)
        if latest_ratios_row
        else None
    )

    profile["sector_data"] = (
        dict(sector_row)
        if sector_row
        else None
    )

    return profile


# ============================================================
# FINANCIAL STATEMENT HELPER
# ============================================================

def _get_financial_statement(
    company_id: str,
    table_name: str,
    from_year: Optional[int],
    to_year: Optional[int],
) -> List[Dict[str, Any]]:
    """
    Shared helper for:

        profitandloss
        balancesheet
        cashflow

    company_id is TEXT.

    Year values are stored as TEXT such as 'Mar 2016'.
    """

    allowed_tables = {
        "profitandloss",
        "balancesheet",
        "cashflow",
    }

    if table_name not in allowed_tables:
        raise ValueError(
            f"Invalid financial statement table: {table_name}"
        )

    with _get_connection() as conn:

        if not _company_exists(
            conn,
            company_id,
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Company id '{company_id}' not found",
            )

        year_clause, year_params = _build_year_filter(
            from_year,
            to_year,
        )

        query = f"""
            SELECT *
            FROM {table_name}
            WHERE company_id = ?
            {year_clause}
            ORDER BY {_year_expression("year")} ASC
        """

        rows = conn.execute(
            query,
            [company_id, *year_params],
        ).fetchall()

    return _rows_to_dicts(rows)


# ============================================================
# PROFIT & LOSS
# ============================================================

@router.get("/companies/{company_id}/pl")
def get_profit_and_loss(
    company_id: str,
    from_year: Optional[int] = Query(
        default=None,
        description="Starting fiscal year",
    ),
    to_year: Optional[int] = Query(
        default=None,
        description="Ending fiscal year",
    ),
) -> List[Dict[str, Any]]:
    """
    Return Profit & Loss history.
    """

    return _get_financial_statement(
        company_id,
        "profitandloss",
        from_year,
        to_year,
    )


# ============================================================
# BALANCE SHEET
# ============================================================

@router.get("/companies/{company_id}/bs")
def get_balance_sheet(
    company_id: str,
    from_year: Optional[int] = Query(
        default=None,
        description="Starting fiscal year",
    ),
    to_year: Optional[int] = Query(
        default=None,
        description="Ending fiscal year",
    ),
) -> List[Dict[str, Any]]:
    """
    Return Balance Sheet history.
    """

    return _get_financial_statement(
        company_id,
        "balancesheet",
        from_year,
        to_year,
    )


# ============================================================
# CASH FLOW
# ============================================================

@router.get("/companies/{company_id}/cashflow")
def get_cash_flow(
    company_id: str,
    from_year: Optional[int] = Query(
        default=None,
        description="Starting fiscal year",
    ),
    to_year: Optional[int] = Query(
        default=None,
        description="Ending fiscal year",
    ),
) -> List[Dict[str, Any]]:
    """
    Return Cash Flow history.
    """

    return _get_financial_statement(
        company_id,
        "cashflow",
        from_year,
        to_year,
    )


# ============================================================
# FINANCIAL RATIOS
# ============================================================

@router.get("/companies/{company_id}/ratios")
def get_ratios(
    company_id: str,
    year: Optional[int] = Query(
        default=None,
        description="Return ratios for a specific fiscal year",
    ),
) -> List[Dict[str, Any]]:
    """
    Return financial ratios for a company.

    If year is supplied, values such as 'Mar 2024'
    are matched using the extracted numeric year.
    """

    with _get_connection() as conn:

        if not _company_exists(
            conn,
            company_id,
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Company id '{company_id}' not found",
            )

        if year is not None:

            year_expr = _year_expression("year")

            rows = conn.execute(
                f"""
                SELECT *
                FROM financial_ratios
                WHERE company_id = ?
                  AND {year_expr} = ?
                ORDER BY {year_expr} ASC
                """,
                (
                    company_id,
                    year,
                ),
            ).fetchall()

        else:

            year_expr = _year_expression("year")

            rows = conn.execute(
                f"""
                SELECT *
                FROM financial_ratios
                WHERE company_id = ?
                ORDER BY {year_expr} ASC
                """,
                (company_id,),
            ).fetchall()

    return _rows_to_dicts(rows)


# ============================================================
# TEARSHEET
# ============================================================

@router.get("/companies/{company_id}/tearsheet")
def get_tearsheet(
    company_id: str,
) -> FileResponse:
    """
    Return the pre-generated company tearsheet PDF.
    """

    with _get_connection() as conn:

        if not _company_exists(
            conn,
            company_id,
        ):
            raise HTTPException(
                status_code=404,
                detail=f"Company id '{company_id}' not found",
            )

    file_path = (
        TEARSHEET_DIR
        / f"{company_id}_tearsheet.pdf"
    )

    if not file_path.is_file():

        raise HTTPException(
            status_code=404,
            detail=(
                f"Tearsheet not found for "
                f"company id '{company_id}'"
            ),
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=f"{company_id}_tearsheet.pdf",
    )

