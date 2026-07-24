"""Display formatting helpers."""

from __future__ import annotations


def format_dollars(value: float) -> str:
    return f"${value:,.2f}"
