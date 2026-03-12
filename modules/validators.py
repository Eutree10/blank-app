"""
Data Validation Module
Validates data quality, detects issues, and produces validation reports.
"""

import pandas as pd
from typing import List, Dict, Any


def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run all validation checks on the merged dataset.
    Returns a dict with warnings, errors, and detailed issue lists.
    """
    issues = []
    warnings = 0
    errors = 0

    # 1. Duplicate SKUs
    dup_skus = df[df.duplicated(subset=["SKU"], keep=False)]["SKU"].unique().tolist()
    if dup_skus:
        errors += len(dup_skus)
        issues.append({
            "type": "error",
            "check": "Duplicate SKUs",
            "count": len(dup_skus),
            "details": f"SKUs with duplicates: {dup_skus[:20]}{'...' if len(dup_skus) > 20 else ''}",
            "skus": dup_skus,
        })

    # 2. Negative or zero surface
    if "Surface_cm2" in df.columns:
        bad_surface = df[df["Surface_cm2"] <= 0]
        if len(bad_surface) > 0:
            warnings += len(bad_surface)
            issues.append({
                "type": "warning",
                "check": "Zero or negative surface",
                "count": len(bad_surface),
                "details": f"{len(bad_surface)} SKUs have surface <= 0",
                "skus": bad_surface["SKU"].tolist(),
            })

    # 3. Missing vendibility inputs
    vend_cols = ["Units_Sold", "Revenue", "SellThrough", "Rotation"]
    for col in vend_cols:
        if col in df.columns:
            missing = df[df[col].isna()]
            if len(missing) > 0:
                warnings += len(missing)
                issues.append({
                    "type": "warning",
                    "check": f"Missing {col}",
                    "count": len(missing),
                    "details": f"{len(missing)} SKUs have missing {col}",
                    "skus": missing["SKU"].tolist(),
                })

    # 4. Extreme surface outliers (>3 std deviations)
    if "Surface_cm2" in df.columns:
        valid_surface = df[df["Surface_cm2"] > 0]["Surface_cm2"]
        if len(valid_surface) > 5:
            mean_s = valid_surface.mean()
            std_s = valid_surface.std()
            if std_s > 0:
                outliers = df[
                    (df["Surface_cm2"] > 0) &
                    (df["Surface_cm2"] > mean_s + 3 * std_s)
                ]
                if len(outliers) > 0:
                    warnings += len(outliers)
                    issues.append({
                        "type": "warning",
                        "check": "Surface outliers (>3 std)",
                        "count": len(outliers),
                        "details": f"{len(outliers)} SKUs have unusually large surface",
                        "skus": outliers["SKU"].tolist(),
                    })

    # 5. Invalid category (empty / NaN)
    if "Category" in df.columns:
        bad_cat = df[df["Category"].isna() | (df["Category"].astype(str).str.strip() == "")]
        if len(bad_cat) > 0:
            warnings += len(bad_cat)
            issues.append({
                "type": "warning",
                "check": "Missing Category",
                "count": len(bad_cat),
                "details": f"{len(bad_cat)} SKUs have missing category",
                "skus": bad_cat["SKU"].tolist(),
            })

    return {
        "total_warnings": warnings,
        "total_errors": errors,
        "issues": issues,
    }


def create_validation_report(validation_result: Dict[str, Any]) -> pd.DataFrame:
    """Create a downloadable validation report as a DataFrame."""
    rows = []
    for issue in validation_result["issues"]:
        for sku in issue.get("skus", []):
            rows.append({
                "Type": issue["type"].upper(),
                "Check": issue["check"],
                "SKU": sku,
                "Details": issue["details"],
            })
    if not rows:
        rows.append({"Type": "INFO", "Check": "All checks passed", "SKU": "-", "Details": "No issues found"})
    return pd.DataFrame(rows)
