"""
Retail Assortment Optimizer - Space Productivity Engine
=======================================================
A production-oriented Streamlit application that optimizes store assortment
for fashion/accessories retail by maximizing vendibility per occupied surface,
while respecting commercial, operational, and merchandising constraints.
"""

import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

from modules.data_loader import (
    load_product_data, load_surface_data, merge_datasets,
    check_required_columns, PRODUCT_REQUIRED_COLS, PRODUCT_RECOMMENDED_COLS,
    SURFACE_REQUIRED_COLS,
)
from modules.validators import validate_data, create_validation_report
from modules.vendibility_engine import (
    calculate_vendibility, DEFAULT_WEIGHTS, get_available_metrics,
)
from modules.surface_engine import compute_surface_metrics, get_surface_diagnostics
from modules.optimization_engine import (
    run_optimization, run_greedy_benchmark, OPTIMIZATION_MODES,
    MODE_MAX_VENDIBILITY, MODE_HYBRID,
)
from modules.scenario_engine import Scenario, ScenarioManager
from modules.visualizations import (
    scatter_vendibility_vs_surface, bubble_productivity,
    category_productivity_chart, pareto_chart, before_after_chart,
    scenario_comparison_chart,
)
from modules.exports import (
    export_to_excel, export_optimization_results,
    export_scenario_comparison, generate_text_summary,
)


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Retail Assortment Optimizer",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------------
# Helper: Generate sample mock data
# ---------------------------------------------------------------------------
def _generate_sample_data():
    """Generate sample product and surface data for testing."""
    np.random.seed(42)
    n = 150
    categories = ["Earrings", "Necklaces", "Bracelets", "Rings", "Bags",
                   "Hair Accessories", "Scarves", "Belts"]
    subcategories = {
        "Earrings": ["Studs", "Hoops", "Drop"],
        "Necklaces": ["Chains", "Pendants", "Chokers"],
        "Bracelets": ["Bangles", "Chains", "Cuffs"],
        "Rings": ["Bands", "Statement", "Stackable"],
        "Bags": ["Clutch", "Tote", "Crossbody"],
        "Hair Accessories": ["Clips", "Headbands", "Scrunchies"],
        "Scarves": ["Silk", "Wool", "Cotton"],
        "Belts": ["Leather", "Fabric", "Chain"],
    }
    brands = ["Lumina", "Aurelia", "Stella", "Vogue", "Elegance"]
    collections = ["SS26", "FW25", "Core", "Limited Edition", "Resort26"]
    countries = ["France", "Italy", "Spain", "Germany", "UK"]
    channels = ["Retail", "Outlet", "Travel Retail"]

    data = []
    for i in range(n):
        cat = np.random.choice(categories)
        subcat = np.random.choice(subcategories[cat])
        data.append({
            "SKU": f"SKU-{i+1:04d}",
            "Product_Name": f"{np.random.choice(brands)} {cat} {subcat} {i+1}",
            "Brand": np.random.choice(brands),
            "Country": np.random.choice(countries),
            "Channel": np.random.choice(channels),
            "Business_Segment": "Fashion Accessories",
            "Category": cat,
            "Subcategory": subcat,
            "Collection": np.random.choice(collections),
            "Units_Sold": max(0, int(np.random.lognormal(4, 1.2))),
            "Revenue": round(max(0, np.random.lognormal(6, 1.5)), 2),
            "SellThrough": round(min(1.0, max(0, np.random.beta(3, 2))), 3),
            "Rotation": round(max(0, np.random.exponential(2.5)), 2),
            "Margin": round(max(0, np.random.lognormal(5, 1.3)), 2),
            "Current_Store_Presence": np.random.choice([0, 1], p=[0.3, 0.7]),
        })

    product_df = pd.DataFrame(data)

    surface_data = []
    for i in range(n):
        cat = product_df.loc[i, "Category"]
        if cat in ["Bags"]:
            w, d = np.random.uniform(25, 50), np.random.uniform(15, 35)
            units = np.random.choice([1, 2])
        elif cat in ["Scarves", "Belts"]:
            w, d = np.random.uniform(15, 30), np.random.uniform(10, 25)
            units = np.random.choice([1, 2, 3])
        else:
            w, d = np.random.uniform(5, 20), np.random.uniform(5, 15)
            units = np.random.choice([1, 2, 3, 4])

        surface_data.append({
            "SKU": f"SKU-{i+1:04d}",
            "Width_cm": round(w, 1),
            "Depth_cm": round(d, 1),
            "Display_units": int(units),
            "Height_cm": round(np.random.uniform(3, 20), 1),
            "Display_type": np.random.choice(["Shelf", "Hook", "Tray", "Stand"]),
        })

    surface_df = pd.DataFrame(surface_data)

    st.session_state.sample_product_df = product_df
    st.session_state.sample_surface_df = surface_df

    merged, diag = merge_datasets(product_df, surface_df)
    st.session_state.merged_df = merged
    st.session_state.diagnostics = diag
    st.session_state.product_df_raw = product_df
    st.session_state.surface_df_raw = surface_df
    st.toast("Sample data generated successfully!")


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "merged_df" not in st.session_state:
    st.session_state.merged_df = None
if "diagnostics" not in st.session_state:
    st.session_state.diagnostics = None
if "vend_df" not in st.session_state:
    st.session_state.vend_df = None
if "opt_df" not in st.session_state:
    st.session_state.opt_df = None
if "opt_summary" not in st.session_state:
    st.session_state.opt_summary = None
if "scenario_manager" not in st.session_state:
    st.session_state.scenario_manager = ScenarioManager()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("Assortment Optimizer")
    st.caption("Space Productivity Engine v1.0")
    st.markdown("---")
    st.markdown("**Navigation**")
    st.markdown(
        "Use the tabs to navigate: "
        "Load Data > Vendibility > Surface > Optimize > Results > Scenarios"
    )
    st.markdown("---")

    if st.session_state.merged_df is not None:
        df_info = st.session_state.merged_df
        st.metric("Total SKUs Loaded", len(df_info))
        if "Category" in df_info.columns:
            st.metric("Categories", df_info["Category"].nunique())
        if "Surface_cm2" in df_info.columns:
            valid_s = (df_info["Surface_cm2"] > 0).sum()
            st.metric("SKUs with Surface", valid_s)
    else:
        st.info("Upload data to begin")

    if st.session_state.opt_summary is not None:
        st.markdown("---")
        st.markdown("**Last Optimization**")
        s = st.session_state.opt_summary
        st.metric("Selected SKUs", s.get("total_skus_selected", 0))
        st.metric("Surface Util.", f"{s.get('surface_utilization_pct', 0):.1f}%")

    st.markdown("---")
    if st.button("Generate Sample Data", use_container_width=True):
        _generate_sample_data()


# ---------------------------------------------------------------------------
# Main Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Data Load",
    "2. Vendibility Engine",
    "3. Surface Analytics",
    "4. Optimization Setup",
    "5. Optimization Results",
    "6. Scenario Comparison",
])


# ===========================
# TAB 1: DATA LOAD
# ===========================
with tab1:
    st.header("Data Load & Validation")
    st.markdown(
        "Upload your product performance data and surface/display data. "
        "The system will validate, merge, and prepare data for optimization."
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Product Performance Data")
        product_file = st.file_uploader(
            "Upload CSV, Excel, or Parquet",
            type=["csv", "xlsx", "xls", "parquet"],
            key="product_upload",
        )
        if product_file:
            product_df = load_product_data(product_file)
            if product_df is not None:
                st.session_state.product_df_raw = product_df
                st.success(f"Loaded {len(product_df)} rows, {len(product_df.columns)} columns")
                present, missing = check_required_columns(product_df, PRODUCT_REQUIRED_COLS)
                if missing:
                    st.error(f"Missing required columns: {missing}")
                else:
                    st.success("All required columns present")
                rec_present, rec_missing = check_required_columns(product_df, PRODUCT_RECOMMENDED_COLS)
                if rec_missing:
                    st.warning(f"Missing recommended columns (will use defaults): {rec_missing}")
                with st.expander("Preview Product Data"):
                    st.dataframe(product_df.head(20), use_container_width=True)

    with col2:
        st.subheader("Surface / Display Data")
        surface_file = st.file_uploader(
            "Upload Excel or CSV with surface dimensions",
            type=["csv", "xlsx", "xls"],
            key="surface_upload",
        )
        if surface_file:
            surface_df = load_surface_data(surface_file)
            if surface_df is not None:
                st.session_state.surface_df_raw = surface_df
                st.success(f"Loaded {len(surface_df)} rows")
                s_present, s_missing = check_required_columns(surface_df, SURFACE_REQUIRED_COLS)
                if s_missing:
                    st.error(f"Missing required columns: {s_missing}")
                else:
                    st.success("All required surface columns present")
                with st.expander("Preview Surface Data"):
                    st.dataframe(surface_df.head(20), use_container_width=True)

    st.markdown("---")

    if st.button("Merge & Validate Data", type="primary", use_container_width=True):
        if "product_df_raw" in st.session_state and "surface_df_raw" in st.session_state:
            merged, diag = merge_datasets(
                st.session_state.product_df_raw,
                st.session_state.surface_df_raw,
            )
            st.session_state.merged_df = merged
            st.session_state.diagnostics = diag
            st.success("Data merged successfully!")
        elif "product_df_raw" in st.session_state:
            merged = st.session_state.product_df_raw.copy()
            merged["Surface_cm2"] = 0.0
            st.session_state.merged_df = merged
            st.session_state.diagnostics = {
                "total_product_skus": len(merged),
                "total_surface_skus": 0,
                "matched_skus": 0,
                "only_in_product": [],
                "only_in_surface": [],
            }
            st.warning("No surface data uploaded. Surface values will need manual entry.")
        else:
            st.error("Please upload product data first (or use 'Generate Sample Data' in the sidebar)")

    # Show merge diagnostics
    if st.session_state.diagnostics is not None:
        diag = st.session_state.diagnostics
        st.subheader("Merge Diagnostics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Product SKUs", diag["total_product_skus"])
        c2.metric("Surface SKUs", diag["total_surface_skus"])
        c3.metric("Matched SKUs", diag["matched_skus"])

        if diag["only_in_product"]:
            with st.expander(f"SKUs only in product data ({len(diag['only_in_product'])})"):
                st.write(diag["only_in_product"][:50])
        if diag["only_in_surface"]:
            with st.expander(f"SKUs only in surface data ({len(diag['only_in_surface'])})"):
                st.write(diag["only_in_surface"][:50])

    # Validation
    if st.session_state.merged_df is not None:
        st.subheader("Data Validation")
        val_result = validate_data(st.session_state.merged_df)

        vc1, vc2 = st.columns(2)
        vc1.metric("Warnings", val_result["total_warnings"],
                    delta_color="inverse" if val_result["total_warnings"] > 0 else "off")
        vc2.metric("Errors", val_result["total_errors"],
                    delta_color="inverse" if val_result["total_errors"] > 0 else "off")

        if val_result["issues"]:
            for issue in val_result["issues"]:
                icon = "WARNING" if issue["type"] == "warning" else "ERROR"
                st.markdown(f"**{icon}** | {issue['check']}: {issue['details']}")

            report_df = create_validation_report(val_result)
            report_bytes = export_to_excel(report_df)
            st.download_button(
                "Download Validation Report",
                data=report_bytes,
                file_name="validation_report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        else:
            st.success("All validation checks passed!")


# ===========================
# TAB 2: VENDIBILITY ENGINE
# ===========================
with tab2:
    st.header("Vendibility Engine")

    if st.session_state.merged_df is None:
        st.warning("Please load and merge data first (Tab 1)")
    else:
        df = st.session_state.merged_df.copy()
        available_metrics = get_available_metrics(df)

        st.subheader("Vendibility Score Configuration")

        use_existing = False
        if "Vendibility_Score" in df.columns:
            use_existing = st.checkbox(
                "Use existing Vendibility_Score column",
                value=True,
                help="If checked, uses the pre-calculated vendibility. Otherwise recalculates."
            )

        if not use_existing:
            st.markdown("**Adjust metric weights** (auto-normalized for available metrics)")
            if available_metrics:
                weight_cols = st.columns(min(len(available_metrics), 5))
                custom_weights = {}
                for i, metric in enumerate(available_metrics):
                    with weight_cols[i % len(weight_cols)]:
                        default_w = DEFAULT_WEIGHTS.get(metric, 0.1)
                        custom_weights[metric] = st.slider(
                            metric, 0.0, 1.0, default_w, 0.05, key=f"w_{metric}"
                        )
            else:
                custom_weights = {}
                st.warning("No vendibility metrics found in data.")
        else:
            custom_weights = None

        if st.button("Calculate Vendibility", type="primary"):
            vend_df = calculate_vendibility(
                df,
                weights=custom_weights,
                use_existing=use_existing,
            )
            vend_df = compute_surface_metrics(vend_df)
            st.session_state.vend_df = vend_df
            st.session_state.merged_df = vend_df
            st.success("Vendibility calculated!")

        if st.session_state.vend_df is not None:
            vdf = st.session_state.vend_df

            st.subheader("Vendibility Distribution")
            c1, c2, c3 = st.columns(3)
            c1.metric("Mean Vendibility", f"{vdf['Vendibility'].mean():.4f}")
            c2.metric("Median Vendibility", f"{vdf['Vendibility'].median():.4f}")
            c3.metric("Std Dev", f"{vdf['Vendibility'].std():.4f}")

            norm_cols = [c for c in vdf.columns if c.startswith("norm_")]
            if norm_cols:
                with st.expander("Normalized Variables"):
                    display_cols = ["SKU", "Product_Name", "Category"] + norm_cols + ["Vendibility"]
                    display_cols = [c for c in display_cols if c in vdf.columns]
                    st.dataframe(
                        vdf[display_cols].sort_values("Vendibility", ascending=False).head(30),
                        use_container_width=True,
                    )

            st.subheader("Vendibility Rankings")
            rank_tab1, rank_tab2 = st.tabs(["Top SKUs", "Bottom SKUs"])
            rank_cols = ["SKU", "Product_Name", "Category", "Subcategory", "Vendibility",
                         "Rank_Category", "Rank_Segment"]
            rank_cols = [c for c in rank_cols if c in vdf.columns]

            with rank_tab1:
                st.dataframe(
                    vdf[rank_cols].sort_values("Vendibility", ascending=False).head(20),
                    use_container_width=True,
                )
            with rank_tab2:
                st.dataframe(
                    vdf[rank_cols].sort_values("Vendibility", ascending=True).head(20),
                    use_container_width=True,
                )


# ===========================
# TAB 3: SURFACE ANALYTICS
# ===========================
with tab3:
    st.header("Surface Analytics")

    if st.session_state.merged_df is None:
        st.warning("Please load and merge data first (Tab 1)")
    else:
        df = st.session_state.merged_df.copy()
        if "Vendibility" not in df.columns:
            st.info("Calculate vendibility first (Tab 2) for full surface productivity metrics.")

        if "Vendibility_per_cm2" not in df.columns and "Vendibility" in df.columns:
            df = compute_surface_metrics(df)
            st.session_state.merged_df = df

        diag = get_surface_diagnostics(df)

        st.subheader("Surface Data Quality")
        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("Total SKUs", diag["total_skus"])
        sc2.metric("Valid Surface", diag["valid_surface"])
        sc3.metric("Zero Surface", diag["zero_surface"])
        sc4.metric("Missing Surface", diag["missing_surface"])

        if diag["stats"]:
            st.subheader("Surface Distribution")
            sc5, sc6, sc7, sc8 = st.columns(4)
            sc5.metric("Mean (cm2)", f"{diag['stats']['mean']:,.1f}")
            sc6.metric("Median (cm2)", f"{diag['stats']['median']:,.1f}")
            sc7.metric("Min (cm2)", f"{diag['stats']['min']:,.1f}")
            sc8.metric("Max (cm2)", f"{diag['stats']['max']:,.1f}")

        st.subheader("Surface per SKU")
        surface_cols = ["SKU", "Product_Name", "Category", "Surface_cm2"]
        if "Vendibility_per_cm2" in df.columns:
            surface_cols.extend(["Vendibility_per_cm2", "Revenue_per_cm2", "Units_per_cm2", "Margin_per_cm2"])
        surface_cols = [c for c in surface_cols if c in df.columns]
        valid_surface_df = df[df["Surface_cm2"] > 0][surface_cols].sort_values("Surface_cm2", ascending=False)
        st.dataframe(valid_surface_df.head(50), use_container_width=True)

        if diag["stats"] and diag["stats"].get("std", 0) > 0:
            threshold = diag["stats"]["mean"] + 3 * diag["stats"]["std"]
            suspicious = df[df["Surface_cm2"] > threshold]
            if len(suspicious) > 0:
                st.subheader("Suspicious High Surface SKUs")
                st.warning(f"{len(suspicious)} SKUs with surface > {threshold:,.0f} cm2 (mean + 3 std)")
                st.dataframe(suspicious[surface_cols], use_container_width=True)

        zero_df = df[df["Surface_cm2"] <= 0]
        if len(zero_df) > 0:
            with st.expander(f"SKUs with zero/missing surface ({len(zero_df)})"):
                zcols = ["SKU", "Product_Name", "Category", "Surface_cm2"]
                zcols = [c for c in zcols if c in zero_df.columns]
                st.dataframe(zero_df[zcols], use_container_width=True)

        st.subheader("Manual Surface Override")
        st.markdown("Override surface values for specific SKUs:")
        override_sku = st.selectbox(
            "Select SKU to override",
            options=df["SKU"].tolist(),
            key="surface_override_sku",
        )
        override_val = st.number_input(
            "New Surface (cm2)",
            min_value=0.0, value=0.0, step=10.0,
            key="surface_override_val",
        )
        if st.button("Apply Override"):
            if override_val > 0:
                idx = df[df["SKU"] == override_sku].index
                st.session_state.merged_df.loc[idx, "Surface_cm2"] = override_val
                if "Vendibility" in st.session_state.merged_df.columns:
                    st.session_state.merged_df = compute_surface_metrics(st.session_state.merged_df)
                st.success(f"Updated surface for {override_sku} to {override_val} cm2")


# ===========================
# TAB 4: OPTIMIZATION SETUP
# ===========================
with tab4:
    st.header("Optimization Setup")

    if st.session_state.merged_df is None:
        st.warning("Please load data and calculate vendibility first (Tabs 1-2)")
    else:
        df = st.session_state.merged_df.copy()

        if "Vendibility" not in df.columns:
            st.warning("Please calculate vendibility first (Tab 2)")
        else:
            # ---- Filters ----
            st.subheader("Filters")
            fc1, fc2 = st.columns(2)

            with fc1:
                seg_opts = (["All"] + sorted(df["Business_Segment"].dropna().unique().tolist())
                            if "Business_Segment" in df.columns else ["All"])
                selected_segment = st.selectbox("Business Segment", seg_opts)

                cat_opts = sorted(df["Category"].dropna().unique().tolist()) if "Category" in df.columns else []
                selected_categories = st.multiselect("Filter Categories", cat_opts, default=cat_opts)

            with fc2:
                brand_opts = sorted(df["Brand"].dropna().unique().tolist()) if "Brand" in df.columns else []
                selected_brands = st.multiselect("Filter Brands", brand_opts, default=brand_opts)

                chan_opts = sorted(df["Channel"].dropna().unique().tolist()) if "Channel" in df.columns else []
                selected_channels = st.multiselect("Filter Channels", chan_opts, default=chan_opts)

            filtered = df.copy()
            if selected_segment != "All" and "Business_Segment" in filtered.columns:
                filtered = filtered[filtered["Business_Segment"] == selected_segment]
            if selected_categories and "Category" in filtered.columns:
                filtered = filtered[filtered["Category"].isin(selected_categories)]
            if selected_brands and "Brand" in filtered.columns:
                filtered = filtered[filtered["Brand"].isin(selected_brands)]
            if selected_channels and "Channel" in filtered.columns:
                filtered = filtered[filtered["Channel"].isin(selected_channels)]

            st.info(f"Filtered dataset: {len(filtered)} SKUs")

            st.markdown("---")

            # ---- Store capacity ----
            st.subheader("Store Capacity & Scenario")
            cap1, cap2 = st.columns(2)
            with cap1:
                total_surface = st.number_input(
                    "Total Available Display Surface (cm2)",
                    min_value=1000.0, max_value=10000000.0,
                    value=50000.0, step=5000.0,
                )
            with cap2:
                scenario_name = st.text_input("Scenario Name", value="Default Scenario")

            # ---- Optimization Mode ----
            st.subheader("Optimization Mode")
            opt_mode = st.selectbox("Optimization Target", OPTIMIZATION_MODES)

            hybrid_weights = None
            if opt_mode == MODE_HYBRID:
                st.markdown("**Hybrid Score Weights**")
                hc1, hc2, hc3 = st.columns(3)
                with hc1:
                    hw_vend = st.slider("Vendibility Weight", 0.0, 1.0, 0.5, 0.05)
                with hc2:
                    hw_rev = st.slider("Revenue Weight", 0.0, 1.0, 0.3, 0.05)
                with hc3:
                    hw_margin = st.slider("Margin Weight", 0.0, 1.0, 0.2, 0.05)
                hybrid_weights = {"Vendibility": hw_vend, "Revenue": hw_rev, "Margin": hw_margin}

            st.markdown("---")

            # ---- Category Constraints ----
            st.subheader("Category Constraints")
            cats_in_data = sorted(filtered["Category"].dropna().unique().tolist()) if "Category" in filtered.columns else []

            use_min_skus = st.checkbox("Set minimum SKUs per category")
            min_skus_per_cat = {}
            if use_min_skus and cats_in_data:
                cols = st.columns(min(4, len(cats_in_data)))
                for i, cat in enumerate(cats_in_data):
                    with cols[i % len(cols)]:
                        val = st.number_input(f"Min SKUs: {cat}", min_value=0, max_value=50, value=0, key=f"min_sku_{cat}")
                        if val > 0:
                            min_skus_per_cat[cat] = val

            use_min_surface_pct = st.checkbox("Set minimum surface % per category")
            min_surface_pct = {}
            if use_min_surface_pct and cats_in_data:
                cols = st.columns(min(4, len(cats_in_data)))
                for i, cat in enumerate(cats_in_data):
                    with cols[i % len(cols)]:
                        val = st.number_input(f"Min Surface %: {cat}", min_value=0.0, max_value=50.0, value=0.0, step=1.0, key=f"min_spct_{cat}")
                        if val > 0:
                            min_surface_pct[cat] = val

            use_max_surface_pct = st.checkbox("Set maximum surface % per category")
            max_surface_pct = {}
            if use_max_surface_pct and cats_in_data:
                cols = st.columns(min(4, len(cats_in_data)))
                for i, cat in enumerate(cats_in_data):
                    with cols[i % len(cols)]:
                        val = st.number_input(f"Max Surface %: {cat}", min_value=0.0, max_value=100.0, value=50.0, step=5.0, key=f"max_spct_{cat}")
                        if val < 100:
                            max_surface_pct[cat] = val

            st.markdown("---")

            # ---- Variety Constraints ----
            st.subheader("Assortment Variety Constraints")
            vc1, vc2, vc3 = st.columns(3)
            with vc1:
                min_cats = st.number_input("Min distinct categories", min_value=0, max_value=20, value=0)
            with vc2:
                min_subcats = st.number_input("Min distinct subcategories", min_value=0, max_value=50, value=0)
            with vc3:
                min_colls = st.number_input("Min distinct collections", min_value=0, max_value=20, value=0)

            max_sku_pct_subcat = st.number_input(
                "Max SKU % per subcategory (0 = no limit)",
                min_value=0.0, max_value=100.0, value=0.0, step=5.0,
            )

            st.markdown("---")

            # ---- Mandatory Inclusions/Exclusions ----
            st.subheader("Mandatory Inclusions / Exclusions")
            all_skus = filtered["SKU"].tolist()
            mandatory_include = st.multiselect(
                "Force include these SKUs (hero products, launches, core assortment)",
                options=all_skus, key="mandatory_include",
            )
            mandatory_exclude = st.multiselect(
                "Force exclude these SKUs (blocked, quality issues)",
                options=all_skus, key="mandatory_exclude",
            )

            min_display = st.number_input(
                "Minimum display surface per selected SKU (cm2, 0 = no minimum)",
                min_value=0.0, max_value=5000.0, value=0.0, step=10.0,
            )

            st.markdown("---")

            # ---- RUN OPTIMIZATION ----
            if st.button("Run Optimization", type="primary", use_container_width=True):
                with st.spinner("Running optimization..."):
                    opt_df, opt_summary = run_optimization(
                        df=filtered,
                        total_surface=total_surface,
                        mode=opt_mode,
                        hybrid_weights=hybrid_weights,
                        min_skus_per_category=min_skus_per_cat if min_skus_per_cat else None,
                        min_surface_pct_per_category=min_surface_pct if min_surface_pct else None,
                        max_surface_pct_per_category=max_surface_pct if max_surface_pct else None,
                        max_sku_pct_per_subcategory=max_sku_pct_subcat if max_sku_pct_subcat > 0 else None,
                        min_categories=min_cats if min_cats > 0 else None,
                        min_subcategories=min_subcats if min_subcats > 0 else None,
                        min_collections=min_colls if min_colls > 0 else None,
                        mandatory_include=mandatory_include if mandatory_include else None,
                        mandatory_exclude=mandatory_exclude if mandatory_exclude else None,
                        min_display_surface=min_display if min_display > 0 else None,
                    )

                    st.session_state.opt_df = opt_df
                    st.session_state.opt_summary = opt_summary

                    scenario = Scenario(
                        name=scenario_name,
                        total_surface=total_surface,
                        optimization_mode=opt_mode,
                        segment_filter=selected_segment if selected_segment != "All" else None,
                        category_filters=selected_categories,
                        hybrid_weights=hybrid_weights,
                        min_skus_per_category=min_skus_per_cat if min_skus_per_cat else None,
                        min_surface_pct_per_category=min_surface_pct if min_surface_pct else None,
                        max_surface_pct_per_category=max_surface_pct if max_surface_pct else None,
                        max_sku_pct_per_subcategory=max_sku_pct_subcat if max_sku_pct_subcat > 0 else None,
                        min_categories=min_cats if min_cats > 0 else None,
                        min_subcategories=min_subcats if min_subcats > 0 else None,
                        min_collections=min_colls if min_colls > 0 else None,
                        mandatory_include=mandatory_include if mandatory_include else None,
                        mandatory_exclude=mandatory_exclude if mandatory_exclude else None,
                        min_display_surface=min_display if min_display > 0 else None,
                        results_summary=opt_summary,
                        selected_skus=opt_df[opt_df["Selected"] == 1]["SKU"].tolist() if "Selected" in opt_df.columns else [],
                    )
                    st.session_state.scenario_manager.add_scenario(scenario)

                    if opt_summary["status"] == "Optimal":
                        st.success(f"Optimization complete! Selected {opt_summary['total_skus_selected']} SKUs. Go to Tab 5 for results.")
                    else:
                        st.warning(f"Optimization status: {opt_summary['status']}. Check constraints for feasibility.")

            if st.checkbox("Also run greedy benchmark for comparison"):
                if st.button("Run Greedy Benchmark"):
                    greedy_df, greedy_summary = run_greedy_benchmark(filtered, total_surface, opt_mode, hybrid_weights)
                    st.subheader("Greedy Benchmark Results")
                    gc1, gc2, gc3 = st.columns(3)
                    gc1.metric("Greedy SKUs", greedy_summary["total_skus_selected"])
                    gc2.metric("Greedy Vendibility", f"{greedy_summary['total_vendibility']:.4f}")
                    gc3.metric("Greedy Surface Used", f"{greedy_summary['total_surface_used']:,.0f}")


# ===========================
# TAB 5: OPTIMIZATION RESULTS
# ===========================
with tab5:
    st.header("Optimization Results")

    if st.session_state.opt_df is None or st.session_state.opt_summary is None:
        st.warning("Run optimization first (Tab 4)")
    else:
        opt_df = st.session_state.opt_df
        summary = st.session_state.opt_summary

        st.subheader("Key Performance Indicators")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Status", summary["status"])
        k2.metric("SKUs Selected", f"{summary['total_skus_selected']} / {summary['total_skus_available']}")
        k3.metric("Surface Utilization", f"{summary['surface_utilization_pct']:.1f}%")
        k4.metric("Categories", summary["categories_represented"])

        k5, k6, k7, k8 = st.columns(4)
        k5.metric("Total Vendibility", f"{summary['total_vendibility']:.4f}")
        k6.metric("Total Revenue", f"{summary['total_revenue']:,.2f}")
        k7.metric("Total Margin", f"{summary['total_margin']:,.2f}")
        k8.metric("Remaining Surface", f"{summary['remaining_surface']:,.0f} cm2")

        st.markdown("---")

        sel_tab, exc_tab, comp_tab = st.tabs(["Selected SKUs", "Excluded SKUs", "Selected vs Not Selected"])

        display_cols = ["SKU", "Product_Name", "Category", "Subcategory", "Vendibility",
                        "Surface_cm2", "Vendibility_per_cm2", "Revenue", "Margin",
                        "Selection_Reason"]
        display_cols = [c for c in display_cols if c in opt_df.columns]

        with sel_tab:
            sel = opt_df[opt_df["Selected"] == 1][display_cols].sort_values("Vendibility", ascending=False)
            st.dataframe(sel, use_container_width=True, height=400)

        with exc_tab:
            exc = opt_df[opt_df["Selected"] == 0][display_cols].sort_values("Vendibility", ascending=False)
            st.dataframe(exc, use_container_width=True, height=400)

        with comp_tab:
            sel_data = opt_df[opt_df["Selected"] == 1]
            not_sel_data = opt_df[opt_df["Selected"] == 0]
            comp_metrics = {
                "Metric": ["Count", "Avg Vendibility", "Avg Surface", "Avg Vendibility/cm2",
                           "Total Revenue", "Total Margin"],
                "Selected": [
                    len(sel_data),
                    round(sel_data["Vendibility"].mean(), 4) if len(sel_data) > 0 else 0,
                    round(sel_data["Surface_cm2"].mean(), 1) if len(sel_data) > 0 else 0,
                    round(sel_data["Vendibility_per_cm2"].mean(), 6) if "Vendibility_per_cm2" in sel_data.columns and len(sel_data) > 0 else 0,
                    round(sel_data["Revenue"].sum(), 2) if "Revenue" in sel_data.columns else 0,
                    round(sel_data["Margin"].sum(), 2) if "Margin" in sel_data.columns else 0,
                ],
                "Not Selected": [
                    len(not_sel_data),
                    round(not_sel_data["Vendibility"].mean(), 4) if len(not_sel_data) > 0 else 0,
                    round(not_sel_data["Surface_cm2"].mean(), 1) if len(not_sel_data) > 0 else 0,
                    round(not_sel_data["Vendibility_per_cm2"].mean(), 6) if "Vendibility_per_cm2" in not_sel_data.columns and len(not_sel_data) > 0 else 0,
                    round(not_sel_data["Revenue"].sum(), 2) if "Revenue" in not_sel_data.columns else 0,
                    round(not_sel_data["Margin"].sum(), 2) if "Margin" in not_sel_data.columns else 0,
                ],
            }
            st.dataframe(pd.DataFrame(comp_metrics), use_container_width=True)

        st.markdown("---")

        if "Category" in opt_df.columns:
            st.subheader("Category Breakdown (Selected)")
            sel_only = opt_df[opt_df["Selected"] == 1]
            agg_dict = {
                "SKUs": ("SKU", "count"),
                "Total_Surface": ("Surface_cm2", "sum"),
                "Total_Vendibility": ("Vendibility", "sum"),
            }
            if "Vendibility_per_cm2" in sel_only.columns:
                agg_dict["Avg_Vend_per_cm2"] = ("Vendibility_per_cm2", "mean")
            if "Revenue" in sel_only.columns:
                agg_dict["Total_Revenue"] = ("Revenue", "sum")

            cat_breakdown = sel_only.groupby("Category").agg(**agg_dict).round(3)
            cat_breakdown = cat_breakdown.sort_values("Total_Vendibility", ascending=False)
            st.dataframe(cat_breakdown, use_container_width=True)

        st.markdown("---")

        # Charts
        st.subheader("Visualizations")
        chart_tab1, chart_tab2, chart_tab3, chart_tab4, chart_tab5 = st.tabs([
            "Scatter", "Bubble Productivity", "Category Productivity", "Pareto", "Before vs After"
        ])

        with chart_tab1:
            size_opts = [c for c in ["Revenue", "Units_Sold", "Margin"] if c in opt_df.columns]
            size_option = st.selectbox("Size by", size_opts if size_opts else ["Revenue"], key="scatter_size")
            fig = scatter_vendibility_vs_surface(opt_df, size_col=size_option)
            st.plotly_chart(fig, use_container_width=True)

        with chart_tab2:
            fig = bubble_productivity(opt_df)
            st.plotly_chart(fig, use_container_width=True)

        with chart_tab3:
            fig = category_productivity_chart(opt_df)
            st.plotly_chart(fig, use_container_width=True)

        with chart_tab4:
            fig = pareto_chart(opt_df)
            st.plotly_chart(fig, use_container_width=True)

        with chart_tab5:
            fig = before_after_chart(opt_df)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Business summary
        st.subheader("Business Summary")
        text_summary = generate_text_summary(opt_df, summary)
        st.text(text_summary)

        # Exports
        st.subheader("Export Results")
        exp1, exp2, exp3 = st.columns(3)

        with exp1:
            excel_bytes = export_optimization_results(opt_df, summary, scenario_name="Optimization")
            st.download_button(
                "Download Full Results (Excel)",
                data=excel_bytes,
                file_name="optimization_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with exp2:
            sel_only_export = opt_df[opt_df["Selected"] == 1]
            sel_bytes = export_to_excel(sel_only_export)
            st.download_button(
                "Download Selected SKUs Only",
                data=sel_bytes,
                file_name="selected_skus.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        with exp3:
            st.download_button(
                "Download Business Summary (TXT)",
                data=text_summary,
                file_name="business_summary.txt",
                mime="text/plain",
            )


# ===========================
# TAB 6: SCENARIO COMPARISON
# ===========================
with tab6:
    st.header("Scenario Comparison")

    sm = st.session_state.scenario_manager
    scenarios = sm.list_scenarios()

    if not scenarios:
        st.info("No scenarios saved yet. Run optimizations from Tab 4 to create scenarios.")
    else:
        st.subheader(f"Saved Scenarios ({len(scenarios)})")

        comparison_df = sm.get_comparison_table()
        st.dataframe(comparison_df, use_container_width=True)

        if len(scenarios) >= 2:
            st.subheader("Side-by-Side Comparison")
            fig = scenario_comparison_chart(comparison_df)
            st.plotly_chart(fig, use_container_width=True)

        if len(comparison_df) > 0:
            comp_bytes = export_scenario_comparison(comparison_df)
            st.download_button(
                "Download Scenario Comparison (Excel)",
                data=comp_bytes,
                file_name="scenario_comparison.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        st.subheader("Manage Scenarios")
        to_remove = st.selectbox("Remove scenario", [""] + scenarios)
        if to_remove and st.button("Remove Selected Scenario"):
            sm.remove_scenario(to_remove)
            st.success(f"Removed scenario: {to_remove}")
            st.rerun()
