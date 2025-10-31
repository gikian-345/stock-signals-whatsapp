from __future__ import annotations
import os, pytz, datetime as dt
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal

# ✅ Use fully qualified imports
from app.indicators import add_indicators, summarize
from app.messenger_telegram import send_telegram
from app.universe_builder import get_universe





# --- Configuration ---
NY_TZ = pytz.timezone("America/New_York")

def is_ny_9am_now() -> bool:
    """Check if current New York time is 09:00."""
    now_ny = dt.datetime.now(NY_TZ)
    return now_ny.hour == 9 and now_ny.minute == 0

def is_market_day(date_ny: dt.date) -> bool:
    """Check if NYSE is open on this date."""
    nyse = mcal.get_calendar("NYSE")
    sched = nyse.schedule(start_date=date_ny, end_date=date_ny)
    return not sched.empty

def fetch_daily(ticker: str) -> pd.DataFrame:
    """Download 14 months of daily data from Yahoo Finance."""
    df = yf.download(ticker, period="14mo", interval="1d", auto_adjust=True, progress=False)
    if df.empty:
        raise RuntimeError("no data")
    for col in ["Close", "High", "Low", "Volume"]:
        if col not in df.columns:
            raise RuntimeError("missing columns")
    df = df.dropna(subset=["Close", "High", "Low"])
    return df

def build_message(date_ny: dt.datetime, picks: list[dict], others: list[dict], top_n: int = 20) -> str:
    """Builds an easy-to-read Telegram summary for beginners."""
    header = f"📊 *Daily Stock Insights* — {date_ny.strftime('%a, %b %d, %Y')} (09:00 New York)\n\n"

    total_up = sum(1 for p in picks if p["trend"] == "Up")
    total_down = sum(1 for p in picks if p["trend"] == "Down")
    avg_rsi = round(sum(p["rsi"] for p in picks if p["rsi"]) / max(len(picks), 1), 1)

    summary = (
        f"*Today’s Market Snapshot:*\n"
        f"• {total_up} stocks show strong upward trends.\n"
        f"• {total_down} stocks are trending down or consolidating.\n"
        f"• Average RSI of top movers: {avg_rsi} (neutral to bullish)\n\n"
    )

    body = "*Top 20 Trending Stocks Today:*\n"
    if not picks:
        body += "_No strong trend signals detected today._\n"
    else:
        for i, p in enumerate(picks[:top_n], start=1):
            body += (
                f"{i}. *{p['ticker']}* — {p['trend']} trend "
                f"(RSI: {p['rsi']}, Δ: {p['pct_chg']:+.2f}%, "
                f"52w: {p['prox_52w']}%, Vol×: {p['vol_spike']})\n"
            )

    explain = (
        "\n📈 *Indicators Explained:*\n"
        "• *SMA20/50*: Short-term (20-day) vs long-term (50-day) price averages.\n"
        "• *RSI(14)*: Momentum indicator (below 40 = oversold, above 70 = overbought).\n"
        "• *52w High*: How close price is to its yearly peak (in %).\n"
        "• *Vol×*: Current volume compared to 30-day average.\n"
    )

    footer = "\n—\n_This is a bot designed and programmed by Hamza Syed and its for Educational only. Use for learning trend analysis, not direct financial advice._"

    return header + summary + body + explain + footer

def main():
    """Main daily pipeline."""
    override = os.environ.get("OVERRIDE_SEND", "false").lower() == "true"
    now_ny = dt.datetime.now(NY_TZ)

    # Skip if not 9 AM NY time or not a trading day (unless forced)
    if not override:
        if not is_ny_9am_now():
            print("Not 09:00 NY; exit.")
            return
        if not is_market_day(now_ny.date()):
            print("Not a NYSE trading day; exit.")
            return

    universe = get_universe()
    buy_candidates, others = [], []

    for tkr in universe:
        try:
            df = fetch_daily(tkr)
            ind = add_indicators(df).dropna().copy()
            if len(ind) < 60:
                continue
            last = ind.iloc[-1]
            prev = ind.iloc[-2]
            info = summarize(prev, last)
            info["ticker"] = tkr
            if info["buy_cross"] and info["trend"] == "Up":
                buy_candidates.append(info)
            else:
                others.append(info)
        except Exception:
            continue

    # Rank BUYs by score and proximity to 52w high
    buy_candidates.sort(key=lambda x: (x["score"], x.get("prox_52w") or 0.0), reverse=True)

    body = build_message(now_ny, buy_candidates, others, top_n=15)

    # --- Send to Telegram ---
    send_telegram(body)
    print("Telegram message sent successfully.")

if __name__ == "__main__":
    main()
