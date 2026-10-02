# src/screener/presets.py

import pandas as pd
from engine import apply_filters, preprocess_special_metrics

PRESETS = {
    "Quality Compounder": {
        "ROE_min": 15,
        "DE_max": 1.0,
        "FCF_min": 0,
        "Revenue_CAGR_5yr_min": 10,
    },
    "Value Pick": {
        "PE_max": 20,
        "PB_max": 3.0,
        "DE_max": 2.0,
        "Dividend_Yield_min": 1,
    },
    "Growth Accelerator": {
        "PAT_CAGR_5yr_min": 20,
        "Revenue_CAGR_5yr_min": 15,
        "DE_max": 2.0,
    },
    "Dividend Champion": {
        "Dividend_Yield_min": 2,
        "Dividend_Payout_max": 80,
        "FCF_min": 0,
    },
    "Debt-Free Blue Chip": {
        "DE_max": 0,          # DE == 0 effectively via max filter
        "ROE_min": 12,
        "Sales_min": 5000,    # "Revenue > 5000 Crore" -> Sales column
    },
}


def check_turnaround_watch(df: pd.DataFrame) -> pd.DataFrame:
    """
    Turnaround Watch alag hai kyunki isme trend condition hai:
    Revenue CAGR 3yr > 10%, FCF positive latest year, D/E declining YoY.
    Isliye ise apply_filters() se nahi, custom function se handle karte hain.
    """
    df = preprocess_special_metrics(df)

    mask = (
        (df["Revenue_CAGR_3yr"] > 10)
        & (df["FCF"] > 0)  # latest year FCF positive
        & (df["DE_current_year"] < df["DE_previous_year"])  # declining trend
    )
    return df[mask].copy()


def run_all_presets(df: pd.DataFrame) -> dict:
    """Har preset chalao aur result dictionary mein store karo: {preset_name: filtered_df}"""
    results = {}

    for name, config in PRESETS.items():
        results[name] = apply_filters(df, config)

    results["Turnaround Watch"] = check_turnaround_watch(df)
    return results


def validate_preset_counts(results: dict, min_count=5, max_count=50) -> pd.DataFrame:
    """
    Har preset ka result count 5-50 range mein hai ya nahi, check karta hai.
    Return: summary DataFrame jisse Day 21 ke test mein use kar sakein.
    """
    rows = []
    for name, res_df in results.items():
        count = len(res_df)
        rows.append({
            "preset": name,
            "count": count,
            "in_range": min_count <= count <= max_count,
        })
    return pd.DataFrame(rows)
import yaml

def load_presets(config_path: str) -> dict:
    """Yaml se saare presets padh leta hai — ek dict of dicts."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config["presets"]  # {"Quality Compounder": {...}, "Value Pick": {...}, ...}


def run_all_presets(df: pd.DataFrame, config_path: str) -> dict:
    presets = load_presets(config_path)
    results = {name: apply_filters(df, filters) for name, filters in presets.items()}
    results["Turnaround Watch"] = check_turnaround_watch(df)
    return results