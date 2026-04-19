# 📱 Analizzatore di Mercato Pro

Mobile-first Streamlit app for RSI + Bollinger Bands confluence scanning on
daily equity data.

## Features

1. **Multi-identifier search** — accepts ticker (`ERG.MI`, `AAPL`), company name
   (`Eni`, `Microsoft`), or ISIN (`IT0001157059`). Resolves via `yfinance.Search`.
2. **Liquidity filter** — blocks unreliable signals on thin-volume names
   (90d avg volume threshold: 300,000).
3. **Indicators** — Wilder RSI(14) + Bollinger(20, 2σ). ATR(14) used for R/R sizing.
4. **Confluence signal** — `Price ≤ BB Lower AND RSI ≤ 30`.
5. **Audit report** — on active signal, computes target (BB mid), stop (1.5× ATR),
   and R/R ratio.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io) → New app → point at `app.py`.
3. No secrets required — all data comes from `yfinance` public endpoints.

## Architecture notes

- **Caching**: `resolve_identifier` cached 1h (stable), `fetch_and_analyze` cached 15min
  (daily bars don't change intraday much; reduces yfinance load on reruns).
- **RSI**: uses Wilder's smoothing (`ewm` with `alpha = 1/period`), not SMA —
  this matches TradingView / standard charting.
- **Bollinger**: population std (`ddof=0`) per the standard definition.
- **Multi-index handling**: `yf.download` returns `MultiIndex` columns even for
  single tickers in recent versions; we flatten defensively.
- **Mobile layout**: `layout="centered"` + max-width 780px + 2-row subplot
  (70/30 split) keeps the chart readable on a phone.

## Known limitations

- `yf.Search` for raw ISINs can be flaky — ISIN → ticker resolution works best
  for widely-held names. If it fails, the UI nudges toward the direct ticker.
- Liquidity threshold (300k) is a blunt instrument; for penny stocks or
  ADR-secondary listings you may want to lower it or switch to dollar volume.
