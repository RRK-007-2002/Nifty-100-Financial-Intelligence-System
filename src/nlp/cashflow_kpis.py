# # src/analytics/cashflow_kpis.py
# import pandas as pd
# import sqlite3
# from pathlib import Path
# def load_data(db_path):
#     conn = sqlite3.connect(db_path)
#     cashflow = pd.read_sql("SELECT * FROM cashflow", conn)
#     pnl = pd.read_sql("SELECT company_id, year, net_profit, sales FROM profitandloss", conn)
#     balancesheet = pd.read_sql("SELECT company_id, year, borrowings FROM balancesheet", conn)
#     companies = pd.read_sql("SELECT id as company_id FROM companies", conn)
#     conn.close()
#     return cashflow, pnl, balancesheet, companies


# def label_cfo_quality(score):
#     if score > 1.0:
#         return "High Quality"
#     elif score >= 0.5:
#         return "Moderate"
#     else:
#         return "Accrual Risk"


# def label_capex_intensity(pct):
#     if pct < 3:
#         return "Asset Light"
#     elif pct <= 8:
#         return "Moderate"
#     else:
#         return "Capital Intensive"


# def compute_company_kpis(company_id, cf, pnl, bs):
#     cf = cf.sort_values("year")
#     pnl = pnl.sort_values("year")
#     bs = bs.sort_values("year")

#     merged = cf.merge(pnl, on=["company_id", "year"], how="inner")
#     recent5 = merged.tail(5).copy()

#     # guard: skip years where PAT is ~0 to avoid absurd ratios
#     recent5 = recent5[recent5["net_profit"].abs() > 1e-6]
#     if recent5.empty:
#         return None

#     recent5["cfo_pat_ratio"] = recent5["cash_from_operations_cr"] / recent5["net_profit"]
#     cfo_quality_score = recent5["cfo_pat_ratio"].mean()

#     latest = merged.iloc[-1]
#     capex_intensity_pct = abs(latest["cfi"]) / latest["sales"] * 100 if latest["sales"] else None

#     distress_flag = bool(latest["cash_from_operations_cr"] < 0 and latest["cff"] > 0)

#     bs_recent = bs.tail(2)
#     deleveraging_flag = False
#     if len(bs_recent) == 2:
#         deleveraging_flag = bool(
#             latest["cff"] < 0 and bs_recent.iloc[-1]["borrowings"] < bs_recent.iloc[0]["borrowings"]
#         )

#     fcf = merged["cash_from_operations_cr"] + merged["cfi"]  # CFI is usually negative for capex, so this nets it out
#     fcf_start, fcf_end = fcf.iloc[0], fcf.iloc[-1]
#     years = len(fcf) - 1
#     fcf_cagr_5yr = None
#     if fcf_start > 0 and years > 0:
#         fcf_cagr_5yr = ((fcf_end / fcf_start) ** (1 / years) - 1) * 100

#     fcf_latest = latest["cash_from_operations_cr"] + latest["cfi"]
#     fcf_conversion_pct = (fcf_latest / latest["net_profit"] * 100) if latest["net_profit"] else None

#     return {
#         "company_id": company_id,
#         "cfo_quality_score": round(cfo_quality_score, 2),
#         "cfo_quality_label": label_cfo_quality(cfo_quality_score),
#         "capex_intensity_pct": round(capex_intensity_pct, 2) if capex_intensity_pct is not None else None,
#         "capex_label": label_capex_intensity(capex_intensity_pct) if capex_intensity_pct is not None else "Unknown",
#         "fcf_cagr_5yr": round(fcf_cagr_5yr, 2) if fcf_cagr_5yr is not None else None,
#         "fcf_conversion_pct": round(fcf_conversion_pct, 2) if fcf_conversion_pct is not None else None,
#         "distress_flag": distress_flag,
#         "deleveraging_flag": deleveraging_flag,
#     }


# def generate_cashflow_intelligence(db_path):
#     cashflow, pnl, balancesheet, companies = load_data(db_path)
#     rows = []

#     for _, comp in companies.iterrows():
#         cid = comp["company_id"]
#         cf = cashflow[cashflow["company_id"] == cid]
#         p = pnl[pnl["company_id"] == cid]
#         bs = balancesheet[balancesheet["company_id"] == cid]

#         result = compute_company_kpis(cid, cf, p, bs)
#         if result:
#             result["sector"] = comp["sector"]
#             rows.append(result)

#     df = pd.DataFrame(rows)
#     df.to_excel("output/cashflow_intelligence.xlsx", index=False)

#     distress = df[df["distress_flag"]].copy()
#     distress.to_csv("output/distress_alerts.csv", index=False)

#     return df


# if __name__ == "__main__":
#     db_path = Path(r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db")
#     df = generate_cashflow_intelligence(db_path)
#     print(f"Processed {len(df)} companies, {df['distress_flag'].sum()} distress flags")

import pandas as pd
import sqlite3
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

# cashflow_kpis.py is inside:
# nifty100/src/analytics/cashflow_kpis.py
#
# parents[2] = nifty100 project root

BASE_DIR = Path(__file__).resolve().parents[2]

DB_PATH = BASE_DIR / "db" / "nifty100.db"
OUTPUT_DIR = BASE_DIR / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# LOAD DATA
# ============================================================

def load_data(db_path):

    conn = sqlite3.connect(db_path)

    try:

        # Cash Flow
        cashflow = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                operating_activity,
                investing_activity,
                financing_activity,
                net_cash_flow
            FROM cashflow
            """,
            conn
        )

        # Profit & Loss
        pnl = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                net_profit,
                sales
            FROM profitandloss
            """,
            conn
        )

        # Balance Sheet
        balancesheet = pd.read_sql(
            """
            SELECT
                company_id,
                year,
                borrowings
            FROM balancesheet
            """,
            conn
        )

        # Companies
        companies = pd.read_sql(
            """
            SELECT
                id AS company_id,
                company_name
            FROM companies
            """,
            conn
        )

    finally:
        conn.close()

    return cashflow, pnl, balancesheet, companies


# ============================================================
# LABEL FUNCTIONS
# ============================================================

def label_cfo_quality(score):

    if score > 1.0:
        return "High Quality"

    elif score >= 0.5:
        return "Moderate"

    else:
        return "Accrual Risk"


def label_capex_intensity(pct):

    if pct < 3:
        return "Asset Light"

    elif pct <= 8:
        return "Moderate"

    else:
        return "Capital Intensive"


# ============================================================
# COMPANY KPI CALCULATION
# ============================================================

def compute_company_kpis(company_id, cf, pnl, bs):

    # --------------------------------------------------------
    # Validate input
    # --------------------------------------------------------

    if cf.empty or pnl.empty:
        return None

    # Sort chronologically
    cf = cf.sort_values("year").copy()
    pnl = pnl.sort_values("year").copy()
    bs = bs.sort_values("year").copy()

    # --------------------------------------------------------
    # Merge Cash Flow + P&L
    # --------------------------------------------------------

    merged = cf.merge(
        pnl,
        on=["company_id", "year"],
        how="inner"
    )

    if merged.empty:
        return None

    merged = merged.sort_values("year").reset_index(drop=True)

    # --------------------------------------------------------
    # Recent 5 years
    # --------------------------------------------------------

    recent5 = merged.tail(5).copy()

    # Remove years where PAT is approximately zero
    recent5 = recent5[
        recent5["net_profit"].abs() > 1e-6
    ].copy()

    if recent5.empty:
        return None

    # --------------------------------------------------------
    # 1. CFO / PAT Ratio
    #
    # CFO = operating_activity
    #
    # CFO/PAT > 1 generally means operating cash generation
    # is stronger than accounting profit.
    # --------------------------------------------------------

    recent5["cfo_pat_ratio"] = (
        recent5["operating_activity"]
        / recent5["net_profit"]
    )

    cfo_quality_score = recent5["cfo_pat_ratio"].mean()

    # --------------------------------------------------------
    # Latest year
    # --------------------------------------------------------

    latest = merged.iloc[-1]

    # --------------------------------------------------------
    # 2. CAPEX Intensity
    #
    # Investing activity is generally negative when cash is
    # spent on investments/capex.
    #
    # CAPEX Intensity =
    # |Investing Activity| / Sales * 100
    # --------------------------------------------------------

    if (
        pd.notna(latest["sales"])
        and latest["sales"] != 0
    ):

        capex_intensity_pct = (
            abs(latest["investing_activity"])
            / latest["sales"]
            * 100
        )

    else:

        capex_intensity_pct = None

    # --------------------------------------------------------
    # 3. Distress Flag
    #
    # Operating cash flow < 0
    # AND
    # Financing cash flow > 0
    #
    # This can indicate dependence on financing despite
    # negative operating cash generation.
    # --------------------------------------------------------

    distress_flag = bool(
        latest["operating_activity"] < 0
        and latest["financing_activity"] > 0
    )

    # --------------------------------------------------------
    # 4. Deleveraging Flag
    #
    # Financing activity < 0
    # AND
    # borrowings decreased
    # --------------------------------------------------------

    deleveraging_flag = False

    if len(bs) >= 2:

        bs_recent = bs.sort_values("year").tail(2)

        previous_bs = bs_recent.iloc[0]
        latest_bs = bs_recent.iloc[1]

        if (
            pd.notna(previous_bs["borrowings"])
            and pd.notna(latest_bs["borrowings"])
        ):

            deleveraging_flag = bool(
                latest["financing_activity"] < 0
                and latest_bs["borrowings"]
                < previous_bs["borrowings"]
            )

    # --------------------------------------------------------
    # 5. Free Cash Flow
    #
    # FCF = CFO + CFI
    #
    # Here:
    #
    # CFO = operating_activity
    # CFI = investing_activity
    #
    # Since investing cash flow is usually negative for
    # capital expenditure:
    #
    # FCF = Operating Activity + Investing Activity
    # --------------------------------------------------------

    merged["fcf"] = (
        merged["operating_activity"]
        + merged["investing_activity"]
    )

    # --------------------------------------------------------
    # 6. FCF CAGR
    # --------------------------------------------------------

    fcf_start = merged["fcf"].iloc[0]
    fcf_end = merged["fcf"].iloc[-1]

    years = len(merged) - 1

    fcf_cagr_5yr = None

    # CAGR only makes mathematical sense here when both
    # starting and ending FCF are positive.

    if (
        pd.notna(fcf_start)
        and pd.notna(fcf_end)
        and fcf_start > 0
        and fcf_end > 0
        and years > 0
    ):

        fcf_cagr_5yr = (
            (fcf_end / fcf_start) ** (1 / years) - 1
        ) * 100

    # --------------------------------------------------------
    # 7. Latest FCF
    # --------------------------------------------------------

    fcf_latest = (
        latest["operating_activity"]
        + latest["investing_activity"]
    )

    # --------------------------------------------------------
    # 8. FCF Conversion
    #
    # FCF Conversion =
    # FCF / Net Profit * 100
    # --------------------------------------------------------

    if (
        pd.notna(latest["net_profit"])
        and latest["net_profit"] != 0
    ):

        fcf_conversion_pct = (
            fcf_latest
            / latest["net_profit"]
            * 100
        )

    else:

        fcf_conversion_pct = None

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {

        "company_id": company_id,

        "latest_year": latest["year"],

        "cfo_quality_score": round(
            cfo_quality_score,
            2
        ),

        "cfo_quality_label": label_cfo_quality(
            cfo_quality_score
        ),

        "capex_intensity_pct": (
            round(capex_intensity_pct, 2)
            if capex_intensity_pct is not None
            else None
        ),

        "capex_label": (
            label_capex_intensity(
                capex_intensity_pct
            )
            if capex_intensity_pct is not None
            else "Unknown"
        ),

        "fcf_cagr_5yr": (
            round(fcf_cagr_5yr, 2)
            if fcf_cagr_5yr is not None
            else None
        ),

        "fcf_conversion_pct": (
            round(fcf_conversion_pct, 2)
            if fcf_conversion_pct is not None
            else None
        ),

        "distress_flag": distress_flag,

        "deleveraging_flag": deleveraging_flag,
    }


# ============================================================
# GENERATE CASH FLOW INTELLIGENCE
# ============================================================

def generate_cashflow_intelligence(db_path):

    cashflow, pnl, balancesheet, companies = load_data(
        db_path
    )

    rows = []

    # --------------------------------------------------------
    # Process every company
    # --------------------------------------------------------

    for _, comp in companies.iterrows():

        cid = comp["company_id"]

        cf = cashflow[
            cashflow["company_id"] == cid
        ].copy()

        p = pnl[
            pnl["company_id"] == cid
        ].copy()

        bs = balancesheet[
            balancesheet["company_id"] == cid
        ].copy()

        result = compute_company_kpis(
            cid,
            cf,
            p,
            bs
        )

        if result:

            result["company_name"] = comp[
                "company_name"
            ]

            rows.append(result)

    # --------------------------------------------------------
    # Final DataFrame
    # --------------------------------------------------------

    df = pd.DataFrame(rows)

    if df.empty:

        print("No cash flow KPI data was generated.")

        return df

    # Put company name near company ID
    column_order = [
        "company_id",
        "company_name",
        "latest_year",
        "cfo_quality_score",
        "cfo_quality_label",
        "capex_intensity_pct",
        "capex_label",
        "fcf_cagr_5yr",
        "fcf_conversion_pct",
        "distress_flag",
        "deleveraging_flag"
    ]

    df = df[column_order]

    # --------------------------------------------------------
    # Save Excel
    # --------------------------------------------------------

    excel_path = (
        OUTPUT_DIR
        / "cashflow_intelligence.xlsx"
    )

    df.to_excel(
        excel_path,
        index=False
    )

    # --------------------------------------------------------
    # Save distress alerts
    # --------------------------------------------------------

    distress = df[
        df["distress_flag"] == True
    ].copy()

    distress_path = (
        OUTPUT_DIR
        / "distress_alerts.csv"
    )

    distress.to_csv(
        distress_path,
        index=False
    )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print(
        f"Processed {len(df)} companies"
    )

    print(
        f"Distress flags: "
        f"{df['distress_flag'].sum()}"
    )

    print(
        f"Deleveraging flags: "
        f"{df['deleveraging_flag'].sum()}"
    )

    print(
        f"\nExcel saved to:\n{excel_path}"
    )

    print(
        f"\nDistress alerts saved to:\n{distress_path}"
    )

    return df


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("Database:")
    print(DB_PATH)

    print("\nStarting Cash Flow Intelligence...\n")

    df = generate_cashflow_intelligence(
        DB_PATH
    )