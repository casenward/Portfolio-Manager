"""Orchestration layer: price fetch, trading calls, and persistence."""

from __future__ import annotations

from . import market_data
from .portfolio import dayChange, portfolio_value
from .repository import save_holdings
from .state import AppState
from .tickers import resolve_yf_ticker
from .trading import buyStock, dividend, sellStock


def _all_yf_tickers(holdings: dict) -> list[str]:
    return [
        position["yf_ticker"]
        for account, positions in holdings.items()
        if account != "cash" and isinstance(positions, list)
        for position in positions
    ]


def _live_price(ticker: str) -> float:
    yf_ticker = resolve_yf_ticker(ticker)
    prices, _ = market_data.fetch_current_prices([yf_ticker])
    price = prices.get(yf_ticker)
    if price is None:
        raise ValueError(f"No price available for {ticker}")
    return price


def get_holdings(state: AppState) -> dict:
    with state.lock:
        return {
            "cash": state.holdings["cash"],
            "traditional": list(state.holdings.get("traditional", [])),
            "sustainable": list(state.holdings.get("sustainable", [])),
        }


def get_portfolio_summary(state: AppState) -> dict:
    with state.lock:
        holdings = state.holdings
        all_yf = _all_yf_tickers(holdings)
        prices, previous_prices = market_data.fetch_current_prices(all_yf)

        traditional, missing_trad = portfolio_value(
            holdings.get("traditional", []), prices
        )
        sustainable, missing_sust = portfolio_value(
            holdings.get("sustainable", []), prices
        )
        missing = sorted(set(missing_trad + missing_sust))
        day_change = dayChange(prices, previous_prices, holdings)

        return {
            "traditional": traditional,
            "sustainable": sustainable,
            "combined": traditional + sustainable,
            "cash": holdings["cash"],
            "day_change": day_change,
            "missing": missing,
        }


def execute_buy(
    state: AppState,
    ticker: str,
    shares: float,
    account: str = "traditional",
) -> dict:
    price = _live_price(ticker)
    with state.lock:
        result = buyStock(price, shares, state.holdings, ticker, account)
        save_holdings(state.holdings, state.holdings_path)
        return result


def execute_sell(
    state: AppState,
    ticker: str,
    shares: int | float,
    account: str = "traditional",
) -> dict:
    price = _live_price(ticker)
    with state.lock:
        result = sellStock(price, int(shares), state.holdings, ticker, account)
        save_holdings(state.holdings, state.holdings_path)
        return result


def execute_dividend(
    state: AppState,
    ticker: str,
    account: str,
    dividend_yield: float,
    reinvest: bool,
) -> dict:
    price = _live_price(ticker)
    with state.lock:
        result = dividend(
            price,
            state.holdings,
            ticker,
            account,
            dividend_yield=dividend_yield,
            reinvest=reinvest,
        )
        save_holdings(state.holdings, state.holdings_path)
        return result
