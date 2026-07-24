"""Calculate current portfolio value from holdings.json and print totals."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import yfinance as yf

HOLDINGS_PATH = Path(__file__).resolve().parent / "data" / "holdings.json"
TRANSACTIONS_PATH = Path(__file__).resolve().parent / "data" / "transactions.csv"

YF_TICKER_OVERRIDES = {
    "B": "GOLD",  # Barrick Mining Corporation
}


def resolve_yf_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()
    return YF_TICKER_OVERRIDES.get(ticker, ticker.replace("/", "-"))


def load_holdings(path: Path = HOLDINGS_PATH) -> dict:
    with path.open(encoding="utf-8") as file:
        raw = json.load(file)

    holdings: dict = {"cash": float(raw.get("cash", 0))}
    for account, positions in raw.items():
        if account.strip().lower() == "cash" or not isinstance(positions, list):
            continue
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


def log_transaction(
    transaction: str,
    amount: float,
    shares: int | float,
    ticker: str,
    account: str = "traditional",
) -> None:
    write_header = not TRANSACTIONS_PATH.exists()
    with TRANSACTIONS_PATH.open("a", encoding="utf-8") as file:
        if write_header:
            file.write("transaction,amount,shares,ticker,account\n")
        file.write(f"{transaction},{amount},{shares},{ticker},{account}\n")


def buyStock(
    price: float,
    shares: int | float,
    holdings: dict,
    ticker: str,
    account: str = "traditional",
) -> None:
    cost = price * shares
    if holdings["cash"] < cost:
        raise ValueError("Not enough cash to buy shares")
    holdings["cash"] -= cost

    ticker = ticker.strip().upper()
    account = account.strip().lower()
    for position in holdings.get(account, []):
        if position["ticker"] == ticker:
            position["shares"] += shares
            break
    else:
        raise ValueError(f"Ticker {ticker} not found in {account} holdings")

    log_transaction("buy", cost, shares, ticker, account)


def sellStock(
    price: float,
    shares: int,
    holdings: dict,
    ticker: str,
    account: str = "traditional",
) -> None:
    ticker = ticker.strip().upper()
    account_key = account.strip().lower()
    positions = holdings.get(account_key, [])

    for position in positions:
        if position["ticker"] == ticker:
            if shares > position["shares"]:
                raise ValueError(f"Not enough shares to sell in {account} holdings")
            proceeds = price * shares
            holdings["cash"] += proceeds
            position["shares"] -= shares
            if position["shares"] == 0:
                positions.remove(position)
            log_transaction("sell", proceeds, shares, ticker, account_key)
            return

    raise ValueError(f"Ticker {ticker} not found in {account} holdings")


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

def dividend(prices: dict[str, float | None], holdings: dict) -> None:
    ticker = input("What stock is receiving dividends? ").strip().upper()
    account = input("Account (traditional/sustainable): ").strip().lower() or "traditional"
    dividend_yield = float(input("What is the dividend yield %? ")) / 100

    price = prices.get(resolve_yf_ticker(ticker))
    if price is None:
        raise ValueError(f"No price available for {ticker}")

    position = next(
        (p for p in holdings.get(account, []) if p["ticker"] == ticker),
        None,
    )
    if position is None:
        raise ValueError(f"Ticker {ticker} not found in {account} holdings")

    cash_yield = dividend_yield * price * position["shares"]
    reinvest = input("Do you want to reinvest the dividends? (y/n): ").strip().lower() == "y"
    log_transaction("dividend", cash_yield, position["shares"], ticker, account)
    if reinvest:
        shares_bought = cash_yield / price
        holdings["cash"] += cash_yield
        buyStock(price, shares_bought, holdings, ticker, account)
        print(f"Reinvested {format_dollars(cash_yield)} into {shares_bought:.4f} {ticker}")
    else:
        holdings["cash"] += cash_yield
        print(f"Received {format_dollars(cash_yield)} in dividends")

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


if __name__ == "__main__":
    raise SystemExit(main())
