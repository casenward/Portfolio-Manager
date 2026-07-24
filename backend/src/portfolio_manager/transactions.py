"""Transaction logging to CSV."""

from __future__ import annotations

from .config import TRANSACTIONS_PATH


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
