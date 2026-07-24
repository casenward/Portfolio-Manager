"""Portfolio valuation and day-change calculations."""

from __future__ import annotations


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


def dayChange(
    prices: dict[str, float | None],
    previous_prices: dict[str, float | None],
    holdings: dict,
) -> float:
    change = 0.0
    for account, positions in holdings.items():
        if account == "cash" or not isinstance(positions, list):
            continue
        for position in positions:
            current = prices.get(position["yf_ticker"])
            previous = previous_prices.get(position["yf_ticker"])
            if current is None or previous is None:
                continue
            change += (current - previous) * position["shares"]
    return change
