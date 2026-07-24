# Portfolio Manager (backend)

Backend service that values Traditional and Sustainable holdings from
`data/holdings.json` (prices via [yfinance](https://pypi.org/project/yfinance/)),
and lets you buy, sell, apply dividends, and log trades to `data/transactions.csv`.

## Layout

```
backend/
├── main.py                  # entry point
├── pyproject.toml           # packaging + pytest config
├── data/holdings.json       # portfolio positions and cash
├── src/portfolio_manager/   # package (config, market_data, portfolio, trading, ...)
└── tests/                   # pytest suite
```

## Setup

```bash
pip install -r requirements.txt        # runtime deps
pip install -r requirements-dev.txt    # + pytest for tests
# or, for a proper editable install with the console script:
pip install -e .
```

## Run

```bash
python main.py
# or, after `pip install -e .`:
portfolio-manager
```

Menu: buy, sell, print portfolio, dividend, exit.

```bash
make run     # run the CLI
make test    # run pytest
make clean   # remove transactions.csv and caches
```

Edit `data/holdings.json` for positions and cash. Ticker `B` maps to `GOLD` for yfinance.
