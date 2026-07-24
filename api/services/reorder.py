"""
api/services/reorder.py

Reorder Point (ROP) and Safety Stock calculations.

ROP = (average_daily_usage × lead_time_days) + safety_stock
Safety Stock = z × σ_daily × √lead_time_days

Defaults:
  lead_time_days = 7 (overridden by products/suppliers/ingredients.lead_time_days)
  z = 1.65  (~95% service level)
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import ceil, sqrt
from typing import Any, Dict, List, Optional, Sequence, Tuple

from api.services.forecasting import std_dev

DEFAULT_LEAD_TIME_DAYS = 7
DEFAULT_Z = 1.65
DEFAULT_LOOKBACK_DAYS = 90


def daily_usage_series(
    rows: Sequence[Tuple[datetime, float]],
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
) -> List[float]:
    """
    Build a contiguous daily demand series (zeros for no-sale days)
    over the lookback window ending today (UTC).
    """
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=lookback_days - 1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    by_day: Dict[str, float] = defaultdict(float)
    for created_at, qty in rows:
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        if created_at < start:
            continue
        key = created_at.date().isoformat()
        by_day[key] += float(qty)

    series: List[float] = []
    for i in range(lookback_days):
        day = (start + timedelta(days=i)).date().isoformat()
        series.append(by_day.get(day, 0.0))
    return series


def compute_rop(
    daily_demand: Sequence[float],
    current_qty: float,
    lead_time_days: int = DEFAULT_LEAD_TIME_DAYS,
    z: float = DEFAULT_Z,
    min_stock_level: float = 0,
) -> Dict[str, Any]:
    lead = max(1, int(lead_time_days))
    if not daily_demand:
        avg_daily = 0.0
        sigma = 0.0
    else:
        avg_daily = sum(daily_demand) / len(daily_demand)
        sigma = std_dev(list(daily_demand))

    safety = z * sigma * sqrt(lead)
    rop = avg_daily * lead + safety
    # Prefer calculated ROP; surface comparison vs configured min_stock too
    below_rop = float(current_qty) <= rop
    below_min = float(current_qty) <= float(min_stock_level)

    return {
        "avg_daily_usage": round(avg_daily, 4),
        "demand_std_dev": round(sigma, 4),
        "lead_time_days": lead,
        "z_score": z,
        "safety_stock": round(safety, 2),
        "reorder_point": round(rop, 2),
        "recommended_order_qty": max(0, ceil(rop - float(current_qty))),
        "current_quantity": float(current_qty),
        "min_stock_level": float(min_stock_level),
        "below_rop": below_rop,
        "below_min_stock": below_min,
        "needs_reorder": below_rop or below_min,
    }
