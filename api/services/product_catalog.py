"""
Duque Food Products catalog — prices taken only from the Excel workbook
(data/Duque_Daily_Transaction_Reports_Jan-Jul_2026.xlsx).

Product names match the daily-report sheets. Bundle/piece prices come from the
Price List sheet (and matching ₱/bundle · ₱/piece columns on daily sheets).
Products with no price in Excel stay at 0 — nothing is invented.
"""

from typing import Any, Dict, List, Optional, Tuple

# name, sku, weight, bundle_₱, piece_₱
CatalogRow = Tuple[str, str, Optional[str], float, float]

DUQUE_PRODUCT_CATALOG: List[CatalogRow] = [
    ("Pork Tocino", "DFP-TOCI-225", "225g", 980.0, 49.0),
    ("Skinless #6", "DFP-LONG-006", "225g", 600.0, 30.0),  # Price List: Skinless Longganisa
    ("Skinless #12", "DFP-LONG-012", None, 640.0, 32.0),  # Price List: Skinless (Favorite)
    ("Native garlic & spicy", "DFP-LONG-NGS", None, 0.0, 0.0),
    ("Native garlic (S&S)", "DFP-LONG-NSS", None, 0.0, 0.0),
    ("Emba x6 (M)", "DFP-EMBO-M350", "350g", 840.0, 42.0),  # Price List: Embotido Medium
    ("Emba x5 (L)", "DFP-EMBO-L450", "450g", 1040.0, 52.0),  # Price List: Embotido Large
    ("Emba Single", "DFP-EMBO-S450", "450g", 0.0, 0.0),
    ("Hamburger (x10)", "DFP-PATT-350", "350g", 645.0, 43.0),  # Price List: Hamburger Patties
    ("Cooked Ham", "DFP-HAM-C225", "225g", 740.0, 37.0),
    ("Sliced Ham", "DFP-HAM-S225", "225g", 0.0, 0.0),
    ("Hungarian", "DFP-SAUS-HUN", "100g", 0.0, 0.0),
    ("Bologna", "DFP-BOLO-001", None, 640.0, 32.0),
]


def catalog_as_dicts(category_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Build Product kwargs from Excel — no invented stock or cost."""
    rows: List[Dict[str, Any]] = []
    for name, sku, weight, bundle, piece in DUQUE_PRODUCT_CATALOG:
        rows.append(
            {
                "name": name,
                "sku": sku,
                "weight": weight,
                "selling_price": bundle,
                "piece_price": piece,
                "cost_price": 0.0,
                "description": None,
                "category_id": category_id,
                "unit_of_measure": "bundles",
                "min_stock_level": 0,
                "quantity": 0,
                "lead_time_days": 5,
                "barcode": None,
            }
        )
    return rows
