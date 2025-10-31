from __future__ import annotations
import re
import requests
import pandas as pd
import yfinance as yf

WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKI_NDQ100 = "https://en.wikipedia.org/wiki/Nasdaq-100"

def _clean_ticker(t: str) -> str:
    t = t.strip().upper()
    # yfinance uses BRK-B instead of BRK.B
    t = t.replace(".", "-")
    return t

def _scrape_symbols(url: str, symbol_col_like: str) -> list[str]:
    """
    Grab a table from Wikipedia and extract tickers from the column
    whose name contains `symbol_col_like`.
    """
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    tables = pd.read_html(res.text)
    for tb in tables:
        cols_lower = [str(c).lower() for c in tb.columns]
        if any(symbol_col_like in c for c in cols_lower):
            idx = [symbol_col_like in c for c in cols_lower].index(True)
            symcol = tb.columns[idx]
            syms = [_clean_ticker(str(x)) for x in tb[symcol].tolist()]
            return [s for s in syms if re.match(r"^[A-Z0-9\-]+$", s)]
    return []

def get_universe() -> list[str]:
    """
    Returns a deduplicated, sorted list of 300+ large-cap US tickers:
    S&P 500 + Nasdaq-100. Tries yfinance first, falls back to Wikipedia.
    """
    universe = set()

    # Try yfinance S&P 500 list
    try:
        for t in yf.tickers_sp500():
            universe.add(_clean_ticker(t))
    except Exception:
        # Fallback: Wikipedia S&P 500 page
        sp = _scrape_symbols(WIKI_SP500, "symbol")
        universe.update(sp)

    # Nasdaq-100
    try:
        ndq = _scrape_symbols(WIKI_NDQ100, "ticker")
        universe.update(ndq)
    except Exception:
        pass

    out = sorted(universe)
    if len(out) < 300:
        raise RuntimeError(f"Universe too small ({len(out)}).")
    return out
