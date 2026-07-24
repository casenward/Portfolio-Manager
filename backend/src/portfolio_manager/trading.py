"""Trading operations: buy, sell, and dividend handling."""

from __future__ import annotations

from .formatting import format_dollars
from .tickers import resolve_yf_ticker
from .transactions import log_transaction


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
