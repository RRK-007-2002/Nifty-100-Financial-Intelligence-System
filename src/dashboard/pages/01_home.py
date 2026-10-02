import streamlit as st
import pandas as pd
import plotly.express as px
from utils import db

st.title("Home")

year = st.sidebar.selectbox("Year", options=[str(y) for y in range(2024, 2018, -1)], index=0)
# VERIFY: financial_ratios.year format — confirm it's plain "2024", not "Mar 2024" etc.

ratios_year = db.get_ratios_for_year(year)
companies = db.get_companies()
valuation_all = db.get_all_valuation()
# Median P/E always reflects the LATEST year — valuation table has no year-wise history,
# so it does not respond to the year selector above.

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Average ROE", f"{ratios_year['return_on_equity_pct'].mean():.1f}%" if not ratios_year.empty else "N/A")
c2.metric("Median P/E", f"{valuation_all['P/E'].median():.1f}" if not valuation_all.empty else "N/A")
c3.metric("Median D/E", f"{ratios_year['debt_to_equity'].median():.2f}" if not ratios_year.empty else "N/A")
c4.metric("Total Companies", len(companies))
c5.metric("Median Revenue CAGR 5yr", f"{ratios_year['revenue_cagr_5yr'].median():.1f}%" if not ratios_year.empty else "N/A")
c6.metric("Debt-Free Companies", int((ratios_year['debt_to_equity'] == 0).sum()) if not ratios_year.empty else 0)

sectors = db.get_sectors()
fig_donut = px.pie(sectors, names="sector_name", values="company_count", hole=0.5, title="Sector Breakdown")
st.plotly_chart(fig_donut, use_container_width=True)

scores = db.get_composite_scores()
top5 = scores.merge(companies, on="company_id").sort_values("composite_score", ascending=False).head(5)
st.subheader("Top 5 Companies by Quality Score")
st.dataframe(top5[["company_id", "company_name", "composite_score"]], use_container_width=True)