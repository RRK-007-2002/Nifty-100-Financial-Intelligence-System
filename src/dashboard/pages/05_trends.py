import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils import db

st.title("Trend Analysis")

companies = db.get_companies()
choice = st.selectbox("Company", companies["company_id"] + " — " + companies["company_name"], index=None)
if choice is None:
    st.stop()
company_id = choice.split(" — ")[0]

metric_options = ["return_on_equity_pct", "debt_to_equity", "net_profit_margin_pct",
                   "operating_profit_margin_pct", "revenue_cagr_5yr", "interest_coverage"]
selected_metrics = st.multiselect("Metrics (max 3)", metric_options, max_selections=3)

ratios = db.get_ratios(company_id)
if ratios.empty or not selected_metrics:
    st.info("Select at least one metric.")
    st.stop()

fig = go.Figure()
for m in selected_metrics:
    yoy = ratios[m].pct_change() * 100
    fig.add_trace(go.Scatter(
        x=ratios["year"], y=ratios[m], name=m, mode="lines+markers+text",
        text=[f"{v:+.1f}%" if pd.notna(v) else "" for v in yoy],
        textposition="top center",
    ))
fig.update_layout(title=f"{company_id} — Trend with YoY %")
st.plotly_chart(fig, use_container_width=True)