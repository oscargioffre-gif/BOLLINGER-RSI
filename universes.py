"""
Curated ticker universes for the screener.

Design decisions:
- Kept small (~60 per market) to guarantee batch fetches finish in <15s on
  Streamlit Cloud free tier and stay within yfinance soft rate limits.
- Milan: FTSE MIB (40) + FTSE Mid Cap selected (20 liquid ones)
- Nasdaq: Nasdaq-100 subset (the ~60 most actively traded by ADV)
- Tickers use yfinance conventions: Milan → .MI suffix, Nasdaq → plain symbol
"""

# FTSE MIB + selected Mid Cap (most liquid names on Borsa Italiana)
MILAN = [
    # FTSE MIB 40
    "ENI.MI", "ENEL.MI", "ISP.MI", "UCG.MI", "STLAM.MI", "RACE.MI", "STM.MI",
    "G.MI", "TIT.MI", "MB.MI", "BAMI.MI", "LDO.MI", "MONC.MI", "PRY.MI",
    "REC.MI", "TEN.MI", "BPE.MI", "BGN.MI", "FBK.MI", "PST.MI", "CNHI.MI",
    "AMP.MI", "HER.MI", "ERG.MI", "INW.MI", "IP.MI", "NEXI.MI", "PIRC.MI",
    "A2A.MI", "SPM.MI", "UNI.MI", "DIA.MI", "MTA.MI", "BMED.MI", "BPSO.MI",
    "AZM.MI", "ENV.MI", "IG.MI", "SRG.MI", "TRN.MI",
    # Mid Cap selected (liquid)
    "CPR.MI", "BC.MI", "IF.MI", "EL.MI", "DAN.MI", "SL.MI", "ARN.MI",
    "TES.MI", "MN.MI", "WBD.MI", "SFER.MI", "PLT.MI", "ZV.MI", "EGPW.MI",
    "ASR.MI", "JUVE.MI", "DOV.MI", "BZU.MI", "CE.MI", "LR.MI",
]

# Nasdaq-100 top ~60 by typical ADV
NASDAQ = [
    # Mega cap
    "AAPL", "MSFT", "NVDA", "GOOGL", "GOOG", "AMZN", "META", "TSLA", "AVGO",
    "COST", "NFLX", "TMUS", "CSCO", "AMD", "PEP", "LIN", "ADBE", "QCOM",
    "TXN", "INTU", "AMGN", "ISRG", "CMCSA", "AMAT", "HON", "BKNG", "VRTX",
    "PANW", "MU", "ADP", "GILD", "LRCX", "SBUX", "ADI", "MDLZ", "REGN",
    "KLAC", "MELI", "PYPL", "SNPS", "CDNS", "MAR", "CRWD", "ORLY", "CEG",
    "CTAS", "DASH", "ASML", "ABNB", "FTNT", "CHTR", "WDAY", "NXPI", "PCAR",
    "MNST", "ROP", "PAYX", "ADSK", "ODFL", "CPRT",
]

UNIVERSES = {
    "🇮🇹  Milano": MILAN,
    "🇺🇸  Nasdaq": NASDAQ,
    "🌍  Entrambi": MILAN + NASDAQ,
}
