"""
api/services/abc_analysis.py

Pareto ABC classification by sales value contribution.
A = cumulative top ~80%, B = next ~15% (to 95%), C = remainder (~5%).
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple


def classify_abc(
    product_values: Sequence[Tuple[int, str, str, float]],
    a_cutoff: float = 0.80,
    b_cutoff: float = 0.95,
) -> List[Dict[str, Any]]:
    """
    product_values: (product_id, name, sku, sales_value)
    Returns rows sorted by sales_value desc with abc_class + cumulative %.
    """
    positive = [
        (pid, name, sku, float(val))
        for pid, name, sku, val in product_values
        if float(val) > 0
    ]
    zeros = [
        (pid, name, sku, 0.0)
        for pid, name, sku, val in product_values
        if float(val) <= 0
    ]
    positive.sort(key=lambda x: x[3], reverse=True)

    total = sum(v for *_, v in positive) or 1.0
    cumulative = 0.0
    rows: List[Dict[str, Any]] = []

    for pid, name, sku, val in positive:
        cumulative += val
        share = cumulative / total
        if share <= a_cutoff:
            abc = "A"
        elif share <= b_cutoff:
            abc = "B"
        else:
            abc = "C"
        rows.append({
            "product_id": pid,
            "name": name,
            "sku": sku,
            "sales_value": round(val, 2),
            "value_share_percent": round(100.0 * val / total, 2),
            "cumulative_percent": round(100.0 * share, 2),
            "abc_class": abc,
        })

    for pid, name, sku, _ in zeros:
        rows.append({
            "product_id": pid,
            "name": name,
            "sku": sku,
            "sales_value": 0.0,
            "value_share_percent": 0.0,
            "cumulative_percent": 100.0,
            "abc_class": "C",
        })

    return rows


def abc_summary(rows: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"A": 0, "B": 0, "C": 0}
    for r in rows:
        counts[r["abc_class"]] = counts.get(r["abc_class"], 0) + 1
    return counts
