"""
Analizzatore di Mercato Pro — Editorial Edition
================================================
Mobile-first Streamlit app for RSI + Bollinger Bands confluence scanning.

Design direction: financial editorial (FT × Bloomberg × modern mobile).
Typography: Fraunces (display serif) + Geist (sans). Bold accent palette.

Author: Built for Os
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

# =============================================================================
# PAGE CONFIG
# =============================================================================
st.set_page_config(
    page_title="Analizzatore di Mercato Pro",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# =============================================================================
# THEME + TYPOGRAPHY
# =============================================================================
st.markdown(
    """
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,800;1,9..144,500&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">

    <style>
    :root {
        --bg: #0a0e1a;
        --bg-elev: #111827;
        --bg-card: #161f2e;
        --border: #1f2a3d;
        --border-strong: #2d3a52;
        --text: #e8ecf3;
        --text-dim: #94a3b8;
        --text-faint: #64748b;
        --accent: #f4a261;
        --accent-bright: #ffb578;
        --bull: #10b981;
        --bear: #ef4444;
        --info: #60a5fa;
        --gold: #fbbf24;
        --warn: #f59e0b;
    }

    html, body, [class*="css"], .stApp {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'Geist', -apple-system, system-ui, sans-serif !important;
        font-feature-settings: "ss01", "cv11";
    }

    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 820px !important;
    }

    .stApp::before {
        content: "";
        position: fixed; inset: 0;
        background:
          radial-gradient(ellipse 80% 50% at 50% -10%, rgba(244,162,97,0.08), transparent),
          radial-gradient(ellipse 60% 40% at 100% 100%, rgba(96,165,250,0.05), transparent);
        pointer-events: none; z-index: 0;
    }
    .block-container { position: relative; z-index: 1; }

    /* ===== MASTHEAD ===== */
    .masthead {
        border-top: 2px solid var(--accent);
        border-bottom: 1px solid var(--border);
        padding: 1.4rem 0 1.2rem;
        margin-bottom: 1.8rem;
    }
    .masthead-kicker {
        font-family: 'Geist Mono', monospace;
        font-size: 0.72rem; font-weight: 500;
        letter-spacing: 0.18em; text-transform: uppercase;
        color: var(--accent); margin-bottom: 0.6rem;
        display: flex; justify-content: space-between; align-items: center;
    }
    .masthead-kicker .date { color: var(--text-faint); }
    .masthead h1 {
        font-family: 'Fraunces', Georgia, serif !important;
        font-weight: 800; font-size: 2.6rem !important;
        line-height: 1.0; letter-spacing: -0.02em;
        color: var(--text) !important; margin: 0 0 0.3rem 0 !important;
    }
    .masthead h1 em { font-style: italic; font-weight: 500; color: var(--accent); }
    .masthead-sub {
        font-family: 'Fraunces', serif; font-style: italic;
        font-size: 1.0rem; color: var(--text-dim); font-weight: 400;
    }

    /* ===== SECTION HEADERS ===== */
    .section-head {
        display: flex; align-items: baseline; gap: 0.8rem;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid var(--border);
    }
    .section-head .num {
        font-family: 'Geist Mono', monospace;
        font-size: 0.75rem; color: var(--accent);
        font-weight: 600; letter-spacing: 0.1em;
    }
    .section-head .title {
        font-family: 'Fraunces', serif; font-size: 1.5rem;
        font-weight: 600; color: var(--text); letter-spacing: -0.01em;
    }

    /* ===== LEGEND CARDS ===== */
    .legend-intro {
        font-family: 'Fraunces', serif; font-style: italic;
        font-size: 1.05rem; line-height: 1.5;
        color: var(--text-dim);
        padding: 0.4rem 0 1rem 0;
        border-bottom: 1px dashed var(--border);
        margin-bottom: 1.2rem;
    }
    .concept-card {
        background: linear-gradient(180deg, var(--bg-card), var(--bg-elev));
        border: 1px solid var(--border);
        border-left: 3px solid var(--accent);
        border-radius: 10px;
        padding: 1.1rem 1.2rem;
        margin-bottom: 0.9rem;
    }
    .concept-card.bull { border-left-color: var(--bull); }
    .concept-card.bear { border-left-color: var(--bear); }
    .concept-card.info { border-left-color: var(--info); }
    .concept-card .head {
        display: flex; align-items: center; gap: 0.6rem;
        margin-bottom: 0.6rem;
    }
    .concept-card .icon {
        font-size: 1.3rem; width: 36px; height: 36px;
        display: flex; align-items: center; justify-content: center;
        background: rgba(244,162,97,0.1); border-radius: 8px;
    }
    .concept-card.bull .icon { background: rgba(16,185,129,0.12); }
    .concept-card.bear .icon { background: rgba(239,68,68,0.12); }
    .concept-card.info .icon { background: rgba(96,165,250,0.12); }
    .concept-card .label {
        font-family: 'Geist', sans-serif; font-size: 0.72rem;
        font-weight: 600; letter-spacing: 0.12em;
        text-transform: uppercase; color: var(--text-faint);
    }
    .concept-card .term {
        font-family: 'Fraunces', serif; font-size: 1.25rem;
        font-weight: 600; color: var(--text); line-height: 1.2;
    }
    .concept-card .body {
        color: var(--text-dim); font-size: 0.94rem; line-height: 1.55;
    }
    .concept-card .body strong { color: var(--text); font-weight: 600; }
    .concept-card .example {
        margin-top: 0.7rem; padding: 0.6rem 0.8rem;
        background: rgba(0,0,0,0.25); border-radius: 6px;
        font-family: 'Geist Mono', monospace;
        font-size: 0.82rem; color: var(--text-dim);
    }
    .concept-card .example .tag {
        color: var(--accent); font-weight: 600; margin-right: 0.5em;
    }

    /* ===== TICKER BADGE ===== */
    .ticker-card {
        background: linear-gradient(135deg, var(--bg-card), var(--bg-elev));
        border: 1px solid var(--border-strong);
        border-radius: 12px;
        padding: 1.1rem 1.3rem;
        margin: 1rem 0;
        display: flex; justify-content: space-between; align-items: center;
    }
    .ticker-card .name {
        font-family: 'Fraunces', serif; font-size: 1.4rem;
        font-weight: 600; color: var(--text); line-height: 1.1;
    }
    .ticker-card .symbol {
        font-family: 'Geist Mono', monospace; font-size: 0.82rem;
        color: var(--accent); margin-top: 0.25rem; font-weight: 500;
    }
    .ticker-card .resolved {
        font-family: 'Geist Mono', monospace; font-size: 0.7rem;
        color: var(--text-faint); text-transform: uppercase;
        letter-spacing: 0.1em; text-align: right;
    }

    /* ===== METRICS ===== */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.9rem 1rem;
    }
    div[data-testid="stMetricLabel"] {
        font-family: 'Geist Mono', monospace !important;
        font-size: 0.68rem !important; font-weight: 500 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        color: var(--text-faint) !important;
    }
    div[data-testid="stMetricValue"] {
        font-family: 'Fraunces', serif !important;
        font-size: 1.75rem !important; font-weight: 600 !important;
        color: var(--text) !important; letter-spacing: -0.01em;
    }
    div[data-testid="stMetricDelta"] {
        font-family: 'Geist Mono', monospace !important;
        font-size: 0.78rem !important; font-weight: 500 !important;
    }

    /* ===== INPUT ===== */
    div[data-testid="stTextInput"] input {
        background: var(--bg-card) !important;
        border: 1px solid var(--border-strong) !important;
        border-radius: 10px !important;
        color: var(--text) !important;
        font-family: 'Geist Mono', monospace !important;
        font-size: 1rem !important;
        padding: 0.85rem 1rem !important;
    }
    div[data-testid="stTextInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(244,162,97,0.15) !important;
    }
    div[data-testid="stTextInput"] input::placeholder {
        color: var(--text-faint) !important; font-style: italic;
    }

    /* ===== STATUS GRID ===== */
    .status-grid {
        display: grid;
        grid-template-columns: 1fr auto auto;
        gap: 0;
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 10px;
        overflow: hidden;
    }
    .status-grid .row { display: contents; }
    .status-grid .cell {
        padding: 0.85rem 1rem;
        border-bottom: 1px solid var(--border);
        display: flex; align-items: center;
    }
    .status-grid .row:last-child .cell { border-bottom: none; }
    .status-grid .param {
        font-family: 'Geist', sans-serif; color: var(--text-dim);
        font-size: 0.9rem; font-weight: 500;
    }
    .status-grid .value {
        font-family: 'Geist Mono', monospace; color: var(--text);
        font-weight: 600; font-size: 0.92rem;
        justify-content: flex-end; padding-right: 1.2rem;
    }
    .pill {
        display: inline-flex; align-items: center; gap: 0.35rem;
        padding: 0.25rem 0.7rem; border-radius: 999px;
        font-family: 'Geist', sans-serif;
        font-size: 0.78rem; font-weight: 600; border: 1px solid;
    }
    .pill.good { background: rgba(16,185,129,0.1); color: var(--bull); border-color: rgba(16,185,129,0.3); }
    .pill.bad { background: rgba(239,68,68,0.1); color: var(--bear); border-color: rgba(239,68,68,0.3); }
    .pill.warn { background: rgba(245,158,11,0.1); color: var(--warn); border-color: rgba(245,158,11,0.3); }
    .pill.neutral { background: rgba(148,163,184,0.1); color: var(--text-dim); border-color: rgba(148,163,184,0.25); }
    .pill.hot { background: rgba(251,191,36,0.12); color: var(--gold); border-color: rgba(251,191,36,0.35); }

    /* ===== AUDIT REPORT ===== */
    .audit-signal {
        background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.03));
        border: 1px solid rgba(16,185,129,0.3);
        border-left: 4px solid var(--bull);
        border-radius: 12px;
        padding: 1.4rem 1.5rem;
        margin-top: 1rem;
    }
    .audit-signal .stamp {
        font-family: 'Geist Mono', monospace; font-size: 0.72rem;
        letter-spacing: 0.15em; text-transform: uppercase;
        color: var(--bull); font-weight: 600; margin-bottom: 0.4rem;
    }
    .audit-signal h3 {
        font-family: 'Fraunces', serif !important;
        font-size: 1.45rem !important; font-weight: 700;
        color: var(--text) !important; margin: 0 0 0.8rem 0 !important;
        letter-spacing: -0.01em;
    }
    .audit-signal .lede {
        font-family: 'Fraunces', serif; font-style: italic;
        color: var(--text-dim); font-size: 1rem; line-height: 1.55;
        margin-bottom: 1rem;
    }
    .audit-metrics {
        display: grid; grid-template-columns: repeat(2, 1fr);
        gap: 0.8rem; margin: 1rem 0;
    }
    .audit-metrics .m {
        background: rgba(0,0,0,0.25); border-radius: 8px;
        padding: 0.7rem 0.9rem;
    }
    .audit-metrics .m .k {
        font-family: 'Geist Mono', monospace; font-size: 0.68rem;
        text-transform: uppercase; letter-spacing: 0.1em;
        color: var(--text-faint); margin-bottom: 0.2rem;
    }
    .audit-metrics .m .v {
        font-family: 'Fraunces', serif; font-size: 1.2rem;
        font-weight: 600; color: var(--text);
    }
    .audit-metrics .m .v.pos { color: var(--bull); }

    .audit-flat {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 4px solid var(--text-faint);
        border-radius: 12px;
        padding: 1.2rem 1.4rem;
        margin-top: 1rem;
    }
    .audit-flat .stamp {
        font-family: 'Geist Mono', monospace; font-size: 0.72rem;
        letter-spacing: 0.15em; text-transform: uppercase;
        color: var(--text-faint); font-weight: 600; margin-bottom: 0.4rem;
    }
    .audit-flat h3 {
        font-family: 'Fraunces', serif !important;
        font-size: 1.3rem !important; color: var(--text) !important;
        margin: 0 0 0.6rem 0 !important;
    }
    .audit-flat .why {
        font-family: 'Geist Mono', monospace; font-size: 0.88rem;
        color: var(--text-dim); line-height: 1.8;
    }

    div[data-testid="stAlert"][kind="warning"] {
        background: rgba(245,158,11,0.08) !important;
        border: 1px solid rgba(245,158,11,0.3) !important;
        border-left: 4px solid var(--warn) !important;
        border-radius: 10px !important;
    }
    div[data-testid="stAlert"][kind="info"] {
        background: rgba(96,165,250,0.06) !important;
        border: 1px solid rgba(96,165,250,0.25) !important;
        border-radius: 10px !important;
    }

    div[data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: 10px !important;
    }
    div[data-testid="stExpander"] summary {
        font-family: 'Fraunces', serif !important;
        font-size: 1.05rem !important; font-weight: 600 !important;
        color: var(--text) !important;
        padding: 0.9rem 1.1rem !important;
    }

    .footer {
        margin-top: 2.5rem;
        padding-top: 1rem;
        border-top: 1px solid var(--border);
        font-family: 'Geist Mono', monospace;
        font-size: 0.72rem; color: var(--text-faint);
        text-align: center; letter-spacing: 0.05em;
    }

    #MainMenu, footer, header { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =============================================================================
# 1. INPUT RESOLUTION
# =============================================================================
ISIN_RE = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def looks_like_isin(s: str) -> bool:
    return bool(ISIN_RE.match(s.strip().upper()))


def looks_like_ticker(s: str) -> bool:
    s = s.strip().upper()
    if " " in s or len(s) > 15:
        return False
    return bool(re.match(r"^[A-Z0-9]{1,6}(\.[A-Z]{1,3})?$", s))


@st.cache_data(ttl=3600, show_spinner=False)
def resolve_identifier(raw: str) -> Optional[dict]:
    query = raw.strip()
    if not query:
        return None

    if looks_like_ticker(query):
        try:
            t = yf.Ticker(query.upper())
            info = t.fast_info
            if info and getattr(info, "last_price", None) is not None:
                name = query.upper()
                try:
                    name = t.info.get("shortName") or t.info.get("longName") or query.upper()
                except Exception:
                    pass
                return {
                    "ticker": query.upper(), "name": name,
                    "exchange": getattr(info, "exchange", "N/A"),
                    "resolved_from": "ticker",
                }
        except Exception:
            pass

    try:
        search = yf.Search(query, max_results=5)
        quotes = search.quotes or []
        if not quotes:
            return None
        equities = [q for q in quotes if q.get("quoteType") == "EQUITY"]
        pick = equities[0] if equities else quotes[0]
        return {
            "ticker": pick.get("symbol"),
            "name": pick.get("longname") or pick.get("shortname") or pick.get("symbol"),
            "exchange": pick.get("exchange", "N/A"),
            "resolved_from": "isin" if looks_like_isin(query) else "name",
        }
    except Exception:
        return None


# =============================================================================
# 2. INDICATORS
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
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def compute_bollinger(close: pd.Series, period: int = 20, n_std: float = 2.0):
    middle = close.rolling(period).mean()
    std = close.rolling(period).std(ddof=0)
    return middle - n_std * std, middle, middle + n_std * std


def compute_atr_pct(df: pd.DataFrame, period: int = 14) -> float:
    high, low, close = df["High"], df["Low"], df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().iloc[-1]
    return float(atr / close.iloc[-1] * 100)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_and_analyze(ticker: str, name: str) -> Optional[AnalysisResult]:
    try:
        df = yf.download(ticker, period="1y", interval="1d",
                         auto_adjust=False, progress=False, threads=False)
    except Exception:
        return None

    if df is None or df.empty:
        return None

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna(subset=["Close"]).copy()
    if len(df) < 30:
        return None

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

    return AnalysisResult(
        ticker=ticker, name=name, df=df,
        avg_volume_90d=avg_vol_90,
        is_liquid=avg_vol_90 > 300_000,
        current_price=current_price,
        current_rsi=current_rsi,
        lower_band=lower_b, upper_band=upper_b, middle_band=middle_b,
        distance_from_lower_pct=distance_pct,
        atr_pct=compute_atr_pct(df),
        confluence_signal=(current_price <= lower_b) and (current_rsi <= 30),
    )


# =============================================================================
# 3. CHART
# =============================================================================
def build_chart(r: AnalysisResult) -> go.Figure:
    df = r.df.tail(180).copy()

    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.72, 0.28],
        subplot_titles=("<b>Prezzo & Bande di Bollinger</b>", "<b>RSI (14)</b>"),
    )

    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_Upper"],
        line=dict(color="rgba(244,162,97,0.55)", width=1.2),
        name="BB Upper", hovertemplate="BB Upper: %{y:.2f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_Lower"],
        line=dict(color="rgba(244,162,97,0.55)", width=1.2),
        fill="tonexty", fillcolor="rgba(244,162,97,0.09)",
        name="BB Lower", hovertemplate="BB Lower: %{y:.2f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=df["BB_Middle"],
        line=dict(color="rgba(148,163,184,0.5)", width=1, dash="dot"),
        name="SMA 20", hovertemplate="SMA 20: %{y:.2f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color="#10b981", decreasing_line_color="#ef4444",
        increasing_fillcolor="#10b981", decreasing_fillcolor="#ef4444",
        name="Prezzo", showlegend=False,
    ), row=1, col=1)

    last_idx = df.index[-1]
    fig.add_trace(go.Scatter(
        x=[last_idx], y=[r.current_price], mode="markers",
        marker=dict(size=14, color="#fbbf24", symbol="diamond",
                    line=dict(color="#0a0e1a", width=2)),
        name="Ora", showlegend=False,
        hovertemplate=f"<b>Ora</b>: {r.current_price:.2f}<extra></extra>",
    ), row=1, col=1)

    # RSI
    rsi = df["RSI"]
    fig.add_hrect(y0=0, y1=30, fillcolor="rgba(16,185,129,0.15)",
                  line_width=0, row=2, col=1)
    fig.add_hrect(y0=70, y1=100, fillcolor="rgba(239,68,68,0.15)",
                  line_width=0, row=2, col=1)

    fig.add_trace(go.Scatter(
        x=df.index, y=rsi,
        line=dict(color="#e8ecf3", width=2),
        name="RSI", showlegend=False,
        hovertemplate="RSI: %{y:.1f}<extra></extra>",
    ), row=2, col=1)

    fig.add_hline(y=30, line=dict(color="#10b981", width=1, dash="dash"), row=2, col=1)
    fig.add_hline(y=70, line=dict(color="#ef4444", width=1, dash="dash"), row=2, col=1)
    fig.add_hline(y=50, line=dict(color="rgba(148,163,184,0.3)", width=0.8, dash="dot"),
                  row=2, col=1)

    fig.add_trace(go.Scatter(
        x=[last_idx], y=[r.current_rsi], mode="markers",
        marker=dict(size=11, color="#fbbf24", symbol="diamond",
                    line=dict(color="#0a0e1a", width=2)),
        showlegend=False,
        hovertemplate=f"<b>RSI ora</b>: {r.current_rsi:.1f}<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        height=640,
        margin=dict(l=10, r=10, t=50, b=20),
        xaxis_rangeslider_visible=False,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(22,31,46,0.5)",
        hovermode="x unified",
        font=dict(family="Geist, sans-serif", size=11, color="#e8ecf3"),
        hoverlabel=dict(bgcolor="#161f2e", bordercolor="#2d3a52",
                        font=dict(family="Geist Mono, monospace", size=11)),
    )

    for ann in fig["layout"]["annotations"]:
        ann["font"] = dict(family="Fraunces, serif", size=13, color="#e8ecf3")
        ann["x"] = 0.01
        ann["xanchor"] = "left"

    fig.update_xaxes(gridcolor="rgba(47,58,82,0.4)", showgrid=True,
                     zeroline=False, rangeslider_visible=False)
    fig.update_yaxes(gridcolor="rgba(47,58,82,0.4)", showgrid=True, zeroline=False)
    fig.update_yaxes(title_text="", row=1, col=1)
    fig.update_yaxes(title_text="", range=[0, 100], row=2, col=1,
                     tickvals=[0, 30, 50, 70, 100])

    return fig


# =============================================================================
# 4. UI
# =============================================================================
today = datetime.now().strftime("%d %B %Y").upper()
st.markdown(
    f"""
    <div class="masthead">
        <div class="masthead-kicker">
            <span>№ 01 · Edizione Digitale</span>
            <span class="date">{today}</span>
        </div>
        <h1>Analizzatore <em>di Mercato</em></h1>
        <div class="masthead-sub">RSI + Bande di Bollinger · Segnali di confluenza su dati giornalieri</div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.expander("📖  Come funziona — guida per chi parte da zero", expanded=False):
    st.markdown(
        """
        <div class="legend-intro">
            Questa app cerca un momento preciso nel mercato: quando un titolo
            è stato venduto così tanto, così in fretta, che probabilmente è
            andato <em>oltre il giusto</em>. Ecco i due strumenti che usa.
        </div>

        <div class="concept-card">
            <div class="head">
                <div class="icon">📏</div>
                <div>
                    <div class="label">Strumento № 1</div>
                    <div class="term">Bande di Bollinger</div>
                </div>
            </div>
            <div class="body">
                Immagina un <strong>corridoio elastico</strong> costruito attorno al prezzo.
                Al centro c'è la media degli ultimi 20 giorni. Sopra e sotto, due
                "pareti" che si allargano quando il mercato è agitato e si stringono
                quando è calmo.<br><br>
                <strong>Regola d'oro:</strong> il prezzo passa circa il 95% del tempo
                dentro questo corridoio. Quando lo sfonda, sta facendo qualcosa
                di statisticamente raro — ed è lì che l'app si accende.
            </div>
            <div class="example">
                <span class="tag">ES.</span>Il prezzo tocca la banda inferiore → "è sceso troppo, troppo in fretta"
            </div>
        </div>

        <div class="concept-card info">
            <div class="head">
                <div class="icon">⚡</div>
                <div>
                    <div class="label">Strumento № 2</div>
                    <div class="term">RSI · Relative Strength Index</div>
                </div>
            </div>
            <div class="body">
                Un <strong>termometro delle emozioni</strong> del mercato,
                da 0 a 100. Misura quanto frenetico è stato il movimento degli
                ultimi 14 giorni.<br><br>
                <strong>Sotto 30</strong> = ipervenduto. Il titolo è stato massacrato,
                tutti scappano. <strong>Sopra 70</strong> = ipercomprato. Euforia,
                tutti comprano. Entrambi gli estremi raramente durano a lungo.
            </div>
            <div class="example">
                <span class="tag">ES.</span>RSI = 28 → "panico diffuso, le mani deboli hanno già venduto"
            </div>
        </div>

        <div class="concept-card bull">
            <div class="head">
                <div class="icon">🎯</div>
                <div>
                    <div class="label">Il segnale che cerchiamo</div>
                    <div class="term">Zona di Confluenza</div>
                </div>
            </div>
            <div class="body">
                Quando <strong>entrambe le condizioni</strong> si verificano insieme:
                prezzo sotto la banda inferiore <em>e</em> RSI sotto 30. Due segnali
                indipendenti che puntano nella stessa direzione — "forse è sceso
                abbastanza". Si chiama <strong>setup di mean-reversion</strong>:
                la scommessa è che il prezzo torni almeno verso la media.
            </div>
            <div class="example">
                <span class="tag">⚠</span>Non è una garanzia. È una <strong>probabilità inclinata</strong>.
            </div>
        </div>

        <div class="concept-card bear">
            <div class="head">
                <div class="icon">🧂</div>
                <div>
                    <div class="label">Il grano di sale</div>
                    <div class="term">Quando il segnale fallisce</div>
                </div>
            </div>
            <div class="body">
                In un <strong>bear market serio</strong> o su titoli con problemi
                fondamentali (frode, bancarotta in arrivo, settore in crisi),
                RSI e Bollinger possono restare "ipervenduti" per settimane
                mentre il prezzo continua a scendere.<br><br>
                Gli indicatori tecnici non leggono i bilanci. Sono un pezzo
                del puzzle, non la soluzione.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("⚠️  Strumento didattico. Non costituisce consulenza finanziaria né raccomandazione d'investimento.")

# ---- Input ----
st.markdown(
    '<div class="section-head"><span class="num">01</span>'
    '<span class="title">Cerca un Titolo</span></div>',
    unsafe_allow_html=True,
)
query = st.text_input(
    "Ticker, Nome o ISIN",
    placeholder="ERG.MI  ·  Microsoft  ·  IT0001157059",
    label_visibility="collapsed",
)

if not query:
    st.info("💡  Puoi inserire un **ticker** (es. `AAPL`, `ERG.MI`), "
            "un **nome** (es. `Microsoft`, `Eni`) o un **codice ISIN**.")
    st.stop()

with st.spinner("Risoluzione identificatore…"):
    resolved = resolve_identifier(query)

if not resolved or not resolved.get("ticker"):
    st.error(f"❌  Nessun titolo trovato per **{query}**. Prova con il ticker diretto.")
    st.stop()

ticker = resolved["ticker"]
name = resolved["name"]

st.markdown(
    f"""
    <div class="ticker-card">
        <div>
            <div class="name">{name}</div>
            <div class="symbol">{ticker}  ·  {resolved.get('exchange', 'N/A')}</div>
        </div>
        <div class="resolved">Risolto da<br><strong style="color:var(--accent);">{resolved['resolved_from']}</strong></div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.spinner("Calcolo indicatori…"):
    r = fetch_and_analyze(ticker, name)

if r is None:
    st.error("Dati insufficienti (servono almeno 30 barre giornaliere).")
    st.stop()

if not r.is_liquid:
    st.warning(
        f"⚠️  **Titolo poco liquido.** Volume medio 90gg: "
        f"**{r.avg_volume_90d:,.0f}** (soglia minima: 300.000). "
        "I segnali tecnici su titoli illiquidi sono spesso distorti da pochi "
        "grandi ordini. Procedi con cautela."
    )

# ---- Metrics ----
st.markdown(
    '<div class="section-head"><span class="num">02</span>'
    '<span class="title">Indicatori Live</span></div>',
    unsafe_allow_html=True,
)

prev_close = float(r.df["Close"].iloc[-2])
delta_pct = (r.current_price - prev_close) / prev_close * 100

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Prezzo", f"{r.current_price:,.2f}", f"{delta_pct:+.2f}%")
with m2:
    rsi_label = "Ipervenduto" if r.current_rsi <= 30 else (
        "Ipercomprato" if r.current_rsi >= 70 else "Neutro"
    )
    st.metric("RSI (14)", f"{r.current_rsi:.1f}", rsi_label)
with m3:
    st.metric(
        "Dist. BB Lower",
        f"{r.distance_from_lower_pct:+.2f}%",
        "Sotto banda" if r.distance_from_lower_pct < 0 else "Sopra banda",
        delta_color="inverse",
    )

# ---- Chart ----
st.markdown(
    '<div class="section-head"><span class="num">03</span>'
    '<span class="title">Grafico Tecnico</span></div>',
    unsafe_allow_html=True,
)
st.plotly_chart(build_chart(r), use_container_width=True, config={"displayModeBar": False})

# ---- Status ----
st.markdown(
    '<div class="section-head"><span class="num">04</span>'
    '<span class="title">Stato Operativo</span></div>',
    unsafe_allow_html=True,
)

vol_pill = '<span class="pill good">Liquido</span>' if r.is_liquid \
    else '<span class="pill warn">Illiquido</span>'

if r.current_rsi <= 30:
    rsi_pill = '<span class="pill hot">🔥 Ipervenduto</span>'
elif r.current_rsi >= 70:
    rsi_pill = '<span class="pill bad">Ipercomprato</span>'
else:
    rsi_pill = '<span class="pill neutral">Neutro</span>'

if r.current_price <= r.lower_band:
    bb_pill = '<span class="pill warn">⚠ Sotto Banda</span>'
elif r.current_price >= r.upper_band:
    bb_pill = '<span class="pill bad">Sopra Banda</span>'
else:
    bb_pill = '<span class="pill neutral">Nel Canale</span>'

st.markdown(
    f"""
    <div class="status-grid">
        <div class="row">
            <div class="cell param">Volumi 90 giorni</div>
            <div class="cell value">{r.avg_volume_90d/1000:,.0f}k</div>
            <div class="cell">{vol_pill}</div>
        </div>
        <div class="row">
            <div class="cell param">RSI (14)</div>
            <div class="cell value">{r.current_rsi:.1f}</div>
            <div class="cell">{rsi_pill}</div>
        </div>
        <div class="row">
            <div class="cell param">Prezzo vs Bollinger</div>
            <div class="cell value">{r.current_price:.2f}</div>
            <div class="cell">{bb_pill}</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- Audit ----
st.markdown(
    '<div class="section-head"><span class="num">05</span>'
    '<span class="title">Audit Report</span></div>',
    unsafe_allow_html=True,
)

if r.confluence_signal and r.is_liquid:
    target = r.middle_band
    upside_pct = (target - r.current_price) / r.current_price * 100
    stop_pct = 1.5 * r.atr_pct
    rr = upside_pct / stop_pct if stop_pct > 0 else 0
    rr_verdict = "favorevole" if rr >= 1.5 else "marginale"

    st.markdown(
        f"""
        <div class="audit-signal">
            <div class="stamp">✓ Segnale Attivo</div>
            <h3>Zona di Confluenza Rilevata</h3>
            <div class="lede">
                {r.name} è sceso sotto la banda inferiore con RSI in ipervenduto.
                Doppio segnale di compressione tecnica — candidato statistico
                per un rimbalzo verso la media.
            </div>
            <div class="audit-metrics">
                <div class="m">
                    <div class="k">Target (BB Mid)</div>
                    <div class="v">{target:.2f}</div>
                </div>
                <div class="m">
                    <div class="k">Upside teorico</div>
                    <div class="v pos">+{upside_pct:.2f}%</div>
                </div>
                <div class="m">
                    <div class="k">Stop (1.5× ATR)</div>
                    <div class="v">−{stop_pct:.2f}%</div>
                </div>
                <div class="m">
                    <div class="k">Rapporto R/R</div>
                    <div class="v">{rr:.2f}<span style="font-size:0.7rem; color: var(--text-faint); margin-left:0.4rem;">({rr_verdict})</span></div>
                </div>
            </div>
            <div style="font-family: 'Fraunces', serif; font-style: italic; color: var(--text-dim); font-size: 0.92rem; margin-top: 0.8rem; line-height: 1.5;">
                Volatilità attuale (ATR): {r.atr_pct:.2f}%. Il segnale indica
                compressione, non una garanzia di rimbalzo. Verifica sempre
                il contesto fondamentale prima di operare.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif r.confluence_signal and not r.is_liquid:
    st.markdown(
        """
        <div class="audit-flat" style="border-left-color: var(--warn);">
            <div class="stamp" style="color: var(--warn);">⚠ Segnale Scartato</div>
            <h3>Confluenza presente ma titolo illiquido</h3>
            <div class="why">L'affidabilità statistica di RSI e Bollinger
            è compromessa sui titoli a basso volume. Segnale ignorato.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:
    reasons = []
    if r.current_price > r.lower_band:
        reasons.append(
            f"prezzo <code style='color:var(--accent);'>{r.current_price:.2f}</code> "
            f"sopra BB Lower <code style='color:var(--accent);'>{r.lower_band:.2f}</code>"
        )
    if r.current_rsi > 30:
        reasons.append(
            f"RSI <code style='color:var(--accent);'>{r.current_rsi:.1f}</code> sopra 30"
        )
    reasons_html = "<br>• ".join(reasons)

    st.markdown(
        f"""
        <div class="audit-flat">
            <div class="stamp">— Nessun Segnale</div>
            <h3>Condizioni non soddisfatte</h3>
            <div class="why">• {reasons_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown(
    f"""
    <div class="footer">
        Dati: {r.df.index[-1].strftime('%Y-%m-%d')}  ·  
        Analisi: {datetime.now().strftime('%Y-%m-%d %H:%M')}  ·  
        Fonte: Yahoo Finance via yfinance
    </div>
    """,
    unsafe_allow_html=True,
)
