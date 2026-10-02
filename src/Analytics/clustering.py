"""
Nifty100 Financial Intelligence Platform
Sprint 6 - Day 36
Company Clustering using KMeans

Clustering universe:
    92 companies defined in the sectors table.

Features:
    1. return_on_equity_pct
    2. debt_to_equity
    3. revenue_cagr_5yr
    4. fcf_cagr_5yr
    5. operating_profit_margin_pct

Important database characteristics handled:
    - company_id is TEXT
    - year is TEXT, e.g. "Mar 2025"
    - duplicate financial-ratio rows
    - missing ratio records
    - missing revenue CAGR
    - missing historical years
    - non-positive FCF
"""

from pathlib import Path
import sqlite3
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


warnings.filterwarnings("ignore")


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"C:\Users\bhrra\Desktop\nifty100")

DB_PATH = BASE_DIR / "db" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"

OUTPUT_CSV = OUTPUT_DIR / "cluster_labels.csv"
ELBOW_PNG = REPORTS_DIR / "elbow_plot.png"


# ============================================================
# CONFIGURATION
# ============================================================

N_CLUSTERS = 5
RANDOM_STATE = 42

FEATURES = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    """Create SQLite connection."""
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"Database not found:\n{DB_PATH}"
        )

    return sqlite3.connect(DB_PATH)


# ============================================================
# YEAR PARSER
# ============================================================

def extract_year(value):
    """
    Convert values such as:

        'Mar 2016'
        'Mar 2025'
        '2019'

    into integer year.
    """

    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    # Extract four-digit year
    import re

    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return int(match.group())

    return np.nan


# ============================================================
# LOAD 92-COMPANY UNIVERSE
# ============================================================

def load_company_universe(conn):
    """
    Load the official 92-company clustering universe
    from the sectors table.
    """

    print("\n[1/8] Loading 92-company universe...")

    query = """
        SELECT DISTINCT
            company_id,
            broad_sector,
            sub_sector
        FROM sectors
        WHERE company_id IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)

    df["company_id"] = df["company_id"].astype(str).str.strip()

    # Remove accidental duplicates
    df = (
        df
        .drop_duplicates(subset=["company_id"])
        .sort_values("company_id")
        .reset_index(drop=True)
    )

    print(f"      Companies loaded: {len(df)}")
    print(f"      Unique companies: {df['company_id'].nunique()}")

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies from sectors table, "
            f"found {len(df)}."
        )

    return df


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

def load_financial_ratios(conn, universe):
    """
    Load financial-ratio data only for the 92-company universe.
    """

    print("\n[2/8] Loading financial-ratio data...")

    query = """
        SELECT
            company_id,
            year,
            return_on_equity_pct,
            debt_to_equity,
            revenue_cagr_5yr,
            operating_profit_margin_pct,
            free_cash_flow_cr
        FROM financial_ratios
    """

    df = pd.read_sql_query(query, conn)

    df["company_id"] = df["company_id"].astype(str).str.strip()

    # Keep only official 92-company universe
    df = df[
        df["company_id"].isin(universe["company_id"])
    ].copy()

    # Convert year
    df["year_num"] = df["year"].apply(extract_year)

    # Numeric columns
    numeric_columns = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "operating_profit_margin_pct",
        "free_cash_flow_cr",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    print(f"      Ratio rows: {len(df)}")
    print(
        f"      Companies with ratio data: "
        f"{df['company_id'].nunique()}"
    )

    return df


# ============================================================
# REMOVE DUPLICATE COMPANY/YEAR RECORDS
# ============================================================

def aggregate_duplicate_years(df):
    """
    financial_ratios contains multiple rows for some
    company/year combinations.

    Aggregate duplicates using median.
    """

    print("\n[3/8] Handling duplicate company/year records...")

    before = len(df)

    group_columns = [
        "company_id",
        "year_num",
    ]

    value_columns = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "operating_profit_margin_pct",
        "free_cash_flow_cr",
    ]

    df = (
        df
        .groupby(group_columns, as_index=False)[value_columns]
        .median()
    )

    after = len(df)

    print(f"      Rows before: {before}")
    print(f"      Rows after : {after}")
    print(f"      Duplicate rows removed: {before - after}")

    return df


# ============================================================
# LOAD LATEST FEATURES
# ============================================================

def load_latest_features(ratios):
    """
    Select the latest available financial-ratio year
    for every company.
    """

    print("\n[4/8] Selecting latest financial data...")

    # Remove rows where year couldn't be parsed
    ratios = ratios.dropna(subset=["year_num"]).copy()

    ratios["year_num"] = ratios["year_num"].astype(int)

    # Latest year for each company
    latest_year = (
        ratios
        .groupby("company_id")["year_num"]
        .max()
        .reset_index()
        .rename(columns={"year_num": "latest_year"})
    )

    latest = ratios.merge(
        latest_year,
        on="company_id",
        how="inner",
    )

    latest = latest[
        latest["year_num"] == latest["latest_year"]
    ].copy()

    # Safety: one row per company
    latest = (
        latest
        .groupby("company_id", as_index=False)
        .agg({
            "return_on_equity_pct": "median",
            "debt_to_equity": "median",
            "revenue_cagr_5yr": "median",
            "operating_profit_margin_pct": "median",
            "latest_year": "max",
        })
    )

    print(
        f"      Companies with latest ratio data: "
        f"{latest['company_id'].nunique()}"
    )

    return latest


# ============================================================
# FCF CAGR
# ============================================================

def calculate_fcf_cagr(ratios):
    """
    Calculate approximately 5-year FCF CAGR.

    CAGR is calculated only when both the starting and ending
    FCF are positive.

    For companies where CAGR cannot be mathematically calculated,
    NaN is retained and handled later by imputation.
    """

    print("\n[5/8] Calculating 5-year FCF CAGR...")

    records = []

    for company_id, group in ratios.groupby("company_id"):

        group = (
            group
            .dropna(subset=["year_num"])
            .sort_values("year_num")
        )

        if group.empty:
            records.append({
                "company_id": company_id,
                "fcf_cagr_5yr": np.nan,
            })
            continue

        # Latest available year
        latest_year = group["year_num"].max()

        # Target year = latest - 5
        target_year = latest_year - 5

        # Exact target-year record if available
        start_candidates = group[
            group["year_num"] == target_year
        ]

        end_candidates = group[
            group["year_num"] == latest_year
        ]

        if start_candidates.empty or end_candidates.empty:

            records.append({
                "company_id": company_id,
                "fcf_cagr_5yr": np.nan,
            })

            continue

        start_fcf = start_candidates["free_cash_flow_cr"].median()
        end_fcf = end_candidates["free_cash_flow_cr"].median()

        # CAGR requires positive start and end values
        if (
            pd.isna(start_fcf)
            or pd.isna(end_fcf)
            or start_fcf <= 0
            or end_fcf <= 0
        ):

            cagr = np.nan

        else:

            cagr = (
                (end_fcf / start_fcf) ** (1 / 5)
            ) - 1

        records.append({
            "company_id": company_id,
            "fcf_cagr_5yr": cagr,
        })

    result = pd.DataFrame(records)

    print(
        f"      Companies processed: "
        f"{len(result)}"
    )

    print(
        f"      Valid FCF CAGR: "
        f"{result['fcf_cagr_5yr'].notna().sum()}"
    )

    print(
        f"      Missing FCF CAGR: "
        f"{result['fcf_cagr_5yr'].isna().sum()}"
    )

    return result


# ============================================================
# BUILD CLUSTERING DATASET
# ============================================================

def build_clustering_dataset(
    universe,
    latest,
    fcf_cagr,
):
    """
    Start from all 92 companies and left join financial data.

    This guarantees that companies such as ATGL, PNB and SBIN
    remain in the dataset.
    """

    print("\n[6/8] Building clustering dataset...")

    df = universe.copy()

    # Add latest financial metrics
    df = df.merge(
        latest[
            [
                "company_id",
                "return_on_equity_pct",
                "debt_to_equity",
                "revenue_cagr_5yr",
                "operating_profit_margin_pct",
            ]
        ],
        on="company_id",
        how="left",
    )

    # Add FCF CAGR
    df = df.merge(
        fcf_cagr,
        on="company_id",
        how="left",
    )

    print(f"      Dataset shape: {df.shape}")
    print(
        f"      Companies: "
        f"{df['company_id'].nunique()}"
    )

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies after merge, "
            f"found {len(df)}."
        )

    print("\n      Missing values before imputation:")

    print(
        df[FEATURES]
        .isna()
        .sum()
        .to_string()
    )

    return df


# ============================================================
# SECTOR MEDIAN IMPUTATION
# ============================================================

def impute_by_sector_median(df):
    """
    Imputation hierarchy:

        1. Sector median
        2. Global median
        3. 0 as final fallback

    This preserves all 92 companies.
    """

    print("\n[7/8] Applying sector-median imputation...")

    result = df.copy()

    before_missing = result[FEATURES].isna().sum()

    # --------------------------------------------------------
    # Sector median
    # --------------------------------------------------------

    for feature in FEATURES:

        sector_median = (
            result
            .groupby("broad_sector")[feature]
            .transform("median")
        )

        result[feature] = (
            result[feature]
            .fillna(sector_median)
        )

    # --------------------------------------------------------
    # Global median
    # --------------------------------------------------------

    for feature in FEATURES:

        global_median = result[feature].median()

        result[feature] = (
            result[feature]
            .fillna(global_median)
        )

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    result[FEATURES] = (
        result[FEATURES]
        .fillna(0)
    )

    after_missing = result[FEATURES].isna().sum()

    print("\n      Missing before:")
    print(before_missing.to_string())

    print("\n      Missing after:")
    print(after_missing.to_string())

    if after_missing.sum() != 0:
        raise ValueError(
            "Missing values remain after imputation."
        )

    return result


# ============================================================
# ELBOW METHOD
# ============================================================

def generate_elbow_plot(X):
    """
    Generate elbow plot for k=2...10.
    """

    print("\n[8/8] Generating elbow plot...")

    inertias = []
    k_values = range(2, 11)

    for k in k_values:

        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=20,
        )

        model.fit(X)

        inertias.append(model.inertia_)

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plt.figure(figsize=(9, 6))

    plt.plot(
        list(k_values),
        inertias,
        marker="o",
    )

    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia")
    plt.title("KMeans Elbow Plot")

    plt.xticks(list(k_values))
    plt.grid(True, alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        ELBOW_PNG,
        dpi=200,
    )

    plt.close()

    print(f"      Saved: {ELBOW_PNG}")


# ============================================================
# CLUSTER NAME GENERATION
# ============================================================

def assign_cluster_names(df):
    """
    Create descriptive names from cluster feature profiles.

    The names are descriptive labels rather than rankings.
    """

    profiles = (
        df
        .groupby("cluster_id")[FEATURES]
        .mean()
    )

    names = {}

    for cluster_id, row in profiles.iterrows():

        growth = (
            row["revenue_cagr_5yr"]
            + row["fcf_cagr_5yr"]
        ) / 2

        profitability = (
            row["return_on_equity_pct"]
            + row["operating_profit_margin_pct"]
        ) / 2

        leverage = row["debt_to_equity"]

        if growth > profiles[
            ["revenue_cagr_5yr", "fcf_cagr_5yr"]
        ].mean().mean() and profitability > profiles[
            ["return_on_equity_pct",
             "operating_profit_margin_pct"]
        ].mean().mean():

            name = "Growth & Profitability"

        elif profitability > profiles[
            ["return_on_equity_pct",
             "operating_profit_margin_pct"]
        ].mean().mean():

            name = "Profitability Focused"

        elif growth > profiles[
            ["revenue_cagr_5yr",
             "fcf_cagr_5yr"]
        ].mean().mean():

            name = "Growth Focused"

        elif leverage > profiles[
            "debt_to_equity"
        ].mean():

            name = "Higher Leverage"

        else:

            name = "Balanced Profile"

        names[cluster_id] = name

    # Make names unique
    used = {}

    final_names = {}

    for cluster_id in sorted(names):

        base = names[cluster_id]

        used[base] = used.get(base, 0) + 1

        if used[base] == 1:
            final_names[cluster_id] = base
        else:
            final_names[cluster_id] = (
                f"{base} {used[base]}"
            )

    return final_names


# ============================================================
# MAIN KMEANS PIPELINE
# ============================================================

def run_kmeans_pipeline():

    print("=" * 70)
    print("NIFTY100 COMPANY CLUSTERING")
    print("=" * 70)

    # --------------------------------------------------------
    # Create directories
    # --------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # Database
    # --------------------------------------------------------

    conn = get_connection()

    try:

        # ----------------------------------------------------
        # 1. Universe
        # ----------------------------------------------------

        universe = load_company_universe(conn)

        # ----------------------------------------------------
        # 2. Financial ratios
        # ----------------------------------------------------

        ratios = load_financial_ratios(
            conn,
            universe,
        )

        # ----------------------------------------------------
        # 3. Remove duplicates
        # ----------------------------------------------------

        ratios = aggregate_duplicate_years(ratios)

        # ----------------------------------------------------
        # 4. Latest features
        # ----------------------------------------------------

        latest = load_latest_features(ratios)

        # ----------------------------------------------------
        # 5. FCF CAGR
        # ----------------------------------------------------

        fcf_cagr = calculate_fcf_cagr(ratios)

        # ----------------------------------------------------
        # 6. Dataset
        # ----------------------------------------------------

        df = build_clustering_dataset(
            universe,
            latest,
            fcf_cagr,
        )

        # ----------------------------------------------------
        # 7. Imputation
        # ----------------------------------------------------

        df = impute_by_sector_median(df)

    finally:

        conn.close()

    # ========================================================
    # STANDARDIZATION
    # ========================================================

    print("\n" + "=" * 70)
    print("STANDARDIZATION")
    print("=" * 70)

    X = df[FEATURES].copy()

    scaler = StandardScaler()

    X_scaled = scaler.fit_transform(X)

    print(
        f"      Feature matrix: "
        f"{X_scaled.shape}"
    )

    # ========================================================
    # ELBOW
    # ========================================================

    generate_elbow_plot(X_scaled)

    # ========================================================
    # KMEANS
    # ========================================================

    print("\n" + "=" * 70)
    print("KMEANS CLUSTERING")
    print("=" * 70)

    kmeans = KMeans(
        n_clusters=N_CLUSTERS,
        random_state=RANDOM_STATE,
        n_init=20,
    )

    cluster_ids = kmeans.fit_predict(X_scaled)

    df["cluster_id"] = cluster_ids

    # Distance from centroid
    distances = kmeans.transform(X_scaled)

    df["distance_from_centroid"] = (
        distances[
            np.arange(len(df)),
            cluster_ids,
        ]
    )

    # ========================================================
    # CLUSTER NAMES
    # ========================================================

    cluster_names = assign_cluster_names(df)

    df["cluster_name"] = (
        df["cluster_id"]
        .map(cluster_names)
    )

    # ========================================================
    # VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("CLUSTER VALIDATION")
    print("=" * 70)

    print(
        f"\nTotal companies: "
        f"{len(df)}"
    )

    print(
        f"Unique companies: "
        f"{df['company_id'].nunique()}"
    )

    print(
        f"Clusters: "
        f"{df['cluster_id'].nunique()}"
    )

    print("\nCompanies per cluster:")

    print(
        df["cluster_id"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    print("\nCluster names:")

    for cluster_id, name in sorted(
        cluster_names.items()
    ):
        print(
            f"      Cluster {cluster_id}: "
            f"{name}"
        )

    # --------------------------------------------------------
    # Validate exactly 92 companies
    # --------------------------------------------------------

    if len(df) != 92:
        raise ValueError(
            "Final clustering dataset does not contain 92 companies."
        )

    if df["company_id"].nunique() != 92:
        raise ValueError(
            "Duplicate company IDs found in final output."
        )

    if df["cluster_id"].isna().any():
        raise ValueError(
            "Some companies do not have a cluster ID."
        )

    # ========================================================
    # SAVE OUTPUT
    # ========================================================

    output_columns = [
        "company_id",
        "broad_sector",
        "sub_sector",
        "cluster_id",
        "cluster_name",
        "distance_from_centroid",
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    output = df[output_columns].copy()

    output = output.sort_values(
        ["cluster_id", "company_id"]
    )

    output.to_csv(
        OUTPUT_CSV,
        index=False,
    )

    print("\n" + "=" * 70)
    print("OUTPUT")
    print("=" * 70)

    print(f"\nSaved cluster labels:")
    print(OUTPUT_CSV)

    print(
        f"\nRows written: "
        f"{len(output)}"
    )

    print("\nSample output:")

    print(
        output.head(10).to_string(
            index=False
        )
    )

    print("\n" + "=" * 70)
    print("KMEANS PIPELINE COMPLETED SUCCESSFULLY")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_kmeans_pipeline()