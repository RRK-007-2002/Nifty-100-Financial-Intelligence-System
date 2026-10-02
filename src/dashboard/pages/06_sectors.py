import streamlit as st
import pandas as pd
import plotly.express as px
from utils import db

st.title("Sector Analysis")

sectors = db.get_sectors()
selected_sector = st.selectbox("Sector", sectors["sector_name"])

companies = db.get_companies()
sector_companies = companies[companies["sector"] == selected_sector]

ratios = db.get_all_latest_ratios()
# valuation = db.get_all_valuation()
market_cap = db.get_all_latest_market_cap()
pl_rows = pd.concat([db.get_pl(cid).tail(1) for cid in sector_companies["company_id"]], ignore_index=True)

merged = sector_companies.merge(ratios, on="company_id", how="left")
merged = merged.merge(market_cap[["company_id", "market_cap_crore"]], on="company_id", how="left")  # CHANGED
merged = merged.merge(pl_rows[["company_id", "sales"]], on="company_id", how="left")

fig_bubble = px.scatter(
    merged, x="sales", y="return_on_equity_pct",
    size="market_cap_crore", color="sub_sector",
    hover_name="company_name", title=f"{selected_sector} — Revenue vs ROE"
)
st.plotly_chart(fig_bubble, use_container_width=True)

median_kpis = merged[["return_on_equity_pct", "debt_to_equity", "operating_profit_margin_pct"]].median()
fig_bar = px.bar(x=median_kpis.index, y=median_kpis.values, title=f"{selected_sector} Median KPIs")
st.plotly_chart(fig_bar, use_container_width=True)