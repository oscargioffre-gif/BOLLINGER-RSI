"""
Analizzatore di Mercato Pro
===========================
Mobile-responsive Streamlit app for technical analysis (RSI + Bollinger Bands)
with multi-identifier search (Ticker / Name / ISIN), liquidity filtering,
and an automated audit report on confluence signals.

Author: Built for Os
Deploy: Streamlit Cloud compatible
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

# -----------------------------------------------------------------------------
# PAGE CONFIG (must be first Streamlit call)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Analizzatore di Mercato Pro",
    page_icon="📱",
    layout="centered",  # mobile-first
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# STYLING — minimal, mobile-friendly
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 780px; }
    .legend-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border-left: 3px solid #3b82f6;
        padding: 12px 16px; border-radius: 8px; margin-bottom: 0.8rem;
        font-size: 0.88rem; line-height: 1.55;
    }
    .legend-box .row { margin: 4px 0; }
    .audit-title { font-size: 1.05rem; font-weight: 600; margin-top: 1.2rem; }
    div[data-testid="stMetricValue"] { font-size: 1.3rem; }
    div[data-testid="stMetricLabel"] { font-size: 0.78rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 1. INPUT RESOLUTION — Multi-Identifier Search
# =============================================================================

ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def looks_like_isin(s: str) -> bool:
    return bool(ISIN_RE.match(s.strip().upper()))


def looks_like_ticker(s: str) -> bool:
    """Heuristic: a ticker is short, uppercase, may contain a dot suffix (e.g. ERG.MI)."""
    s = s.strip().upper()
    if " " in s:
        return False
    if len(s) > 15:
        return False
    return bool(re.match(r"^[A-Z0-9]{1,6}(\.[A-Z]{1,3})?$", s))


@st.cache_data(ttl=3600, show_spinner=False)
def resolve_identifier(raw: str) -> Optional[dict]:
    """
    Resolve a user query (ticker, company name, or ISIN) to a yfinance ticker.
    Uses yfinance's built-in Search API (replaces the deprecated Lookup).
    Returns {'ticker', 'name', 'exchange', 'resolved_from'} or None.
    """
    query = raw.strip()
    if not query:
        return None

    # Fast path: already a valid yfinance ticker
    if looks_like_ticker(query):
        try:
            t = yf.Ticker(query.upper())
            info = t.fast_info
            # fast_info will raise or return empty for bad tickers
            if info and getattr(info, "last_price", None) is not None:
                name = query.upper()
                try:
                    name = t.info.get("shortName") or t.info.get("longName") or query.upper()
                except Exception:
                    pass
                return {
                    "ticker": query.upper(),
                    "name": name,
                    "exchange": getattr(info, "exchange", "N/A"),
                    "resolved_from": "ticker",
                }
        except Exception:
            pass  # fall through to search

    # Search path: name or ISIN
    try:
        search = yf.Search(query, max_results=5)
        quotes = search.quotes or []
        if not quotes:
            return None

        # Prefer equities over ETFs/currencies when possible
        equities = [q for q in quotes if q.get("quoteType") == "EQUITY"]
        pick = equities[0] if equities else quotes[0]

        return {
            "ticker": pick.get("symbol"),
            "name": pick.get("longname") or pick.get("shortname") or pick.get("symbol"),
            "exchange": pick.get("exchange", "N/A"),
            "resolved_from": "isin" if looks_like_isin(query) else "name",
        }
    except Exception as e:
        st.caption(f"🔎 Ricerca fallita: {e}")
        return None


# =============================================================================
# 2. DATA FETCH + INDICATORS
# =============================================================================

@dataclass
class AnalysisResult:
    ticker: str
    name: str
    df: pd.DataFrame
    avg_volume_90d: float
    is_liquid: bool
    current_price: float
    current_rsi: float
    lower_band: float
    upper_band: float
    middle_band: float
    distance_from_lower_pct: float
    atr_pct: float
    confluence_signal: bool


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """Wilder's RSI — the canonical formulation."""
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    # Wilder smoothing == EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_bollinger(close: pd.Series, period: int = 20, n_std: float = 2.0):
    middle = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    upper = middle + n_std * std
    lower = middle - n_std * std
    return lower, middle, upper


def compute_atr_pct(df: pd.DataFrame, period: int = 14) -> float:
    """ATR as % of last close — used for risk/reward sizing in the audit report."""
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().iloc[-1]
    return float(atr / close.iloc[-1] * 100)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_and_analyze(ticker: str, name: str) -> Optional[AnalysisResult]:
    """Fetch ~1 year of daily bars and compute all indicators."""
    try:
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
    except Exception as e:
        st.error(f"Errore nel download dati: {e}")
        return None

    if df is None or df.empty:
        return None

    # yfinance sometimes returns multi-index columns for single tickers
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(subset=["Close"]).copy()
    if len(df) < 30:
        return None

    # Indicators
    df["RSI"] = compute_rsi(df["Close"], 14)
    lower, middle, upper = compute_bollinger(df["Close"], 20, 2.0)
    df["BB_Lower"], df["BB_Middle"], df["BB_Upper"] = lower, middle, upper

    last = df.iloc[-1]
    avg_vol_90 = float(df["Volume"].tail(90).mean())
    current_price = float(last["Close"])
    current_rsi = float(last["RSI"])
    lower_b = float(last["BB_Lower"])
    upper_b = float(last["BB_Upper"])
    middle_b = float(last["BB_Middle"])
    distance_pct = (current_price - lower_b) / lower_b * 100

    confluence = (current_price <= lower_b) and (current_rsi <= 30)

    return AnalysisResult(
        ticker=ticker,
        name=name,
        df=df,
        avg_volume_90d=avg_vol_90,
        is_liquid=avg_vol_90 > 300_000,
        current_price=current_price,
        current_rsi=current_rsi,
        lower_band=lower_b,
        upper_band=upper_b,
        middle_band=middle_b,
        distance_from_lower_pct=distance_pct,
        atr_pct=compute_atr_pct(df),
        confluence_signal=confluence,
    )


# =============================================================================
# 3. CHARTING
# =============================================================================

def build_chart(r: AnalysisResult) -> go.Figure:
    df = r.df.tail(180).copy()  # last ~6 months for mobile readability

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.06,
        row_heights=[0.7, 0.3],
        subplot_titles=("Prezzo + Bande di Bollinger", "RSI (14)"),
    )

    # --- Top: Candlestick ---
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            name="Prezzo",
            increasing_line_color="#10b981",
            decreasing_line_color="#ef4444",
            showlegend=False,
        ),
        row=1, col=1,
    )

    # Bollinger fill (20% opacity band)
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["BB_Upper"],
            line=dict(color="rgba(59,130,246,0.5)", width=1),
            name="BB Upper", showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["BB_Lower"],
            line=dict(color="rgba(59,130,246,0.5)", width=1),
            fill="tonexty",
            fillcolor="rgba(59,130,246,0.20)",
            name="BB Lower", showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index, y=df["BB_Middle"],
            line=dict(color="rgba(148,163,184,0.7)", width=1, dash="dot"),
            name="BB Mid (SMA20)", showlegend=False,
        ),
        row=1, col=1,
    )

    # Marker on current low
    last_idx = df.index[-1]
    fig.add_trace(
        go.Scatter(
            x=[last_idx], y=[df["Low"].iloc[-1]],
            mode="markers+text",
            marker=dict(size=12, color="#fbbf24", symbol="triangle-up",
                        line=dict(color="#000", width=1)),
            text=[f"  {r.current_price:.2f}"],
            textposition="middle right",
            textfont=dict(size=11, color="#fbbf24"),
            showlegend=False,
            hovertemplate="Minimo attuale: %{y:.2f}<extra></extra>",
        ),
        row=1, col=1,
    )

    # --- Bottom: RSI with colored zones ---
    rsi = df["RSI"]
    fig.add_trace(
        go.Scatter(
            x=df.index, y=rsi,
            line=dict(color="#e2e8f0", width=1.8),
            name="RSI", showlegend=False,
            hovertemplate="RSI: %{y:.1f}<extra></extra>",
        ),
        row=2, col=1,
    )

    # Oversold zone (green) — fills 0..30
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16,185,129,0.18)",
                  line_width=0, row=2, col=1)
    # Overbought zone (red) — fills 70..100
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.18)",
                  line_width=0, row=2, col=1)

    fig.add_hline(y=30, line=dict(color="#10b981", width=1, dash="dash"),
                  row=2, col=1)
    fig.add_hline(y=70, line=dict(color="#ef4444", width=1, dash="dash"),
                  row=2, col=1)

    fig.update_layout(
        height=620,
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.6)",
        hovermode="x unified",
        font=dict(size=11),
    )
    fig.update_yaxes(title_text="Prezzo", row=1, col=1)
    fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
    fig.update_xaxes(rangeslider_visible=False)

    return fig


# =============================================================================
# 4. UI — HEADER, LEGEND, INPUT
# =============================================================================

st.markdown("## 📱 Analizzatore di Mercato Pro")
st.caption("RSI + Bollinger Bands • Daily • Confluence Scanner")

with st.expander("📖 Legenda Semplice (come leggere i risultati)", expanded=False):
    st.markdown(
        """
        <div class="legend-box">
        <div class="row">🔵 <b>Prezzo Blu</b>: il valore attuale del titolo.</div>
        <div class="row">📉 <b>Banda Inferiore</b>: il "pavimento" statistico del prezzo.
          Se il prezzo la tocca, è sceso molto rispetto alla media recente.</div>
        <div class="row">⚡ <b>RSI a 30</b>: tutti stanno vendendo freneticamente (ipervenduto).</div>
        <div class="row">✅ <b>Segnale OK</b>: box verde = titolo "schiacciato",
          possibile candidato per un rimbalzo tecnico.</div>
        <div class="row" style="color:#fbbf24; margin-top:8px;">
          ⚠️ Strumento didattico. Non è una raccomandazione d'investimento.
        </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("### 🔍 Cerca Titolo")
query = st.text_input(
    label="Ticker, Nome o ISIN",
    placeholder="Es. ERG.MI, Microsoft, IT0001157059…",
    label_visibility="collapsed",
)

if not query:
    st.info("Inserisci un ticker (es. `AAPL`, `ERG.MI`), un nome (es. `Microsoft`) o un ISIN.")
    st.stop()

# -----------------------------------------------------------------------------
# RESOLVE
# -----------------------------------------------------------------------------
with st.spinner("Risoluzione identificatore…"):
    resolved = resolve_identifier(query)

if not resolved or not resolved.get("ticker"):
    st.error(f"❌ Nessun titolo trovato per **{query}**. Prova con il ticker diretto.")
    st.stop()

ticker = resolved["ticker"]
name = resolved["name"]

col_a, col_b = st.columns([3, 2])
with col_a:
    st.markdown(f"**{name}**")
    st.caption(f"`{ticker}` • {resolved.get('exchange', 'N/A')}")
with col_b:
    st.caption(f"Risolto da: *{resolved['resolved_from']}*")

# -----------------------------------------------------------------------------
# FETCH + ANALYZE
# -----------------------------------------------------------------------------
with st.spinner("Calcolo indicatori…"):
    r = fetch_and_analyze(ticker, name)

if r is None:
    st.error("Dati insufficienti per l'analisi (servono almeno 30 barre giornaliere).")
    st.stop()

# =============================================================================
# 5. LIQUIDITY CHECK
# =============================================================================
if not r.is_liquid:
    st.warning(
        f"⚠️ **Titolo poco liquido.** Volume medio 90gg: "
        f"**{r.avg_volume_90d:,.0f}** (soglia: 300.000).  \n"
        "I segnali RSI / Bollinger su titoli illiquidi sono spesso inaffidabili "
        "perché pochi scambi distorcono la price action. Procedi con cautela."
    )

# =============================================================================
# 6. METRICS
# =============================================================================
st.markdown("### 📊 Indicatori Live")
m1, m2, m3 = st.columns(3)

with m1:
    # Use latest delta vs previous close as sanity signal
    prev_close = float(r.df["Close"].iloc[-2])
    delta_pct = (r.current_price - prev_close) / prev_close * 100
    st.metric("Prezzo", f"{r.current_price:,.2f}", f"{delta_pct:+.2f}%")

with m2:
    rsi_label = "🔥 Ipervenduto" if r.current_rsi <= 30 else (
        "🥵 Ipercomprato" if r.current_rsi >= 70 else "Neutro"
    )
    st.metric("RSI (14)", f"{r.current_rsi:.1f}", rsi_label)

with m3:
    st.metric(
        "Dist. da BB Lower",
        f"{r.distance_from_lower_pct:+.2f}%",
        "Sotto banda" if r.distance_from_lower_pct < 0 else "Sopra banda",
        delta_color="inverse",
    )

# =============================================================================
# 7. CHART
# =============================================================================
st.markdown("### 📈 Grafico Tecnico")
st.plotly_chart(build_chart(r), use_container_width=True, config={"displayModeBar": False})

# =============================================================================
# 8. STATO OPERATIVO — summary table
# =============================================================================
st.markdown("### 📋 Stato Operativo")

vol_status = "✅ Liquido" if r.is_liquid else "⚠️ Illiquido"
rsi_status = "🔥 Ipervenduto" if r.current_rsi <= 30 else (
    "🥵 Ipercomprato" if r.current_rsi >= 70 else "➖ Neutro"
)
bb_status = "⚠️ Sotto Banda" if r.current_price <= r.lower_band else (
    "🚨 Sopra Banda Sup." if r.current_price >= r.upper_band else "➖ Nel Canale"
)

status_df = pd.DataFrame({
    "Parametro": ["Volumi 90d", "RSI", "Prezzo vs BB"],
    "Valore": [
        f"{r.avg_volume_90d/1000:,.0f}k",
        f"{r.current_rsi:.1f}",
        "Sotto Banda" if r.current_price <= r.lower_band else (
            "Sopra Banda" if r.current_price >= r.upper_band else "Nel Canale"
        ),
    ],
    "Stato": [vol_status, rsi_status, bb_status],
})
st.dataframe(status_df, hide_index=True, use_container_width=True)

# =============================================================================
# 9. AUDIT REPORT
# =============================================================================
st.markdown('<div class="audit-title">🧾 Audit Report Automatico</div>', unsafe_allow_html=True)

if r.confluence_signal and r.is_liquid:
    # Risk/reward framing using ATR and distance to middle band (mean-reversion target)
    target_price = r.middle_band
    upside_pct = (target_price - r.current_price) / r.current_price * 100
    # Suggested stop: 1.5 ATR below current
    stop_distance_pct = 1.5 * r.atr_pct
    rr_ratio = upside_pct / stop_distance_pct if stop_distance_pct > 0 else 0

    st.success(
        f"""
        ### ✅ Segnale di Confluenza ATTIVO

        **{r.name}** (`{r.ticker}`) si trova in zona di potenziale reversal:
        - Prezzo `{r.current_price:.2f}` ≤ BB Lower `{r.lower_band:.2f}`
        - RSI `{r.current_rsi:.1f}` ≤ 30 (ipervenduto)

        **Analisi Rischio/Rendimento** (mean-reversion verso SMA20):
        - 🎯 Target tecnico (BB Mid): **{target_price:.2f}** → upside **{upside_pct:+.2f}%**
        - 🛑 Stop suggerito (1.5× ATR): distanza **{stop_distance_pct:.2f}%**
        - ⚖️ R/R ratio: **{rr_ratio:.2f}** {'(favorevole)' if rr_ratio >= 1.5 else '(marginale)'}
        - 📊 Volatilità attuale (ATR%): **{r.atr_pct:.2f}%**

        *Il segnale indica una compressione tecnica, non una garanzia di rimbalzo.
        Verifica il contesto fondamentale prima di agire.*
        """
    )
elif r.confluence_signal and not r.is_liquid:
    st.warning(
        "Segnale di confluenza presente **ma titolo illiquido** — l'affidabilità "
        "statistica degli indicatori è compromessa. Segnale scartato."
    )
else:
    reasons = []
    if r.current_price > r.lower_band:
        reasons.append(f"prezzo `{r.current_price:.2f}` sopra BB Lower `{r.lower_band:.2f}`")
    if r.current_rsi > 30:
        reasons.append(f"RSI `{r.current_rsi:.1f}` > 30")
    st.info(
        "❌ **Nessun segnale di confluenza.** Condizioni non soddisfatte: "
        + "; ".join(reasons) + "."
    )

st.caption(
    f"Ultimo aggiornamento dati: {r.df.index[-1].strftime('%Y-%m-%d')} • "
    f"Analisi generata: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
