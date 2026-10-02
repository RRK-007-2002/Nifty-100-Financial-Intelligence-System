"""
src/analytics/profiling.py

Cluster profiling, correlation analysis, outlier detection and portfolio
statistics for the Nifty 100 Financial Intelligence Platform.

Sprint 6 - Day 37

Requires:
    output/cluster_labels.csv

Outputs:
    output/cluster_profile.csv
    output/outlier_report.csv
    output/portfolio_stats.csv
    reports/correlation_heatmap.png

Database characteristics handled:
    - 92-company universe comes from sectors
    - company_id is TEXT
    - year is TEXT, e.g. "Mar 2025"
    - duplicate financial-ratio rows
    - missing financial-ratio records
    - missing KPI values
    - companies without financial-ratio records
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import List

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(r"C:\Users\bhrra\Desktop\nifty100")

DB_PATH = BASE_DIR / "db" / "nifty100.db"

OUTPUT_DIR = BASE_DIR / "output"
REPORTS_DIR = BASE_DIR / "reports"

CLUSTER_LABELS_PATH = OUTPUT_DIR / "cluster_labels.csv"

CLUSTER_PROFILE_PATH = OUTPUT_DIR / "cluster_profile.csv"

CORRELATION_HEATMAP_PATH = (
    REPORTS_DIR / "correlation_heatmap.png"
)

OUTLIER_REPORT_PATH = (
    OUTPUT_DIR / "outlier_report.csv"
)

PORTFOLIO_STATS_PATH = (
    OUTPUT_DIR / "portfolio_stats.csv"
)


# ============================================================
# CONFIGURATION
# ============================================================

EXPECTED_COMPANIES = 92

OUTLIER_Z_THRESHOLD = 3.0

PORTFOLIO_PERCENTILES: List[float] = [
    0.10,
    0.25,
    0.50,
    0.75,
    0.90,
]


# ============================================================
# 5 CLUSTERING FEATURES
# ============================================================

FEATURE_COLUMNS: List[str] = [
    "return_on_equity_pct",
    "debt_to_equity",
    "revenue_cagr_5yr",
    "fcf_cagr_5yr",
    "operating_profit_margin_pct",
]


# ============================================================
# 10 CORE KPIs
# ============================================================

CORE_KPI_COLUMNS: List[str] = [
    "net_profit_margin_pct",
    "operating_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
    "eps_cagr_5yr",
    "capex_intensity_pct",
]


# ============================================================
# YEAR PARSER
# ============================================================

def _extract_year(value) -> float:
    """
    Extract a four-digit year from values such as:

        Mar 2016
        Mar 2025
        2024

    Returns NaN if no year can be extracted.
    """

    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    match = re.search(r"(19|20)\d{2}", value)

    if match:
        return float(match.group())

    return np.nan


# ============================================================
# DATABASE CONNECTION
# ============================================================

def _get_connection(db_path: str | Path) -> sqlite3.Connection:
    """Create and validate a SQLite database connection."""

    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found:\n{db_path}"
        )

    return sqlite3.connect(db_path)


# ============================================================
# LOAD OFFICIAL 92-COMPANY UNIVERSE
# ============================================================

def _load_company_universe(
    conn: sqlite3.Connection,
) -> pd.DataFrame:
    """
    Load the official 92-company universe from sectors.

    The sectors table is the source of truth for the project's
    92-company universe.
    """

    query = """
        SELECT DISTINCT
            company_id,
            broad_sector,
            sub_sector
        FROM sectors
        WHERE company_id IS NOT NULL
    """

    df = pd.read_sql_query(query, conn)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    df = (
        df
        .drop_duplicates(subset=["company_id"])
        .reset_index(drop=True)
    )

    if len(df) != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} companies "
            f"in sectors table, found {len(df)}."
        )

    return df


# ============================================================
# LOAD FINANCIAL RATIOS
# ============================================================

def _load_financial_ratios(
    conn: sqlite3.Connection,
    universe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Load financial-ratio data for the official 92-company universe.
    """

    query = """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            revenue_cagr_5yr,
            pat_cagr_5yr,
            eps_cagr_5yr,
            capex_intensity_pct
        FROM financial_ratios
    """

    df = pd.read_sql_query(query, conn)

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    # Keep only the official 92-company universe
    df = df[
        df["company_id"].isin(
            universe["company_id"]
        )
    ].copy()

    # Parse year
    df["year_num"] = (
        df["year"]
        .apply(_extract_year)
    )

    # Convert KPI columns to numeric
    for column in CORE_KPI_COLUMNS:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    return df


# ============================================================
# REMOVE DUPLICATE COMPANY/YEAR ROWS
# ============================================================

def _aggregate_duplicate_years(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    financial_ratios contains duplicate company/year records.

    Aggregate duplicates using the median of each KPI.
    """

    value_columns = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
        "capex_intensity_pct",
    ]

    df = df.dropna(
        subset=["year_num"]
    ).copy()

    df["year_num"] = (
        df["year_num"]
        .astype(int)
    )

    result = (
        df
        .groupby(
            ["company_id", "year_num"],
            as_index=False,
        )[value_columns]
        .median()
    )

    return result


# ============================================================
# LOAD LATEST KPI VALUES
# ============================================================

def _load_latest_year_kpis(
    db_path: str | Path,
) -> pd.DataFrame:
    """
    Load the latest available KPI values for all 92 companies.

    The function starts from the sectors table so that companies
    without financial-ratio records are retained.
    """

    with _get_connection(db_path) as conn:

        # ----------------------------------------------------
        # Official universe
        # ----------------------------------------------------

        universe = _load_company_universe(conn)

        # ----------------------------------------------------
        # Financial ratios
        # ----------------------------------------------------

        ratios = _load_financial_ratios(
            conn,
            universe,
        )

    # --------------------------------------------------------
    # Remove duplicate company/year records
    # --------------------------------------------------------

    ratios = _aggregate_duplicate_years(
        ratios
    )

    # --------------------------------------------------------
    # Latest year per company
    # --------------------------------------------------------

    latest_year = (
        ratios
        .groupby("company_id")["year_num"]
        .max()
        .reset_index()
        .rename(
            columns={
                "year_num": "latest_year"
            }
        )
    )

    latest = ratios.merge(
        latest_year,
        on="company_id",
        how="inner",
    )

    latest = latest[
        latest["year_num"]
        == latest["latest_year"]
    ].copy()

    # If multiple records still remain for the same company,
    # median them.
    latest = (
        latest
        .groupby("company_id", as_index=False)
        .agg(
            {
                **{
                    col: "median"
                    for col in CORE_KPI_COLUMNS
                },
                "latest_year": "max",
            }
        )
    )

    # --------------------------------------------------------
    # LEFT JOIN TO 92-COMPANY UNIVERSE
    # --------------------------------------------------------

    result = universe.merge(
        latest,
        on="company_id",
        how="left",
    )

    print("\nLatest KPI data")
    print("-" * 60)
    print(
        f"Universe companies: "
        f"{result['company_id'].nunique()}"
    )
    print(
        f"Companies with ratio data: "
        f"{latest['company_id'].nunique()}"
    )

    missing_companies = result[
        result["latest_year"].isna()
    ]

    if not missing_companies.empty:

        print("\nCompanies without financial-ratio data:")

        print(
            missing_companies[
                [
                    "company_id",
                    "broad_sector",
                    "sub_sector",
                ]
            ].to_string(index=False)
        )

    return result


# ============================================================
# SECTOR MEDIAN IMPUTATION
# ============================================================

def _impute_kpis_by_sector(
    kpi_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Imputation hierarchy:

        1. Sector median
        2. Global median
        3. Zero as final fallback

    This preserves all 92 companies.
    """

    result = kpi_df.copy()

    print("\nMissing KPI values before imputation:")
    print(
        result[CORE_KPI_COLUMNS]
        .isna()
        .sum()
        .to_string()
    )

    # --------------------------------------------------------
    # Sector median
    # --------------------------------------------------------

    for metric in CORE_KPI_COLUMNS:

        sector_median = (
            result
            .groupby("broad_sector")[metric]
            .transform("median")
        )

        result[metric] = (
            result[metric]
            .fillna(sector_median)
        )

    # --------------------------------------------------------
    # Global median
    # --------------------------------------------------------

    for metric in CORE_KPI_COLUMNS:

        global_median = (
            result[metric]
            .median()
        )

        if pd.notna(global_median):

            result[metric] = (
                result[metric]
                .fillna(global_median)
            )

    # --------------------------------------------------------
    # Final fallback
    # --------------------------------------------------------

    result[CORE_KPI_COLUMNS] = (
        result[CORE_KPI_COLUMNS]
        .fillna(0)
    )

    remaining = (
        result[CORE_KPI_COLUMNS]
        .isna()
        .sum()
        .sum()
    )

    if remaining != 0:
        raise ValueError(
            "KPI imputation failed. "
            "Missing values still remain."
        )

    print("\nMissing KPI values after imputation:")
    print(
        result[CORE_KPI_COLUMNS]
        .isna()
        .sum()
        .to_string()
    )

    return result


# ============================================================
# LOAD CLUSTER LABELS
# ============================================================

def _load_cluster_labels(
    path: str | Path,
) -> pd.DataFrame:
    """
    Load cluster assignments generated by clustering.py.
    """

    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Cluster-label file not found:\n{path}\n\n"
            "Run clustering.py first."
        )

    clusters = pd.read_csv(path)

    if "company_id" not in clusters.columns:
        raise ValueError(
            "cluster_labels.csv does not contain "
            "'company_id'."
        )

    required_columns = [
        "cluster_id",
        "cluster_name",
    ]

    missing = [
        col
        for col in required_columns
        if col not in clusters.columns
    ]

    if missing:
        raise ValueError(
            "cluster_labels.csv is missing columns: "
            + ", ".join(missing)
        )

    clusters["company_id"] = (
        clusters["company_id"]
        .astype(str)
        .str.strip()
    )

    clusters = (
        clusters
        .drop_duplicates(
            subset=["company_id"]
        )
    )

    return clusters


# ============================================================
# LOAD CLUSTER DATA
# ============================================================

def _load_cluster_and_features(
    db_path: str | Path,
) -> pd.DataFrame:
    """
    Load the 92-company universe, latest clustering features,
    and previously generated cluster assignments.

    The five clustering features are taken directly from
    cluster_labels.csv because clustering.py already performed
    the required feature engineering and imputation.
    """

    clusters_df = _load_cluster_labels(
        CLUSTER_LABELS_PATH
    )

    if clusters_df["company_id"].nunique() != EXPECTED_COMPANIES:
        raise ValueError(
            f"Expected {EXPECTED_COMPANIES} cluster assignments, "
            f"found {clusters_df['company_id'].nunique()}."
        )

    with _get_connection(db_path) as conn:

        universe = _load_company_universe(conn)

    # --------------------------------------------------------
    # Keep exactly the 92-company universe
    # --------------------------------------------------------

    merged = universe.merge(
        clusters_df,
        on="company_id",
        how="left",
    )

    missing_clusters = merged[
        merged["cluster_id"].isna()
    ]

    if not missing_clusters.empty:

        raise ValueError(
            "Some companies in the 92-company universe "
            "do not have cluster assignments:\n"
            + missing_clusters[
                "company_id"
            ].to_string(index=False)
        )

    # --------------------------------------------------------
    # Verify clustering feature columns
    # --------------------------------------------------------

    missing_features = [
        col
        for col in FEATURE_COLUMNS
        if col not in merged.columns
    ]

    if missing_features:
        raise ValueError(
            "cluster_labels.csv does not contain the required "
            "clustering features:\n"
            + "\n".join(missing_features)
        )

    return merged


# ============================================================
# CLUSTER PROFILE
# ============================================================

def _profile_clusters(
    merged_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute mean and median of the five clustering features
    for each cluster.
    """

    grouped = (
        merged_df
        .groupby(
            ["cluster_id", "cluster_name"]
        )[FEATURE_COLUMNS]
    )

    means = (
        grouped
        .mean()
        .add_prefix("mean_")
    )

    medians = (
        grouped
        .median()
        .add_prefix("median_")
    )

    result = (
        means
        .join(medians)
        .reset_index()
    )

    return result


# ============================================================
# CORRELATION HEATMAP
# ============================================================

def _generate_correlation_heatmap(
    kpi_df: pd.DataFrame,
    output_path: str | Path,
) -> None:
    """
    Generate Pearson correlation heatmap for the 10 core KPIs.
    """

    corr_matrix = (
        kpi_df[
            CORE_KPI_COLUMNS
        ]
        .corr(method="pearson")
    )

    fig, ax = plt.subplots(
        figsize=(12, 9)
    )

    sns.heatmap(
        corr_matrix,
        annot=True,
        fmt=".2f",
        cmap="coolwarm",
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=0.5,
        ax=ax,
    )

    ax.set_title(
        "Pearson Correlation Matrix — "
        "Core KPIs (Latest Fiscal Year)"
    )

    fig.tight_layout()

    fig.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight",
    )

    plt.close(fig)


# ============================================================
# OUTLIER DETECTION
# ============================================================

def _detect_outliers(
    kpi_df: pd.DataFrame,
    output_path: str | Path,
) -> pd.DataFrame:
    """
    Detect outliers independently within each broad sector.

    A company is flagged when:

        |Z-score| > 3

    for at least one KPI.
    """

    df = kpi_df.copy()

    flagged_rows = []

    for sector, group in df.groupby(
        "broad_sector",
        dropna=False,
    ):

        for metric in CORE_KPI_COLUMNS:

            values = pd.to_numeric(
                group[metric],
                errors="coerce",
            )

            valid = values.notna()

            if valid.sum() < 2:
                continue

            mean = values[valid].mean()

            std = values[valid].std(
                ddof=0
            )

            if pd.isna(std) or std == 0:
                continue

            z_scores = (
                values - mean
            ) / std

            mask = (
                z_scores.abs()
                > OUTLIER_Z_THRESHOLD
            )

            for index in group.index[mask]:

                flagged_rows.append(
                    {
                        "company_id":
                            group.loc[
                                index,
                                "company_id",
                            ],
                        "broad_sector":
                            sector,
                        "metric":
                            metric,
                        "value":
                            float(
                                group.loc[
                                    index,
                                    metric,
                                ]
                            ),
                        "z_score":
                            round(
                                float(
                                    z_scores.loc[
                                        index
                                    ]
                                ),
                                4,
                            ),
                    }
                )

    outlier_df = pd.DataFrame(
        flagged_rows,
        columns=[
            "company_id",
            "broad_sector",
            "metric",
            "value",
            "z_score",
        ],
    )

    outlier_df.to_csv(
        output_path,
        index=False,
    )

    return outlier_df


# ============================================================
# PORTFOLIO STATISTICS
# ============================================================

def _compute_portfolio_stats(
    kpi_df: pd.DataFrame,
    output_path: str | Path,
) -> pd.DataFrame:
    """
    Compute:

        P10
        P25
        P50
        P75
        P90
        Mean
        Std

    for every core KPI.
    """

    stats_rows = []

    for metric in CORE_KPI_COLUMNS:

        values = pd.to_numeric(
            kpi_df[metric],
            errors="coerce",
        ).dropna()

        row = {
            "metric": metric
        }

        if values.empty:

            for pct in PORTFOLIO_PERCENTILES:
                row[
                    f"P{int(pct * 100)}"
                ] = np.nan

            row["Mean"] = np.nan
            row["Std"] = np.nan

        else:

            for pct in PORTFOLIO_PERCENTILES:

                row[
                    f"P{int(pct * 100)}"
                ] = float(
                    np.percentile(
                        values,
                        pct * 100,
                    )
                )

            row["Mean"] = float(
                values.mean()
            )

            row["Std"] = float(
                values.std(ddof=0)
            )

        stats_rows.append(row)

    stats_df = pd.DataFrame(
        stats_rows
    )

    stats_df.to_csv(
        output_path,
        index=False,
    )

    return stats_df


# ============================================================
# MAIN WORKFLOW
# ============================================================

def generate_profiles_and_reports(
    db_path: str | Path = DB_PATH,
) -> None:
    """
    Run the complete Sprint 6 Day 37 profiling workflow.

    Outputs:

        1. output/cluster_profile.csv
        2. reports/correlation_heatmap.png
        3. output/outlier_report.csv
        4. output/portfolio_stats.csv
    """

    print("=" * 70)
    print("NIFTY100 — DAY 37 PROFILING")
    print("=" * 70)

    # --------------------------------------------------------
    # Validate paths
    # --------------------------------------------------------

    db_path = Path(db_path)

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database not found:\n{db_path}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. CLUSTER PROFILE
    # ========================================================

    print("\n[1/4] Loading cluster assignments...")

    merged_df = _load_cluster_and_features(
        db_path
    )

    print(
        f"      Companies: "
        f"{merged_df['company_id'].nunique()}"
    )

    print(
        f"      Clusters: "
        f"{merged_df['cluster_id'].nunique()}"
    )

    cluster_profile = _profile_clusters(
        merged_df
    )

    cluster_profile.to_csv(
        CLUSTER_PROFILE_PATH,
        index=False,
    )

    print(
        f"      Saved: "
        f"{CLUSTER_PROFILE_PATH}"
    )

    # ========================================================
    # 2. LATEST 10 KPIs
    # ========================================================

    print("\n[2/4] Loading latest-year KPIs...")

    kpi_df = _load_latest_year_kpis(
        db_path
    )

    # Preserve all 92 companies
    kpi_df = _impute_kpis_by_sector(
        kpi_df
    )

    if (
        kpi_df["company_id"].nunique()
        != EXPECTED_COMPANIES
    ):
        raise ValueError(
            "KPI dataset does not contain all 92 companies."
        )

    # ========================================================
    # 3. CORRELATION + OUTLIERS
    # ========================================================

    print("\n[3/4] Generating correlation heatmap...")

    _generate_correlation_heatmap(
        kpi_df,
        CORRELATION_HEATMAP_PATH,
    )

    print(
        f"      Saved: "
        f"{CORRELATION_HEATMAP_PATH}"
    )

    print("\n      Detecting sector-level outliers...")

    outlier_df = _detect_outliers(
        kpi_df,
        OUTLIER_REPORT_PATH,
    )

    print(
        f"      Outlier records: "
        f"{len(outlier_df)}"
    )

    print(
        f"      Saved: "
        f"{OUTLIER_REPORT_PATH}"
    )

    # ========================================================
    # 4. PORTFOLIO STATISTICS
    # ========================================================

    print("\n[4/4] Computing portfolio statistics...")

    stats_df = _compute_portfolio_stats(
        kpi_df,
        PORTFOLIO_STATS_PATH,
    )

    print(
        f"      Metrics: "
        f"{len(stats_df)}"
    )

    print(
        f"      Saved: "
        f"{PORTFOLIO_STATS_PATH}"
    )

    # ========================================================
    # FINAL VALIDATION
    # ========================================================

    print("\n" + "=" * 70)
    print("DAY 37 VALIDATION")
    print("=" * 70)

    print(
        f"\n92-company universe: "
        f"{kpi_df['company_id'].nunique()} companies"
    )

    print(
        f"Cluster assignments: "
        f"{merged_df['company_id'].nunique()} companies"
    )

    print(
        f"Core KPIs: "
        f"{len(CORE_KPI_COLUMNS)}"
    )

    print(
        f"Outlier records: "
        f"{len(outlier_df)}"
    )

    print("\nGenerated files:")

    print(
        f"  ✓ {CLUSTER_PROFILE_PATH}"
    )

    print(
        f"  ✓ {CORRELATION_HEATMAP_PATH}"
    )

    print(
        f"  ✓ {OUTLIER_REPORT_PATH}"
    )

    print(
        f"  ✓ {PORTFOLIO_STATS_PATH}"
    )

    print("\n" + "=" * 70)
    print("DAY 37 PROFILING COMPLETED SUCCESSFULLY")
    print("=" * 70)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    generate_profiles_and_reports()