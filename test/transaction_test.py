"""Test suite for calculate.py's portfolio operations.

Run with:  python -m pytest test/transaction_test.py -v
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

import calculate


# ---------------------------------------------------------------------------
# resolve_yf_ticker
# ---------------------------------------------------------------------------

class TestResolveYfTicker:
    def test_plain_ticker_passthrough(self):
        assert calculate.resolve_yf_ticker("AAPL") == "AAPL"

    def test_lowercase_is_uppercased(self):
        assert calculate.resolve_yf_ticker("aapl") == "AAPL"

    def test_whitespace_is_stripped(self):
        assert calculate.resolve_yf_ticker("  msft  ") == "MSFT"

    def test_override_b_maps_to_gold(self):
        # "B" is special-cased to Barrick Mining's yfinance symbol.
        assert calculate.resolve_yf_ticker("B") == "GOLD"

    def test_override_is_case_insensitive(self):
        assert calculate.resolve_yf_ticker("b") == "GOLD"

    def test_slash_ticker_is_dashed(self):
        # e.g. share classes like BRK/B -> BRK-B for yfinance
        assert calculate.resolve_yf_ticker("BRK/B") == "BRK-B"


# ---------------------------------------------------------------------------
# load_holdings
# ---------------------------------------------------------------------------

class TestLoadHoldings:
    def _write(self, tmp_path: Path, data: dict) -> Path:
        path = tmp_path / "holdings.json"
        path.write_text(json.dumps(data))
        return path

    def test_basic_load_normalizes_account_and_ticker(self, tmp_path):
        path = self._write(tmp_path, {
            "cash": 5000,
            "Traditional": [{"name": "Apple", "ticker": "aapl", "shares": 10}],
        })
        holdings = calculate.load_holdings(path)
        assert holdings["cash"] == 5000.0
        assert "traditional" in holdings
        pos = holdings["traditional"][0]
        assert pos["ticker"] == "AAPL"
        assert pos["yf_ticker"] == "AAPL"
        assert pos["shares"] == 10.0
        assert isinstance(pos["shares"], float)

    def test_load_applies_ticker_override(self, tmp_path):
        path = self._write(tmp_path, {
            "traditional": [{"name": "Barrick", "ticker": "B", "shares": 5}],
        })
        holdings = calculate.load_holdings(path)
        assert holdings["cash"] == 0.0
        assert holdings["traditional"][0]["yf_ticker"] == "GOLD"

    def test_load_multiple_accounts(self, tmp_path):
        path = self._write(tmp_path, {
            "cash": 100.0,
            "traditional": [{"name": "Apple", "ticker": "AAPL", "shares": 1}],
            "sustainable": [{"name": "Tesla", "ticker": "TSLA", "shares": 2}],
        })
        holdings = calculate.load_holdings(path)
        assert set(holdings.keys()) == {"cash", "traditional", "sustainable"}

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            calculate.load_holdings(tmp_path / "nope.json")


# ---------------------------------------------------------------------------
# portfolio_value
# ---------------------------------------------------------------------------

class TestPortfolioValue:
    def test_basic_sum(self):
        positions = [
            {"ticker": "AAPL", "yf_ticker": "AAPL", "shares": 10},
            {"ticker": "MSFT", "yf_ticker": "MSFT", "shares": 5},
        ]
        prices = {"AAPL": 100.0, "MSFT": 200.0}
        total, missing = calculate.portfolio_value(positions, prices)
        assert total == 10 * 100.0 + 5 * 200.0
        assert missing == []

    def test_empty_positions_returns_zero(self):
        total, missing = calculate.portfolio_value([], {})
        assert total == 0.0
        assert missing == []

    def test_missing_price_is_excluded_from_total_and_reported(self):
        positions = [
            {"ticker": "AAPL", "yf_ticker": "AAPL", "shares": 10},
            {"ticker": "ZZZZ", "yf_ticker": "ZZZZ", "shares": 5},
        ]
        prices = {"AAPL": 100.0, "ZZZZ": None}
        total, missing = calculate.portfolio_value(positions, prices)
        assert total == 1000.0
        assert missing == ["ZZZZ"]

    def test_ticker_absent_from_prices_dict_counts_as_missing(self):
        positions = [{"ticker": "AAPL", "yf_ticker": "AAPL", "shares": 10}]
        total, missing = calculate.portfolio_value(positions, {})
        assert total == 0.0
        assert missing == ["AAPL"]

    def test_fractional_shares(self):
        positions = [{"ticker": "AAPL", "yf_ticker": "AAPL", "shares": 0.5}]
        total, _ = calculate.portfolio_value(positions, {"AAPL": 100.0})
        assert total == 50.0


# ---------------------------------------------------------------------------
# format_dollars
# ---------------------------------------------------------------------------

class TestFormatDollars:
    def test_thousands_separator_and_two_decimals(self):
        assert calculate.format_dollars(1234567.891) == "$1,234,567.89"

    def test_zero(self):
        assert calculate.format_dollars(0) == "$0.00"

    def test_negative_value(self):
        assert calculate.format_dollars(-500.5) == "$-500.50"

    def test_rounding(self):
        assert calculate.format_dollars(9.995) == "$10.00" or calculate.format_dollars(9.995) == "$9.99"
        # banker's rounding / float repr can go either way; just confirm it doesn't crash
        # and produces a 2-decimal dollar string
        result = calculate.format_dollars(9.995)
        assert result.startswith("$") and result.count(".") == 1


# ---------------------------------------------------------------------------
# buyStock / sellStock
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolate_transactions_file(tmp_path, monkeypatch):
    """Redirect TRANSACTIONS_PATH so tests never touch the real repo file."""
    monkeypatch.setattr(calculate, "TRANSACTIONS_PATH", tmp_path / "transactions.csv")
    yield


@pytest.fixture
def holdings():
    return {
        "cash": 1000.0,
        "traditional": [
            {"name": "Apple", "ticker": "AAPL", "yf_ticker": "AAPL", "shares": 10.0},
        ],
        "sustainable": [
            {"name": "Tesla", "ticker": "TSLA", "yf_ticker": "TSLA", "shares": 4.0},
        ],
    }


class TestBuyStock:
    def test_buy_increases_shares_and_deducts_cash(self, holdings):
        calculate.buyStock(100.0, 2, holdings, "AAPL", "traditional")
        assert holdings["cash"] == 800.0
        assert holdings["traditional"][0]["shares"] == 12.0

    def test_buy_insufficient_cash_raises_and_does_not_mutate(self, holdings):
        holdings["cash"] = 50.0
        with pytest.raises(ValueError, match="Not enough cash"):
            calculate.buyStock(100.0, 1, holdings, "AAPL", "traditional")
        assert holdings["traditional"][0]["shares"] == 10.0
        assert holdings["cash"] == 50.0

    def test_buy_exact_cash_amount_succeeds(self, holdings):
        calculate.buyStock(100.0, 10, holdings, "AAPL", "traditional")
        assert holdings["cash"] == 0.0

    def test_buy_unknown_ticker_in_account_raises(self, holdings):
        with pytest.raises(ValueError, match="not found"):
            calculate.buyStock(50.0, 1, holdings, "GOOG", "traditional")

    def test_buy_ticker_only_in_other_account_still_raises(self, holdings):
        with pytest.raises(ValueError, match="not found"):
            calculate.buyStock(50.0, 1, holdings, "TSLA", "traditional")

    def test_buy_is_case_and_whitespace_insensitive_for_ticker_and_account(self, holdings):
        calculate.buyStock(100.0, 1, holdings, " aapl ", " TRADITIONAL ")
        assert holdings["cash"] == 900.0
        assert holdings["traditional"][0]["shares"] == 11.0

    def test_buy_logs_transaction(self, holdings, tmp_path):
        calculate.buyStock(100.0, 2, holdings, "AAPL", "traditional")
        rows = list(csv.DictReader((tmp_path / "transactions.csv").open()))
        assert len(rows) == 1
        assert rows[0]["transaction"] == "buy"
        assert rows[0]["ticker"] == "AAPL"
        assert float(rows[0]["amount"]) == 200.0


class TestSellStock:
    def test_sell_decreases_shares_and_increases_cash(self, holdings):
        holdings["cash"] = 0.0
        calculate.sellStock(100.0, 3, holdings, "AAPL", "traditional")
        assert holdings["cash"] == 300.0
        assert holdings["traditional"][0]["shares"] == 7.0

    def test_sell_all_shares_removes_position(self, holdings):
        calculate.sellStock(100.0, 10, holdings, "AAPL", "traditional")
        tickers = [p["ticker"] for p in holdings["traditional"]]
        assert "AAPL" not in tickers

    def test_sell_more_than_owned_raises_and_does_not_mutate(self, holdings):
        with pytest.raises(ValueError, match="Not enough shares"):
            calculate.sellStock(100.0, 999, holdings, "AAPL", "traditional")
        assert holdings["traditional"][0]["shares"] == 10.0

    def test_sell_unknown_ticker_raises(self, holdings):
        with pytest.raises(ValueError, match="not found"):
            calculate.sellStock(100.0, 1, holdings, "GOOG", "traditional")

    def test_sell_wrong_account_raises_even_if_ticker_exists_elsewhere(self, holdings):
        with pytest.raises(ValueError, match="not found"):
            calculate.sellStock(100.0, 1, holdings, "TSLA", "traditional")

    def test_sell_logs_transaction(self, holdings, tmp_path):
        calculate.sellStock(100.0, 2, holdings, "AAPL", "traditional")
        rows = list(csv.DictReader((tmp_path / "transactions.csv").open()))
        assert len(rows) == 1
        assert rows[0]["transaction"] == "sell"
        assert float(rows[0]["amount"]) == 200.0


# ---------------------------------------------------------------------------
# dividend (interactive) -- test via monkeypatched input()
# ---------------------------------------------------------------------------

class TestDividend:
    def _feed_input(self, monkeypatch, answers):
        it = iter(answers)
        monkeypatch.setattr("builtins.input", lambda *_: next(it))

    def test_dividend_without_reinvest_adds_cash_only(self, holdings, monkeypatch):
        self._feed_input(monkeypatch, ["AAPL", "traditional", "2", "n"])
        prices = {"AAPL": 100.0}
        calculate.dividend(prices, holdings)
        # 2% yield * $100 price * 10 shares = $20
        assert holdings["cash"] == 1020.0
        assert holdings["traditional"][0]["shares"] == 10.0

    def test_dividend_with_reinvest_buys_more_shares(self, holdings, monkeypatch):
        self._feed_input(monkeypatch, ["AAPL", "traditional", "10", "y"])
        prices = {"AAPL": 100.0}
        # 10% yield * $100 * 10 shares = $100 dividend -> buys 1 more share
        calculate.dividend(prices, holdings)
        assert holdings["cash"] == 1000.0
        assert holdings["traditional"][0]["shares"] == pytest.approx(11.0)

    def test_dividend_unknown_ticker_raises(self, holdings, monkeypatch):
        self._feed_input(monkeypatch, ["GOOG", "traditional", "2"])
        with pytest.raises(ValueError, match="not found"):
            calculate.dividend({"GOOG": 50.0}, holdings)

    def test_dividend_missing_price_raises(self, holdings, monkeypatch):
        self._feed_input(monkeypatch, ["AAPL", "traditional", "2"])
        with pytest.raises(ValueError, match="No price available"):
            calculate.dividend({}, holdings)
