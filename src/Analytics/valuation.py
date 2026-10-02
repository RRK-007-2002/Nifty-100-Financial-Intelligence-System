import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db"         # adjust to match your layout
MARKET_CAP_CSV = r"C:\Users\bhrra\Desktop\nifty100\data\processed\market_cap.csv"  # VERIFY actual path
OUTPUT_DIR = Path(r"C:\Users\bhrra\Desktop\nifty100\output")
# OUTPUT_DIR.mkdir(exist_ok=True)


def load_companies_sectors(conn):
    return pd.read_sql_query("""
        SELECT c.id AS company_id, c.company_name, s.broad_sector AS sector
        FROM companies c
        LEFT JOIN (
            SELECT company_id, broad_sector FROM sectors GROUP BY company_id
        ) s ON s.company_id = c.id
    """, conn)


def load_latest_fcf(conn):
    fr = pd.read_sql_query("SELECT company_id, year, free_cash_flow_cr FROM financial_ratios", conn)
    fr = fr.sort_values("year")
    return fr.groupby("company_id").tail(1)[["company_id", "free_cash_flow_cr"]]


def compute_valuation() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        companies = load_companies_sectors(conn)
        fcf = load_latest_fcf(conn)

    market_all = pd.read_csv(MARKET_CAP_CSV)
    latest_market = market_all.sort_values("year").groupby("company_id").tail(1)

    df = companies.merge(latest_market, on="company_id", how="left")
    df = df.merge(fcf, on="company_id", how="left")

    df["FCF_yield_pct"] = (df["free_cash_flow_cr"] / df["market_cap_crore"]) * 100

    df["sector_median_PE"] = df.groupby("sector")["pe_ratio"].transform("median")

    def flag_row(row):
        if pd.isna(row["pe_ratio"]) or pd.isna(row["sector_median_PE"]):
            return "N/A"
        if row["pe_ratio"] > row["sector_median_PE"] * 1.5:
            return "Caution"
        if row["pe_ratio"] < row["sector_median_PE"] * 0.7:
            return "Discount"
        return "Fair"

    df["flag"] = df.apply(flag_row, axis=1)
    df["PE_vs_sector_median_pct"] = (df["pe_ratio"] - df["sector_median_PE"]) / df["sector_median_PE"] * 100

    recent5 = market_all.sort_values("year").groupby("company_id").tail(5)
    median_5yr = recent5.groupby("company_id")["pe_ratio"].median().rename("5yr_median_PE")
    df = df.merge(median_5yr, on="company_id", how="left")

    out = df.rename(columns={"pe_ratio": "P/E", "pb_ratio": "P/B", "ev_ebitda": "EV/EBITDA"})[[
        "company_id", "company_name", "sector", "P/E", "P/B", "EV/EBITDA",
        "FCF_yield_pct", "5yr_median_PE", "PE_vs_sector_median_pct", "flag"
    ]]
    return out


def main():
    result = compute_valuation()
    if len(result) != 92:

        print(f"⚠️ WARNING: expected 92 companies, got {len(result)} — check merges for dropped rows")
    

    result.to_csv(OUTPUT_DIR / "valuation_summary.csv", index=False)

    flagged = result[result["flag"].isin(["Caution", "Discount"])]
    flagged.to_csv(OUTPUT_DIR / "valuation_flags.csv", index=False)

    with sqlite3.connect(DB_PATH) as conn:
        result.to_sql("valuation", conn, if_exists="replace", index=False)

    print(f"Done. {len(result)} companies written, {len(flagged)} flagged, DB table `valuation` refreshed.")


if __name__ == "__main__":
    main()