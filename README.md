# Portfolio Manager

FastAPI service that values Traditional and Sustainable holdings from
`backend/data/holdings.json` (prices via [yfinance](https://pypi.org/project/yfinance/)),
and lets you buy, sell, apply dividends, and log trades to `backend/data/transactions.csv`.

Mutations are persisted back to `holdings.json` (cash, name, ticker, shares).
Derived fields like `yf_ticker` and original `date_bought` are not written back.

The React dashboard lives in [`frontend/`](frontend/).

## Layout

```
.
├── README.md
├── Makefile
├── requirements.txt / requirements-dev.txt
├── backend/
│   ├── main.py                  # uvicorn entry point
│   ├── pyproject.toml           # packaging + pytest config
│   ├── data/holdings.json       # portfolio positions and cash
│   ├── src/portfolio_manager/   # core logic + api/
│   └── tests/                   # pytest suite
└── frontend/                    # Vite + React dashboard
```

## Setup

```bash
pip install -r requirements.txt        # runtime deps
pip install -r requirements-dev.txt    # + pytest, httpx
# or, for a proper editable install with the console script:
pip install -e "./backend[dev]"
```

## Run

```bash
cd backend && python main.py
# or from repo root:
make run
# or:
cd backend && uvicorn portfolio_manager.api.app:app --host 127.0.0.1 --port 8001
# or, after `pip install -e "./backend[dev]"`:
portfolio-manager
```

Open interactive docs at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

For the dashboard: start the API, then `cd frontend && npm install && npm run dev`.

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/holdings` | Cash + positions |
| GET | `/portfolio` | Live valuation + day change |
| GET | `/dashboard` | Total worth, companies, sector allocation |
| GET | `/performance` | Cumulative return series vs S&P 500 (1M–ALL) |
| POST | `/buy` | `{ticker, shares, account}` |
| POST | `/sell` | `{ticker, shares, account}` |
| POST | `/dividend` | `{ticker, account, dividend_yield, reinvest}` |

`dividend_yield` is a fraction (e.g. `0.02` for 2%). Prices are fetched live from yfinance on each request that needs them.

```bash
make run     # start the API server
make test    # run pytest
make clean   # remove transactions.csv and caches
```

Edit `backend/data/holdings.json` for positions and cash. Ticker `B` maps to `GOLD` for yfinance.
