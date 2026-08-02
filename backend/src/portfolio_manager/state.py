"""Shared application state for the FastAPI service."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AppState:
    holdings: dict
    holdings_path: Path
    lock: threading.Lock = field(default_factory=threading.Lock)
