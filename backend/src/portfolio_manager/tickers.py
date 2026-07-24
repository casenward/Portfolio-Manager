"""Ticker symbol normalization and yfinance overrides."""

from __future__ import annotations

from .config import YF_TICKER_OVERRIDES


def resolve_yf_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()
    return YF_TICKER_OVERRIDES.get(ticker, ticker.replace("/", "-"))
