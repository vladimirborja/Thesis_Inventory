"""
Line-item template matching Duque Food Products daily transaction Excel layout
(Duque_Daily_Transaction_Reports_Jan-Jul_2026.xlsx).

Unit prices come from the Excel Price List / sheet columns — never invented.
"""

from typing import Any, Dict, List, Optional

from api.services.product_catalog import DUQUE_PRODUCT_CATALOG

# category order matching Excel sheet section headers
_CATEGORY_BY_NAME = {
    "Pork Tocino": "TOCINO",
    "Skinless #6": "LONGANISA",
    "Skinless #12": "LONGANISA",
    "Native garlic & spicy": "LONGANISA",
    "Native garlic (S&S)": "LONGANISA",
    "Emba x6 (M)": "EMBOTIDO",
    "Emba x5 (L)": "EMBOTIDO",
    "Emba Single": "EMBOTIDO",
    "Hamburger (x10)": "Hamburger Patties",
    "Cooked Ham": "HAM",
    "Sliced Ham": "HAM",
    "Hungarian": "SAUSAGES",
    "Bologna": "SAUSAGES",
}


def empty_line_item(
    category: str,
    product_name: str,
    weight: Optional[str],
    sort_order: int,
    price_bundle: Optional[float] = None,
    price_piece: Optional[float] = None,
) -> Dict[str, Any]:
    return {
        "category": category,
        "product_name": product_name,
        "weight": weight or None,
        "price_bundle": price_bundle if price_bundle else None,
        "price_piece": price_piece if price_piece else None,
        "load_in": None,
        "load_out_bundle": None,
        "load_out_piece": None,
        "sales_bundle": None,
        "sales_piece": None,
        "sales_peso_bundle": None,
        "sales_peso_piece": None,
        "total_sales": 0.0,
        "sort_order": sort_order,
    }


def get_report_line_template() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i, (name, _sku, weight, bundle, piece) in enumerate(DUQUE_PRODUCT_CATALOG):
        rows.append(
            empty_line_item(
                _CATEGORY_BY_NAME.get(name, "OTHER"),
                name,
                weight,
                i,
                bundle or None,
                piece or None,
            )
        )
    return rows


def calc_denom_total(
    bill_1000: int = 0,
    bill_500: int = 0,
    bill_200: int = 0,
    bill_100: int = 0,
    bill_50: int = 0,
    bill_20: int = 0,
    coins: float = 0,
) -> float:
    return round(
        bill_1000 * 1000
        + bill_500 * 500
        + bill_200 * 200
        + bill_100 * 100
        + bill_50 * 50
        + bill_20 * 20
        + float(coins),
        2,
    )
