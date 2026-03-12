"""
Surface Engine Module
Computes surface-related productivity metrics per SKU.
"""

import pandas as pd
import numpy as np


def compute_surface_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute surface productivity metrics for each SKU.

    Adds columns:
        - Vendibility_per_cm2
        - Revenue_per_cm2
        - Units_per_cm2
        - Margin_per_cm2
    """
    df = df.copy()
    surface = df["Surface_cm2"].replace(0, np.nan)

    if "Vendibility" in df.columns:
        df["Vendibility_per_cm2"] = df["Vendibility"] / surface
    else:
        df["Vendibility_per_cm2"] = np.nan

    if "Revenue" in df.columns:
        df["Revenue_per_cm2"] = df["Revenue"].fillna(0) / surface
    else:
        df["Revenue_per_cm2"] = np.nan

    if "Units_Sold" in df.columns:
        df["Units_per_cm2"] = df["Units_Sold"].fillna(0) / surface
    else:
        df["Units_per_cm2"] = np.nan

    if "Margin" in df.columns:
        df["Margin_per_cm2"] = df["Margin"].fillna(0) / surface
    else:
        df["Margin_per_cm2"] = np.nan

    return df


def get_surface_diagnostics(df: pd.DataFrame) -> dict:
    """Return diagnostic info about surface data quality."""
    total = len(df)
    zero_surface = (df["Surface_cm2"] == 0).sum() if "Surface_cm2" in df.columns else 0
    missing_surface = df["Surface_cm2"].isna().sum() if "Surface_cm2" in df.columns else total
    valid = total - zero_surface - missing_surface

    stats = {}
    if "Surface_cm2" in df.columns:
        valid_data = df[df["Surface_cm2"] > 0]["Surface_cm2"]
        if len(valid_data) > 0:
            stats = {
                "mean": round(valid_data.mean(), 1),
                "median": round(valid_data.median(), 1),
                "min": round(valid_data.min(), 1),
                "max": round(valid_data.max(), 1),
                "std": round(valid_data.std(), 1),
            }

    return {
        "total_skus": total,
        "valid_surface": int(valid),
        "zero_surface": int(zero_surface),
        "missing_surface": int(missing_surface),
        "stats": stats,
    }
