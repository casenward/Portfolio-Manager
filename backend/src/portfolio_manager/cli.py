"""Interactive command-line interface and application entry loop."""

from __future__ import annotations

from .formatting import format_dollars
from .market_data import fetch_current_prices
from .portfolio import dayChange, portfolio_value
from .repository import load_holdings
from .tickers import resolve_yf_ticker
from .trading import buyStock, dividend, sellStock


def print_portfolio(
    holdings: dict,
    prices: dict[str, float | None],
    previous_prices: dict[str, float | None],
) -> None:
    traditional, _ = portfolio_value(holdings.get("traditional", []), prices)
    sustainable, _ = portfolio_value(holdings.get("sustainable", []), prices)
    combined = traditional + sustainable

    print(f"Traditional: {format_dollars(traditional)}")
    print(f"Sustainable: {format_dollars(sustainable)}")
    print(f"Combined:    {format_dollars(combined)}")
    print(f"Cash:        {format_dollars(holdings['cash'])}")
    print(f"Day change:  {format_dollars(dayChange(prices, previous_prices, holdings))}")


def prompt_trade() -> tuple[str, int, str]:
    ticker = input("Ticker: ").strip().upper()
    shares = int(input("Shares: ").strip())
    account = input("Account (traditional/sustainable): ").strip().lower() or "traditional"
    return ticker, shares, account


def main() -> int:
    holdings = load_holdings()
    all_yf = [
        position["yf_ticker"]
        for account, positions in holdings.items()
        if account != "cash"
        for position in positions
    ]
    prices, previous_prices = fetch_current_prices(all_yf)

    print_portfolio(holdings, prices, previous_prices)

    missing_trad = portfolio_value(holdings.get("traditional", []), prices)[1]
    missing_sust = portfolio_value(holdings.get("sustainable", []), prices)[1]
    missing = sorted(set(missing_trad + missing_sust))
    if missing:
        print(f"\nMissing prices (excluded): {', '.join(missing)}")

    while True:
        print("\n1. Buy Stock")
        print("2. Sell Stock")
        print("3. Print Portfolio")
        print("4. Dividend")
        print("5. Exit")
        choice = input("Enter your choice: ").strip()

        if choice in ("1", "2"):
            try:
                ticker, shares, account = prompt_trade()
                price = prices.get(resolve_yf_ticker(ticker))
                if price is None:
                    print(f"No price available for {ticker}")
                    continue
                if choice == "1":
                    buyStock(price, shares, holdings, ticker, account)
                    print(f"Bought {shares} {ticker}")
                else:
                    sellStock(price, shares, holdings, ticker, account)
                    print(f"Sold {shares} {ticker}")
            except (ValueError, TypeError) as exc:
                print(f"Error: {exc}")
        elif choice == "3":
            print_portfolio(holdings, prices, previous_prices)
        elif choice == "4":
            try:
                dividend(prices, holdings)
            except (ValueError, TypeError) as exc:
                print(f"Error: {exc}")
        elif choice == "5":
            break
        else:
            print("Invalid choice")

    return 0
