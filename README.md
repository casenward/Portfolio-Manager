# Portfolio Manager (bare calculator)

Standalone CLI that loads `holdings.json`, fetches the latest prices via
[yfinance](https://pypi.org/project/yfinance/), and prints Traditional,
Sustainable, and Combined portfolio values.

This folder is self-contained — copy it anywhere and run it on its own.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python calculate.py
```

Example output:

```
Traditional: $X,XXX,XXX.XX
Sustainable: $X,XXX,XXX.XX
Combined:    $X,XXX,XXX.XX
```

Edit `holdings.json` to change positions. Ticker `B` is mapped to `GOLD` for
yfinance (Barrick Mining).
