import re
import pandas as pd
from pathlib import Path
CRITICAL, WARNING, INFO = "CRITICAL", "WARNING", "INFO"

def fail(company_id, year, field, issue, severity):
    return {"company_id": company_id, "year": year, "field": field,
            "issue": issue, "severity": severity}

# ── Structural / uniqueness ────────────────────────────────────────────

def dq01_pk_uniqueness(companies):
    dupes = companies[companies["id"].duplicated(keep=False)]
    return [fail(r.id, None, "id", "duplicate company PK", CRITICAL)
            for r in dupes.itertuples()]

def dq02_annual_pk(df, table_name):
    dupes = df[df.duplicated(subset=["company_id", "year"], keep=False)]
    return [fail(r.company_id, r.year, "company_id+year",
                 f"duplicate PK in {table_name}", CRITICAL)
            for r in dupes.itertuples()]

def dq03_fk_integrity(child_df, valid_ids, table_name):
    orphans = child_df[~child_df["company_id"].isin(valid_ids)]
    return [fail(r.company_id, getattr(r, "year", None), "company_id",
                 f"orphan FK in {table_name}", CRITICAL)
            for r in orphans.itertuples()]

def dq07_year_format(df, table_name):
    bad = df[~df["year"].astype(str).str.match(r"^\d{4}-\d{2}$")]
    return [fail(r.company_id, r.year, "year",
                 f"unparsed year in {table_name}", CRITICAL)
            for r in bad.itertuples()]

def dq08_ticker_format(companies):
    bad = companies[~companies["id"].str.len().between(2, 12)]
    return [fail(r.id, None, "id", "ticker length out of range", CRITICAL)
            for r in bad.itertuples()]

# ── Cross-field arithmetic (tolerance-based) ───────────────────────────

def dq04_bs_balance(bs):
    diff_pct = (bs["total_assets"] - bs["total_liabilities"]).abs() / bs["total_assets"]
    bad = bs[diff_pct >= 0.01]
    return [fail(r.company_id, r.year, "total_assets",
                 "assets/liabilities mismatch >1%", WARNING)
            for r in bad.itertuples()]

def dq05_opm_crosscheck(pl):
    computed = pl["operating_profit"] / pl["sales"] * 100
    bad = pl[(pl["opm_percentage"] - computed).abs() >= 1.0]
    return [fail(r.company_id, r.year, "opm_percentage",
                 "OPM mismatch vs computed", WARNING)
            for r in bad.itertuples()]

def dq09_net_cash_check(cf):
    computed = cf["operating_activity"] + cf["investing_activity"] + cf["financing_activity"]
    bad = cf[(cf["net_cash_flow"] - computed).abs() > 10]
    return [fail(r.company_id, r.year, "net_cash_flow",
                 "net cash flow != CFO+CFI+CFF (±10 Cr)", WARNING)
            for r in bad.itertuples()]

def dq14_eps_sign(pl):
    bad = pl[(pl["net_profit"] > 0) & (pl["eps"] <= 0)]
    return [fail(r.company_id, r.year, "eps",
                 "EPS sign inconsistent with net_profit", WARNING)
            for r in bad.itertuples()]

# ── Range / plausibility ────────────────────────────────────────────────

def dq06_positive_sales(pl):
    bad = pl[pl["sales"] <= 0]
    return [fail(r.company_id, r.year, "sales", "sales <= 0", WARNING)
            for r in bad.itertuples()]

def dq10_nonneg_fixed_assets(bs):
    bad = bs[bs["fixed_assets"] < 0]
    return [fail(r.company_id, r.year, "fixed_assets", "negative fixed_assets", WARNING)
            for r in bad.itertuples()]

def dq11_tax_rate_range(pl):
    bad = pl[~pl["tax_percentage"].between(0, 60)]
    return [fail(r.company_id, r.year, "tax_percentage", "tax rate out of [0,60]", WARNING)
            for r in bad.itertuples()]

def dq12_dividend_cap(pl):
    bad = pl[pl["dividend_payout"] > 200]
    return [fail(r.company_id, r.year, "dividend_payout", "payout > 200%", WARNING)
            for r in bad.itertuples()]

def dq16_coverage_check(pl):
    counts = pl.groupby("company_id")["year"].nunique()
    short = counts[counts < 5]
    return [fail(cid, None, "year", f"only {n} years of history", WARNING)
            for cid, n in short.items()]

# ── Runner ───────────────────────────────────────────────────────────────

def run_all_rules(companies, pl, bs, cf) -> pd.DataFrame:
    failures = []
    failures += dq01_pk_uniqueness(companies)
    failures += dq02_annual_pk(pl, "profitandloss")
    failures += dq03_fk_integrity(pl, set(companies["id"]), "profitandloss")
    failures += dq04_bs_balance(bs)
    failures += dq05_opm_crosscheck(pl)
    failures += dq06_positive_sales(pl)
    failures += dq07_year_format(pl, "profitandloss")
    failures += dq08_ticker_format(companies)
    failures += dq09_net_cash_check(cf)
    failures += dq10_nonneg_fixed_assets(bs)
    failures += dq11_tax_rate_range(pl)
    failures += dq12_dividend_cap(pl)
    failures += dq14_eps_sign(pl)
    failures += dq16_coverage_check(pl)
    # DQ-13 (URL check) and DQ-15 (info-only strict balance) omitted here —
    # DQ-13 needs a live requests.head() loop; DQ-15 is just a counter, see below.
    df =  pd.DataFrame(failures)
    df.to_csv('validation_failures.csv', index=False)


# ===================================



# CRITICAL, WARNING, INFO = "CRITICAL", "WARNING", "INFO"

# def fail(company_id, year, field, issue, severity):
#     return {"company_id": company_id, "year": year, "field": field,
#             "issue": issue, "severity": severity}

# ── [ ...all 14 dq0X functions unchanged from before... ] ──────────────
# (dq01_pk_uniqueness, dq02_annual_pk, dq03_fk_integrity, dq04_bs_balance,
#  dq05_opm_crosscheck, dq06_positive_sales, dq07_year_format,
#  dq08_ticker_format, dq09_net_cash_check, dq10_nonneg_fixed_assets,
#  dq11_tax_rate_range, dq12_dividend_cap, dq14_eps_sign, dq16_coverage_check)

def run_all_rules(companies, pl, bs, cf) -> pd.DataFrame:
    failures = []
    failures += dq01_pk_uniqueness(companies)
    failures += dq02_annual_pk(pl, "profitandloss")
    failures += dq03_fk_integrity(pl, set(companies["id"]), "profitandloss")
    failures += dq04_bs_balance(bs)
    failures += dq05_opm_crosscheck(pl)
    failures += dq06_positive_sales(pl)
    failures += dq07_year_format(pl, "profitandloss")
    failures += dq08_ticker_format(companies)
    failures += dq09_net_cash_check(cf)
    failures += dq10_nonneg_fixed_assets(bs)
    failures += dq11_tax_rate_range(pl)
    failures += dq12_dividend_cap(pl)
    failures += dq14_eps_sign(pl)
    failures += dq16_coverage_check(pl)
    return pd.DataFrame(failures)

# ── Stage 1: null-completeness split ────────────────────────────────────

RAW_DIR = Path(r"C:\Users\bhrra\Desktop\nifty100\data\raw")
SUPP_DIR = RAW_DIR / "supporting datasets"
OUT_DIR = Path(r"C:\Users\bhrra\Desktop\nifty100\output")
OUT_DIR.mkdir(exist_ok=True)

CORE_FILES = ["companies", "profitandloss", "balancesheet", "cashflow",
              "analysis", "documents", "prosandcons"]
SUPP_FILES = ["sectors", "stock_prices", "market_cap",
              "financial_ratios", "peer_groups"]

def load_and_split(name: str, path: Path, header_row: int):
    df = pd.read_excel(path, header=header_row)
    null_mask = df.isnull().any(axis=1)
    clean_df, null_df = df[~null_mask], df[null_mask]
    null_df.to_csv(OUT_DIR / f"{name}_null_values.csv", index=False)
    print(f"{name}: {len(df)} rows -> {len(clean_df)} null-free, {len(null_df)} dropped (nulls)")
    return clean_df

# ── Stage 2 + orchestration ──────────────────────────────────────────────

def run_pipeline():
    tables = {}
    for name in CORE_FILES:
        tables[name] = load_and_split(name, RAW_DIR / f"{name}.xlsx", header_row=1)
    for name in SUPP_FILES:
        tables[name] = load_and_split(name, SUPP_DIR / f"{name}.xlsx", header_row=0)

    dq_failures = run_all_rules(
        tables["companies"], tables["profitandloss"],
        tables["balancesheet"], tables["cashflow"]
    )
    dq_failures.to_csv(OUT_DIR / "validation_failures.csv", index=False)

    # Final clean data = null-free rows minus any row with a CRITICAL failure
    critical_bad_ids = set(
        dq_failures.loc[dq_failures.severity == CRITICAL, "company_id"]
    )
    clean_pl = tables["profitandloss"][
        ~tables["profitandloss"]["company_id"].isin(critical_bad_ids)
    ]
    clean_pl.to_csv(OUT_DIR / "profitandloss_clean.csv", index=False)

    print(f"\nDQ failures: {len(dq_failures)} "
          f"({(dq_failures.severity == CRITICAL).sum()} CRITICAL)")
    print(f"Final clean profitandloss rows: {len(clean_pl)}")

if __name__ == "__main__":
    run_pipeline()




# =====================================