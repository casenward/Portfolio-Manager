"""Trading operations: buy, sell, and dividend handling."""

from __future__ import annotations

from .transactions import log_transaction


def buyStock(
    price: float,
    shares: int | float,
    holdings: dict,
    ticker: str,
    account: str = "traditional",
) -> dict:
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
    return {
        "action": "buy",
        "ticker": ticker,
        "account": account,
        "shares": shares,
        "price": price,
        "cost": cost,
        "cash": holdings["cash"],
    }


def sellStock(
    price: float,
    shares: int,
    holdings: dict,
    ticker: str,
    account: str = "traditional",
) -> dict:
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
            return {
                "action": "sell",
                "ticker": ticker,
                "account": account_key,
                "shares": shares,
                "price": price,
                "proceeds": proceeds,
                "cash": holdings["cash"],
            }

    raise ValueError(f"Ticker {ticker} not found in {account} holdings")


def dividend(
    price: float,
    holdings: dict,
    ticker: str,
    account: str = "traditional",
    dividend_yield: float = 0.0,
    reinvest: bool = False,
) -> dict:
    if price is None:
        raise ValueError(f"No price available for {ticker}")

    ticker = ticker.strip().upper()
    account = account.strip().lower()

    position = next(
        (p for p in holdings.get(account, []) if p["ticker"] == ticker),
        None,
    )
    if position is None:
        raise ValueError(f"Ticker {ticker} not found in {account} holdings")

    cash_yield = dividend_yield * price * position["shares"]
    log_transaction("dividend", cash_yield, position["shares"], ticker, account)

    shares_bought = 0.0
    if reinvest:
        shares_bought = cash_yield / price
        holdings["cash"] += cash_yield
        buyStock(price, shares_bought, holdings, ticker, account)
    else:
        holdings["cash"] += cash_yield

    return {
        "action": "dividend",
        "ticker": ticker,
        "account": account,
        "cash_yield": cash_yield,
        "reinvested": reinvest,
        "shares_bought": shares_bought,
        "cash": holdings["cash"],
    }
