# How to Load Your Holdings

This guide is for loading your portfolio into Portfolio Manager. You do **not** need to write code. You only need to put one file in the right place, in the right shape.

---

## What you are doing (high level)

1. Gather your portfolio: cash, each stock/ETF name, ticker symbol, and number of shares.
2. Turn that list into a file named `holdings.json` (an AI can do this for you — see the prompt below).
3. Save that file here:

   **`backend/data/holdings.json`**

4. Restart the app (or ask whoever runs it for you to restart it) so it picks up the new file.

That is the whole process. The app reads this file whenever it starts.

---

## What belongs in the file

Think of the file as three buckets:

| Bucket | Meaning |
|--------|---------|
| **Cash** | Uninvested cash in the account (one number) |
| **Traditional** | Positions in your traditional / core portfolio |
| **Sustainable** | Positions in your sustainable / ESG portfolio (can be empty) |

Each stock or ETF in Traditional or Sustainable needs only three things:

| Field | What to put |
|-------|-------------|
| **name** | Full company or fund name (e.g. `Apple Inc.`) |
| **ticker** | Exchange symbol (e.g. `AAPL`) |
| **shares** | How many shares you own (decimals are OK) |

Do **not** put prices, sectors, or market values in this file. The app looks those up live.

---

## Example (small)

```json
{
  "cash": 50000.0,
  "traditional": [
    {
      "name": "Apple Inc.",
      "ticker": "AAPL",
      "shares": 100.0
    },
    {
      "name": "Exxon Mobil Corporation",
      "ticker": "XOM",
      "shares": 250.0
    }
  ],
  "sustainable": [
    {
      "name": "NextEra Energy, Inc.",
      "ticker": "NEE",
      "shares": 80.0
    }
  ]
}
```

If you have no sustainable holdings, still include the section, but leave it empty:

```json
"sustainable": []
```

---

## Tips

- Use the **official ticker** from your brokerage (usually all caps).
- One row per ticker in each account. If you bought the same stock twice, add the shares together.
- Cash is a single number for the whole portfolio (not per account).
- Replace the existing `holdings.json` — do not create a second copy with a different name unless you know how to point the app at it.
- Keep a backup of the old file before you overwrite it (copy/paste into a folder like `holdings-backup`).

---

## Copy-and-paste AI prompt

Copy everything in the box below into ChatGPT, Claude, Cursor, or similar. Then paste your holdings (spreadsheet export, brokerage statement text, or a rough list) under the prompt.

```
I need a holdings.json file for a Portfolio Manager app. Convert my portfolio data into valid JSON that matches this exact format and rules.

FORMAT:
{
  "cash": <number>,
  "traditional": [
    { "name": "<full company or fund name>", "ticker": "<SYMBOL>", "shares": <number> }
  ],
  "sustainable": [
    { "name": "<full company or fund name>", "ticker": "<SYMBOL>", "shares": <number> }
  ]
}

RULES:
1. Output ONLY the JSON file contents — no markdown fences, no commentary before or after.
2. Include all three top-level keys: cash, traditional, sustainable.
3. If I do not specify an account, put positions in "traditional".
4. If I have no sustainable positions, use "sustainable": [].
5. Each position must have exactly: name, ticker, shares.
6. Do NOT include price, sector, market value, cost basis, date, account number, or any other fields.
7. ticker must be the exchange symbol in uppercase (e.g. AAPL, MSFT).
8. shares must be a number (decimals allowed). Combine duplicate tickers in the same account by summing shares.
9. cash must be a single number. If I do not give cash, use 0.
10. Use the full security name when I provide it; if I only give a ticker, use a reasonable full name.
11. Validate that the result is parseable JSON before you finish.

MY PORTFOLIO DATA:
<paste your holdings / brokerage export / spreadsheet here>
```

After the AI replies, save the result as `holdings.json` in `backend/data/`, replacing the old file.
