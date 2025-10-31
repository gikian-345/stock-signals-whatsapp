from __future__ import annotations
import numpy as np
import pandas as pd

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds:
      - SMA20, SMA50
      - RSI14
      - prox_52w (proximity to 52-week high, %)
      - vol_spike (Volume / 30d avg)
    """
    out = df.copy()

    # Moving averages (trend)
    out["SMA20"] = out["Close"].rolling(20).mean()
    out["SMA50"] = out["Close"].rolling(50).mean()

    # RSI(14)
    delta = out["Close"].diff()
    up = delta.clip(lower=0.0)
    down = -delta.clip(upper=0.0)
    roll_up = up.ewm(alpha=1/14, adjust=False).mean()
    roll_down = down.ewm(alpha=1/14, adjust=False).mean().replace(0, np.nan)
    rs = roll_up / roll_down
    out["RSI14"] = 100 - (100 / (1 + rs))

    # 52-week high proximity (252 trading days)
    out["H52W"] = out["High"].rolling(252, min_periods=50).max()
    out["prox_52w"] = (out["Close"] / out["H52W"]) * 100

    # Volume spike vs 30-day average
    out["vol30"] = out["Volume"].rolling(30).mean()
    out["vol_spike"] = out["Volume"] / out["vol30"]

    return out
