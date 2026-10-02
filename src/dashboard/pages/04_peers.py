import streamlit as st
import pandas as pd
from utils import db

st.title("Peer Comparison")

group_names = db.get_peer_group_names()["peer_group_name"].tolist()
selected_group = st.selectbox("Peer group", group_names)
peers = db.get_peers(selected_group)  # company_id, company_name, is_benchmark

ratios = db.get_all_latest_ratios()
companies = db.get_companies()

peers_full = peers.merge(ratios, on="company_id", how="left").merge(
    companies[["company_id", "roce_percentage"]], on="company_id", how="left"
)

default_benchmark = peers_full.loc[peers_full["is_benchmark"] == 1, "company_id"]
default_idx = int(peers_full.index[peers_full["company_id"] == default_benchmark.iloc[0]][0]) if not default_benchmark.empty else 0
benchmark_company = st.selectbox("Benchmark company", peers_full["company_id"], index=default_idx)

metrics = ["return_on_equity_pct", "roce_percentage", "debt_to_equity", "net_profit_margin_pct",
           "operating_profit_margin_pct", "revenue_cagr_5yr", "pat_cagr_5yr", "interest_coverage"]

peer_avg = peers_full[metrics].mean()
bench_row = peers_full[peers_full["company_id"] == benchmark_company][metrics].iloc[0]

import plotly.graph_objects as go
fig = go.Figure()
fig.add_trace(go.Scatterpolar(r=bench_row.values, theta=metrics, fill="toself", name=benchmark_company))
fig.add_trace(go.Scatterpolar(r=peer_avg.values, theta=metrics, fill="toself", name="Peer Group Avg"))
fig.update_layout(title=f"{benchmark_company} vs {selected_group} Average")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Peer Group KPI Table")
display = peers_full[["company_id", "company_name"] + metrics]

def highlight_benchmark(row):
    return ["background-color: #b0ffe5" if row["company_id"] == benchmark_company else "" for _ in row]

st.dataframe(display.style.apply(highlight_benchmark, axis=1), use_container_width=True)