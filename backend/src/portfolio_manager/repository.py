"""Holdings persistence: load portfolio positions and cash from disk."""

from __future__ import annotations

import json
from pathlib import Path

from .config import HOLDINGS_PATH
from .tickers import resolve_yf_ticker


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
