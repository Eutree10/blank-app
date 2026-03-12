"""
Visualizations Module
Creates Plotly charts for the assortment optimizer dashboard.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional


def scatter_vendibility_vs_surface(
    df: pd.DataFrame,
    size_col: str = "Revenue",
    color_col: str = "Category",
) -> go.Figure:
    """
    Scatter plot: Surface_cm2 vs Vendibility.
    Size = Revenue or Units. Color = Category. Highlight selected.
    """
    plot_df = df[df["Surface_cm2"] > 0].copy()
    if "Selected" in plot_df.columns:
        plot_df["Status"] = plot_df["Selected"].map({1: "Selected", 0: "Not Selected"})
    else:
        plot_df["Status"] = "N/A"

    size_values = plot_df[size_col].fillna(1).clip(lower=1) if size_col in plot_df.columns else 10

    fig = px.scatter(
        plot_df,
        x="Surface_cm2",
        y="Vendibility",
        size=size_values,
        color=color_col if color_col in plot_df.columns else None,
        symbol="Status" if "Status" in plot_df.columns else None,
        hover_data=["SKU", "Product_Name"] if "Product_Name" in plot_df.columns else ["SKU"],
        title="Vendibility vs Surface (size = {})".format(size_col),
        labels={"Surface_cm2": "Surface (cm2)", "Vendibility": "Vendibility Score"},
    )
    fig.update_layout(height=500)
    return fig


def bubble_productivity(df: pd.DataFrame) -> go.Figure:
    """
    Bubble chart: Surface_cm2 vs Vendibility_per_cm2.
    Color by selection status.
    """
    plot_df = df[(df["Surface_cm2"] > 0) & (df["Vendibility_per_cm2"].notna())].copy()
    if "Selected" in plot_df.columns:
        plot_df["Status"] = plot_df["Selected"].map({1: "Selected", 0: "Not Selected"})
    else:
        plot_df["Status"] = "N/A"

    fig = px.scatter(
        plot_df,
        x="Surface_cm2",
        y="Vendibility_per_cm2",
        color="Status",
        size="Vendibility",
        hover_data=["SKU", "Product_Name"] if "Product_Name" in plot_df.columns else ["SKU"],
        title="Space Productivity: Vendibility per cm2",
        color_discrete_map={"Selected": "#2ecc71", "Not Selected": "#e74c3c", "N/A": "#95a5a6"},
        labels={"Surface_cm2": "Surface (cm2)", "Vendibility_per_cm2": "Vendibility / cm2"},
    )
    fig.update_layout(height=500)
    return fig


def category_productivity_chart(df: pd.DataFrame) -> go.Figure:
    """Category-level average vendibility per cm2 and surface share."""
    if "Category" not in df.columns or "Selected" not in df.columns:
        return go.Figure()

    sel = df[df["Selected"] == 1]
    if len(sel) == 0:
        return go.Figure()

    cat_stats = sel.groupby("Category").agg(
        Avg_Vend_per_cm2=("Vendibility_per_cm2", "mean"),
        Total_Surface=("Surface_cm2", "sum"),
        SKU_Count=("SKU", "count"),
    ).reset_index()

    total_surface = cat_stats["Total_Surface"].sum()
    cat_stats["Surface_Share_Pct"] = (cat_stats["Total_Surface"] / total_surface * 100).round(1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=cat_stats["Category"],
        y=cat_stats["Avg_Vend_per_cm2"],
        name="Avg Vendibility/cm2",
        marker_color="#3498db",
    ))
    fig.add_trace(go.Bar(
        x=cat_stats["Category"],
        y=cat_stats["Surface_Share_Pct"],
        name="Surface Share %",
        marker_color="#e67e22",
        yaxis="y2",
    ))

    fig.update_layout(
        title="Category Productivity (Selected Assortment)",
        yaxis=dict(title="Avg Vendibility / cm2"),
        yaxis2=dict(title="Surface Share %", overlaying="y", side="right"),
        barmode="group",
        height=450,
    )
    return fig


def pareto_chart(df: pd.DataFrame) -> go.Figure:
    """Pareto chart: cumulative vendibility contribution by selected SKU."""
    if "Selected" not in df.columns:
        return go.Figure()

    sel = df[df["Selected"] == 1].sort_values("Vendibility", ascending=False).copy()
    if len(sel) == 0:
        return go.Figure()

    total_vend = sel["Vendibility"].sum()
    sel["Cumulative_Pct"] = (sel["Vendibility"].cumsum() / total_vend * 100).round(1)
    sel["Rank"] = range(1, len(sel) + 1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=sel["Rank"],
        y=sel["Vendibility"],
        name="Vendibility",
        marker_color="#2ecc71",
    ))
    fig.add_trace(go.Scatter(
        x=sel["Rank"],
        y=sel["Cumulative_Pct"],
        name="Cumulative %",
        yaxis="y2",
        mode="lines+markers",
        marker_color="#e74c3c",
    ))

    fig.update_layout(
        title="Pareto: Cumulative Vendibility by Selected SKU",
        xaxis_title="SKU Rank",
        yaxis=dict(title="Vendibility"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
        height=450,
    )
    return fig


def before_after_chart(
    df: pd.DataFrame,
    current_col: str = "Current_Store_Presence",
) -> go.Figure:
    """Compare current assortment vs optimized assortment by category."""
    if "Category" not in df.columns or "Selected" not in df.columns:
        return go.Figure()

    has_current = current_col in df.columns

    cat_data = []
    for cat in df["Category"].dropna().unique():
        cat_df = df[df["Category"] == cat]
        row = {"Category": cat}
        if has_current:
            row["Current_SKUs"] = cat_df[cat_df[current_col].fillna(0) > 0].shape[0] if has_current else 0
        else:
            row["Current_SKUs"] = 0
        row["Optimized_SKUs"] = cat_df[cat_df["Selected"] == 1].shape[0]
        cat_data.append(row)

    cat_df = pd.DataFrame(cat_data)

    fig = go.Figure()
    if has_current:
        fig.add_trace(go.Bar(
            x=cat_df["Category"],
            y=cat_df["Current_SKUs"],
            name="Current Assortment",
            marker_color="#95a5a6",
        ))
    fig.add_trace(go.Bar(
        x=cat_df["Category"],
        y=cat_df["Optimized_SKUs"],
        name="Optimized Assortment",
        marker_color="#2ecc71",
    ))

    fig.update_layout(
        title="Before vs After: SKU Count by Category",
        barmode="group",
        xaxis_title="Category",
        yaxis_title="Number of SKUs",
        height=450,
    )
    return fig


def scenario_comparison_chart(comparison_df: pd.DataFrame) -> go.Figure:
    """Bar chart comparing key metrics across scenarios."""
    if comparison_df.empty:
        return go.Figure()

    metrics = ["Total Vendibility", "Total Revenue", "SKUs Selected", "Surface Utilization %"]
    available_metrics = [m for m in metrics if m in comparison_df.columns]

    if not available_metrics:
        return go.Figure()

    fig = go.Figure()
    for metric in available_metrics:
        fig.add_trace(go.Bar(
            x=comparison_df["Scenario"],
            y=comparison_df[metric],
            name=metric,
        ))

    fig.update_layout(
        title="Scenario Comparison",
        barmode="group",
        height=450,
    )
    return fig
