# # from pathlib import Path
# # import sys

# # # Project root = nifty100
# # ROOT = Path(__file__).resolve().parents[2]
# # sys.path.insert(0, str(ROOT))
# # import sqlite3

# # import pandas as pd
# # from reportlab.lib.pagesizes import A4
# # from reportlab.lib.units import cm
# # from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# # from reportlab.lib import colors
# # from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
# # from src.nlp.tearsheet import make_kpi_tile_table, NAVY

# # styles = getSampleStyleSheet()

# # UP_ARROW, DOWN_ARROW, FLAT_ARROW = "\u2191", "\u2193", "\u2192"
# # FLAT_BAND_PCT = 2.0

# # # Only genuinely numeric fields get a trend arrow.
# # NUMERIC_KPI_FIELDS = [
# #     "cfo_quality_score", "capex_intensity_pct", "fcf_cagr_5yr", "fcf_conversion_pct",
# # ]
# # # Booleans shown as plain Yes/No badges — a "% change" on True/False isn't meaningful
# # FLAG_FIELDS = ["distress_flag", "deleveraging_flag"]


# # def trend_arrow(latest, previous):
# #     if previous is None or pd.isna(previous) or previous == 0:
# #         return FLAT_ARROW
# #     pct_change = (latest - previous) / abs(previous) * 100
# #     if abs(pct_change) <= FLAT_BAND_PCT:
# #         return FLAT_ARROW
# #     return UP_ARROW if pct_change > 0 else DOWN_ARROW


# # def build_company_summary_page(company_row, prev_year_row):
# #     story = []
# #     header_style = ParagraphStyle("header", parent=styles["Title"],
# #                                    textColor=colors.white, backColor=NAVY,
# #                                    fontSize=14, leading=18)
# #     story.append(Paragraph(
# #         f"{company_row['company_name']} ({company_row['company_id']}) — {company_row['sector']}",
# #         header_style
# #     ))
# #     story.append(Spacer(1, 10))

# #     kpis = {}
# #     for field in NUMERIC_KPI_FIELDS:
# #         latest_val = company_row.get(field)
# #         prev_val = prev_year_row.get(field) if prev_year_row is not None else None
# #         arrow = trend_arrow(latest_val, prev_val) if pd.notna(latest_val) else ""
# #         display_val = f"{latest_val:.2f}" if pd.notna(latest_val) else "N/A"
# #         kpis[field.replace("_", " ").title()] = f"{display_val} {arrow}"

# #     for field in FLAG_FIELDS:
# #         val = company_row.get(field)
# #         kpis[field.replace("_", " ").title()] = "Yes" if val else "No"

# #     story.append(make_kpi_tile_table(kpis))
# #     story.append(PageBreak())
# #     return story


# # def build_portfolio_summary(db_path, cashflow_intel_path, prev_year_intel_path=None,
# #                              output_path="reports/portfolio/portfolio_summary.pdf"):
# #     """
# #     cashflow_intel_path: current output/cashflow_intelligence.xlsx (Day 31)
# #     prev_year_intel_path: an OLD copy of the same-shaped cashflow_intelligence.xlsx
# #                            (not the raw cashflow.csv — different schema, won't align)
# #     """
# #     conn = sqlite3.connect(db_path)
# #     companies = pd.read_sql(
# #         "SELECT c.id AS company_id, c.company_name, s.broad_sector AS sector "
# #         "FROM companies c LEFT JOIN sectors s ON s.company_id = c.id",
# #         conn
# #     )
# #     conn.close()

# #     current = pd.read_excel(cashflow_intel_path)
# #     # cashflow_intelligence.xlsx has no company_name/ticker — join them in from the DB
# #     current = current.drop(columns=["sector"], errors="ignore").merge(companies, on="company_id", how="left")
# #     current = current.sort_values("company_id")  # alphabetical by ticker == company_id

# #     previous = None
# #     if prev_year_intel_path:
# #         try:
# #             previous = pd.read_excel(prev_year_intel_path).set_index("company_id")
# #         except FileNotFoundError:
# #             print(f"No prior-year file found at {prev_year_intel_path} — all arrows will show flat")

# #     doc = SimpleDocTemplate(output_path, pagesize=A4,
# #                              topMargin=1.2 * cm, bottomMargin=1.2 * cm,
# #                              leftMargin=1.5 * cm, rightMargin=1.5 * cm)
# #     story = []
# #     for _, row in current.iterrows():
# #         prev_row = (previous.loc[row["company_id"]].to_dict()
# #                     if previous is not None and row["company_id"] in previous.index else None)
# #         story.extend(build_company_summary_page(row, prev_row))

# #     doc.build(story)
# #     print(f"Portfolio summary generated: {output_path} ({len(current)} pages)")


# # if __name__ == "__main__":
# #     build_portfolio_summary(
# #         db_path=r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db",
# #         cashflow_intel_path=r"C:\Users\bhrra\Desktop\nifty100\output\cashflow_intelligence.xlsx",
# #         prev_year_intel_path=None,  # set this to an OLD saved copy of cashflow_intelligence.xlsx if you have one
# #     )

# from pathlib import Path
# import sys
# import sqlite3
# import pandas as pd

# # ============================================================
# # PROJECT ROOT
# # ============================================================

# ROOT = Path(__file__).resolve().parents[2]
# sys.path.insert(0, str(ROOT))

# from reportlab.lib.pagesizes import A4
# from reportlab.lib.units import cm
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
# from reportlab.platypus import (
#     SimpleDocTemplate,
#     Paragraph,
#     Spacer,
#     PageBreak,
# )

# from src.nlp.tearsheet import make_kpi_tile_table, NAVY


# styles = getSampleStyleSheet()

# UP_ARROW = "\u2191"
# DOWN_ARROW = "\u2193"
# FLAT_ARROW = "\u2192"

# FLAT_BAND_PCT = 2.0


# # ============================================================
# # KPI FIELDS — THESE EXIST IN financial_ratios TABLE
# # ============================================================

# NUMERIC_KPI_FIELDS = [
#     "net_profit_margin_pct",
#     "return_on_equity_pct",
#     "debt_to_equity",
#     "interest_coverage",
#     "free_cash_flow_cr",
#     "cash_from_operations_cr",
#     "revenue_cagr_5yr",
#     "pat_cagr_5yr",
# ]


# # ============================================================
# # CATEGORICAL FIELDS — THESE EXIST IN financial_ratios TABLE
# # ============================================================

# FLAG_FIELDS = [
#     "icr_label",
#     "capital_allocation_label",
# ]


# # ============================================================
# # TREND ARROW
# # ============================================================

# def trend_arrow(latest, previous):

#     if (
#         previous is None
#         or pd.isna(previous)
#         or previous == 0
#         or pd.isna(latest)
#     ):
#         return FLAT_ARROW

#     pct_change = (latest - previous) / abs(previous) * 100

#     if abs(pct_change) <= FLAT_BAND_PCT:
#         return FLAT_ARROW

#     return UP_ARROW if pct_change > 0 else DOWN_ARROW


# # ============================================================
# # COMPANY SUMMARY PAGE
# # ============================================================

# def build_company_summary_page(company_row, prev_year_row):

#     story = []

#     header_style = ParagraphStyle(
#         "header",
#         parent=styles["Title"],
#         textColor=colors.white,
#         backColor=NAVY,
#         fontSize=14,
#         leading=18,
#     )

#     story.append(
#         Paragraph(
#             f"{company_row['company_name']} "
#             f"({company_row['company_id']}) — "
#             f"{company_row['sector']}",
#             header_style,
#         )
#     )

#     story.append(Spacer(1, 10))

#     # --------------------------------------------------------
#     # Numeric KPIs
#     # --------------------------------------------------------

#     kpis = {}

#     for field in NUMERIC_KPI_FIELDS:

#         latest_val = company_row.get(field)

#         prev_val = (
#             prev_year_row.get(field)
#             if prev_year_row is not None
#             else None
#         )

#         if pd.notna(latest_val):

#             arrow = trend_arrow(latest_val, prev_val)

#             display_val = f"{latest_val:.2f}"

#             kpis[
#                 field.replace("_", " ").title()
#             ] = f"{display_val} {arrow}"

#         else:

#             kpis[
#                 field.replace("_", " ").title()
#             ] = "N/A"

#     # --------------------------------------------------------
#     # Categorical fields
#     # --------------------------------------------------------

#     for field in FLAG_FIELDS:

#         val = company_row.get(field)

#         if pd.notna(val) and str(val).strip():

#             kpis[
#                 field.replace("_", " ").title()
#             ] = str(val)

#         else:

#             kpis[
#                 field.replace("_", " ").title()
#             ] = "N/A"

#     # --------------------------------------------------------
#     # KPI TABLE
#     # --------------------------------------------------------

#     story.append(make_kpi_tile_table(kpis))

#     story.append(PageBreak())

#     return story


# # ============================================================
# # PORTFOLIO SUMMARY
# # ============================================================

# def build_portfolio_summary(
#     db_path,
#     output_path="reports/portfolio/portfolio_summary.pdf",
# ):

#     conn = sqlite3.connect(db_path)

#     # --------------------------------------------------------
#     # Get latest financial_ratios row for every company
#     # --------------------------------------------------------

#     query = """
#         SELECT
#             c.id AS company_id,
#             c.company_name,
#             s.broad_sector AS sector,

#             f.year,

#             f.net_profit_margin_pct,
#             f.return_on_equity_pct,
#             f.debt_to_equity,
#             f.interest_coverage,
#             f.free_cash_flow_cr,
#             f.cash_from_operations_cr,
#             f.revenue_cagr_5yr,
#             f.pat_cagr_5yr,

#             f.icr_label,
#             f.capital_allocation_label

#         FROM companies c

#         LEFT JOIN sectors s
#             ON s.company_id = c.id

#         JOIN financial_ratios f
#             ON f.company_id = c.id

#         WHERE f.year = (
#             SELECT MAX(f2.year)
#             FROM financial_ratios f2
#             WHERE f2.company_id = f.company_id
#         )

#         ORDER BY c.id
#     """

#     current = pd.read_sql(query, conn)

#     # --------------------------------------------------------
#     # Get previous-year financial ratios
#     # --------------------------------------------------------

#     previous_query = """
#         SELECT
#             company_id,
#             year,

#             net_profit_margin_pct,
#             return_on_equity_pct,
#             debt_to_equity,
#             interest_coverage,
#             free_cash_flow_cr,
#             cash_from_operations_cr,
#             revenue_cagr_5yr,
#             pat_cagr_5yr

#         FROM financial_ratios
#     """

#     previous_all = pd.read_sql(previous_query, conn)

#     conn.close()

#     # --------------------------------------------------------
#     # Create output directory
#     # --------------------------------------------------------

#     output_path = Path(output_path)

#     if not output_path.is_absolute():
#         output_path = ROOT / output_path

#     output_path.parent.mkdir(
#         parents=True,
#         exist_ok=True,
#     )

#     # --------------------------------------------------------
#     # Build previous-year lookup
#     # --------------------------------------------------------

#     previous = {}

#     for company_id, group in previous_all.groupby("company_id"):

#         group = group.sort_values("year")

#         if len(group) >= 2:

#             previous_year = group.iloc[-2]

#             previous[company_id] = previous_year.to_dict()

#     # --------------------------------------------------------
#     # Build PDF
#     # --------------------------------------------------------

#     doc = SimpleDocTemplate(
#         str(output_path),
#         pagesize=A4,
#         topMargin=1.2 * cm,
#         bottomMargin=1.2 * cm,
#         leftMargin=1.5 * cm,
#         rightMargin=1.5 * cm,
#     )

#     story = []

#     for _, row in current.iterrows():

#         company_id = row["company_id"]

#         prev_row = previous.get(company_id)

#         story.extend(
#             build_company_summary_page(
#                 row,
#                 prev_row,
#             )
#         )

#     doc.build(story)

#     print(
#         f"Portfolio summary generated: "
#         f"{output_path} "
#         f"({len(current)} pages)"
#     )


# # ============================================================
# # MAIN
# # ============================================================

# if __name__ == "__main__":

#     db_path = ROOT / "db" / "nifty100.db"

#     build_portfolio_summary(
#         db_path=db_path,
#         output_path="reports/portfolio/portfolio_summary.pdf",
#     )

# =====================         ================================================

from pathlib import Path
import sys
import sqlite3

import pandas as pd

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
)

# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.nlp.tearsheet import make_kpi_tile_table, NAVY


# ============================================================
# STYLES
# ============================================================

styles = getSampleStyleSheet()

UP_ARROW = "\u2191"
DOWN_ARROW = "\u2193"
FLAT_ARROW = "\u2192"

FLAT_BAND_PCT = 2.0


# ============================================================
# KPI FIELDS
# ============================================================

NUMERIC_KPI_FIELDS = [
    "net_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "free_cash_flow_cr",
    "cash_from_operations_cr",
    "revenue_cagr_5yr",
    "pat_cagr_5yr",
]


FLAG_FIELDS = [
    "icr_label",
    "capital_allocation_label",
]


# ============================================================
# TREND ARROW
# ============================================================

def trend_arrow(latest, previous):

    if (
        previous is None
        or pd.isna(previous)
        or previous == 0
        or pd.isna(latest)
    ):
        return FLAT_ARROW

    pct_change = (latest - previous) / abs(previous) * 100

    if abs(pct_change) <= FLAT_BAND_PCT:
        return FLAT_ARROW

    return UP_ARROW if pct_change > 0 else DOWN_ARROW


# ============================================================
# COMPANY SUMMARY PAGE
# ============================================================

def build_company_summary_page(company_row, prev_year_row):

    story = []

    header_style = ParagraphStyle(
        "header",
        parent=styles["Title"],
        textColor=colors.white,
        backColor=NAVY,
        fontSize=14,
        leading=18,
        spaceAfter=0,
    )

    # --------------------------------------------------------
    # HEADER
    # --------------------------------------------------------

    company_name = company_row.get("company_name", "Unknown Company")
    company_id = company_row.get("company_id", "N/A")
    sector = company_row.get("sector", "N/A")

    if pd.isna(sector):
        sector = "N/A"

    story.append(
        Paragraph(
            f"{company_name} ({company_id}) — {sector}",
            header_style,
        )
    )

    story.append(Spacer(1, 10))

    # --------------------------------------------------------
    # KPI DATA
    # --------------------------------------------------------

    kpis = {}

    # --------------------------------------------------------
    # NUMERIC KPIs
    # --------------------------------------------------------

    for field in NUMERIC_KPI_FIELDS:

        latest_val = company_row.get(field)

        if prev_year_row is not None:
            prev_val = prev_year_row.get(field)
        else:
            prev_val = None

        if pd.notna(latest_val):

            arrow = trend_arrow(
                latest_val,
                prev_val
            )

            display_val = f"{latest_val:.2f}"

            kpis[
                field.replace("_", " ").title()
            ] = f"{display_val} {arrow}"

        else:

            kpis[
                field.replace("_", " ").title()
            ] = "N/A"

    # --------------------------------------------------------
    # CATEGORICAL KPIs
    # --------------------------------------------------------

    for field in FLAG_FIELDS:

        val = company_row.get(field)

        if pd.notna(val) and str(val).strip():

            kpis[
                field.replace("_", " ").title()
            ] = str(val)

        else:

            kpis[
                field.replace("_", " ").title()
            ] = "N/A"

    # --------------------------------------------------------
    # KPI TABLE
    # --------------------------------------------------------

    story.append(
        make_kpi_tile_table(kpis)
    )

    return story


# ============================================================
# NUMBERED CANVAS
# Used to display "Page X of Y"
# ============================================================

class NumberedCanvas(canvas.Canvas):

    def __init__(self, *args, **kwargs):

        canvas.Canvas.__init__(
            self,
            *args,
            **kwargs
        )

        self.pages = []

        self._saved_page_states = []

    def showPage(self):

        self._saved_page_states.append(
            dict(self.__dict__)
        )

        self._startPage()

    def save(self):

        total_pages = len(
            self._saved_page_states
        )

        for state in self._saved_page_states:

            self.__dict__.update(state)

            self.draw_page_number(
                total_pages
            )

            canvas.Canvas.showPage(self)

        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):

        self.saveState()

        page_width, page_height = A4

        # ----------------------------------------------------
        # Footer line
        # ----------------------------------------------------

        self.setStrokeColor(
            colors.HexColor("#D0D0D0")
        )

        self.setLineWidth(0.5)

        self.line(
            1.5 * cm,
            1.0 * cm,
            page_width - 1.5 * cm,
            1.0 * cm,
        )

        # ----------------------------------------------------
        # Footer text
        # ----------------------------------------------------

        self.setFont(
            "Helvetica",
            8
        )

        self.setFillColor(
            colors.grey
        )

        self.drawString(
            1.5 * cm,
            0.6 * cm,
            f"Portfolio Summary | Companies: {page_count}",
        )

        self.drawRightString(
            page_width - 1.5 * cm,
            0.6 * cm,
            f"Page {self._pageNumber} of {page_count}",
        )

        self.restoreState()


# ============================================================
# PORTFOLIO SUMMARY
# ============================================================

def build_portfolio_summary(
    db_path,
    output_path="reports/portfolio/portfolio_summary.pdf",
):

    # ========================================================
    # CONNECT DATABASE
    # ========================================================

    conn = sqlite3.connect(db_path)

    # ========================================================
    # GET LATEST FINANCIAL RATIOS
    #
    # sector_one prevents duplicate companies if the sectors
    # table contains multiple rows for the same company.
    # ========================================================

    query = """
        WITH sector_one AS (
            SELECT
                company_id,
                MAX(broad_sector) AS sector
            FROM sectors
            GROUP BY company_id
        )

        SELECT
            c.id AS company_id,
            c.company_name,
            s.sector,

            f.year,

            f.net_profit_margin_pct,
            f.return_on_equity_pct,
            f.debt_to_equity,
            f.interest_coverage,
            f.free_cash_flow_cr,
            f.cash_from_operations_cr,
            f.revenue_cagr_5yr,
            f.pat_cagr_5yr,

            f.icr_label,
            f.capital_allocation_label

        FROM companies c

        LEFT JOIN sector_one s
            ON s.company_id = c.id

        JOIN financial_ratios f
            ON f.company_id = c.id

        WHERE f.year = (
            SELECT MAX(f2.year)
            FROM financial_ratios f2
            WHERE f2.company_id = f.company_id
        )

        ORDER BY c.id
    """

    current = pd.read_sql(
        query,
        conn
    )

    # ========================================================
    # GET ALL FINANCIAL RATIO HISTORY
    # ========================================================

    previous_query = """
        SELECT
            company_id,
            year,

            net_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            free_cash_flow_cr,
            cash_from_operations_cr,
            revenue_cagr_5yr,
            pat_cagr_5yr

        FROM financial_ratios
    """

    previous_all = pd.read_sql(
        previous_query,
        conn
    )

    conn.close()

    # ========================================================
    # REMOVE DUPLICATE COMPANIES SAFELY
    # ========================================================

    current = (
        current
        .drop_duplicates(
            subset=["company_id"],
            keep="first"
        )
        .reset_index(drop=True)
    )

    # ========================================================
    # TOTAL COMPANY COUNT
    # ========================================================

    total_companies = len(current)

    # ========================================================
    # CREATE OUTPUT DIRECTORY
    # ========================================================

    output_path = Path(output_path)

    if not output_path.is_absolute():

        output_path = (
            ROOT / output_path
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ========================================================
    # BUILD PREVIOUS-YEAR LOOKUP
    # ========================================================

    previous = {}

    for company_id, group in previous_all.groupby(
        "company_id"
    ):

        group = group.sort_values(
            "year"
        )

        if len(group) >= 2:

            previous_year = group.iloc[-2]

            previous[
                company_id
            ] = previous_year.to_dict()

    # ========================================================
    # CREATE PDF
    # ========================================================

    doc = SimpleDocTemplate(
        str(output_path),

        pagesize=A4,

        topMargin=1.2 * cm,
        bottomMargin=1.5 * cm,

        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    story = []

    # ========================================================
    # ADD EACH COMPANY
    # ========================================================

    for index, (_, row) in enumerate(
        current.iterrows()
    ):

        company_id = row["company_id"]

        prev_row = previous.get(
            company_id
        )

        # ----------------------------------------------------
        # Company page content
        # ----------------------------------------------------

        story.extend(
            build_company_summary_page(
                row,
                prev_row
            )
        )

        # ----------------------------------------------------
        # Page break ONLY between companies
        #
        # This prevents a blank page after the last company.
        # ----------------------------------------------------

        if index < total_companies - 1:

            story.append(
                PageBreak()
            )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story,
        canvasmaker=NumberedCanvas
    )

    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print()
    print("=" * 60)
    print("PORTFOLIO SUMMARY GENERATED")
    print("=" * 60)
    print(f"File      : {output_path}")
    print(f"Companies : {total_companies}")
    print(f"Pages     : {total_companies}")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    db_path = (
        ROOT
        / "db"
        / "nifty100.db"
    )

    output_path = (
        ROOT
        / "reports"
        / "portfolio"
        / "portfolio_summary.pdf"
    )

    build_portfolio_summary(
        db_path=r"C:\Users\bhrra\Desktop\nifty100\db\nifty100.db",
        output_path=r"C:\Users\bhrra\Desktop\nifty100\output",
    )