"""Historical price helpers for performance charts."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from .market_data import _close_frame

BENCHMARK_TICKER = "SPY"
PERFORMANCE_RANGES = ("1M", "3M", "YTD", "1Y", "ALL")


def range_start(range_key: str, today: date | None = None) -> date:
    today = today or datetime.now().astimezone().date()
    if range_key == "1M":
        return today - timedelta(days=31)
    if range_key == "3M":
        return today - timedelta(days=93)
    if range_key == "YTD":
        return date(today.year, 1, 1)
    if range_key == "1Y":
        return today - timedelta(days=365)
    if range_key == "ALL":
        return today - timedelta(days=365 * 5)
    raise ValueError(f"Unknown range: {range_key}")


def fetch_price_history(
    yf_tickers: list[str],
    start: date,
    end: date | None = None,
) -> pd.DataFrame:
    """Download adjusted close prices; columns are tickers, index is dates."""
    tickers = list(dict.fromkeys(t for t in yf_tickers if t))
    if not tickers:
        return pd.DataFrame()

    end = end or (datetime.now().astimezone().date() + timedelta(days=1))
    raw = yf.download(
        tickers,
        start=start.strftime("%Y-%m-%d"),
        end=end.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )
    close = _close_frame(raw, tickers)
    if close is None or close.empty:
        return pd.DataFrame()

    close = close.sort_index().ffill()
    return close


def _portfolio_values(
    closes: pd.DataFrame,
    share_map: dict[str, float],
) -> pd.Series:
    if closes.empty or not share_map:
        return pd.Series(dtype=float)

    total = pd.Series(0.0, index=closes.index, dtype=float)
    for ticker, shares in share_map.items():
        if ticker not in closes.columns:
            continue
        total = total + closes[ticker].astype(float) * float(shares)
    return total


def _cumulative_pct(values: pd.Series) -> pd.Series:
    clean = values.dropna()
    clean = clean[clean > 0]
    if clean.empty:
        return pd.Series(dtype=float)
    base = float(clean.iloc[0])
    if base == 0:
        return pd.Series(dtype=float)
    return (clean / base - 1.0) * 100.0


def _label_for(ts: pd.Timestamp, range_key: str) -> str:
    if range_key in ("1M", "3M"):
        return ts.strftime("%b %d")
    if range_key in ("YTD", "1Y"):
        return ts.strftime("%b")
    return ts.strftime("%Y")


def _downsample_frame(frame: pd.DataFrame, range_key: str) -> pd.DataFrame:
    if frame.empty:
        return frame
    if range_key == "1M":
        return frame
    if range_key == "3M":
        return frame.iloc[::2]
    if range_key in ("YTD", "1Y"):
        weekly = frame.resample("W-FRI").last().dropna(subset=["portfolio"])
        return weekly if not weekly.empty else frame.iloc[::5]
    monthly = frame.resample("ME").last().dropna(subset=["portfolio"])
    return monthly if not monthly.empty else frame.iloc[::20]


def build_range_series(
    closes: pd.DataFrame,
    share_map: dict[str, float],
    range_key: str,
    today: date | None = None,
) -> list[dict[str, Any]]:
    """Return [{label, portfolio, benchmark}, ...] as cumulative % returns."""
    today = today or datetime.now().astimezone().date()
    start = range_start(range_key, today)
    if closes.empty:
        return []

    window = closes.loc[closes.index.date >= start].copy()
    if window.empty:
        return []

    port = _cumulative_pct(_portfolio_values(window, share_map))
    if port.empty:
        return []

    if BENCHMARK_TICKER in window.columns:
        bench = _cumulative_pct(window[BENCHMARK_TICKER].astype(float))
    else:
        bench = pd.Series(dtype=float)

    aligned = pd.DataFrame({"portfolio": port})
    aligned["benchmark"] = bench.reindex(aligned.index).ffill()
    sampled = _downsample_frame(aligned.dropna(subset=["portfolio"]), range_key)
    if sampled.empty:
        return []

    points: list[dict[str, Any]] = []
    for ts, row in sampled.iterrows():
        bench_val = row["benchmark"]
        points.append(
            {
                "label": _label_for(pd.Timestamp(ts), range_key),
                "portfolio": round(float(row["portfolio"]), 2),
                "benchmark": (
                    round(float(bench_val), 2)
                    if bench_val is not None and not pd.isna(bench_val)
                    else None
                ),
            }
        )
    return points


def build_all_performance_series(
    closes: pd.DataFrame,
    share_map: dict[str, float],
    today: date | None = None,
) -> dict[str, list[dict[str, Any]]]:
    return {
        key: build_range_series(closes, share_map, key, today=today)
        for key in PERFORMANCE_RANGES
    }
