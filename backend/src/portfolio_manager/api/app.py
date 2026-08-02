"""FastAPI application factory and module-level app instance."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from portfolio_manager.api.routes import router
from portfolio_manager.config import HOLDINGS_PATH
from portfolio_manager.repository import load_holdings
from portfolio_manager.state import AppState


def create_app(holdings_path: Path | None = None) -> FastAPI:
    path = holdings_path or HOLDINGS_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        holdings = load_holdings(path)
        app.state.app_state = AppState(holdings=holdings, holdings_path=path)
        yield

    app = FastAPI(
        title="Portfolio Manager",
        description="HTTP API for portfolio valuation and trading",
        version="0.1.0",
        lifespan=lifespan,
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(router)
    return app


app = create_app()
