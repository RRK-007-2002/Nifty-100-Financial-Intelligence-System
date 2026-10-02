import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import db

st.title("Company Profile")

companies = db.get_companies()
options = companies["company_id"] + " — " + companies["company_name"]
choice = st.selectbox("Company Name ", options, index=None, placeholder="Type to search...")
if choice is None:
    st.stop()

company_id = choice.split(" — ")[0]
row = companies[companies["company_id"] == company_id]
if row.empty:
    st.warning("Ticker not found — please try another")
    st.stop()
row = row.iloc[0]

st.subheader(f"{row['company_name']} ({company_id})")
st.caption(f"{row.get('sector', 'N/A')} · {row.get('sub_sector', 'N/A')}")
st.write(row.get("about_company", "No description available."))

ratios = db.get_ratios(company_id)
if ratios.empty:
    st.warning("No ratio data available for this company.")
    st.stop()

latest = ratios.sort_values("year").iloc[-1]

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("ROE", "N/A" if pd.isna(latest.get("return_on_equity_pct")) else f"{latest['return_on_equity_pct']:.1f}%")
c2.metric("ROCE", "N/A" if pd.isna(row.get("roce_percentage")) else f"{row['roce_percentage']:.1f}%")
c3.metric("Net Profit Margin", "N/A" if pd.isna(latest.get("net_profit_margin_pct")) else f"{latest['net_profit_margin_pct']:.1f}%")
c4.metric("D/E", "N/A" if pd.isna(latest.get("debt_to_equity")) else round(latest["debt_to_equity"], 2))
c5.metric("Revenue CAGR 5yr", "N/A" if pd.isna(latest.get("revenue_cagr_5yr")) else f"{latest['revenue_cagr_5yr']:.1f}%")
c6.metric("FCF (₹cr)", "N/A" if pd.isna(latest.get("free_cash_flow_cr")) else round(latest["free_cash_flow_cr"], 1))

pl = db.get_pl(company_id)
if not pl.empty:
    fig_bar = go.Figure()
    fig_bar.add_bar(x=pl["year"], y=pl["sales"], name="Revenue")
    fig_bar.add_bar(x=pl["year"], y=pl["net_profit"], name="Net Profit")
    fig_bar.update_layout(barmode="group", title="Revenue & Net Profit")
    st.plotly_chart(fig_bar, use_container_width=True)
else:
    st.info("P&L data not available for this company.")

# ROCE has only ONE static value per company (companies.roce_percentage) — no year-wise
# history exists in financial_ratios, so a true 10-year ROCE trend isn't possible currently.
if not ratios.empty:
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=ratios["year"], y=ratios["return_on_equity_pct"], name="ROE"))
    fig_line.update_layout(title="ROE Trend (ROCE has no year-wise history in current schema)")
    st.plotly_chart(fig_line, use_container_width=True)

pc = db.get_pros_cons(company_id)
st.subheader("Pros & Cons")
pcol1, pcol2 = st.columns(2)
if not pc.empty:
    pros_text = pc.iloc[0]["pros"] or ""
    cons_text = pc.iloc[0]["cons"] or ""
    for line in [p.strip() for p in pros_text.split("\n") if p.strip()]:
        pcol1.success(f"✅ {line}")
    for line in [c.strip() for c in cons_text.split("\n") if c.strip()]:
        pcol2.error(f"❌ {line}")
else:
    st.info("No pros/cons data available.")