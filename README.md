# Portfolio Manager

CLI that values Traditional and Sustainable holdings from `data/holdings.json`
(prices via [yfinance](https://pypi.org/project/yfinance/)), then lets you
buy, sell, apply dividends, and log trades to `data/transactions.csv`.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python calculate.py
```

Menu: buy, sell, print portfolio, dividend, exit.

```bash
make clean   # delete data/transactions.csv
```

Edit `data/holdings.json` for positions. Ticker `B` maps to `GOLD` for yfinance.
