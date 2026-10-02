import io
import sqlite3
import matplotlib

# No GUI backend needed
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
    PageBreak
)


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

NAVY = colors.HexColor("#1a2744")
GREEN = colors.HexColor("#0a7d3e")
RED = colors.HexColor("#b3261e")

pro_style = ParagraphStyle(
    "pro", parent=styles["Normal"], textColor=GREEN, leftIndent=10
)
con_style = ParagraphStyle(
    "con", parent=styles["Normal"], textColor=RED, leftIndent=10
)
cell_style = ParagraphStyle(
    "cell", parent=styles["Normal"], fontSize=9, wordWrap="CJK"
)


# ============================================================
# KPI TILE TABLE  (unchanged — already correct)
# ============================================================

def make_kpi_tile_table(kpi_dict):
    """6 KPI tiles arranged in 2 rows x 3 columns."""
    items = list(kpi_dict.items())
    rows = [items[i:i + 3] for i in range(0, len(items), 3)]
    table_data = []
    for row in rows:
        table_data.append([
            Paragraph(f"<b>{label}</b><br/>{value}", cell_style)
            for label, value in row
        ])

    table = Table(table_data, colWidths=[5.5 * cm] * 3)
    table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f2f4f8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return table


# ============================================================
# REVENUE VS PROFIT CHART  (unchanged — sales/net_profit are real columns)
# ============================================================

def make_revenue_profit_chart(history_df):
    """10-year Revenue vs Net Profit bar chart. Expects: year, sales, net_profit."""
    fig, ax = plt.subplots(figsize=(5, 2.8))
    x = history_df["year"]
    width = 0.35
    positions = range(len(x))

    ax.bar([p - width / 2 for p in positions], history_df["sales"], width, label="Revenue")
    ax.bar([p + width / 2 for p in positions], history_df["net_profit"], width, label="Net Profit")
    ax.set_xticks(list(positions))
    ax.set_xticklabels(x, rotation=45, fontsize=7)
    ax.legend(fontsize=7)
    ax.set_title("Revenue vs Net Profit (10Y)", fontsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=12 * cm, height=6.5 * cm)


# ============================================================
# ROE VS ROCE CHART  (FIXED — real column is return_on_equity_pct;
# ROCE has NO per-year history anywhere in the schema, only a single
# current snapshot in companies.roce_percentage. Plotting that as a
# flat reference line rather than fabricating a fake trend.)
# ============================================================

def make_roe_roce_chart(ratios_df, roce_snapshot=None):
    """
    ROE line (real history) + ROCE flat reference line (snapshot only —
    no ROCE time series exists in the DB).

    Expects ratios_df columns: year, return_on_equity_pct
    roce_snapshot: single float from companies.roce_percentage, or None
    """
    fig, ax1 = plt.subplots(figsize=(5, 2.8))
    ax2 = ax1.twinx()

    ax1.plot(ratios_df["year"], ratios_df["return_on_equity_pct"], marker="o", label="ROE")
    ax1.set_ylabel("ROE %", fontsize=8)

    if roce_snapshot is not None:
        ax2.axhline(roce_snapshot, color="#c9622a", linestyle="--", label="ROCE (latest, snapshot only)")
        ax2.set_ylabel("ROCE % (snapshot)", fontsize=8)

    ax1.set_title("ROE (history) vs ROCE (latest snapshot)", fontsize=9)
    ax1.tick_params(axis="x", rotation=45, labelsize=7)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=12 * cm, height=6.5 * cm)


# ============================================================
# BALANCE SHEET CHART  (FIXED — equity computed from
# equity_capital + reserves, since no combined "equity" column exists)
# ============================================================

def make_balance_sheet_chart(balance_df):
    """
    Stacked bar: Equity (= equity_capital + reserves), Borrowings, Other Liabilities.
    Expects columns: year, equity_capital, reserves, borrowings, other_liabilities
    """
    fig, ax = plt.subplots(figsize=(5, 2.8))
    years = balance_df["year"]
    equity = balance_df["equity_capital"] + balance_df["reserves"]

    ax.bar(years, equity, label="Equity")
    ax.bar(years, balance_df["borrowings"], bottom=equity, label="Borrowings")
    bottom2 = equity + balance_df["borrowings"]
    ax.bar(years, balance_df["other_liabilities"], bottom=bottom2, label="Other Liabilities")

    ax.set_xticks(years)
    ax.set_xticklabels(years, rotation=45, fontsize=7)
    ax.legend(fontsize=7)
    ax.set_title("Balance Sheet Composition", fontsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=12 * cm, height=6.5 * cm)


# ============================================================
# CASH FLOW CHART  (FIXED — real column names are operating_activity /
# investing_activity / financing_activity, not cfo/cfi/cff)
# ============================================================

def make_cashflow_waterfall(operating_activity, investing_activity, financing_activity):
    """Cash-flow bar chart for latest year. Net CF = sum of the three."""
    net = operating_activity + investing_activity + financing_activity
    labels = ["CFO", "CFI", "CFF", "Net CF"]
    values = [operating_activity, investing_activity, financing_activity, net]
    bar_colors = ["#2b5fad" if v >= 0 else "#b3261e" for v in values]

    fig, ax = plt.subplots(figsize=(5, 2.8))
    ax.bar(labels, values, color=bar_colors)
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_title("Cash Flow Summary (Latest Year)", fontsize=9)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return Image(buf, width=12 * cm, height=6.5 * cm)


# ============================================================
# BUILD TEARSHEET
# ============================================================

def build_tearsheet(
    company_id, company_name, ticker, kpis,
    history_df, ratios_df, balance_df, cashflow_row,
    pros, cons, capital_label, roce_snapshot, output_path
):
    """
    Build a 2-page company tearsheet PDF.

    cashflow_row: dict with keys operating_activity, investing_activity, financing_activity
    roce_snapshot: single float (companies.roce_percentage) or None
    """
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm
    )
    story = []

    # --- PAGE 1 ---
    header_style = ParagraphStyle(
        "header", parent=styles["Title"], textColor=colors.white,
        backColor=NAVY, alignment=0, fontSize=16, leading=20
    )
    story.append(Paragraph(f"{company_name} ({ticker})", header_style))
    story.append(Spacer(1, 12))
    story.append(make_kpi_tile_table(kpis))
    story.append(Spacer(1, 12))

    if not history_df.empty:
        story.append(make_revenue_profit_chart(history_df))
    story.append(Spacer(1, 8))

    if not ratios_df.empty:
        story.append(make_roe_roce_chart(ratios_df, roce_snapshot))

    story.append(PageBreak())

    # --- PAGE 2 ---
    story.append(Paragraph("Balance Sheet Composition", styles["Heading2"]))
    if not balance_df.empty:
        story.append(make_balance_sheet_chart(balance_df))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Cash Flow Summary (Latest Year)", styles["Heading2"]))
    if cashflow_row:
        story.append(make_cashflow_waterfall(
            cashflow_row.get("operating_activity", 0),
            cashflow_row.get("investing_activity", 0),
            cashflow_row.get("financing_activity", 0),
        ))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Pros", styles["Heading2"]))
    for p in pros:
        story.append(Paragraph(f"\u2022 {p}", pro_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Cons", styles["Heading2"]))
    for c in cons:
        story.append(Paragraph(f"\u2022 {c}", con_style))
    story.append(Spacer(1, 10))

    story.append(Paragraph(f"Capital Allocation: <b>{capital_label}</b>", styles["Normal"]))

    doc.build(story)


# ============================================================
# REAL DATA WIRING FOR 5-COMPANY TEST
# ============================================================

def load_company_data(conn, company_id):
    """Pull everything build_tearsheet needs for one company_id (== ticker, per company_id convention)."""

    company_row = pd.read_sql(
        "SELECT id, company_name, roce_percentage FROM companies WHERE id = ?",
        conn, params=(company_id,)
    )
    if company_row.empty:
        return None
    company_name = company_row.iloc[0]["company_name"]
    roce_snapshot = company_row.iloc[0]["roce_percentage"]

    history_df = pd.read_sql(
        "SELECT year, sales, net_profit FROM profitandloss WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    ).tail(10)

    ratios_df = pd.read_sql(
        "SELECT year, return_on_equity_pct, net_profit_margin_pct, debt_to_equity, "
        "interest_coverage, revenue_cagr_5yr, capex_intensity_pct, capital_allocation_label "
        "FROM financial_ratios WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )

    balance_df = pd.read_sql(
        "SELECT year, equity_capital, reserves, borrowings, other_liabilities "
        "FROM balancesheet WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    ).tail(10)

    cashflow_df = pd.read_sql(
        "SELECT year, operating_activity, investing_activity, financing_activity "
        "FROM cashflow WHERE company_id = ? ORDER BY year",
        conn, params=(company_id,)
    )
    cashflow_row = cashflow_df.iloc[-1].to_dict() if not cashflow_df.empty else {}

    # pros/cons: single TEXT field, assumed newline- or semicolon-separated.
    # VERIFY this against your real data — this is a guess.
    pc_row = pd.read_sql(
        "SELECT pros, cons FROM prosandcons WHERE company_id = ?",
        conn, params=(company_id,)
    )
    pros, cons = [], []
    if not pc_row.empty:
        raw_pros = pc_row.iloc[0]["pros"] or ""
        raw_cons = pc_row.iloc[0]["cons"] or ""
        pros = [p.strip() for p in raw_pros.replace(";", "\n").split("\n") if p.strip()]
        cons = [c.strip() for c in raw_cons.replace(";", "\n").split("\n") if c.strip()]

    latest_ratios = ratios_df.iloc[-1] if not ratios_df.empty else None
    capital_label = latest_ratios["capital_allocation_label"] if latest_ratios is not None else "Unknown"

    kpis = {}
    if latest_ratios is not None:
        kpis = {
            "Net Profit Margin": f"{latest_ratios['net_profit_margin_pct']:.1f}%",
            "ROE": f"{latest_ratios['return_on_equity_pct']:.1f}%",
            "Debt/Equity": f"{latest_ratios['debt_to_equity']:.2f}",
            "Interest Coverage": f"{latest_ratios['interest_coverage']:.1f}x",
            "Revenue CAGR (5yr)": f"{latest_ratios['revenue_cagr_5yr']:.1f}%",
            "CapEx Intensity": f"{latest_ratios['capex_intensity_pct']:.1f}%",
        }

    return dict(
        company_id=company_id, company_name=company_name, ticker=company_id,
        kpis=kpis, history_df=history_df, ratios_df=ratios_df.drop(columns=["capital_allocation_label"], errors="ignore"),
        balance_df=balance_df, cashflow_row=cashflow_row, pros=pros, cons=cons,
        capital_label=capital_label, roce_snapshot=roce_snapshot,
    )


if __name__ == "__main__":
    import os
    from pathlib import Path
    db_path = Path(r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db")
    os.makedirs(f"C:/Users/bhrra/Desktop/nifty100/reports/tearsheets", exist_ok=True)

    test_tickers = ["TCS", "HDFCBANK", "RELIANCE", "SUNPHARMA", "TATASTEEL"]
    conn = sqlite3.connect(db_path)

    for ticker in test_tickers:
        data = load_company_data(conn, ticker)
        if data is None:
            print(f"SKIPPED {ticker}: no matching row in companies table (check id/ticker assumption)")
            continue

        output_path = f"C:/Users/bhrra/Desktop/nifty100/reports/tearsheets/{ticker}_tearsheet.pdf"
        build_tearsheet(output_path=output_path, **data)
        print(f"Built {output_path}")

    conn.close()