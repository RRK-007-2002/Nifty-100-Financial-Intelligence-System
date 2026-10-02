# src/analytics/radar.py
"""
Day 19: Radar/polar charts per company, 8 axes, peer-group average overlay.
Reuses scoring.py's _winsorize_scale() for a common 0-100 axis scale —
no duplicate normalisation logic.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.screener.scoring import _winsorize_scale

RADAR_AXES = [
    ("return_on_equity_pct", "ROE", False),
    ("roce_percentage", "ROCE*", False),          # * = display-only source, see docstring
    ("net_profit_margin_pct", "NPM", False),
    ("debt_to_equity", "D/E", True),               # invert: lower D/E = better = higher score
    ("free_cash_flow_cr", "FCF", False),
    ("pat_cagr_5yr", "PAT CAGR 5yr", False),
    ("revenue_cagr_5yr", "Revenue CAGR 5yr", False),
    ("composite_quality_score", "Composite Score", False),
]


def build_radar_scores(universe: pd.DataFrame) -> pd.DataFrame:
    """
    Adds one _radar_score column per axis (0-100, winsorised) to the
    universe DataFrame. composite_quality_score is already 0-100
    (from Day 17) so it is NOT re-winsorised, just clipped/passed through
    — if it's NaN (pending Day-17 debug), it stays NaN here too; the
    plotting function below handles that gracefully rather than crashing.
    """
    df = universe.copy()
    for col, label, invert in RADAR_AXES:
        score_col = f"_radar_{col}"
        if col not in df.columns:
            df[score_col] = np.nan
            continue
        if col == "composite_quality_score":
            df[score_col] = df[col].clip(0, 100)
        else:
            df[score_col] = _winsorize_scale(df[col], higher_is_better=not invert)
    return df


def _plot_radar(ax, company_values: list, avg_values: list, labels: list, title: str) -> None:
    n = len(labels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    company_plot = [0 if (v is None or np.isnan(v)) else v for v in company_values] + \
                   [0 if (company_values[0] is None or np.isnan(company_values[0])) else company_values[0]]
    avg_plot = [0 if (v is None or np.isnan(v)) else v for v in avg_values] + \
               [0 if (avg_values[0] is None or np.isnan(avg_values[0])) else avg_values[0]]

    ax.plot(angles, company_plot, linewidth=2, label="Company", color="#2E86AB")
    ax.fill(angles, company_plot, alpha=0.25, color="#2E86AB")
    ax.plot(angles, avg_plot, linewidth=1.5, linestyle="--", label="Group Avg", color="#A23B72")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_title(title, fontsize=11, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1), fontsize=8)


def generate_radar_chart(
    company_id: str,
    scored_universe: pd.DataFrame,
    peer_groups: pd.DataFrame,
    output_dir: str | Path,
) -> Path:
    """
    One PNG per company. If the company has a peer group, overlay is the
    peer-group average. If not, overlay is the full-universe (Nifty 100)
    average, per spec's 'no peer group -> standalone vs Nifty 100 average'
    fallback.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    row = scored_universe[scored_universe["company_id"] == company_id]
    if row.empty:
        raise KeyError(f"company_id '{company_id}' not found in scored_universe")
    row = row.iloc[0]

    labels = [label for _, label, _ in RADAR_AXES]
    score_cols = [f"_radar_{col}" for col, _, _ in RADAR_AXES]
    company_values = [row[c] for c in score_cols]

    group_row = peer_groups[peer_groups["company_id"] == company_id]
    if not group_row.empty:
        group_name = group_row["peer_group_name"].iloc[0]
        peer_ids = peer_groups[peer_groups["peer_group_name"] == group_name]["company_id"]
        peer_subset = scored_universe[scored_universe["company_id"].isin(peer_ids)]
        title_suffix = f"vs {group_name} avg"
    else:
        peer_subset = scored_universe  # Nifty 100 fallback
        title_suffix = "vs Nifty 100 avg (no peer group)"

    avg_values = [peer_subset[c].mean(skipna=True) for c in score_cols]

    fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
    _plot_radar(ax, company_values, avg_values, labels, f"{company_id} {title_suffix}")

    out_path = output_dir / f"{company_id}_radar.png"
    fig.savefig(out_path, bbox_inches="tight", dpi=120)
    plt.close(fig)
    return out_path


def generate_all_radar_charts(scored_universe: pd.DataFrame, peer_groups: pd.DataFrame, output_dir: str | Path) -> list[Path]:
    """Generates one PNG per company in scored_universe. Logs (not silently skips) any failures."""
    paths = []
    for company_id in scored_universe["company_id"]:
        try:
            paths.append(generate_radar_chart(company_id, scored_universe, peer_groups, output_dir))
        except Exception as e:
            print(f"[radar] WARNING: failed for {company_id}: {e}")
    return paths