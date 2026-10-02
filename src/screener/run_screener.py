import pandas as pd
import numpy as np
from src.screener.engine import apply_filters
from src.screener.presets import load_presets, run_all_presets, validate_preset_counts

# STEP A: Apna financial_ratios data load karo
# (Sprint 1-2 mein jo SQLite table banayi thi, wahan se aayega)
financial_ratios_df = pd.read_excel("data/financial_ratios.xlsx")
# ya: financial_ratios_df = pd.read_sql("SELECT * FROM financial_ratios", conn)

# STEP B: Sab presets chalao
results = run_all_presets(financial_ratios_df, "config/screener_config.yaml")

# STEP C: Har preset ka result count dekho
for name, df in results.items():
    print(f"{name}: {len(df)} companies")

# STEP D: Counts valid hain ya nahi (5-50 range) check karo
summary = validate_preset_counts(results)
print(summary)

# STEP E: Ek preset ka top-5 dekho (sanity check)
print(results["Quality Compounder"].head())


dummy_df = pd.DataFrame({
    "company_id": [1, 2, 3, 4],
    "broad_sector": ["IT", "Financials", "FMCG", "IT"],
    "ROE": [18, 22, 10, 16],
    "DE": [0.5, 8.0, 0.3, 0.9],   # note: company 2 ka DE bahut high hai, but Financials hai
    "ICR": [12, "Debt Free", 5, 20],
    "FCF": [100, 200, -50, 300],
    "Revenue_CAGR_5yr": [12, 8, 15, 11],
    "Sales": [6000, 8000, 3000, 5500],
})

filtered = apply_filters(dummy_df, {"ROE_min": 15, "DE_max": 1.0})
print(filtered)