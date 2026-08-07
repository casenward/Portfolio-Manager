"""Unit tests for performance series construction."""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from portfolio_manager import performance as perf


def _closes(days: int = 40, end: str | None = None) -> pd.DataFrame:
    end = end or "2026-02-27"
    idx = pd.bdate_range(end=end, periods=days)
    aapl = pd.Series([100 + i * 0.5 for i in range(days)], index=idx)
    spy = pd.Series([400 + i * 0.2 for i in range(days)], index=idx)
    return pd.DataFrame({"AAPL": aapl, "SPY": spy})


class TestRangeStart:
    def test_ytd(self):
        assert perf.range_start("YTD", date(2026, 8, 6)) == date(2026, 1, 1)

    def test_unknown_raises(self):
        with pytest.raises(ValueError):
            perf.range_start("2Y", date(2026, 1, 1))


class TestBuildRangeSeries:
    def test_cumulative_starts_near_zero(self):
        closes = _closes(days=40, end="2026-02-27")
        points = perf.build_range_series(
            closes,
            {"AAPL": 10.0},
            "1M",
            today=date(2026, 2, 28),
        )
        assert len(points) >= 2
        assert points[0]["portfolio"] == pytest.approx(0.0, abs=0.01)
        assert points[-1]["portfolio"] > 0
        assert points[0]["benchmark"] == pytest.approx(0.0, abs=0.01)

    def test_empty_without_prices(self):
        assert perf.build_range_series(pd.DataFrame(), {"AAPL": 1}, "1M") == []

    def test_all_ranges_keys(self):
        closes = _closes(days=260, end="2026-02-27")
        series = perf.build_all_performance_series(
            closes, {"AAPL": 5.0}, today=date(2026, 2, 28)
        )
        assert set(series) == set(perf.PERFORMANCE_RANGES)
        assert len(series["1M"]) >= 1
