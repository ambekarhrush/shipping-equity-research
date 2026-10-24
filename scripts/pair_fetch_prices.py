"""Download daily prices for the SBLK/GNK pair, the bidder (DSX), a peer and benchmarks.

Vendor data is written to the git-ignored .cache/pair/prices.csv and is not committed.
Run: uv run --with yfinance python scripts/pair_fetch_prices.py
"""

import warnings
from pathlib import Path

import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
TICKERS = ["SBLK", "GNK", "DSX", "SB", "BDRY", "SPY"]

frames = []
for t in TICKERS:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        h = yf.Ticker(t).history(start="2021-01-01", auto_adjust=False, actions=True)
    h.index = pd.to_datetime(h.index).tz_localize(None).normalize()
    frames.append(
        pd.DataFrame(
            {
                "date": h.index.strftime("%Y-%m-%d"),
                "ticker": t,
                "close": h["Close"].values,
                "adj_close": h["Adj Close"].values,
                "dividend": h["Dividends"].values,
                "volume": h["Volume"].values,
            }
        )
    )
    print(
        f"{t:5s} {h.index[0].date()} -> {h.index[-1].date()} last close {h['Close'].iloc[-1]:.2f}"
    )

out = ROOT / ".cache" / "pair" / "prices.csv"
out.parent.mkdir(parents=True, exist_ok=True)
pd.concat(frames).to_csv(out, index=False)
print("wrote", out)
