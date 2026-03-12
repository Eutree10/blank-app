"""
Data Loader Module
Handles loading product performance data and surface data from CSV, Excel, or Parquet.
"""

import pandas as pd
import streamlit as st
from typing import Optional, Tuple, List

# Required columns for product performance data
PRODUCT_REQUIRED_COLS = [
    "SKU", "Product_Name", "Category"
]

PRODUCT_RECOMMENDED_COLS = [
    "SKU", "Product_Name", "Brand", "Country", "Channel",
    "Business_Segment", "Category", "Subcategory",
    "Collection", "Units_Sold", "Revenue", "SellThrough",
    "Rotation", "Margin", "Current_Store_Presence", "Vendibility_Score"
]

SURFACE_REQUIRED_COLS = ["SKU", "Width_cm", "Depth_cm", "Display_units"]
SURFACE_OPTIONAL_COLS = ["Height_cm", "Display_type"]


@st.cache_data
def load_product_data(uploaded_file) -> Optional[pd.DataFrame]:
    """Load product performance data from uploaded file."""
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith(".parquet"):
            df = pd.read_parquet(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            return None
        # Normalize column names: strip whitespace
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading product data: {e}")
        return None


@st.cache_data
def load_surface_data(uploaded_file) -> Optional[pd.DataFrame]:
    """Load surface/display data from uploaded Excel or CSV."""
    try:
        name = uploaded_file.name.lower()
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            return None
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Error loading surface data: {e}")
        return None


def merge_datasets(
    product_df: pd.DataFrame,
    surface_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, dict]:
    """
    Merge product and surface datasets on SKU.
    Returns merged dataframe and merge diagnostics.
    """
    product_skus = set(product_df["SKU"].astype(str).unique())
    surface_skus = set(surface_df["SKU"].astype(str).unique())

    only_in_product = product_skus - surface_skus
    only_in_surface = surface_skus - product_skus
    matched = product_skus & surface_skus

    # Ensure SKU types match
    product_df = product_df.copy()
    surface_df = surface_df.copy()
    product_df["SKU"] = product_df["SKU"].astype(str)
    surface_df["SKU"] = surface_df["SKU"].astype(str)

    merged = product_df.merge(surface_df, on="SKU", how="left")

    # Calculate surface
    if "Width_cm" in merged.columns and "Depth_cm" in merged.columns and "Display_units" in merged.columns:
        merged["Surface_cm2"] = (
            merged["Width_cm"].fillna(0) *
            merged["Depth_cm"].fillna(0) *
            merged["Display_units"].fillna(1)
        )
    elif "Surface_cm2" not in merged.columns:
        merged["Surface_cm2"] = 0.0

    diagnostics = {
        "total_product_skus": len(product_skus),
        "total_surface_skus": len(surface_skus),
        "matched_skus": len(matched),
        "only_in_product": sorted(only_in_product),
        "only_in_surface": sorted(only_in_surface),
    }

    return merged, diagnostics


def check_required_columns(df: pd.DataFrame, required: List[str]) -> Tuple[List[str], List[str]]:
    """Check which required columns are present and missing."""
    present = [c for c in required if c in df.columns]
    missing = [c for c in required if c not in df.columns]
    return present, missing
