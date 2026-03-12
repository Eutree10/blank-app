"""
Scenario Engine Module
Manages scenario creation, storage, and comparison.
"""

import pandas as pd
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import json


@dataclass
class Scenario:
    """Represents a single optimization scenario configuration and results."""
    name: str
    total_surface: float
    optimization_mode: str
    segment_filter: Optional[str] = None
    category_filters: Optional[List[str]] = None
    brand_filters: Optional[List[str]] = None
    country_filters: Optional[List[str]] = None
    channel_filters: Optional[List[str]] = None
    hybrid_weights: Optional[Dict[str, float]] = None
    min_skus_per_category: Optional[Dict[str, int]] = None
    min_surface_pct_per_category: Optional[Dict[str, float]] = None
    max_surface_pct_per_category: Optional[Dict[str, float]] = None
    max_sku_pct_per_subcategory: Optional[float] = None
    min_categories: Optional[int] = None
    min_subcategories: Optional[int] = None
    min_collections: Optional[int] = None
    mandatory_include: Optional[List[str]] = None
    mandatory_exclude: Optional[List[str]] = None
    min_display_surface: Optional[float] = None
    vendibility_weights: Optional[Dict[str, float]] = None
    # Results (filled after optimization)
    results_summary: Optional[Dict[str, Any]] = None
    selected_skus: Optional[List[str]] = None

    def to_dict(self) -> dict:
        return asdict(self)


class ScenarioManager:
    """Manages multiple scenarios for comparison."""

    def __init__(self):
        self.scenarios: Dict[str, Scenario] = {}

    def add_scenario(self, scenario: Scenario):
        self.scenarios[scenario.name] = scenario

    def remove_scenario(self, name: str):
        if name in self.scenarios:
            del self.scenarios[name]

    def get_scenario(self, name: str) -> Optional[Scenario]:
        return self.scenarios.get(name)

    def list_scenarios(self) -> List[str]:
        return list(self.scenarios.keys())

    def get_comparison_table(self) -> pd.DataFrame:
        """Create a comparison table across all scenarios."""
        if not self.scenarios:
            return pd.DataFrame()

        rows = []
        for name, scenario in self.scenarios.items():
            row = {"Scenario": name}
            if scenario.results_summary:
                row.update({
                    "Total Surface": scenario.total_surface,
                    "Mode": scenario.optimization_mode,
                    "SKUs Selected": scenario.results_summary.get("total_skus_selected", 0),
                    "Total Vendibility": scenario.results_summary.get("total_vendibility", 0),
                    "Total Revenue": scenario.results_summary.get("total_revenue", 0),
                    "Total Margin": scenario.results_summary.get("total_margin", 0),
                    "Surface Used": scenario.results_summary.get("total_surface_used", 0),
                    "Surface Utilization %": scenario.results_summary.get("surface_utilization_pct", 0),
                    "Categories": scenario.results_summary.get("categories_represented", 0),
                    "Status": scenario.results_summary.get("status", "N/A"),
                })
            rows.append(row)

        return pd.DataFrame(rows)
