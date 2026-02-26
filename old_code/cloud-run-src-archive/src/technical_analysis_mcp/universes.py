"""Stock universe lists for screening.

Hardcoded lists of symbols organized by universe type.
Update quarterly from official sources.
"""

from typing import Final

UNIVERSES: Final[dict[str, list[str]]] = {
    "sp500": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
        "UNH", "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK",
        "ABBV", "KO", "AVGO", "PEP", "COST", "WMT", "LLY", "MCD", "TMO",
        "ACN", "ABT", "CSCO", "DHR", "CRM", "ADBE", "NKE", "TXN", "PM",
        "NEE", "DIS", "VZ", "NFLX", "CMCSA", "BMY", "WFC", "INTC", "UPS",
        "AMD", "HON", "QCOM", "UNP", "LIN", "ORCL", "BA", "COP", "IBM",
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
        "MU", "GLD", "NVDA", "RGTI", "RR", "PL", "GEV", "GOOG", "IBIT", "LICX", "APLD",
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
