# 📱 Analizzatore di Mercato Pro

Mobile-first Streamlit app for RSI + Bollinger Bands confluence scanning on
daily equity data. **Includes a screener for Milan + Nasdaq.**

## Features

1. **Screener (NEW)** — scans 60 Milan + 60 Nasdaq tickers and shows up to 10
   names that simultaneously meet the confluence condition, sorted by signal
   strength (depth below BB + RSI intensity).
2. **Multi-identifier search** — accepts ticker (`ERG.MI`, `AAPL`), company
   name (`Eni`, `Microsoft`), or ISIN (`IT0001157059`).
3. **Liquidity filter** — blocks unreliable signals on thin-volume names
   (90d avg volume threshold: 300,000).
4. **Indicators** — Wilder RSI(14) + Bollinger(20, 2σ). ATR(14) for R/R sizing.
5. **Confluence signal** — `Price ≤ BB Lower AND RSI ≤ 30`.
6. **Audit report** — on active signal, computes target (BB mid), stop (1.5× ATR),
   and R/R ratio.

## Files

- `app.py` — Streamlit entry point
- `universes.py` — curated ticker lists (Milan/Nasdaq)
- `requirements.txt` — pinned deps

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Cloud

1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io) → New app → point at `app.py`.
3. No secrets required.

## Architecture notes

### Screener performance
- **Batch download**: single `yf.download(tickers=[...], threads=True)` call
  for all 120 names — yfinance parallelizes internally, finishes in ~10-15s.
- **Cache**: `scan_universe` cached 30min, keyed on the ticker tuple +
  universe label. Hit → instant. Miss → one batch call.
- **Refresh button**: calls `scan_universe.clear()` to force a fresh fetch.
- **Empty state**: an empty screener is *not* an error. Confluence is rare
  in healthy markets — expect it to light up only after correction days.

### Why not real-time intraday?
Real-time intraday scanning of 100+ tickers from a Streamlit frontend would:
- Hit yfinance rate limits fast (soft limit ~2000 req/hour per IP)
- Block the UI for 30-60s on cold cache
- Break on mobile due to connection timeouts

If you want true intraday refresh, migrate to the same pattern as your
`edgar-sec`: a GitHub Actions job fetches every N minutes, writes to
`data.json` in the repo, and the app only reads `raw.githubusercontent.com`.

### Indicator precision
- **RSI**: Wilder smoothing (`ewm` with `alpha = 1/period`) — matches
  TradingView/IBKR, not the "SMA-based RSI" used by some retail brokers.
- **Bollinger**: population std (`ddof=0`), per Bollinger's original spec.
- **Signal strength**: `depth_below_band_pct + (30 - rsi)` — equal-weight
  composite. If you want to re-weight, it's in `scan_universe()`.

### Multi-index column handling
`yf.download` returns MultiIndex columns even for single tickers. Flattening
is done defensively in both `fetch_and_analyze` and `scan_universe`.

## Known limitations

- Screener universe is hardcoded (60+60). If you want to expand, edit
  `universes.py` — but keep it under ~200 total or batch fetches slow down.
- `yf.Search` for raw ISINs can be flaky on less-liquid names.
- Liquidity threshold (300k shares) is a blunt instrument — for penny stocks
  or ADR-secondary listings, consider switching to dollar volume.

## Future improvements

- Add insider-buy overlay from `edgar-sec` — "oversold + insider purchase"
  is statistically a stronger setup than technicals alone.
- Migrate screener to GitHub Actions fetcher pattern for sub-5min refresh.
- Per-universe caching keys (currently one cache entry per universe).

