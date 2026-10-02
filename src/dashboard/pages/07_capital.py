import streamlit as st
import plotly.express as px
from utils import db

st.title("Capital Allocation Map")

patterns = db.get_capital_patterns()
companies = db.get_companies()
merged = patterns.merge(companies, on="company_id", how="left")
merged["capital_allocation_label"] = merged["capital_allocation_label"].fillna("Unclassified")
merged = merged.dropna(subset=["company_name"])   # ← THIS LINE must be present, before px.treemap

fig = px.treemap(merged, path=["capital_allocation_label", "company_name"],
                  title="Capital Allocation Patterns — 92 Companies")
st.plotly_chart(fig, use_container_width=True)

pattern_choice = st.selectbox("Or pick a pattern directly", merged["capital_allocation_label"].unique())
st.dataframe(merged[merged["capital_allocation_label"] == pattern_choice][["company_id", "company_name"]],
             use_container_width=True)

# import streamlit as st
# import plotly.express as px
# from utils import db

# st.title("Capital Allocation Map")

# patterns = db.get_capital_patterns()
# companies = db.get_companies()
# merged = patterns.merge(companies, on="company_id", how="left")
# merged["capital_allocation_label"] = merged["capital_allocation_label"].fillna("Unclassified")

# fig = px.treemap(merged, path=["capital_allocation_label", "company_name"],
#                   title="Capital Allocation Patterns — 92 Companies")
# st.plotly_chart(fig, use_container_width=True)

# pattern_choice = st.selectbox("Or pick a pattern directly", merged["capital_allocation_label"].unique())
# st.dataframe(merged[merged["capital_allocation_label"] == pattern_choice][["company_id", "company_name"]],
#              use_container_width=True)


# patterns = db.get_capital_patterns()
# companies = db.get_companies()
# merged = patterns.merge(companies, on="company_id", how="left")
# merged["capital_allocation_label"] = merged["capital_allocation_label"].fillna("Unclassified")

# # NEW — drop rows with missing company_name; these can't be valid treemap leaves
# merged = merged.dropna(subset=["company_name"])

# fig = px.treemap(merged, path=["capital_allocation_label", "company_name"],
#                   title="Capital Allocation Patterns — 92 Companies")
# st.plotly_chart(fig, use_container_width=True)

# pattern_choice = st.selectbox("Or pick a pattern directly", merged["capital_allocation_label"].unique())
# st.dataframe(merged[merged["capital_allocation_label"] == pattern_choice][["company_id", "company_name"]],
#              use_container_width=True)