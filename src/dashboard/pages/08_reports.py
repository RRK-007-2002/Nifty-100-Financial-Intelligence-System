import streamlit as st
import requests
from utils import db

st.title("Annual Reports")

companies = db.get_companies()
choice = st.selectbox("Company", companies["company_id"] + " — " + companies["company_name"], index=None)
if choice is None:
    st.stop()
company_id = choice.split(" — ")[0]

docs = db.get_documents(company_id)
if docs.empty:
    st.info("No annual reports found for this company.")
    st.stop()

for _, row in docs.sort_values("year", ascending=False).iterrows():
    try:
        resp = requests.head(row["pdf_url"], timeout=5)
        if resp.status_code == 404:
            st.markdown(f"{row['year']} — :red_badge[Report unavailable]")
        else:
            st.markdown(f"[{row['year']} Annual Report]({row['pdf_url']})")
    except requests.RequestException:
        st.markdown(f"{row['year']} — :red_badge[Report unavailable]")