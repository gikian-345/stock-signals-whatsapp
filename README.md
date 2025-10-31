# Daily WhatsApp Stock Signals (GitHub Actions)

Every **NY trading day at 09:00 New York**, this workflow ranks **300+ US stocks** (S&P 500 + Nasdaq‑100) by trend signals and **WhatsApps** you a compact list of **Top BUY candidates** plus notable **SELL crossovers**.

**Signals:** SMA20/50 trend & crossovers, RSI(14), 52‑week proximity, volume spike vs 30‑day average.  
**Delivery:** WhatsApp via Twilio sandbox or business sender.  
**Scheduler:** GitHub Actions runs hourly but the script **sends only at exactly 09:00 America/New_York** and **only on NYSE trading days** (skips weekends & holidays).

## Quick start

1. Create a Twilio account → Messaging → *Try it out* → **WhatsApp Sandbox**. Join the sandbox from your phone.  
2. Fork / upload this repo.  
3. Add **Actions → Secrets and variables → Secrets**:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_TO` (format: `whatsapp:+1XXXXXXXXXX`)
   - *(optional)* `TWILIO_WHATSAPP_FROM` if you have a dedicated WhatsApp sender  
4. (Optional test) Add a **repository variable** `OVERRIDE_SEND=true`, then trigger **Actions → Run workflow** to receive a test message immediately. Remove the variable after testing.  
5. Let it run; you’ll get messages each trading day at 09:00 New York time.

> Educational use only. Not financial advice.
