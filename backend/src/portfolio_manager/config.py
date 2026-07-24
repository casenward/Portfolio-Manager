"""Configuration constants: filesystem paths and ticker overrides."""

from __future__ import annotations

from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parents[2]

HOLDINGS_PATH = _BASE_DIR / "data" / "holdings.json"
TRANSACTIONS_PATH = _BASE_DIR / "data" / "transactions.csv"

YF_TICKER_OVERRIDES = {
    "B": "GOLD",  # Barrick Mining Corporation
}
