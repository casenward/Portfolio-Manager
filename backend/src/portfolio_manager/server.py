"""Uvicorn entry point for the console script and main.py."""

from __future__ import annotations

import uvicorn


def serve() -> None:
    uvicorn.run(
        "portfolio_manager.api.app:app",
        host="127.0.0.1",
        port=8001,
    )


if __name__ == "__main__":
    serve()
