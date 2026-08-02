"""API tests using FastAPI TestClient with mocked market data."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from portfolio_manager.api.app import create_app
from portfolio_manager import market_data, transactions


SAMPLE_HOLDINGS = {
    "cash": 1000.0,
    "traditional": [
        {"name": "Apple", "ticker": "AAPL", "shares": 10.0},
    ],
    "sustainable": [
        {"name": "Tesla", "ticker": "TSLA", "shares": 4.0},
    ],
}


@pytest.fixture
def holdings_file(tmp_path: Path) -> Path:
    path = tmp_path / "holdings.json"
    path.write_text(json.dumps(SAMPLE_HOLDINGS), encoding="utf-8")
    return path


@pytest.fixture
def client(holdings_file: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        transactions, "TRANSACTIONS_PATH", tmp_path / "transactions.csv"
    )

    def fake_prices(yf_tickers: list[str]):
        latest = {t: 100.0 for t in yf_tickers}
        previous = {t: 95.0 for t in yf_tickers}
        return latest, previous

    monkeypatch.setattr(market_data, "fetch_current_prices", fake_prices)

    app = create_app(holdings_path=holdings_file)
    with TestClient(app) as test_client:
        yield test_client, holdings_file


class TestHealth:
    def test_health(self, client):
        test_client, _ = client
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestHoldings:
    def test_get_holdings(self, client):
        test_client, _ = client
        response = test_client.get("/holdings")
        assert response.status_code == 200
        data = response.json()
        assert data["cash"] == 1000.0
        assert data["traditional"][0]["ticker"] == "AAPL"
        assert data["traditional"][0]["yf_ticker"] == "AAPL"


class TestPortfolio:
    def test_portfolio_summary(self, client):
        test_client, _ = client
        response = test_client.get("/portfolio")
        assert response.status_code == 200
        data = response.json()
        # AAPL 10*100 + TSLA 4*100 = 1400; day change (100-95)*14 = 70
        assert data["traditional"] == 1000.0
        assert data["sustainable"] == 400.0
        assert data["combined"] == 1400.0
        assert data["cash"] == 1000.0
        assert data["day_change"] == 70.0
        assert data["missing"] == []


class TestBuy:
    def test_buy_success_and_persists(self, client):
        test_client, holdings_file = client
        response = test_client.post(
            "/buy",
            json={"ticker": "AAPL", "shares": 2, "account": "traditional"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "buy"
        assert data["cost"] == 200.0
        assert data["cash"] == 800.0

        saved = json.loads(holdings_file.read_text(encoding="utf-8"))
        assert saved["cash"] == 800.0
        assert saved["traditional"][0]["shares"] == 12.0

    def test_buy_insufficient_cash_returns_400(self, client):
        test_client, _ = client
        response = test_client.post(
            "/buy",
            json={"ticker": "AAPL", "shares": 100, "account": "traditional"},
        )
        assert response.status_code == 400
        assert "Not enough cash" in response.json()["detail"]

    def test_buy_unknown_ticker_returns_400(self, client):
        test_client, _ = client
        response = test_client.post(
            "/buy",
            json={"ticker": "GOOG", "shares": 1, "account": "traditional"},
        )
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]


class TestSell:
    def test_sell_success(self, client):
        test_client, holdings_file = client
        response = test_client.post(
            "/sell",
            json={"ticker": "AAPL", "shares": 3, "account": "traditional"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "sell"
        assert data["proceeds"] == 300.0
        assert data["cash"] == 1300.0

        saved = json.loads(holdings_file.read_text(encoding="utf-8"))
        assert saved["traditional"][0]["shares"] == 7.0


class TestDividend:
    def test_dividend_without_reinvest(self, client):
        test_client, holdings_file = client
        response = test_client.post(
            "/dividend",
            json={
                "ticker": "AAPL",
                "account": "traditional",
                "dividend_yield": 0.02,
                "reinvest": False,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cash_yield"] == 20.0
        assert data["reinvested"] is False
        assert data["cash"] == 1020.0

        saved = json.loads(holdings_file.read_text(encoding="utf-8"))
        assert saved["cash"] == 1020.0

    def test_dividend_with_reinvest(self, client):
        test_client, _ = client
        response = test_client.post(
            "/dividend",
            json={
                "ticker": "AAPL",
                "account": "traditional",
                "dividend_yield": 0.10,
                "reinvest": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["reinvested"] is True
        assert data["shares_bought"] == pytest.approx(1.0)
        assert data["cash"] == 1000.0
