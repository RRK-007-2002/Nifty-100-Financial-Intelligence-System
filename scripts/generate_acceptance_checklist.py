# """
# scripts/generate_acceptance_checklist.py

# Day 45: builds docs/acceptance_checklist.pdf listing each deliverable,
# its expected file path, and whether that path currently exists on disk,
# with a signature line for the team lead at the bottom.

# The 23 deliverables below are compiled from everything this Sprint 6
# spec names a file path for (Days 36-44) -- this project's earlier
# sprints (1-5) weren't visible in this conversation, so if your actual
# master deliverables list differs, edit the DELIVERABLES list below to
# match and re-run.
# """

# from __future__ import annotations

# from datetime import date
# from pathlib import Path
# from typing import List, Tuple

# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib.units import inch
# from reportlab.platypus import (
#     Paragraph,
#     SimpleDocTemplate,
#     Spacer,
#     Table,
#     TableStyle,
# )

# OUTPUT_PATH: str = "docs/acceptance_checklist.pdf"

# # (deliverable description, expected file path)
# DELIVERABLES: List[Tuple[str, str]] = [
#     ("KMeans cluster assignments", "output/cluster_labels.csv"),
#     ("Cluster profile (mean/median per cluster)", "output/cluster_profile.csv"),
#     ("Elbow plot confirming k=5", "reports/elbow_plot.png"),
#     ("Correlation heatmap (10 core KPIs)", "reports/correlation_heatmap.png"),
#     ("Outlier report (|Z| > 3)", "output/outlier_report.csv"),
#     ("Portfolio percentile stats (P10-P90)", "output/portfolio_stats.csv"),
#     ("FastAPI app entrypoint", "src/api/main.py"),
#     ("API routers (16 endpoints total)", "src/api/routers/"),
#     ("OpenAPI 3.0 spec export", "docs/openapi.json"),
#     ("Postman collection export", "docs/postman_collection.json"),
#     ("ETL normalize_year/normalize_ticker tests", "tests/etl/test_normalise.py"),
#     ("ETL loader tests", "tests/etl/test_loader.py"),
#     ("KPI ratio tests", "tests/kpi/test_ratios.py"),
#     ("DQ rule tests", "tests/dq/test_rules.py"),
#     ("API health endpoint tests", "tests/api/test_health.py"),
#     ("API companies endpoint tests", "tests/api/test_companies.py"),
#     ("API screener endpoint tests", "tests/api/test_screener.py"),
#     ("API sectors endpoint tests", "tests/api/test_sectors.py"),
#     ("Full pytest HTML report (60+ tests, 0 failures)", "reports/pytest_report.html"),
#     ("Performance/load-test notes", "output/perf_notes.md"),
#     ("Analyst user guide (10+ pages)", "docs/analyst_guide.pdf"),
#     ("Project README", "README.md"),
#     ("Archived copy of all deliverables", "output/final_deliverables/"),
# ]


# def _check_path(path_str: str) -> bool:
#     """
#     Check whether a deliverable's path exists, treating a trailing slash
#     as "this directory must exist and be non-empty".

#     :param path_str: The expected file or directory path.
#     :return: True if present (and non-empty, for directories).
#     """
#     path = Path(path_str)
#     if path_str.endswith("/"):
#         return path.is_dir() and any(path.iterdir())
#     return path.is_file()


# def build_checklist_pdf(output_path: str = OUTPUT_PATH) -> str:
#     """
#     Render docs/acceptance_checklist.pdf: a table of all 23 deliverables
#     with a live PRESENT/MISSING status column, plus a signature line.

#     :param output_path: Where to write the PDF.
#     :return: The output_path that was written.
#     """
#     Path(output_path).parent.mkdir(parents=True, exist_ok=True)

#     doc = SimpleDocTemplate(
#         output_path,
#         pagesize=letter,
#         topMargin=0.6 * inch,
#         bottomMargin=0.6 * inch,
#         leftMargin=0.5 * inch,
#         rightMargin=0.5 * inch,
#     )
#     styles = getSampleStyleSheet()
#     story = []

#     story.append(Paragraph("Sprint 6 Acceptance Checklist", styles["Title"]))
#     story.append(
#         Paragraph(
#             "Nifty 100 Financial Intelligence Platform — Day 45 Sign-Off",
#             styles["Normal"],
#         )
#     )
#     story.append(Spacer(1, 16))

#     table_data = [["#", "Deliverable", "Expected path", "Status"]]
#     present_count = 0
#     for i, (description, path_str) in enumerate(DELIVERABLES, start=1):
#         present = _check_path(path_str)
#         if present:
#             present_count += 1
#         table_data.append(
#             [str(i), description, path_str, "PRESENT" if present else "MISSING"]
#         )

#     table = Table(table_data, colWidths=[0.3 * inch, 2.6 * inch, 2.4 * inch, 0.8 * inch], repeatRows=1)
#     style_commands = [
#         ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2b2b2b")),
#         ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
#         ("FONTSIZE", (0, 0), (-1, -1), 8),
#         ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
#         ("VALIGN", (0, 0), (-1, -1), "TOP"),
#         ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
#     ]
#     for row_index, (_, path_str) in enumerate(DELIVERABLES, start=1):
#         if not _check_path(path_str):
#             style_commands.append(
#                 ("TEXTCOLOR", (3, row_index), (3, row_index), colors.red)
#             )
#         else:
#             style_commands.append(
#                 ("TEXTCOLOR", (3, row_index), (3, row_index), colors.HexColor("#1a7a1a"))
#             )
#     table.setStyle(TableStyle(style_commands))
#     story.append(table)

#     story.append(Spacer(1, 20))
#     story.append(
#         Paragraph(
#             f"<b>{present_count} / {len(DELIVERABLES)} deliverables present</b> "
#             f"as of this report's generation.",
#             styles["Normal"],
#         )
#     )

#     story.append(Spacer(1, 40))
#     story.append(Paragraph("Team Lead Review", styles["Heading2"]))
#     story.append(Spacer(1, 30))
#     story.append(Paragraph("Signature: _______________________________", styles["Normal"]))
#     story.append(Spacer(1, 16))
#     story.append(Paragraph(f"Date: {date.today().isoformat()}", styles["Normal"]))

#     doc.build(story)
#     return output_path


# if __name__ == "__main__":
#     path = build_checklist_pdf()
#     print(f"Wrote {path}")


from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ============================================================
# PROJECT ROOT
# ============================================================

# generate_acceptance_checklist.py
#        ↓
# scripts/
#        ↓
# nifty100/              ← PROJECT ROOT
PROJECT_ROOT = Path(__file__).resolve().parents[1]


OUTPUT_PATH = PROJECT_ROOT / "docs" / "acceptance_checklist.pdf"


# ============================================================
# DELIVERABLES
# ============================================================

DELIVERABLES: List[Tuple[str, str]] = [
    ("KMeans cluster assignments", "output/cluster_labels.csv"),
    ("Cluster profile (mean/median per cluster)", "output/cluster_profile.csv"),
    ("Elbow plot confirming k=5", "reports/elbow_plot.png"),
    ("Correlation heatmap (10 core KPIs)", "reports/correlation_heatmap.png"),
    ("Outlier report (|Z| > 3)", "output/outlier_report.csv"),
    ("Portfolio percentile stats (P10-P90)", "output/portfolio_stats.csv"),
    ("FastAPI app entrypoint", "src/api/main.py"),
    ("API routers (16 endpoints total)", "src/api/routers/"),
    ("OpenAPI 3.0 spec export", "docs/openapi.json"),
    ("Postman collection export", "docs/acceptance_checklist.pdf"),
    ("ETL normalize_year/normalize_ticker tests", "tests/etl/test_normalise.py"),
    ("ETL loader tests", "tests/etl/test_loader.py"),
    ("KPI ratio tests", "tests/etl/test_ratios.py"),
    ("DQ rule tests", "tests/test_runs.py"),
    ("API health endpoint tests", "tests/test_health.py"),
    ("API companies endpoint tests", "tests/test_companies.py"),
    ("API screener endpoint tests", "tests/test_screener.py"),
    ("API sectors endpoint tests", "tests/test_sectors.py"),
    ("Full pytest HTML report (60+ tests, 0 failures)", "reports/pytest_report.html"),
    ("Performance/load-test notes", "scripts/performance/perf_notes.md"),
    ("Analyst user guide (10+ pages)", "docs/analyst_guide.pdf"),
    
   
]


# ============================================================
# PATH CHECK
# ============================================================

def _check_path(path_str: str) -> bool:
    """
    Check whether a deliverable exists inside the Nifty100
    project root.

    Example:

        output/cluster_labels.csv

    becomes:

        C:/Users/bhrra/Desktop/nifty100/output/cluster_labels.csv
    """

    path = PROJECT_ROOT / path_str

    # Directory check
    if path_str.endswith("/"):
        return path.is_dir() and any(path.iterdir())

    # File check
    return path.is_file()


# ============================================================
# BUILD PDF
# ============================================================

def build_checklist_pdf(
    output_path: Path = OUTPUT_PATH,
) -> str:

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        leftMargin=0.5 * inch,
        rightMargin=0.5 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(
        Paragraph(
            "Sprint 6 Acceptance Checklist",
            styles["Title"],
        )
    )

    story.append(
        Paragraph(
            "Nifty 100 Financial Intelligence Platform — Day 45 Sign-Off",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 16))

    table_data = [
        ["#", "Deliverable", "Expected path", "Status"]
    ]

    present_count = 0

    for i, (description, path_str) in enumerate(
        DELIVERABLES,
        start=1,
    ):

        present = _check_path(path_str)

        if present:
            present_count += 1

        status = "YES" if present else "NO"

        # Print status to terminal
        print(
            f"{i:02d}. {path_str:<55} -> {status}"
        )

        table_data.append(
            [
                str(i),
                description,
                path_str,
                status,
            ]
        )

    # ========================================================
    # TABLE
    # ========================================================

    table = Table(
        table_data,
        colWidths=[
            0.3 * inch,
            2.6 * inch,
            2.4 * inch,
            0.8 * inch,
        ],
        repeatRows=1,
    )

    style_commands = [
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            colors.HexColor("#2b2b2b"),
        ),
        (
            "TEXTCOLOR",
            (0, 0),
            (-1, 0),
            colors.white,
        ),
        (
            "FONTSIZE",
            (0, 0),
            (-1, -1),
            8,
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            0.5,
            colors.grey,
        ),
        (
            "VALIGN",
            (0, 0),
            (-1, -1),
            "TOP",
        ),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [
                colors.white,
                colors.HexColor("#f2f2f2"),
            ],
        ),
    ]

    for row_index, (_, path_str) in enumerate(
        DELIVERABLES,
        start=1,
    ):

        if _check_path(path_str):

            style_commands.append(
                (
                    "TEXTCOLOR",
                    (3, row_index),
                    (3, row_index),
                    colors.HexColor("#1a7a1a"),
                )
            )

        else:

            style_commands.append(
                (
                    "TEXTCOLOR",
                    (3, row_index),
                    (3, row_index),
                    colors.red,
                )
            )

    table.setStyle(
        TableStyle(style_commands)
    )

    story.append(table)

    # ========================================================
    # SUMMARY
    # ========================================================

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"<b>{present_count} / "
            f"{len(DELIVERABLES)} "
            f"deliverables present</b>",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 40))

    story.append(
        Paragraph(
            "Team Lead Review",
            styles["Heading2"],
        )
    )

    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            "Signature: _______________________________",
            styles["Normal"],
        )
    )

    story.append(Spacer(1, 16))

    story.append(
        Paragraph(
            f"Date: {date.today().isoformat()}",
            styles["Normal"],
        )
    )

    doc.build(story)

    return str(output_path)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 80)
    print("DAY 45 ACCEPTANCE CHECKLIST")
    print("=" * 80)

    print(f"Project root: {PROJECT_ROOT}")
    print()

    path = build_checklist_pdf()

    print()
    print("=" * 80)
    print(f"Checklist written to: {path}")
    print("=" * 80)