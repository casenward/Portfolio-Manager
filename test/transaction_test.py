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

    def test_dividend_logs_transaction(self, holdings, monkeypatch, tmp_path):
        self._feed_input(monkeypatch, ["AAPL", "traditional", "2", "n"])
        calculate.dividend({"AAPL": 100.0}, holdings)
        rows = list(csv.DictReader((tmp_path / "transactions.csv").open()))
        assert len(rows) == 1
        assert rows[0]["transaction"] == "dividend"
        assert float(rows[0]["amount"]) == 20.0


# ---------------------------------------------------------------------------
# dayChange
# ---------------------------------------------------------------------------

class TestDayChange:
    def test_sums_change_across_accounts(self, holdings):
        prices = {"AAPL": 110.0, "TSLA": 200.0}
        previous = {"AAPL": 100.0, "TSLA": 190.0}
        # AAPL: (110-100)*10 = 100; TSLA: (200-190)*4 = 40
        assert calculate.dayChange(prices, previous, holdings) == 140.0

    def test_negative_day_change(self, holdings):
        prices = {"AAPL": 90.0, "TSLA": 180.0}
        previous = {"AAPL": 100.0, "TSLA": 190.0}
        # AAPL: -100; TSLA: -40
        assert calculate.dayChange(prices, previous, holdings) == -140.0

    def test_skips_missing_current_or_previous_price(self, holdings):
        prices = {"AAPL": 110.0, "TSLA": None}
        previous = {"AAPL": 100.0, "TSLA": 190.0}
        assert calculate.dayChange(prices, previous, holdings) == 100.0

        prices = {"AAPL": 110.0, "TSLA": 200.0}
        previous = {"AAPL": 100.0}  # TSLA previous missing
        assert calculate.dayChange(prices, previous, holdings) == 100.0

    def test_cash_key_is_ignored(self, holdings):
        holdings["cash"] = 999999.0
        prices = {"AAPL": 105.0, "TSLA": 190.0}
        previous = {"AAPL": 100.0, "TSLA": 190.0}
        # only AAPL moves: +5 * 10 = 50
        assert calculate.dayChange(prices, previous, holdings) == 50.0

    def test_uses_yf_ticker_not_display_ticker(self):
        holdings = {
            "cash": 0.0,
            "traditional": [
                {"name": "Barrick", "ticker": "B", "yf_ticker": "GOLD", "shares": 10.0},
            ],
        }
        prices = {"GOLD": 42.0, "B": 999.0}
        previous = {"GOLD": 40.0, "B": 1.0}
        # must use GOLD, not B: (42-40)*10 = 20
        assert calculate.dayChange(prices, previous, holdings) == 20.0

    def test_empty_holdings_returns_zero(self):
        assert calculate.dayChange({}, {}, {"cash": 100.0}) == 0.0

    def test_fractional_shares(self):
        holdings = {
            "cash": 0.0,
            "traditional": [
                {"name": "Apple", "ticker": "AAPL", "yf_ticker": "AAPL", "shares": 0.5},
            ],
        }
        assert calculate.dayChange({"AAPL": 110.0}, {"AAPL": 100.0}, holdings) == 5.0


# ---------------------------------------------------------------------------
# _last_price / _previous_price
# ---------------------------------------------------------------------------

class TestPriceHelpers:
    def _close_frame(self, values_by_ticker: dict[str, list[float]]):
        import pandas as pd

        return pd.DataFrame(values_by_ticker)

    def test_last_price_returns_latest_close(self):
        close = self._close_frame({"AAPL": [100.0, 101.0, 105.0]})
        assert calculate._last_price(close, "AAPL") == 105.0

    def test_previous_price_returns_second_to_last_close(self):
        close = self._close_frame({"AAPL": [100.0, 101.0, 105.0]})
        assert calculate._previous_price(close, "AAPL") == 101.0

    def test_previous_price_none_when_fewer_than_two_closes(self):
        close = self._close_frame({"AAPL": [100.0]})
        assert calculate._previous_price(close, "AAPL") is None

    def test_last_price_none_for_unknown_ticker(self):
        close = self._close_frame({"AAPL": [100.0, 101.0]})
        assert calculate._last_price(close, "MSFT") is None

    def test_last_price_none_when_close_is_none(self):
        assert calculate._last_price(None, "AAPL") is None
        assert calculate._previous_price(None, "AAPL") is None

    def test_last_price_skips_nan_values(self):
        import math

        close = self._close_frame({"AAPL": [100.0, 101.0, float("nan")]})
        assert calculate._last_price(close, "AAPL") == 101.0


# ---------------------------------------------------------------------------
# log_transaction
# ---------------------------------------------------------------------------

class TestLogTransaction:
    def test_writes_header_on_first_write(self, tmp_path):
        path = tmp_path / "transactions.csv"
        assert not path.exists()
        calculate.log_transaction("buy", 100.0, 2, "AAPL", "traditional")
        text = path.read_text(encoding="utf-8")
        lines = text.strip().splitlines()
        assert lines[0] == "transaction,amount,shares,ticker,account"
        assert lines[1] == "buy,100.0,2,AAPL,traditional"

    def test_appends_without_duplicate_header(self, tmp_path):
        calculate.log_transaction("buy", 100.0, 1, "AAPL", "traditional")
        calculate.log_transaction("sell", 50.0, 1, "AAPL", "traditional")
        lines = (tmp_path / "transactions.csv").read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 3
        assert lines[0].startswith("transaction,")
        assert lines[1].startswith("buy,")
        assert lines[2].startswith("sell,")


# ---------------------------------------------------------------------------
# buyStock edge cases
# ---------------------------------------------------------------------------

class TestBuyStockExtra:
    def test_buy_fractional_shares(self, holdings):
        calculate.buyStock(100.0, 0.5, holdings, "AAPL", "traditional")
        assert holdings["cash"] == 950.0
        assert holdings["traditional"][0]["shares"] == 10.5

    def test_buy_on_sustainable_account(self, holdings):
        calculate.buyStock(50.0, 2, holdings, "TSLA", "sustainable")
        assert holdings["cash"] == 900.0
        assert holdings["sustainable"][0]["shares"] == 6.0
