from pathlib import Path
# import sys
import os
import sqlite3
import pandas as pd

# Project root = nifty100
# ROOT = Path(__file__).resolve().parents[2]
# sys.path.insert(0, str(ROOT))

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)

from src.nlp.tearsheet import (
    load_company_data,
    build_tearsheet,
    NAVY
)
# from tearsheet import load_company_data, build_tearsheet, NAVY

styles = getSampleStyleSheet()
MIN_YEARS = 3

# The 8 metrics shown per company in each sector report
SECTOR_METRICS = [
    "net_profit_margin_pct", "return_on_equity_pct", "debt_to_equity",
    "interest_coverage", "revenue_cagr_5yr", "pat_cagr_5yr",
    "eps_cagr_5yr", "capex_intensity_pct",
]


# ============================================================
# JOB 1 — 92 TEARSHEETS
# ============================================================

def batch_generate_tearsheets(conn, out_dir="reports/tearsheets"):
    os.makedirs(out_dir, exist_ok=True)
    companies = pd.read_sql("SELECT id AS company_id FROM companies", conn)

    skipped = []

    for company_id in companies["company_id"]:
        years_available = pd.read_sql(
            "SELECT COUNT(*) AS n FROM profitandloss WHERE company_id = ?",
            conn, params=(company_id,)
        ).iloc[0]["n"]

        if years_available < MIN_YEARS:
            skipped.append({"company_id": company_id, "reason": "insufficient_history", "years_available": years_available})
            continue

        try:
            data = load_company_data(conn, company_id)
            if data is None:
                skipped.append({"company_id": company_id, "reason": "not_found_in_companies_table"})
                continue

            output_path = f"{out_dir}/{company_id}_tearsheet.pdf"
            build_tearsheet(output_path=output_path, **data)

        except Exception as e:
            skipped.append({"company_id": company_id, "reason": f"error: {e}"})

    pd.DataFrame(skipped).to_csv("output/skipped_tearsheets.csv", index=False)
    print(f"Tearsheets: {len(companies) - len(skipped)} built, {len(skipped)} skipped")


# ============================================================
# JOB 2 — 11 SECTOR REPORTS
# ============================================================

def build_sector_report(sector_name, sector_companies_df, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=A4,
                             topMargin=1.2 * cm, bottomMargin=1.2 * cm,
                             leftMargin=1.5 * cm, rightMargin=1.5 * cm)
    story = []

    header_style = ParagraphStyle("header", parent=styles["Title"],
                                   textColor=colors.white, backColor=NAVY, fontSize=16, leading=20)
    story.append(Paragraph(f"Sector Report: {sector_name}", header_style))
    story.append(Spacer(1, 10))

    medians = sector_companies_df[SECTOR_METRICS].median(numeric_only=True)
    median_lines = "<br/>".join(f"{m}: {medians[m]:.2f}" for m in SECTOR_METRICS)
    story.append(Paragraph(f"<b>Sector Median KPIs</b><br/>{median_lines}", styles["Normal"]))
    story.append(Spacer(1, 14))

    story.append(Paragraph("Companies in this sector", styles["Heading2"]))
    header_row = ["Company"] + SECTOR_METRICS
    table_data = [header_row]
    for _, row in sector_companies_df.iterrows():
        table_data.append([row["company_name"]] + [f"{row[m]:.2f}" if pd.notna(row[m]) else "-" for m in SECTOR_METRICS])

    # Paragraph-wrapped cells so long company names / values never overflow the column
    cell_style = ParagraphStyle("scell", parent=styles["Normal"], fontSize=7, wordWrap="CJK")
    wrapped_data = [[Paragraph(str(cell), cell_style) for cell in row] for row in table_data]

    t = Table(wrapped_data, repeatRows=1)
    t.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(t)

    doc.build(story)


def batch_generate_sector_reports(conn, out_dir="reports/sector"):
    os.makedirs(out_dir, exist_ok=True)

    query = """
        SELECT s.broad_sector AS sector, c.company_name, f.*
        FROM sectors s
        JOIN companies c ON c.id = s.company_id
        JOIN financial_ratios f ON f.company_id = s.company_id
        WHERE f.year = (
            SELECT MAX(year) FROM financial_ratios f2 WHERE f2.company_id = f.company_id
        )
    """
    df = pd.read_sql(query, conn)

    for sector_name, group in df.groupby("sector"):
        output_path = f"{out_dir}/{sector_name.replace(' ', '_')}_report.pdf"
        build_sector_report(sector_name, group, output_path)

    print(f"Sector reports: {df['sector'].nunique()} built")


if __name__ == "__main__":
    # from pathlib import Path
    db_path = Path(r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db")
    conn = sqlite3.connect(db_path)
    batch_generate_tearsheets(conn)
    batch_generate_sector_reports(conn)
    conn.close()