"""
api/services/forecasting.py

Demand forecasting from sale_items history.
Method: simple exponential smoothing (SES) with a moving-average fallback
when fewer than 2 periods exist. Explainable and suitable for sparse data.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from math import sqrt
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple


Period = Literal["week", "month"]

# SES smoothing factor — higher reacts faster to recent demand
DEFAULT_ALPHA = 0.35
# How many historical buckets to return alongside the forecast
DEFAULT_HISTORY_BUCKETS = 12


def _period_key(dt: datetime, period: Period) -> str:
    if period == "week":
        iso = dt.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"
    return f"{dt.year:04d}-{dt.month:02d}"


def _period_label(key: str, period: Period) -> str:
    if period == "week":
        return key  # e.g. 2026-W12
    y, m = key.split("-")
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    return f"{months[int(m) - 1]} {y}"


def _bucket_start(dt: datetime, period: Period) -> datetime:
    dt = dt.astimezone(timezone.utc) if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    if period == "week":
        # Monday-start ISO week
        return (dt - timedelta(days=dt.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _add_periods(dt: datetime, n: int, period: Period) -> datetime:
    if period == "week":
        return dt + timedelta(weeks=n)
    # month
    y = dt.year + (dt.month - 1 + n) // 12
    m = (dt.month - 1 + n) % 12 + 1
    return dt.replace(year=y, month=m, day=1)


def aggregate_demand_series(
    rows: Sequence[Tuple[datetime, float]],
    period: Period,
) -> List[Tuple[str, float]]:
    """
    rows: (created_at, quantity) from sale_items joined to sales.
    Returns sorted list of (period_key, total_qty).
    """
    buckets: Dict[str, float] = defaultdict(float)
    for created_at, qty in rows:
        if created_at is None:
            continue
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        buckets[_period_key(created_at, period)] += float(qty)
    return sorted(buckets.items(), key=lambda x: x[0])


def exponential_smoothing(
    values: Sequence[float],
    alpha: float = DEFAULT_ALPHA,
) -> Tuple[float, List[float]]:
    """
    Returns (next_forecast, fitted_series).
    fitted_series[i] is the one-step-ahead forecast for values[i] (level before observing i).
    """
    if not values:
        return 0.0, []
    if len(values) == 1:
        return float(values[0]), [float(values[0])]

    level = float(values[0])
    fitted: List[float] = [level]
    for v in values[1:]:
        fitted.append(level)
        level = alpha * float(v) + (1.0 - alpha) * level
    next_forecast = level
    return next_forecast, fitted


def mape(actuals: Sequence[float], forecasts: Sequence[float]) -> Optional[float]:
    """Mean Absolute Percentage Error; None if not calculable."""
    pairs = [(a, f) for a, f in zip(actuals, forecasts) if a and a != 0]
    if not pairs:
        return None
    return round(100.0 * sum(abs(a - f) / abs(a) for a, f in pairs) / len(pairs), 2)


def forecast_product_demand(
    rows: Sequence[Tuple[datetime, float]],
    period: Period = "week",
    horizon: int = 4,
    alpha: float = DEFAULT_ALPHA,
    history_limit: int = DEFAULT_HISTORY_BUCKETS,
) -> Dict[str, Any]:
    """
    Build historical actuals + forward forecast for one product.
    horizon: number of future periods to project (flat SES level).
    """
    series = aggregate_demand_series(rows, period)
    # Keep a trailing window for chart readability
    if len(series) > history_limit:
        series = series[-history_limit:]

    keys = [k for k, _ in series]
    actuals = [v for _, v in series]
    next_level, fitted = exponential_smoothing(actuals, alpha=alpha)

    # Accuracy on overlapping fitted vs actual (skip first point)
    accuracy_mape = mape(actuals[1:], fitted[1:]) if len(actuals) > 1 else None

    history = [
        {
            "period": key,
            "label": _period_label(key, period),
            "actual": round(actual, 2),
            "fitted": round(fitted[i], 2) if i < len(fitted) else None,
        }
        for i, (key, actual) in enumerate(series)
    ]

    # Anchor future keys off last observed bucket start
    if series:
        # Parse last key into a datetime anchor
        last_key = keys[-1]
        if period == "week":
            y_str, w_str = last_key.split("-W")
            anchor = datetime.fromisocalendar(int(y_str), int(w_str), 1).replace(tzinfo=timezone.utc)
        else:
            y_str, m_str = last_key.split("-")
            anchor = datetime(int(y_str), int(m_str), 1, tzinfo=timezone.utc)
    else:
        anchor = _bucket_start(datetime.now(timezone.utc), period)
        # Step back one so first forecast is "next" period
        anchor = _add_periods(anchor, -1, period)

    forecast_points = []
    for i in range(1, horizon + 1):
        fut = _add_periods(anchor, i, period)
        key = _period_key(fut, period)
        forecast_points.append({
            "period": key,
            "label": _period_label(key, period),
            "predicted": round(next_level, 2),
        })

    method = "exponential_smoothing" if len(actuals) >= 2 else (
        "last_value" if actuals else "no_history"
    )

    return {
        "period": period,
        "horizon": horizon,
        "method": method,
        "alpha": alpha if method == "exponential_smoothing" else None,
        "mape_percent": accuracy_mape,
        "next_period_demand": round(next_level, 2) if actuals else 0.0,
        "history": history,
        "forecast": forecast_points,
    }


def std_dev(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    mean = sum(values) / n
    return sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))
