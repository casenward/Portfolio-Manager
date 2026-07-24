"""Market data retrieval via yfinance."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import yfinance as yf


def _close_frame(raw, tickers):
    if raw.empty or "Close" not in raw:
        return None

    close = raw["Close"]
    if hasattr(close, "to_frame") and close.ndim == 1:
        return close.to_frame(tickers[0])
    return close


def _last_price(close, ticker: str) -> float | None:
    if close is None or ticker not in close:
        return None

    series = close[ticker].dropna()
    if series.empty:
        return None

    return float(series.iloc[-1])


def _previous_price(close, ticker: str) -> float | None:
    if close is None or ticker not in close:
        return None

    series = close[ticker].dropna()
    if len(series) < 2:
        return None

    return float(series.iloc[-2])


def fetch_current_prices(
    yf_tickers: list[str],
) -> tuple[dict[str, float | None], dict[str, float | None]]:
    tickers = list(dict.fromkeys(t for t in yf_tickers if t))
    if not tickers:
        return {}, {}

    today = datetime.now(UTC).date()
    start_date = today - timedelta(days=14)
    end_date = today + timedelta(days=1)

    raw = yf.download(
        tickers,
        start=start_date.strftime("%Y-%m-%d"),
        end=end_date.strftime("%Y-%m-%d"),
        auto_adjust=True,
        progress=False,
    )
    close = _close_frame(raw, tickers)

    latest = {ticker: _last_price(close, ticker) for ticker in tickers}
    previous = {ticker: _previous_price(close, ticker) for ticker in tickers}
    return latest, previous
