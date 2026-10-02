from pathlib import Path
import re
import pandas as pd
import sqlite3


# ======================================================
# PROJECT PATHS
# ================================

BASE_DIR = Path(r"C:\Users\bhrra\Desktop\nifty100")

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db"

ANALYSIS_CSV = "C:\\Users\\bhrra\\Desktop\\nifty100\\output\\cleaned\\analysis.csv"




PATTERN = re.compile(
    r"(\d+)\s*\*?\s*Years?\s*:?\s*\*?\s*([-+]?\d+(?:\.\d+)?)\s*%"
)


TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# ==========================================================
# 1. PARSE ANALYSIS CSV
# ==========================================

# def parse_analysis_text(analysis_csv_path):

#     df = pd.read_csv(analysis_csv_path)

#     parsed_rows = []
#     failed_rows = []

#     for _, row in df.iterrows():

#         company_id = row.get("company_id")

#         for field in TARGET_FIELDS:

#             raw_text = row.get(field)

#             if pd.isna(raw_text):
#                 continue

#             raw_text = str(raw_text)

#             matches = PATTERN.findall(raw_text)

#             if not matches:

#                 failed_rows.append({
#                     "company_id": company_id,
#                     "metric_type": field,
#                     "raw_text": raw_text,
#                 })

#                 continue

#             for period_str, value_str in matches:

#                 parsed_rows.append({
#                     "company_id": str(company_id),
#                     "metric_type": field,
#                     "period_years": int(period_str),
#                     "value_pct": float(value_str),
#                 })

#     parsed_df = pd.DataFrame(parsed_rows)

#     failed_df = pd.DataFrame(failed_rows)

#     # Save parsed data
#     parsed_df.to_csv(
#         OUTPUT_DIR / "analysis_parsed.csv",
#         index=False
#     )

#     # Save parsing failures
#     failed_df.to_csv(
#         OUTPUT_DIR / "parse_failures.csv",
#         index=False
#     )

#     return parsed_df, failed_df


def parse_analysis_text(analysis_csv_path):

    analysis_csv_path = Path(analysis_csv_path)

    print("\n[1/3] Checking analysis CSV...")

    if not analysis_csv_path.is_file():
        raise FileNotFoundError(
            f"Analysis CSV not found: {analysis_csv_path}"
        )

    df = pd.read_csv(analysis_csv_path)

    # Normalize column names to avoid whitespace/case mismatches.
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", "_", regex=True)
    )

    print(f"CSV loaded successfully: {len(df)} rows")
    print("Available columns:", df.columns.tolist())

    if "company_id" not in df.columns:
        raise ValueError(
            "Missing required column 'company_id'. "
            f"Available columns: {df.columns.tolist()}"
        )

    available_fields = [
        field for field in TARGET_FIELDS
        if field in df.columns
    ]

    missing_fields = [
        field for field in TARGET_FIELDS
        if field not in df.columns
    ]

    if missing_fields:
        print(f"WARNING: Missing target columns: {missing_fields}")

    if not available_fields:
        raise ValueError(
            "None of the TARGET_FIELDS were found in the CSV. "
            "Update TARGET_FIELDS to match the actual column names."
        )

    parsed_rows = []
    failed_rows = []

    print("\n[2/3] Parsing analysis text...")

    for _, row in df.iterrows():

        company_id = row["company_id"]

        for field in available_fields:

            raw_text = row[field]

            if pd.isna(raw_text) or not str(raw_text).strip():
                continue

            raw_text = str(raw_text).strip()

            matches = PATTERN.findall(raw_text)

            if not matches:
                failed_rows.append({
                    "company_id": company_id,
                    "metric_type": field,
                    "raw_text": raw_text,
                })
                continue

            for period_str, value_str in matches:
                parsed_rows.append({
                    "company_id": str(company_id).strip(),
                    "metric_type": field,
                    "period_years": int(period_str),
                    "value_pct": float(value_str),
                })

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failed_df = pd.DataFrame(
        failed_rows,
        columns=["company_id", "metric_type", "raw_text"],
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    parsed_path = OUTPUT_DIR / "analysis_parsed.csv"
    failed_path = OUTPUT_DIR / "parse_failures.csv"

    parsed_df.to_csv(parsed_path, index=False)
    failed_df.to_csv(failed_path, index=False)

    print(f"Parsed records: {len(parsed_df)}")
    print(f"Failed records: {len(failed_df)}")
    print(f"Parsed output: {parsed_path}")
    print(f"Failure output: {failed_path}")

    if not parsed_df.empty:
        print("\nSample parsed records:")
        print(parsed_df.head(5).to_string(index=False))

    if not failed_df.empty:
        print("\nSample failed records:")
        print(failed_df.head(5).to_string(index=False))

    return parsed_df, failed_df
# ============================================================
# 2. CAGR FUNCTION
# ============================================================

def calculate_cagr(start_value, end_value, years):

    if pd.isna(start_value) or pd.isna(end_value):
        return None

    if years <= 0:
        return None

    # CAGR is not mathematically valid with zero/negative
    # beginning values.
    if start_value <= 0 or end_value <= 0:
        return None

    cagr = (
        (end_value / start_value) ** (1 / years) - 1
    ) * 100

    return cagr


# ============================================================
# 3. CALCULATE CAGR FROM PROFIT AND LOSS
# ============================================================

def calculate_pnl_cagr(
    conn,
    company_id,
    period_years,
    value_column
):

    query = f"""
        SELECT
            year,
            {value_column}
        FROM profitandloss
        WHERE company_id = ?
    """

    df = pd.read_sql(
        query,
        conn,
        params=(company_id,)
    )

    if df.empty:
        return None

    # Convert year to numeric.
    # Handles values such as:
    # 2022
    # 2022-23
    # etc. depending on your DB format.
    df["year_num"] = pd.to_numeric(
        df["year"].astype(str).str[:4],
        errors="coerce"
    )

    df[value_column] = pd.to_numeric(
        df[value_column],
        errors="coerce"
    )

    df = df.dropna(
        subset=["year_num", value_column]
    )

    df = df.sort_values("year_num")

    if len(df) < 2:
        return None

    latest_year = df["year_num"].max()

    target_start_year = latest_year - period_years

    # Find exact starting year
    start_df = df[
        df["year_num"] == target_start_year
    ]

    # Find latest year
    end_df = df[
        df["year_num"] == latest_year
    ]

    if start_df.empty or end_df.empty:
        return None

    start_value = start_df.iloc[0][value_column]
    end_value = end_df.iloc[0][value_column]

    return calculate_cagr(
        start_value,
        end_value,
        period_years
    )


# ============================================================
# 4. CALCULATE STOCK PRICE CAGR
# ============================================================

def calculate_stock_cagr(
    conn,
    company_id,
    period_years
):

    query = """
        SELECT
            date,
            close_price
        FROM stock_prices
        WHERE company_id = ?
        ORDER BY date
    """

    df = pd.read_sql(
        query,
        conn,
        params=(company_id,)
    )

    if df.empty:
        return None

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    df["close_price"] = pd.to_numeric(
        df["close_price"],
        errors="coerce"
    )

    df = df.dropna(
        subset=["date", "close_price"]
    )

    if df.empty:
        return None

    latest_date = df["date"].max()

    target_date = latest_date - pd.DateOffset(
        years=period_years
    )

    # Find the closest available trading day
    before_target = df[
        df["date"] <= target_date
    ]

    if before_target.empty:
        return None

    start_row = before_target.iloc[-1]

    end_row = df.iloc[-1]

    start_price = start_row["close_price"]
    end_price = end_row["close_price"]

    actual_years = (
        (end_row["date"] - start_row["date"]).days
        / 365.25
    )

    if actual_years <= 0:
        return None

    return calculate_cagr(
        start_price,
        end_price,
        actual_years
    )


# ============================================================
# 5. GET ROE FROM FINANCIAL RATIOS
# ============================================================

def get_roe(
    conn,
    company_id,
    period_years
):

    query = """
        SELECT
            year,
            return_on_equity_pct
        FROM financial_ratios
        WHERE company_id = ?
        ORDER BY year
    """

    df = pd.read_sql(
        query,
        conn,
        params=(company_id,)
    )

    if df.empty:
        return None

    df["year_num"] = pd.to_numeric(
        df["year"].astype(str).str[:4],
        errors="coerce"
    )

    df["return_on_equity_pct"] = pd.to_numeric(
        df["return_on_equity_pct"],
        errors="coerce"
    )

    df = df.dropna(
        subset=[
            "year_num",
            "return_on_equity_pct"
        ]
    )

    if df.empty:
        return None

    # For ROE, the analysis text may say something like
    # "5 Years: 18.5%".
    #
    # Here we use the most recent available ROE.
    latest_row = df.sort_values(
        "year_num"
    ).iloc[-1]

    return float(
        latest_row["return_on_equity_pct"]
    )


# ============================================================
# 6. CROSS VALIDATION
# ============================================================

def cross_validate(
    parsed_df,
    db_path,
    tolerance=5.0
):

    conn = sqlite3.connect(db_path)

    validation_rows = []

    for _, row in parsed_df.iterrows():

        company_id = row["company_id"]

        metric_type = row["metric_type"]

        period_years = int(
            row["period_years"]
        )

        parsed_value = float(
            row["value_pct"]
        )

        computed_value = None

        # ----------------------------------------
        # SALES CAGR
        # ----------------------------------------

        if metric_type == "compounded_sales_growth":

            computed_value = calculate_pnl_cagr(
                conn,
                company_id,
                period_years,
                "sales"
            )

        # ----------------------------------------
        # PROFIT CAGR
        # ----------------------------------------

        elif metric_type == "compounded_profit_growth":

            computed_value = calculate_pnl_cagr(
                conn,
                company_id,
                period_years,
                "net_profit"
            )

        # ----------------------------------------
        # STOCK PRICE CAGR
        # ----------------------------------------

        elif metric_type == "stock_price_cagr":

            computed_value = calculate_stock_cagr(
                conn,
                company_id,
                period_years
            )

        # ----------------------------------------
        # ROE
        # ----------------------------------------

        elif metric_type == "roe":

            computed_value = get_roe(
                conn,
                company_id,
                period_years
            )

        # ----------------------------------------
        # DIVERGENCE
        # ----------------------------------------

        if computed_value is not None:

            divergence = abs(
                parsed_value - computed_value
            )

        else:

            divergence = None

        validation_rows.append({

            "company_id": company_id,

            "metric_type": metric_type,

            "period_years": period_years,

            "parsed_value_pct": parsed_value,

            "computed_value_pct": computed_value,

            "divergence": divergence,

            "within_tolerance": (
                divergence is not None
                and divergence <= tolerance
            ),

        })

    conn.close()

    validation_df = pd.DataFrame(
        validation_rows
    )

    # Only actual divergence > tolerance
    flagged = validation_df[
        validation_df["divergence"].notna()
        & (validation_df["divergence"] > tolerance)
    ]

    # Save complete validation results
    validation_df.to_csv(
        OUTPUT_DIR / "parse_validation.csv",
        index=False
    )

    # Save only problematic rows
    flagged.to_csv(
        OUTPUT_DIR / "parse_divergence_flags.csv",
        index=False
    )

    return validation_df, flagged


# ============================================================
# MAIN
# ============================================================


if __name__ == "__main__":

    print("=" * 60)
    print("NIFTY 100 NLP ANALYSIS PARSER")
    print("=" * 60)

    print(f"\nAnalysis CSV: {ANALYSIS_CSV}")
    print(f"Database:     {DB_PATH}")
    print(f"Output folder: {OUTPUT_DIR}")

    try:
        parsed, failed = parse_analysis_text(ANALYSIS_CSV)

        if parsed.empty:
            print("\nSTOP: No records were parsed.")
            print(
                "Check the CSV columns and the raw text in "
                "output/parse_failures.csv."
            )

        else:
            print("\n[3/3] Starting cross-validation...")

            validation, flags = cross_validate(
                parsed,
                DB_PATH,
                tolerance=5.0,
            )

            print(f"\nValidation rows: {len(validation)}")
            print(f"Divergence above tolerance: {len(flags)}")

            print("\nValidation output files:")
            print(OUTPUT_DIR / "parse_validation.csv")
            print(OUTPUT_DIR / "parse_divergence_flags.csv")

        print("\nParser finished.")

    except Exception as exc:
        print(f"\nERROR: {type(exc).__name__}: {exc}")
        raise