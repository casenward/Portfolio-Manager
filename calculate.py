"""Calculate current portfolio value from holdings.json and print totals."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yfinance as yf

HOLDINGS_PATH = Path(__file__).resolve().parent / "holdings.json"

YF_TICKER_OVERRIDES = {
    "B": "GOLD",  # Barrick Mining Corporation
}


def resolve_yf_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()
    return YF_TICKER_OVERRIDES.get(ticker, ticker.replace("/", "-"))


def load_holdings(path: Path = HOLDINGS_PATH) -> dict[str, list[dict]]:
    with path.open(encoding="utf-8") as file:
        raw = json.load(file)

    holdings: dict[str, list[dict]] = {}
    for account, positions in raw.items():
        holdings[account.strip().lower()] = [
            {
                "name": entry["name"],
                "ticker": str(entry["ticker"]).strip().upper(),
                "yf_ticker": resolve_yf_ticker(str(entry["ticker"])),
                "shares": float(entry["shares"]),
            }
            for entry in positions
        ]
    return holdings


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


def fetch_current_prices(yf_tickers: list[str]) -> dict[str, float | None]:
    tickers = list(dict.fromkeys(t for t in yf_tickers if t))
    if not tickers:
        return {}

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

    return {ticker: _last_price(close, ticker) for ticker in tickers}


def portfolio_value(
    positions: list[dict],
    prices: dict[str, float | None],
) -> tuple[float, list[str]]:
    total = 0.0
    missing: list[str] = []

    for position in positions:
        price = prices.get(position["yf_ticker"])
        if price is None:
            missing.append(position["ticker"])
            continue
        total += price * position["shares"]

    return total, missing


def format_dollars(value: float) -> str:
    return f"${value:,.2f}"


def main() -> int:
    holdings = load_holdings()
    all_yf = [
        position["yf_ticker"]
        for positions in holdings.values()
        for position in positions
    ]
    prices = fetch_current_prices(all_yf)

    traditional, missing_trad = portfolio_value(holdings.get("traditional", []), prices)
    sustainable, missing_sust = portfolio_value(holdings.get("sustainable", []), prices)
    combined = traditional + sustainable

    print(f"Traditional: {format_dollars(traditional)}")
    print(f"Sustainable: {format_dollars(sustainable)}")
    print(f"Combined:    {format_dollars(combined)}")

    missing = sorted(set(missing_trad + missing_sust))
    if missing:
        print(f"\nMissing prices (excluded): {', '.join(missing)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
