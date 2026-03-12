"""
Exports Module
Handles exporting optimization results, diagnostics, and scenarios to Excel.
"""

import pandas as pd
import io
from typing import Dict, Any, Optional


EXPORT_COLUMNS = [
    "SKU", "Product_Name", "Category", "Subcategory",
    "Vendibility", "Surface_cm2", "Vendibility_per_cm2",
    "Revenue", "Margin", "Selected", "Selection_Reason", "Scenario_Name",
]


def prepare_export_df(df: pd.DataFrame, scenario_name: str = "Default") -> pd.DataFrame:
    """Prepare the dataframe for export with standard columns."""
    export_df = df.copy()
    export_df["Scenario_Name"] = scenario_name

    # Keep only available export columns
    cols = [c for c in EXPORT_COLUMNS if c in export_df.columns]
    # Add any extra useful columns
    extras = ["Brand", "Country", "Channel", "Business_Segment",
              "Collection", "Units_Sold", "SellThrough", "Rotation",
              "Revenue_per_cm2", "Units_per_cm2", "Margin_per_cm2",
              "Rank_Category", "Rank_Segment"]
    for e in extras:
        if e in export_df.columns and e not in cols:
            cols.append(e)

    return export_df[cols]


def export_to_excel(df: pd.DataFrame) -> bytes:
    """Export a DataFrame to Excel bytes for download."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Assortment")
    return buffer.getvalue()


def export_optimization_results(
    df: pd.DataFrame,
    summary: Dict[str, Any],
    scenario_name: str = "Default",
) -> bytes:
    """Export full optimization results with multiple sheets."""
    buffer = io.BytesIO()
    export_df = prepare_export_df(df, scenario_name)
    selected_df = export_df[export_df["Selected"] == 1] if "Selected" in export_df.columns else export_df
    excluded_df = export_df[export_df["Selected"] == 0] if "Selected" in export_df.columns else pd.DataFrame()

    summary_df = pd.DataFrame([summary])

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        selected_df.to_excel(writer, index=False, sheet_name="Selected SKUs")
        excluded_df.to_excel(writer, index=False, sheet_name="Excluded SKUs")
        export_df.to_excel(writer, index=False, sheet_name="Full Diagnostic")
        summary_df.to_excel(writer, index=False, sheet_name="Summary")

    return buffer.getvalue()


def export_scenario_comparison(comparison_df: pd.DataFrame) -> bytes:
    """Export scenario comparison table to Excel."""
    return export_to_excel(comparison_df)


def generate_text_summary(df: pd.DataFrame, summary: Dict[str, Any]) -> str:
    """Generate a text business summary of the optimization results."""
    lines = []
    lines.append("=" * 60)
    lines.append("ASSORTMENT OPTIMIZATION SUMMARY")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Optimization Mode: {summary.get('optimization_mode', 'N/A')}")
    lines.append(f"Status: {summary.get('status', 'N/A')}")
    lines.append("")
    lines.append("--- KEY METRICS ---")
    lines.append(f"SKUs Selected: {summary.get('total_skus_selected', 0)} / {summary.get('total_skus_available', 0)}")
    lines.append(f"Total Vendibility: {summary.get('total_vendibility', 0)}")
    lines.append(f"Total Revenue: {summary.get('total_revenue', 0):,.2f}")
    lines.append(f"Total Margin: {summary.get('total_margin', 0):,.2f}")
    lines.append(f"Surface Used: {summary.get('total_surface_used', 0):,.0f} / {summary.get('total_surface_available', 0):,.0f} cm2")
    lines.append(f"Surface Utilization: {summary.get('surface_utilization_pct', 0):.1f}%")
    lines.append(f"Categories Represented: {summary.get('categories_represented', 0)}")
    lines.append("")

    # Category breakdown
    if "Selected" in df.columns and "Category" in df.columns:
        sel = df[df["Selected"] == 1]
        not_sel = df[df["Selected"] == 0]

        lines.append("--- CATEGORY BREAKDOWN (Selected) ---")
        cat_summary = sel.groupby("Category").agg(
            SKUs=("SKU", "count"),
            Total_Surface=("Surface_cm2", "sum"),
            Avg_Vendibility=("Vendibility", "mean"),
        ).round(2)
        for cat, row in cat_summary.iterrows():
            lines.append(f"  {cat}: {int(row['SKUs'])} SKUs, {row['Total_Surface']:,.0f} cm2, Avg Vend={row['Avg_Vendibility']:.3f}")

        lines.append("")
        lines.append("--- BUSINESS DIAGNOSTICS ---")

        # Identify top efficient and inefficient
        if "Vendibility_per_cm2" in sel.columns and len(sel) > 0:
            top_eff = sel.nlargest(3, "Vendibility_per_cm2")
            lines.append("Top 3 most space-efficient selected SKUs:")
            for _, row in top_eff.iterrows():
                name = row.get("Product_Name", row["SKU"])
                lines.append(f"  - {name} (Vend/cm2: {row['Vendibility_per_cm2']:.4f})")

        if "Vendibility_per_cm2" in not_sel.columns and len(not_sel) > 0:
            # Top excluded that had decent vendibility
            candidates = not_sel[not_sel["Vendibility"] > 0].nlargest(3, "Vendibility")
            if len(candidates) > 0:
                lines.append("")
                lines.append("Top 3 excluded SKUs with highest vendibility:")
                for _, row in candidates.iterrows():
                    name = row.get("Product_Name", row["SKU"])
                    reason = row.get("Selection_Reason", "")
                    lines.append(f"  - {name} (Vend: {row['Vendibility']:.3f}) - {reason}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)
