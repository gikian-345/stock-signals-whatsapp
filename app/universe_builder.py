from __future__ import annotations
import re
import requests
import pandas as pd
import yfinance as yf

WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKI_NDQ100 = "https://en.wikipedia.org/wiki/Nasdaq-100"

def _clean_ticker(t: str) -> str:
    t = t.strip().upper()
    t = t.replace(".", "-")  # BRK.B -> BRK-B
    return t

def _from_wikipedia(url: str, symbol_col_like: str) -> list[str]:
    res = requests.get(url, timeout=20)
    res.raise_for_status()
    tables = pd.read_html(res.text)
    for tb in tables:
        cols = [c.lower() for c in tb.columns]
        if any(symbol_col_like in c for c in cols):
            idx = [symbol_col_like in c for c in cols].index(True)
            symcol = tb.columns[idx]
            syms = [_clean_ticker(str(x)) for x in tb[symcol].tolist()]
            return [s for s in syms if re.match(r"^[A-Z0-9\-]+$", s)]
    return []

def get_universe() -> list[str]:
    universe = set()
    try:
        for t in yf.tickers_sp500():
            universe.add(_clean_ticker(t))
    except Exception:
        sp = _from_wikipedia(WIKI_SP500, "symbol")
        universe.update(sp)
    try:
        ndq = _from_wikipedia(WIKI_NDQ100, "ticker")
        universe.update(ndq)
    except Exception:
        pass
    out = sorted(universe)
    if len(out) < 300:
        raise RuntimeError(f"Universe too small ({len(out)}).")
    return out
