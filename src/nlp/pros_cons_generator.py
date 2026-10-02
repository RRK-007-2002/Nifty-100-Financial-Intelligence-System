# src/nlp/pros_cons_generator.py
import pandas as pd
import sqlite3
from pathlib import Path

def load_data(db_path):
    conn = sqlite3.connect(db_path)
    ratios = pd.read_sql("SELECT * FROM financial_ratios", conn)
    cashflow = pd.read_sql("SELECT * FROM cashflow", conn)
    companies = pd.read_sql("SELECT id FROM companies", conn)
    conn.close()
    return ratios, cashflow, companies


# ---- Example PRO rules (pattern to replicate for all 12) ----

def rule_pro_01_high_roe(company_ratios):
    """ROE > 20% sustained for 3+ years."""
    recent = company_ratios.sort_values("year").tail(3)
    if len(recent) < 3:
        return None
    if (recent["return_on_equity_pct"] > 20).all():
        min_roe = recent["return_on_equity_pct"].min()
        confidence = min(100, 60 + (min_roe - 20) * 2)  # further above 20 -> higher confidence
        text = "Consistently high return on equity above 20% demonstrates exceptional capital efficiency"
        return {"confidence_pct": round(confidence), "text": text}
    return None


def rule_pro_03_debt_free(company_ratios):
    """D/E = 0 in latest year."""
    latest = company_ratios.sort_values("year").iloc[-1]
    if latest["debt_to_equity"] == 0:
        return {"confidence_pct": 95, "text": "Debt-free balance sheet provides financial flexibility and eliminates interest burden"}
    return None


# ---- Example CON rules ----

def rule_con_01_high_de(company_ratios):
    """D/E > 2.0 for non-financial companies."""
    latest = company_ratios.sort_values("year").iloc[-1]
    de = latest["debt_to_equity"]
    if de > 2.0:
        confidence = min(100, 60 + (de - 2.0) * 15)
        text = f"Debt-to-equity ratio of {de:.1f} is elevated for a non-financial company and warrants monitoring"
        return {"confidence_pct": round(confidence), "text": text}
    return None


def rule_con_04_net_loss(company_ratios):
    """Net profit negative in latest year."""
    latest = company_ratios.sort_values("year").iloc[-1]
    if latest.get("net_profit", 0) < 0:
        return {"confidence_pct": 100, "text": "Company reported a net loss in the most recent financial year"}
    return None


PRO_RULES = {
    "pro_01": rule_pro_01_high_roe,
    "pro_03": rule_pro_03_debt_free,
    # pro_02, pro_04..pro_12 follow the same (fn, ratios) -> dict|None pattern
}

CON_RULES = {
    "con_01": rule_con_01_high_de,
    "con_04": rule_con_04_net_loss,
    # con_02, con_03, con_05..con_12 follow the same pattern
}


def generate_pros_cons(db_path):
    ratios, cashflow, companies = load_data(db_path)
    rows = []

    for company_id in companies["id"]:
        company_ratios = ratios[ratios["company_id"] == company_id]
        if company_ratios.empty:
            continue

        for rule_id, fn in PRO_RULES.items():
            result = fn(company_ratios)
            if result and result["confidence_pct"] > 60:
                rows.append({"company_id": company_id, "type": "pro", "rule_id": rule_id, **result})

        for rule_id, fn in CON_RULES.items():
            result = fn(company_ratios)
            if result and result["confidence_pct"] > 60:
                rows.append({"company_id": company_id, "type": "con", "rule_id": rule_id, **result})

    output_df = pd.DataFrame(rows)
    output_df.to_csv(r"C:\Users\bhrra\Desktop\nifty100/pros_cons_generated.csv", index=False)

    # sanity check: every company needs >=1 pro and >=1 con
    counts = output_df.groupby(["company_id", "type"]).size().unstack(fill_value=0)
    missing = counts[(counts.get("pro", 0) == 0) | (counts.get("con", 0) == 0)]
    if not missing.empty:
        missing.to_csv(r"C:\Users\bhrra\Desktop\nifty100/pros_cons_missing.csv")
        print(f"WARNING: {len(missing)} companies missing a pro or con — see output/pros_cons_missing.csv")

    return output_df


if __name__ == "__main__":
    db_path = Path(r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db")
    df = generate_pros_cons(db_path)
    print(f"Generated {len(df)} pro/con rows across {df['company_id'].nunique()} companies")
    