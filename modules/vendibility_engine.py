"""
Vendibility Engine Module
Calculates normalized composite vendibility scores with configurable weights.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional


# Default weights for vendibility calculation
DEFAULT_WEIGHTS = {
    "Units_Sold": 0.35,
    "SellThrough": 0.25,
    "Revenue": 0.20,
    "Rotation": 0.10,
    "Margin": 0.10,
}


def normalize_series(s: pd.Series) -> pd.Series:
    """Normalize a Series to [0, 1] using min-max scaling."""
    smin = s.min()
    smax = s.max()
    if smax == smin:
        return pd.Series(0.5, index=s.index)
    return (s - smin) / (smax - smin)


def calculate_vendibility(
    df: pd.DataFrame,
    weights: Optional[Dict[str, float]] = None,
    use_existing: bool = False,
) -> pd.DataFrame:
    """
    Calculate vendibility score for each SKU.

    If use_existing=True and 'Vendibility_Score' already exists, uses it directly.
    Otherwise computes from component metrics with configurable weights.

    Weights are redistributed proportionally if some metrics are missing.

    Returns the dataframe with additional columns:
        - norm_{metric} for each available metric
        - Vendibility (final score)
        - Rank_Category (rank within category)
        - Rank_Segment (rank within segment)
    """
    df = df.copy()

    if use_existing and "Vendibility_Score" in df.columns:
        df["Vendibility"] = df["Vendibility_Score"].fillna(0)
    else:
        if weights is None:
            weights = DEFAULT_WEIGHTS.copy()

        # Determine which metrics are available
        available = {k: v for k, v in weights.items() if k in df.columns}

        if not available:
            df["Vendibility"] = 0.0
            return df

        # Redistribute weights proportionally for missing metrics
        total_available_weight = sum(available.values())
        if total_available_weight > 0:
            adjusted_weights = {k: v / total_available_weight for k, v in available.items()}
        else:
            adjusted_weights = {k: 1.0 / len(available) for k in available}

        # Normalize each variable and compute weighted score
        df["Vendibility"] = 0.0
        for metric, weight in adjusted_weights.items():
            col = f"norm_{metric}"
            df[col] = normalize_series(df[metric].fillna(0).astype(float))
            df["Vendibility"] += df[col] * weight

    # Rankings
    if "Category" in df.columns:
        df["Rank_Category"] = df.groupby("Category")["Vendibility"].rank(
            ascending=False, method="min"
        ).astype(int)
    else:
        df["Rank_Category"] = df["Vendibility"].rank(ascending=False, method="min").astype(int)

    if "Business_Segment" in df.columns:
        df["Rank_Segment"] = df.groupby("Business_Segment")["Vendibility"].rank(
            ascending=False, method="min"
        ).astype(int)
    else:
        df["Rank_Segment"] = df["Vendibility"].rank(ascending=False, method="min").astype(int)

    return df


def get_available_metrics(df: pd.DataFrame) -> list:
    """Return list of vendibility metrics available in the dataframe."""
    all_metrics = ["Units_Sold", "SellThrough", "Revenue", "Rotation", "Margin"]
    return [m for m in all_metrics if m in df.columns]
