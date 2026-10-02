import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

# File location:
# nifty100/src/analytics/capital_allocation_report.py

BASE_DIR = Path(__file__).resolve().parents[2]

OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data" / "processed"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# VERIFY COMPLETENESS
# ============================================================

def verify_completeness(
    capital_alloc_df,
    companies_df,
    expected_years
):
    """
    Check whether every company has a capital allocation
    pattern for every expected year.
    """

    # --------------------------------------------------------
    # Normalize company ID column
    # --------------------------------------------------------

    companies_df = companies_df.copy()

    if "company_id" not in companies_df.columns:

        if "id" in companies_df.columns:
            companies_df = companies_df.rename(
                columns={"id": "company_id"}
            )

        else:
            raise KeyError(
                "companies_df must contain either "
                "'company_id' or 'id'."
            )

    # --------------------------------------------------------
    # Create every possible company-year combination
    # --------------------------------------------------------

    all_combos = pd.MultiIndex.from_product(
        [
            companies_df["company_id"].dropna().unique(),
            expected_years
        ],
        names=["company_id", "year"]
    ).to_frame(index=False)

    # --------------------------------------------------------
    # Keep only required columns
    # --------------------------------------------------------

    pattern_df = capital_alloc_df[
        [
            "company_id",
            "year",
            "pattern_label"
        ]
    ].copy()

    # --------------------------------------------------------
    # Merge expected combinations with actual data
    # --------------------------------------------------------

    merged = all_combos.merge(
        pattern_df,
        on=["company_id", "year"],
        how="left"
    )

    # --------------------------------------------------------
    # Find missing rows
    # --------------------------------------------------------

    missing = merged[
        merged["pattern_label"].isna()
    ].copy()

    # --------------------------------------------------------
    # Save missing rows
    # --------------------------------------------------------

    if not missing.empty:

        output_path = (
            OUTPUT_DIR
            / "capital_allocation_gaps.csv"
        )

        missing.to_csv(
            output_path,
            index=False
        )

        print(
            f"WARNING: {len(missing)} missing "
            f"company-year pattern rows"
        )

        print(
            f"See: {output_path}"
        )

    else:

        print(
            "Completeness check passed: "
            "no missing company-year patterns."
        )

    return missing


# ============================================================
# DISTRIBUTION SUMMARY
# ============================================================

def generate_distribution_summary(
    capital_alloc_df,
    latest_year
):
    """
    Count how many companies belong to each capital
    allocation pattern in the latest year.
    """

    latest = capital_alloc_df[
        capital_alloc_df["year"] == latest_year
    ].copy()

    # Count pattern labels
    dist = (
        latest["pattern_label"]
        .value_counts()
        .reset_index()
    )

    dist.columns = [
        "pattern_label",
        "company_count"
    ]

    # Save
    output_path = (
        OUTPUT_DIR
        / "pattern_distribution_latest.csv"
    )

    dist.to_csv(
        output_path,
        index=False
    )

    print(
        f"Pattern distribution saved to:\n{output_path}"
    )

    return dist


# ============================================================
# ADD PATTERN TO CASHFLOW INTELLIGENCE
# ============================================================

def add_pattern_to_cashflow_intelligence(
    capital_alloc_df,
    latest_year,
    cashflow_intel_path=None
):
    """
    Add the latest capital allocation pattern to the
    cashflow intelligence Excel report.
    """

    # --------------------------------------------------------
    # Default cashflow intelligence path
    # --------------------------------------------------------

    if cashflow_intel_path is None:

        cashflow_intel_path = (
            OUTPUT_DIR
            / "cashflow_intelligence.xlsx"
        )

    else:

        cashflow_intel_path = Path(
            cashflow_intel_path
        )

        # If a relative path was supplied,
        # interpret it relative to project root.

        if not cashflow_intel_path.is_absolute():
            cashflow_intel_path = (
                BASE_DIR / cashflow_intel_path
            )

    # --------------------------------------------------------
    # Check file exists
    # --------------------------------------------------------

    if not cashflow_intel_path.exists():

        raise FileNotFoundError(
            f"Cashflow intelligence file not found:\n"
            f"{cashflow_intel_path}"
        )

    # --------------------------------------------------------
    # Read Excel
    # --------------------------------------------------------

    intel_df = pd.read_excel(
        cashflow_intel_path
    )

    # --------------------------------------------------------
    # Latest year's patterns
    # --------------------------------------------------------

    latest_patterns = capital_alloc_df[
        capital_alloc_df["year"] == latest_year
    ][
        [
            "company_id",
            "pattern_label"
        ]
    ].copy()

    # Rename for final report
    latest_patterns = latest_patterns.rename(
        columns={
            "pattern_label":
            "capital_allocation_label"
        }
    )

    # --------------------------------------------------------
    # Remove existing column if present
    # --------------------------------------------------------

    intel_df = intel_df.drop(
        columns=["capital_allocation_label"],
        errors="ignore"
    )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    intel_df = intel_df.merge(
        latest_patterns,
        on="company_id",
        how="left"
    )

    # --------------------------------------------------------
    # Save updated Excel
    # --------------------------------------------------------

    output_path = (
        OUTPUT_DIR
        / "cashflow_intelligence.xlsx"
    )

    intel_df.to_excel(
        output_path,
        index=False
    )

    print(
        f"Cashflow intelligence updated:\n{output_path}"
    )

    return intel_df


# ============================================================
# FIND PATTERN CHANGES
# ============================================================

def find_pattern_changes(capital_alloc_df):
    """
    Find years where a company's capital allocation pattern
    changed compared with the previous year.
    """

    df = capital_alloc_df.sort_values(
        ["company_id", "year"]
    ).copy()

    # Previous year's pattern
    df["previous_pattern"] = (
        df.groupby("company_id")["pattern_label"]
        .shift(1)
    )

    # Keep only actual changes
    changed = df[
        (
            df["pattern_label"]
            != df["previous_pattern"]
        )
        &
        df["previous_pattern"].notna()
    ].copy()

    # Select useful columns
    changed = changed[
        [
            "company_id",
            "year",
            "previous_pattern",
            "pattern_label"
        ]
    ]

    # Rename final column
    changed = changed.rename(
        columns={
            "pattern_label":
            "current_pattern"
        }
    )

    # Save
    output_path = (
        OUTPUT_DIR
        / "pattern_changes.csv"
    )

    changed.to_csv(
        output_path,
        index=False
    )

    print(
        f"Pattern changes saved to:\n{output_path}"
    )

    return changed


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # Input files
    # --------------------------------------------------------

    capital_allocation_path = (
        OUTPUT_DIR
        / "capital_allocation.csv"
    )

    companies_path = (
        DATA_DIR
        / "companies.csv"
    )

    # --------------------------------------------------------
    # Read capital allocation
    # --------------------------------------------------------

    if not capital_allocation_path.exists():

        raise FileNotFoundError(
            f"capital_allocation.csv not found:\n"
            f"{capital_allocation_path}"
        )

    capital_alloc_df = pd.read_csv(
        capital_allocation_path
    )

    # --------------------------------------------------------
    # Validate capital allocation columns
    # --------------------------------------------------------

    required_columns = {
        "company_id",
        "year",
        "cfo_sign",
        "cfi_sign",
        "cff_sign",
        "pattern_label"
    }

    missing_columns = (
        required_columns
        - set(capital_alloc_df.columns)
    )

    if missing_columns:

        raise ValueError(
            "capital_allocation.csv is missing "
            f"columns: {sorted(missing_columns)}"
        )

    # --------------------------------------------------------
    # Read companies
    # --------------------------------------------------------

    if not companies_path.exists():

        raise FileNotFoundError(
            f"companies.csv not found:\n"
            f"{companies_path}"
        )

    companies_df = pd.read_csv(
        companies_path
    )

    # --------------------------------------------------------
    # Normalize companies ID
    # --------------------------------------------------------

    if (
        "company_id" not in companies_df.columns
        and "id" in companies_df.columns
    ):

        companies_df = companies_df.rename(
            columns={
                "id": "company_id"
            }
        )

    # --------------------------------------------------------
    # Expected years
    # --------------------------------------------------------

    expected_years = sorted(
        capital_alloc_df["year"]
        .dropna()
        .unique()
    )

    if not expected_years:

        raise ValueError(
            "No years found in capital_allocation.csv"
        )

    latest_year = max(expected_years)

    print("=" * 60)
    print("CAPITAL ALLOCATION REPORT")
    print("=" * 60)

    print(
        f"\nCompanies: "
        f"{companies_df['company_id'].nunique()}"
    )

    print(
        f"Years: "
        f"{expected_years}"
    )

    print(
        f"Latest year: "
        f"{latest_year}"
    )

    # --------------------------------------------------------
    # 1. Completeness
    # --------------------------------------------------------

    missing = verify_completeness(
        capital_alloc_df,
        companies_df,
        expected_years
    )

    # --------------------------------------------------------
    # 2. Latest-year distribution
    # --------------------------------------------------------

    dist = generate_distribution_summary(
        capital_alloc_df,
        latest_year
    )

    print("\nLatest-year pattern distribution:")
    print(dist.to_string(index=False))

    # --------------------------------------------------------
    # 3. Add pattern to cashflow intelligence
    # --------------------------------------------------------

    intel_df = add_pattern_to_cashflow_intelligence(
        capital_alloc_df,
        latest_year
    )

    # --------------------------------------------------------
    # 4. Find pattern changes
    # --------------------------------------------------------

    changes = find_pattern_changes(
        capital_alloc_df
    )

    print(
        f"\nPattern changes detected: "
        f"{len(changes)}"
    )

    print("\n" + "=" * 60)
    print("CAPITAL ALLOCATION REPORT COMPLETE")
    print("=" * 60)