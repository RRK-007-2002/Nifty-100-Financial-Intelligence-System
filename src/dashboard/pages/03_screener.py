import streamlit as st
import pandas as pd
from utils import db

st.title("Screener")

PRESETS = {
    "Quality":    dict(roe_min=15, de_max=0.5,  fcf_min=0,     rev_cagr_min=8,   pat_cagr_min=8,   opm_min=15,  pe_max=100, pb_max=20, div_min=0.0, icr_min=3),
    "Value":      dict(roe_min=0,  de_max=100.0,fcf_min=-1000, rev_cagr_min=-50, pat_cagr_min=-50, opm_min=-50, pe_max=15,  pb_max=2,  div_min=0.0, icr_min=-10),
    "Growth":     dict(roe_min=10, de_max=100.0,fcf_min=-1000, rev_cagr_min=15,  pat_cagr_min=15,  opm_min=-50, pe_max=100, pb_max=20, div_min=0.0, icr_min=-10),
    "Dividend":   dict(roe_min=0,  de_max=100.0,fcf_min=-1000, rev_cagr_min=-50, pat_cagr_min=-50, opm_min=-50, pe_max=100, pb_max=20, div_min=2.0, icr_min=-10),
    "Debt-Free":  dict(roe_min=0,  de_max=0.1,  fcf_min=-1000, rev_cagr_min=-50, pat_cagr_min=-50, opm_min=-50, pe_max=100, pb_max=20, div_min=0.0, icr_min=-10),
    "Turnaround": dict(roe_min=-50,de_max=100.0,fcf_min=-1000, rev_cagr_min=-20, pat_cagr_min=-20, opm_min=-20, pe_max=100, pb_max=20, div_min=0.0, icr_min=-10),
}  # VERIFY against your Sprint 3 real definitions

st.write("Presets:")
cols = st.columns(6)
for col, (name, vals) in zip(cols, PRESETS.items()):
    if col.button(name):
        for k, v in vals.items():
            st.session_state[k] = v

roe_min      = st.sidebar.slider("ROE min %",             -50, 100, st.session_state.get("roe_min", 0), key="roe_min")
de_max  = st.sidebar.slider("D/E max", 0.0, 10.0, st.session_state.get("de_max", 10.0), key="de_max")
div_min = st.sidebar.slider("Dividend Yield min %", 0.0, 20.0, st.session_state.get("div_min", 0.0), key="div_min")
# de_max       = st.sidebar.slider("D/E max",                0.0, 10.0, st.session_state.get("de_max", 10.0), key="de_max")
fcf_min      = st.sidebar.slider("FCF min (₹cr)",       -1000, 5000, st.session_state.get("fcf_min", -1000), key="fcf_min")
rev_cagr_min = st.sidebar.slider("Revenue CAGR min %",   -50, 100, st.session_state.get("rev_cagr_min", -50), key="rev_cagr_min")
pat_cagr_min = st.sidebar.slider("PAT CAGR min %",       -50, 100, st.session_state.get("pat_cagr_min", -50), key="pat_cagr_min")
opm_min      = st.sidebar.slider("OPM min %",             -50, 100, st.session_state.get("opm_min", -50), key="opm_min")
pe_max       = st.sidebar.slider("P/E max",                0, 500, st.session_state.get("pe_max", 500), key="pe_max")
pb_max       = st.sidebar.slider("P/B max",                0, 100, st.session_state.get("pb_max", 100), key="pb_max")
# div_min      = st.sidebar.slider("Dividend Yield min %",   0.0, 20.0, st.session_state.get("div_min", 0.0), key="div_min")
icr_min      = st.sidebar.slider("ICR min",               -10, 50, st.session_state.get("icr_min", -10), key="icr_min")

companies = db.get_companies()
ratios = db.get_all_latest_ratios()
valuation = db.get_all_valuation()
market_cap = db.get_all_latest_market_cap()
scores = db.get_composite_scores()

merged = companies.merge(ratios, on="company_id", how="left")
merged = merged.merge(valuation[["company_id", "P/E", "P/B"]], on="company_id", how="left")
merged = merged.merge(market_cap[["company_id", "dividend_yield_pct"]], on="company_id", how="left")  # CHANGED
merged = merged.merge(scores, on="company_id", how="left")

filtered = merged[
    (merged["return_on_equity_pct"] >= roe_min) &
    (merged["debt_to_equity"] <= de_max) &
    (merged["free_cash_flow_cr"] >= fcf_min) &
    (merged["revenue_cagr_5yr"] >= rev_cagr_min) &
    (merged["pat_cagr_5yr"] >= pat_cagr_min) &
    (merged["operating_profit_margin_pct"] >= opm_min) &
    (merged["P/E"] <= pe_max) &
    (merged["P/B"] <= pb_max) &
    (merged["dividend_yield_pct"] >= div_min) &
    (merged["interest_coverage"] >= icr_min)
]

st.write(f"**{len(filtered)} companies match your filters**")

display_cols = ["company_id", "company_name", "sector", "composite_score",
                 "return_on_equity_pct", "debt_to_equity", "free_cash_flow_cr", "revenue_cagr_5yr",
                 "pat_cagr_5yr", "operating_profit_margin_pct", "P/E", "P/B", "dividend_yield_pct", "interest_coverage"]
st.dataframe(filtered[display_cols], use_container_width=True)

csv = filtered[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", csv, "screener_results.csv", "text/csv")