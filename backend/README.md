# Portfolio Manager (backend)

FastAPI service that values Traditional and Sustainable holdings from
`data/holdings.json` (prices via [yfinance](https://pypi.org/project/yfinance/)),
and lets you buy, sell, apply dividends, and log trades to `data/transactions.csv`.

Mutations are persisted back to `holdings.json` (cash, name, ticker, shares).
Derived fields like `yf_ticker` and original `date_bought` are not written back.

## Layout

```
backend/
├── main.py                  # uvicorn entry point
├── pyproject.toml           # packaging + pytest config
├── data/holdings.json       # portfolio positions and cash
├── src/portfolio_manager/   # core logic + api/
└── tests/                   # pytest suite
```

## Setup

```bash
pip install -r requirements.txt        # runtime deps
pip install -r requirements-dev.txt    # + pytest, httpx
# or, for a proper editable install with the console script:
pip install -e ".[dev]"
```

## Run

```bash
python main.py
# or:
uvicorn portfolio_manager.api.app:app --host 127.0.0.1 --port 8001
# or, after `pip install -e .`:
portfolio-manager
```

Open interactive docs at [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs).

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness check |
| GET | `/holdings` | Cash + positions |
| GET | `/portfolio` | Live valuation + day change |
| POST | `/buy` | `{ticker, shares, account}` |
| POST | `/sell` | `{ticker, shares, account}` |
| POST | `/dividend` | `{ticker, account, dividend_yield, reinvest}` |

`dividend_yield` is a fraction (e.g. `0.02` for 2%). Prices are fetched live from yfinance on each request that needs them.

```bash
make run     # start the API server
make test    # run pytest
make clean   # remove transactions.csv and caches
```

Edit `data/holdings.json` for positions and cash. Ticker `B` maps to `GOLD` for yfinance.
