import pandas as pd
import math


# =============== Day 13 =============================================

def cross_check_roce(company_id, computed_roce, source_roce, threshold_pct=5.0):
    """Compares our computed ROCE against companies.xlsx's roce_percentage.
    Returns a log entry dict if the difference exceeds threshold, else None."""
    if source_roce is None or computed_roce is None:
        return None
    diff_pct = abs(computed_roce - source_roce)
    if diff_pct > threshold_pct:
        return {
            "company_id": company_id,
            "metric": "ROCE",
            "computed": computed_roce,
            "source": source_roce,
            "diff_pct": round(diff_pct, 2),
            "category": None,  # filled in during manual review
        }
    return None


def cross_check_roe(company_id, computed_roe, source_roe, threshold_pct=5.0):
    """Same idea for ROE -- but source_roe has a KNOWN scaling anomaly
    (e.g. TCS shows 0.52 instead of ~52%). We still log it, but the
    category is pre-filled since we already know the explanation."""
    if source_roe is None or computed_roe is None:
        return None
    diff_pct = abs(computed_roe - source_roe)
    if diff_pct > threshold_pct:
        category = ("data source issue - likely decimal scaling"
                     if source_roe < 5 and computed_roe > 20 else None)
        return {
            "company_id": company_id, "metric": "ROE",
            "computed": computed_roe, "source": source_roe,
            "diff_pct": round(diff_pct, 2), "category": category,
        }
    return None

# def run_edge_case_audit(financial_ratios_df:pd.DataFrame, companies_df:pd.DataFrame, sectors_df:pd.DataFrame, log_path):
#     financials_ids = set(sectors_df[sectors_df.broad_sector == "Financials"].company_id)
#     latest = financial_ratios_df.sort_values("year").groupby("company_id").last()
#     log_entries = []

#     for company_id, row in latest.iterrows():
#         source_row = companies_df[companies_df.company_id == company_id].iloc[0]

#         roce_entry = cross_check_roce(company_id, row.get("return_on_capital_employed_pct"),
#                                        source_row.get("roce_percentage"))
#         if roce_entry:
#             log_entries.append(roce_entry)

#         roe_entry = cross_check_roe(company_id, row.get("return_on_equity_pct"),
#                                      source_row.get("roe_percentage"))
#         if roe_entry:
#             log_entries.append(roe_entry)

#     with open(log_path, "w") as f:
#         for e in log_entries:
#             f.write(f"{e['company_id']} | {e['metric']} | computed={e['computed']} "
#                     f"source={e['source']} | diff={e['diff_pct']}% "
#                     f"| category={e['category'] or 'NEEDS REVIEW'}\n")

#     print(f"{len(log_entries)} anomalies logged to {log_path}")
#     print(f"Financials sector companies (D/E flag suppressed): {len(financials_ids)}")
def run_edge_case_audit(
    financial_ratios_df: pd.DataFrame,
    companies_df: pd.DataFrame,
    sectors_df: pd.DataFrame,
    log_path
):
    # Normalize company_id in all DataFrames
    financial_ratios_df = financial_ratios_df.copy()
    companies_df = companies_df.copy()
    sectors_df = sectors_df.copy()

    financial_ratios_df["company_id"] = (
        financial_ratios_df["company_id"].astype(str).str.strip()
    )

    companies_df["company_id"] = (
        companies_df["company_id"].astype(str).str.strip()
    )

    sectors_df["company_id"] = (
        sectors_df["company_id"].astype(str).str.strip()
    )

    financials_ids = set(
        sectors_df[
            sectors_df["broad_sector"] == "Financials"
        ]["company_id"]
    )

    latest = (
        financial_ratios_df
        .sort_values("year")
        .groupby("company_id")
        .last()
    )

    log_entries = []

    for company_id, row in latest.iterrows():

        # Find company
        company_match = companies_df[
            companies_df["company_id"] == company_id
        ]

        # Prevent .iloc[0] error
        if company_match.empty:
            print(
                f"WARNING: company_id {company_id} "
                f"not found in companies_df"
            )
            continue

        source_row = company_match.iloc[0]

        # ROCE cross-check
        roce_entry = cross_check_roce(
            company_id,
            row.get("return_on_capital_employed_pct"),
            source_row.get("roce_percentage")
        )

        if roce_entry:
            log_entries.append(roce_entry)

        # ROE cross-check
        roe_entry = cross_check_roe(
            company_id,
            row.get("return_on_equity_pct"),
            source_row.get("roe_percentage")
        )

        if roe_entry:
            log_entries.append(roe_entry)

    # Write log
    with open(log_path, "w") as f:
        for e in log_entries:
            f.write(
                f"{e['company_id']} | "
                f"{e['metric']} | "
                f"computed={e['computed']} | "
                f"source={e['source']} | "
                f"diff={e['diff_pct']}% | "
                f"category={e['category'] or 'NEEDS REVIEW'}\n"
            )

    print(
        f"{len(log_entries)} anomalies logged to {log_path}"
    )

    print(
        f"Financials sector companies "
        f"(D/E flag suppressed): {len(financials_ids)}"
    )