"""Application entry point for the Portfolio Manager FastAPI service."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from portfolio_manager.server import serve

if __name__ == "__main__":
    serve()
