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

def _crossover(prev: pd.Series, last: pd.Series) -> tuple[bool, bool]:
    up = (last["SMA20"] > last["SMA50"]) and (prev["SMA20"] <= prev["SMA50"])
    down = (last["SMA20"] < last["SMA50"]) and (prev["SMA20"] >= prev["SMA50"])
    return up, down

def _score(prev: pd.Series, last: pd.Series) -> float:
    score = 0.0
    # Trend bias
    if last["SMA20"] > last["SMA50"]:
        score += 1.0
    # Fresh bullish crossover
    up, _ = _crossover(prev, last)
    if up:
        score += 2.0
    # RSI sweet spot
    rsi = last["RSI14"]
    if pd.notna(rsi) and 45 <= rsi <= 60:
        score += 1.0
    # Near 52-week high
    if pd.notna(last["prox_52w"]) and last["prox_52w"] >= 90:
        score += 1.0
    # Volume confirmation
    if pd.notna(last["vol_spike"]) and last["vol_spike"] >= 1.2:
        score += 1.0
    return float(score)

def summarize(prev: pd.Series, last: pd.Series) -> dict:
    up, down = _crossover(prev, last)
    trend = "Up" if last["SMA20"] > last["SMA50"] else "Down"
    pct_chg = (last["Close"] / prev["Close"] - 1) * 100

    return {
        "trend": trend,
        "buy_cross": up,
        "sell_cross": down,
        "rsi": None if pd.isna(last["RSI14"]) else round(float(last["RSI14"]), 1),
        "prox_52w": None if pd.isna(last["prox_52w"]) else round(float(last["prox_52w"]), 1),
        "vol_spike": None if pd.isna(last["vol_spike"]) else round(float(last["vol_spike"]), 2),
        "pct_chg": round(float(pct_chg), 2),
        "score": round(_score(prev, last), 2),
    }
