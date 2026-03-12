"""
Optimization Engine Module
Uses PuLP for mathematical optimization of assortment selection.
Supports multiple optimization modes and business constraints.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from pulp import (
    LpProblem, LpMaximize, LpVariable, LpBinary,
    lpSum, PULP_CBC_CMD, LpStatus
)


# Optimization mode constants
MODE_MAX_VENDIBILITY = "Max Vendibility"
MODE_MAX_VEND_PER_CM2 = "Max Vendibility per Surface"
MODE_MAX_REVENUE = "Max Revenue"
MODE_MAX_MARGIN = "Max Margin"
MODE_HYBRID = "Hybrid Score"

OPTIMIZATION_MODES = [
    MODE_MAX_VENDIBILITY,
    MODE_MAX_VEND_PER_CM2,
    MODE_MAX_REVENUE,
    MODE_MAX_MARGIN,
    MODE_HYBRID,
]


def _get_objective_values(
    df: pd.DataFrame,
    mode: str,
    hybrid_weights: Optional[Dict[str, float]] = None,
) -> pd.Series:
    """Compute the objective coefficient for each SKU based on optimization mode."""
    if mode == MODE_MAX_VENDIBILITY:
        return df["Vendibility"].fillna(0)
    elif mode == MODE_MAX_VEND_PER_CM2:
        return df["Vendibility_per_cm2"].fillna(0)
    elif mode == MODE_MAX_REVENUE:
        return df["Revenue"].fillna(0)
    elif mode == MODE_MAX_MARGIN:
        return df["Margin"].fillna(0)
    elif mode == MODE_HYBRID:
        if hybrid_weights is None:
            hybrid_weights = {"Vendibility": 0.5, "Revenue": 0.3, "Margin": 0.2}
        score = pd.Series(0.0, index=df.index)
        for col, w in hybrid_weights.items():
            if col in df.columns:
                # Normalize to [0,1] before weighting
                vals = df[col].fillna(0).astype(float)
                vmin, vmax = vals.min(), vals.max()
                if vmax > vmin:
                    norm = (vals - vmin) / (vmax - vmin)
                else:
                    norm = pd.Series(0.5, index=df.index)
                score += norm * w
        return score
    else:
        return df["Vendibility"].fillna(0)


def run_optimization(
    df: pd.DataFrame,
    total_surface: float,
    mode: str = MODE_MAX_VENDIBILITY,
    hybrid_weights: Optional[Dict[str, float]] = None,
    # Constraint parameters
    min_skus_per_category: Optional[Dict[str, int]] = None,
    min_surface_pct_per_category: Optional[Dict[str, float]] = None,
    max_surface_pct_per_category: Optional[Dict[str, float]] = None,
    max_sku_pct_per_subcategory: Optional[float] = None,
    min_categories: Optional[int] = None,
    min_subcategories: Optional[int] = None,
    min_collections: Optional[int] = None,
    mandatory_include: Optional[List[str]] = None,
    mandatory_exclude: Optional[List[str]] = None,
    min_display_surface: Optional[float] = None,
) -> Tuple[pd.DataFrame, dict]:
    """
    Run the assortment optimization using PuLP.

    Returns:
        - DataFrame with a 'Selected' column (1/0)
        - Summary dict with KPIs
    """
    df = df.copy()
    df = df.reset_index(drop=True)

    # Filter out SKUs with no surface data
    valid_mask = df["Surface_cm2"] > 0
    df_valid = df[valid_mask].copy()
    df_excluded_surface = df[~valid_mask].copy()

    if len(df_valid) == 0:
        df["Selected"] = 0
        df["Selection_Reason"] = "No valid surface data"
        return df, {"status": "Infeasible", "message": "No SKUs with valid surface data"}

    # Apply mandatory exclusions
    if mandatory_exclude:
        exclude_mask = df_valid["SKU"].astype(str).isin([str(s) for s in mandatory_exclude])
        df_excluded_manual = df_valid[exclude_mask].copy()
        df_valid = df_valid[~exclude_mask].copy()
    else:
        df_excluded_manual = pd.DataFrame()

    if len(df_valid) == 0:
        df["Selected"] = 0
        df["Selection_Reason"] = "All SKUs excluded"
        return df, {"status": "Infeasible", "message": "All SKUs were excluded"}

    n = len(df_valid)
    indices = df_valid.index.tolist()
    objective_values = _get_objective_values(df_valid, mode, hybrid_weights)

    # Create problem
    prob = LpProblem("Assortment_Optimization", LpMaximize)

    # Decision variables
    x = {i: LpVariable(f"x_{i}", cat=LpBinary) for i in indices}

    # Objective function
    prob += lpSum(objective_values.loc[i] * x[i] for i in indices), "Total_Objective"

    # Constraint 1: Total surface
    prob += (
        lpSum(df_valid.loc[i, "Surface_cm2"] * x[i] for i in indices) <= total_surface,
        "Total_Surface"
    )

    # Constraint: Mandatory inclusions
    if mandatory_include:
        for sku in mandatory_include:
            sku_indices = df_valid[df_valid["SKU"].astype(str) == str(sku)].index.tolist()
            for idx in sku_indices:
                prob += (x[idx] == 1, f"Mandatory_Include_{sku}_{idx}")

    # Constraint: Min SKUs per category
    if min_skus_per_category and "Category" in df_valid.columns:
        for cat, min_count in min_skus_per_category.items():
            cat_indices = df_valid[df_valid["Category"] == cat].index.tolist()
            if cat_indices:
                prob += (
                    lpSum(x[i] for i in cat_indices) >= min_count,
                    f"Min_SKUs_{cat}"
                )

    # Constraint: Min surface % per category
    if min_surface_pct_per_category and "Category" in df_valid.columns:
        for cat, min_pct in min_surface_pct_per_category.items():
            cat_indices = df_valid[df_valid["Category"] == cat].index.tolist()
            if cat_indices:
                prob += (
                    lpSum(df_valid.loc[i, "Surface_cm2"] * x[i] for i in cat_indices)
                    >= min_pct / 100.0 * total_surface,
                    f"Min_Surface_Pct_{cat}"
                )

    # Constraint: Max surface % per category
    if max_surface_pct_per_category and "Category" in df_valid.columns:
        for cat, max_pct in max_surface_pct_per_category.items():
            cat_indices = df_valid[df_valid["Category"] == cat].index.tolist()
            if cat_indices:
                prob += (
                    lpSum(df_valid.loc[i, "Surface_cm2"] * x[i] for i in cat_indices)
                    <= max_pct / 100.0 * total_surface,
                    f"Max_Surface_Pct_{cat}"
                )

    # Constraint: Max SKU % per subcategory
    if max_sku_pct_per_subcategory and "Subcategory" in df_valid.columns:
        max_sku_count = int(n * max_sku_pct_per_subcategory / 100.0)
        for subcat in df_valid["Subcategory"].dropna().unique():
            sub_indices = df_valid[df_valid["Subcategory"] == subcat].index.tolist()
            if sub_indices:
                prob += (
                    lpSum(x[i] for i in sub_indices) <= max_sku_count,
                    f"Max_SKU_Pct_Subcat_{subcat}"
                )

    # Constraint: Minimum distinct categories
    if min_categories and "Category" in df_valid.columns:
        categories = df_valid["Category"].dropna().unique().tolist()
        # Binary variable for each category: 1 if at least one SKU selected
        y_cat = {
            cat: LpVariable(f"y_cat_{cat}", cat=LpBinary)
            for cat in categories
        }
        for cat in categories:
            cat_indices = df_valid[df_valid["Category"] == cat].index.tolist()
            if cat_indices:
                # y_cat = 1 only if at least one SKU from category selected
                prob += (lpSum(x[i] for i in cat_indices) >= y_cat[cat], f"Link_Cat_{cat}")
                prob += (lpSum(x[i] for i in cat_indices) <= len(cat_indices) * y_cat[cat], f"Link_Cat_Upper_{cat}")
        prob += (lpSum(y_cat[cat] for cat in categories) >= min_categories, "Min_Categories")

    # Constraint: Minimum distinct subcategories
    if min_subcategories and "Subcategory" in df_valid.columns:
        subcategories = df_valid["Subcategory"].dropna().unique().tolist()
        y_sub = {
            sub: LpVariable(f"y_sub_{sub}", cat=LpBinary)
            for sub in subcategories
        }
        for sub in subcategories:
            sub_indices = df_valid[df_valid["Subcategory"] == sub].index.tolist()
            if sub_indices:
                prob += (lpSum(x[i] for i in sub_indices) >= y_sub[sub], f"Link_Sub_{sub}")
                prob += (lpSum(x[i] for i in sub_indices) <= len(sub_indices) * y_sub[sub], f"Link_Sub_Upper_{sub}")
        prob += (lpSum(y_sub[sub] for sub in subcategories) >= min_subcategories, "Min_Subcategories")

    # Constraint: Minimum collections
    if min_collections and "Collection" in df_valid.columns:
        collections = df_valid["Collection"].dropna().unique().tolist()
        y_col = {
            col: LpVariable(f"y_col_{col}", cat=LpBinary)
            for col in collections
        }
        for col in collections:
            col_indices = df_valid[df_valid["Collection"] == col].index.tolist()
            if col_indices:
                prob += (lpSum(x[i] for i in col_indices) >= y_col[col], f"Link_Col_{col}")
                prob += (lpSum(x[i] for i in col_indices) <= len(col_indices) * y_col[col], f"Link_Col_Upper_{col}")
        prob += (lpSum(y_col[col] for col in collections) >= min_collections, "Min_Collections")

    # Constraint: Minimum display surface per selected SKU
    if min_display_surface:
        for i in indices:
            if df_valid.loc[i, "Surface_cm2"] < min_display_surface:
                prob += (x[i] == 0, f"Min_Display_{i}")

    # Solve
    solver = PULP_CBC_CMD(msg=0, timeLimit=60)
    prob.solve(solver)

    status = LpStatus[prob.status]

    # Extract results
    selected_indices = [i for i in indices if x[i].varValue and x[i].varValue > 0.5]

    # Build selection column on original df
    df["Selected"] = 0
    df.loc[selected_indices, "Selected"] = 1

    # Mark excluded SKUs
    df["Selection_Reason"] = ""
    df.loc[selected_indices, "Selection_Reason"] = "Selected by optimizer"
    df.loc[df_excluded_surface.index, "Selection_Reason"] = "Excluded: no surface data"
    if len(df_excluded_manual) > 0:
        df.loc[df_excluded_manual.index, "Selection_Reason"] = "Excluded: mandatory exclusion"

    # Unselected valid SKUs
    unselected_valid = set(indices) - set(selected_indices)
    df.loc[list(unselected_valid), "Selection_Reason"] = "Not selected: lower optimization score"

    # Compute summary
    sel = df[df["Selected"] == 1]
    summary = {
        "status": status,
        "total_skus_selected": len(sel),
        "total_skus_available": len(df),
        "total_vendibility": round(sel["Vendibility"].sum(), 4) if "Vendibility" in sel.columns else 0,
        "total_revenue": round(sel["Revenue"].sum(), 2) if "Revenue" in sel.columns else 0,
        "total_margin": round(sel["Margin"].sum(), 2) if "Margin" in sel.columns else 0,
        "total_surface_used": round(sel["Surface_cm2"].sum(), 2),
        "total_surface_available": total_surface,
        "remaining_surface": round(total_surface - sel["Surface_cm2"].sum(), 2),
        "surface_utilization_pct": round(sel["Surface_cm2"].sum() / total_surface * 100, 1) if total_surface > 0 else 0,
        "categories_represented": sel["Category"].nunique() if "Category" in sel.columns else 0,
        "optimization_mode": mode,
        "objective_value": round(prob.objective.value(), 4) if prob.objective.value() is not None else 0,
    }

    return df, summary


def run_greedy_benchmark(
    df: pd.DataFrame,
    total_surface: float,
    mode: str = MODE_MAX_VENDIBILITY,
    hybrid_weights: Optional[Dict[str, float]] = None,
) -> Tuple[pd.DataFrame, dict]:
    """
    Run a greedy benchmark for comparison.
    Sorts by objective/surface ratio and greedily fills.
    """
    df = df.copy()
    df_valid = df[df["Surface_cm2"] > 0].copy()

    obj_values = _get_objective_values(df_valid, mode, hybrid_weights)
    df_valid["_obj"] = obj_values
    df_valid["_efficiency"] = df_valid["_obj"] / df_valid["Surface_cm2"]
    df_valid = df_valid.sort_values("_efficiency", ascending=False)

    remaining = total_surface
    selected = []
    for idx, row in df_valid.iterrows():
        if row["Surface_cm2"] <= remaining:
            selected.append(idx)
            remaining -= row["Surface_cm2"]

    df["Greedy_Selected"] = 0
    df.loc[selected, "Greedy_Selected"] = 1

    sel = df[df["Greedy_Selected"] == 1]
    summary = {
        "total_skus_selected": len(sel),
        "total_vendibility": round(sel["Vendibility"].sum(), 4) if "Vendibility" in sel.columns else 0,
        "total_revenue": round(sel["Revenue"].sum(), 2) if "Revenue" in sel.columns else 0,
        "total_surface_used": round(sel["Surface_cm2"].sum(), 2),
    }

    return df, summary
