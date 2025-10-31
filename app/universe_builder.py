from __future__ import annotations
import re
import time
import requests
import pandas as pd

# Official pages we scrape (we'll send a real User-Agent to avoid 403)
WIKI_SP500 = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
WIKI_NDQ100 = "https://en.wikipedia.org/wiki/Nasdaq-100"

HEADERS = {
    # A polite UA per Wikipedia robots policy; adjust contact if you wish
    "User-Agent": "StockSignalsBot/1.0 (+https://github.com/yourrepo) contact: admin@example.com",
    "Accept-Language": "en-US,en;q=0.8",
    "Cache-Control": "no-cache",
}

def _clean_ticker(t: str) -> str:
    t = str(t).strip().upper()
    # yfinance uses BRK-B (not BRK.B), BF-B (not BF.B), etc.
    t = t.replace(".", "-")
    return t

def _http_get(url: str, tries: int = 3, backoff: float = 1.5) -> requests.Response:
    last_exc = None
    for i in range(tries):
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r
            # Some CDNs return 403/429 intermittently; brief backoff helps
            time.sleep(backoff * (i + 1))
        except requests.RequestException as e:
            last_exc = e
            time.sleep(backoff * (i + 1))
    if last_exc:
        raise last_exc
    raise requests.HTTPError(f"Failed to fetch {url}")

def _scrape_symbols(url: str, symbol_col_like: str) -> list[str]:
    """
    Load tables from a page and return the first column whose header contains `symbol_col_like`.
    For S&P 500 we look for 'symbol', for Nasdaq-100 we look for 'ticker'.
    """
    res = _http_get(url)
    # Use the response text directly (don’t let pandas fetch again without our headers)
    tables = pd.read_html(res.text)
    for tb in tables:
        cols_lower = [str(c).lower() for c in tb.columns]
        if any(symbol_col_like in c for c in cols_lower):
            idx = [symbol_col_like in c for c in cols_lower].index(True)
            symcol = tb.columns[idx]
            raw = tb[symcol].tolist()
            syms = [_clean_ticker(x) for x in raw]
            # Keep only “regular” tickers (letters, digits, dash)
            return [s for s in syms if re.fullmatch(r"[A-Z0-9\-]+", s)]
    return []

def _load_static_universe() -> list[str]:
    """
    Fallback: read a static list if present.
    Create app/universe.txt with one ticker per line to control your own universe.
    """
    import pathlib
    path = pathlib.Path(__file__).parent / "universe.txt"
    if not path.exists():
        return []
    tickers = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        tickers.append(_clean_ticker(line))
    return tickers

def get_universe() -> list[str]:
    """
    Return a deduplicated, sorted list of >300 large-cap US tickers:
    S&P 500 + Nasdaq-100 via Wikipedia scrape (with User-Agent), else fall back to app/universe.txt.
    """
    universe = set()

    # Primary: scrape S&P 500 + Nasdaq-100 from Wikipedia with proper headers
    try:
        sp = _scrape_symbols(WIKI_SP500, "symbol")
        universe.update(sp)
    except Exception:
        pass

    try:
        ndq = _scrape_symbols(WIKI_NDQ100, "ticker")
        universe.update(ndq)
    except Exception:
        pass

    # Fallback: static file if scraping failed or returned too few
    if len(universe) < 300:
        static_list = _load_static_universe()
        universe.update(static_list)

    out = sorted(universe)
    if len(out) < 300:
        raise RuntimeError(f"Universe too small ({len(out)}). "
                           f"Scrape may be blocked. Add more tickers to app/universe.txt to exceed 300.")
    return out
