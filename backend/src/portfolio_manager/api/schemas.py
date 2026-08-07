"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class Position(BaseModel):
    name: str
    ticker: str
    yf_ticker: str
    shares: float


class HoldingsResponse(BaseModel):
    cash: float
    traditional: list[Position]
    sustainable: list[Position]


class PortfolioResponse(BaseModel):
    traditional: float
    sustainable: float
    combined: float
    cash: float
    day_change: float
    missing: list[str]


class CompanyPosition(BaseModel):
    symbol: str
    name: str
    account: str
    sector: str
    price: float
    weight: float
    dayChg: float
    value: float


class SectorAllocation(BaseModel):
    name: str
    value: float


class DashboardResponse(BaseModel):
    total_worth: float
    companies: list[CompanyPosition]
    sectors: list[SectorAllocation]


class TradeRequest(BaseModel):
    ticker: str
    shares: float = Field(gt=0)
    account: str = "traditional"


class TradeResponse(BaseModel):
    action: str
    ticker: str
    account: str
    shares: float
    price: float
    cash: float
    cost: float | None = None
    proceeds: float | None = None


class DividendRequest(BaseModel):
    ticker: str
    account: str = "traditional"
    dividend_yield: float = Field(
        gt=0,
        description="Yield as a fraction (e.g. 0.02 for 2%)",
    )
    reinvest: bool = False


class DividendResponse(BaseModel):
    action: str
    ticker: str
    account: str
    cash_yield: float
    reinvested: bool
    shares_bought: float
    cash: float


class ErrorResponse(BaseModel):
    detail: str
