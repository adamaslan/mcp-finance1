"""Stock universe lists for screening.

Hardcoded lists of symbols organized by universe type.
Update quarterly from official sources.
"""

from typing import Final

UNIVERSES: Final[dict[str, list[str]]] = {
    "sp500": [
        "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "AVGO", "META", "TSLA", "BRK.B",
        "WMT", "LLY", "JPM", "V", "ORCL", "XOM", "JNJ", "MA", "COST", "MU",
        "PLTR", "BAC", "ABBV", "HD", "AMD", "NFLX", "GE", "PG", "CVX", "KO",
        "CAT", "UNH", "MS", "CSCO", "GS", "IBM", "LRCX", "WFC", "RTX", "PM",
        "MRK", "AMAT", "AXP", "TMO", "INTC", "MCD", "CRM", "ABT", "TMUS", "C",
        "KLAC", "LIN", "PEP", "DIS", "BA", "APP", "ISRG", "APH", "GEV", "SCHW",
        "BLK", "AMGN", "UBER", "ACN", "TJX", "NEE", "TXN", "QCOM", "DHR", "T",
        "SPGI", "BKNG", "VZ", "ANET", "LOW", "GILD", "COF", "INTU", "ADI", "PFE",
        "DE", "HON", "SYK", "UNP", "LMT", "NOW", "ETN", "WELL", "PANW", "BSX",
        "BX", "NEM", "MDT", "PLD", "ADBE", "COP", "PH", "PGR", "CB", "KKR",
        "CRWD", "BMY", "VRTX", "CEG", "HCA", "SBUX", "ADP", "MCK", "MO", "CMCSA",
        "CME", "CVS", "GD", "ICE", "SNPS", "SO", "HOOD", "MCO", "NKE", "NOC",
        "DUK", "UPS", "HWM", "PNC", "MRSH", "MMM", "WM", "SHW", "DASH", "MAR",
        "CDNS", "TT", "AMT", "USB", "FCX", "EMR", "APO", "BK", "ELV", "CRH",
        "TDG", "GLW", "ORLY", "CMI", "DELL", "ABNB", "CTAS", "EQIX", "ECL", "REGN",
        "ITW", "MNST", "WDC", "GM", "RCL", "WMB", "AON", "MDLZ", "CI", "FDX",
        "STX", "WBD", "TEL", "JCI", "HLT", "SLB", "PWR", "COR", "CL", "CSX",
        "MSI", "AJG", "RSG", "NSC", "COIN", "LHX", "AEP", "TFC", "PCAR", "CVNA",
        "ROST", "KMI", "SNDK", "SRE", "SPG", "TRV", "NXPI", "APD", "BDX", "URI",
        "AZO", "NDAQ", "AFL", "EOG", "IDXX", "VST", "O", "ADSK", "DLR", "FTNT",
        "VLO", "PSX", "ZTS", "F", "PYPL", "CMG", "MPC", "D", "PSA", "EA",
        "BKR", "CBRE", "GWW", "MET", "AXON", "CAH", "TGT", "ALL", "FAST", "AME",
        "MPWR", "WDAY", "EW", "CARR", "AMP", "CTVA", "OKE", "ROK", "DAL", "DHI",
        "MSCI", "EXC", "ROP", "XEL", "YUM", "TTWO", "FANG", "ETR", "OXY", "EBAY",
        "DDOG", "EL", "CTSH", "GRMN", "IQV", "VMC", "MCHP", "HSY", "XYZ", "KR",
    ],

    "nasdaq100": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO",
        "COST", "NFLX", "AMD", "PEP", "ADBE", "CSCO", "CMCSA", "TMUS",
        "QCOM", "INTC", "HON", "INTU", "AMGN", "AMAT", "TXN", "BKNG",
        "ADP", "SBUX", "GILD", "MDLZ", "ADI", "ISRG", "LRCX", "REGN",
    ],

    "etf_large_cap": [
        "SPY", "VOO", "IVV", "VTI", "QQQ", "DIA", "IWM", "VEA", "VWO",
        "EFA", "IEFA", "AGG", "BND", "VIG", "VYM", "SCHD", "VUG", "VTV",
    ],

    "etf_sector": [
        "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE",
    ],

    "crypto": [
        "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD",
        "DOGE-USD", "SOL-USD", "DOT-USD", "MATIC-USD", "AVAX-USD",
    ],

    "tech_leaders": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
        "AMD", "INTC", "CRM", "ADBE", "ORCL", "IBM", "CSCO",
    ],

    "beta1": [
        "MU", "GLD", "NVDA", "RGTI", "RR", "PL", "GEV", "GOOG", "IBIT", "LRCX", "APLD",
    ],
}


def get_universe(name: str) -> list[str]:
    """Get symbols for a named universe.

    Args:
        name: Universe name (case-insensitive).

    Returns:
        List of ticker symbols, empty if unknown universe.
    """
    return UNIVERSES.get(name.lower(), [])


def list_universes() -> list[str]:
    """Get list of available universe names.

    Returns:
        List of universe names.
    """
    return list(UNIVERSES.keys())
