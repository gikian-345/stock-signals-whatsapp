from __future__ import annotations
import os, pytz, datetime as dt
import pandas as pd
import yfinance as yf
import pandas_market_calendars as mcal
from indicators import add_indicators, summarize
from messenger_telegram import send_telegram
from universe_builder import get_universe


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


def build_message(date_ny: dt.datetime, picks: list[dict], others: list[dict], top_n: int = 15) -> str:
    """Format the Telegram message text."""
    header = f"📊 *Daily Trend Signals* — {date_ny.strftime('%a, %b %d, %Y')} (09:00 New York)\n"
    header += "_Universe: S&P 500 + Nasdaq-100_\n_Signals: SMA20/50, RSI(14), 52w proximity, volume spike_\n\n"

    lines = []

    if picks:
        lines.append("✅ *Top BUY Candidates*")
        for p in picks[:top_n]:
            lines.append(
                f"• {p['ticker']}: score {p['score']:.2f} | Trend:{p['trend']} | RSI:{p['rsi']} | "
                f"Δ:{p['pct_chg']:+.2f}% | 52w:{p['prox_52w']}% | Vol×:{p['vol_spike']}"
            )
        lines.append("")

    sells = [o for o in others if o.get("sell_cross")]
    if sells:
        lines.append("⚠️ *SELL Crossovers (heads-up)*")
        for s in sells[:10]:
            lines.append(
                f"• {s['ticker']}: Trend:{s['trend']} | RSI:{s['rsi']} | Δ:{s['pct_chg']:+.2f}%"
            )
        lines.append("")

    footer = "\n—\n_Educational only. Tune rules in repo to fit your strategy._"
    return header + "\n".join(lines) + footer


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
