"""
Line-item template matching Duque Food Products daily transaction Excel layout.
"""

from typing import Any, Dict, List

# (category, product_name, weight)
_REPORT_ROWS: List[tuple] = [
    ("TOCINO", "Pork Tocino", "225g"),
    ("TOCINO", "Pork Tocino", "450g"),
    ("PORK HOTDOG", "POGI", "225g"),
    ("PORK HOTDOG", "POGI", "450g"),
    ("PORK HOTDOG", "POGI", "1kg"),
    ("PORK HOTDOG", "POGI", "2.5kg"),
    ("CHICKEN HOTDOG", "SEXY", "225g"),
    ("CHICKEN HOTDOG", "SEXY", "450g"),
    ("CHICKEN HOTDOG", "SEXY", "1kg"),
    ("CHICKEN HOTDOG", "SEXY", "2.5kg"),
    ("LONGANISA", "Skinless #6", ""),
    ("LONGANISA", "Skinless #12", ""),
    ("LONGANISA", "Native garlic & spicy", ""),
    ("LONGANISA", "Native garlic (S&S)", ""),
    ("EMBOTIDO", "Embo x6 (M)", "350g"),
    ("EMBOTIDO", "Embo x5 (L)", "450g"),
    ("EMBOTIDO", "Embo Single", "450g"),
    ("Hamburger Patties", "Hamburger (x10)", "350g"),
    ("HAM", "Cooked Ham", "225g"),
    ("HAM", "Sliced Ham", "225g"),
    ("SAUSAGES", "Hungarian", "100g"),
]


def empty_line_item(category: str, product_name: str, weight: str, sort_order: int) -> Dict[str, Any]:
    return {
        "category": category,
        "product_name": product_name,
        "weight": weight or None,
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
    return [
        empty_line_item(cat, name, wt, i)
        for i, (cat, name, wt) in enumerate(_REPORT_ROWS)
    ]


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
