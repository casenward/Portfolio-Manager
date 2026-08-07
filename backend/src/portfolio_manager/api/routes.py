"""HTTP route handlers."""

from __future__ import annotations

from fastapi import APIRouter, Request

from portfolio_manager import service
from portfolio_manager.api.schemas import (
    DashboardResponse,
    DividendRequest,
    DividendResponse,
    HealthResponse,
    HoldingsResponse,
    PerformanceResponse,
    PortfolioResponse,
    TradeRequest,
    TradeResponse,
)
from portfolio_manager.state import AppState

router = APIRouter()


def _state(request: Request) -> AppState:
    return request.app.state.app_state


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/holdings", response_model=HoldingsResponse)
def holdings(request: Request) -> HoldingsResponse:
    return HoldingsResponse(**service.get_holdings(_state(request)))


@router.get("/portfolio", response_model=PortfolioResponse)
def portfolio(request: Request) -> PortfolioResponse:
    return PortfolioResponse(**service.get_portfolio_summary(_state(request)))


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(request: Request) -> DashboardResponse:
    return DashboardResponse(**service.get_dashboard(_state(request)))


@router.get("/performance", response_model=PerformanceResponse)
def performance(request: Request) -> PerformanceResponse:
    return PerformanceResponse(**service.get_performance(_state(request)))


@router.post("/buy", response_model=TradeResponse)
def buy(body: TradeRequest, request: Request) -> TradeResponse:
    result = service.execute_buy(
        _state(request),
        body.ticker,
        body.shares,
        body.account,
    )
    return TradeResponse(**result)


@router.post("/sell", response_model=TradeResponse)
def sell(body: TradeRequest, request: Request) -> TradeResponse:
    result = service.execute_sell(
        _state(request),
        body.ticker,
        body.shares,
        body.account,
    )
    return TradeResponse(**result)


@router.post("/dividend", response_model=DividendResponse)
def apply_dividend(body: DividendRequest, request: Request) -> DividendResponse:
    result = service.execute_dividend(
        _state(request),
        body.ticker,
        body.account,
        body.dividend_yield,
        body.reinvest,
    )
    return DividendResponse(**result)
