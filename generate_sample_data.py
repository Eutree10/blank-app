"""
Sample Data Generator
=====================
Generates realistic mock product performance and surface data
for testing the Retail Assortment Optimizer.

Run: python generate_sample_data.py
Output: data/sample_products.csv, data/sample_surfaces.xlsx
"""

import pandas as pd
import numpy as np
import os


def generate():
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

    # --- Product data ---
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

    # --- Surface data ---
    surface_data = []
    for i in range(n):
        cat = product_df.loc[i, "Category"]
        if cat == "Bags":
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

    # --- Save ---
    os.makedirs("data", exist_ok=True)
    product_df.to_csv("data/sample_products.csv", index=False)
    surface_df.to_excel("data/sample_surfaces.xlsx", index=False)

    print(f"Generated {n} products -> data/sample_products.csv")
    print(f"Generated {n} surfaces -> data/sample_surfaces.xlsx")
    print("\nProduct columns:", list(product_df.columns))
    print("Surface columns:", list(surface_df.columns))


if __name__ == "__main__":
    generate()
