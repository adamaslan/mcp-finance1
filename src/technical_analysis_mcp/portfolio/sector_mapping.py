"""Sector mapping for equities."""

# S&P 500 stock to sector mapping
SECTOR_MAPPING = {
    # Technology
    "AAPL": "Technology",
    "MSFT": "Technology",
    "NVDA": "Technology",
    "GOOGL": "Technology",
    "GOOG": "Technology",
    "META": "Technology",
    "AMZN": "Technology",
    "TSLA": "Technology",
    "NFLX": "Technology",
    "ADBE": "Technology",
    "CSCO": "Technology",
    "INTC": "Technology",
    "AMD": "Technology",
    "CRM": "Technology",
    "ORACLE": "Technology",
    "IBM": "Technology",
    "ACN": "Technology",
    "QCOM": "Technology",
    "AVGO": "Technology",
    "MU": "Technology",
    "AMAT": "Technology",
    "ASML": "Technology",
    "LRCX": "Technology",
    "SNPS": "Technology",
    "CDNS": "Technology",
    "WDAY": "Technology",
    "OKTA": "Technology",
    "NOW": "Technology",
    "CRWD": "Technology",
    "NET": "Technology",
    # Healthcare
    "JNJ": "Healthcare",
    "UNH": "Healthcare",
    "PFE": "Healthcare",
    "ABBV": "Healthcare",
    "TMO": "Healthcare",
    "MRNA": "Healthcare",
    "LLY": "Healthcare",
    "MRK": "Healthcare",
    "AMGN": "Healthcare",
    "GILD": "Healthcare",
    "BIIB": "Healthcare",
    "ANTM": "Healthcare",
    "CI": "Healthcare",
    "HUM": "Healthcare",
    "REGN": "Healthcare",
    "ILMN": "Healthcare",
    "VRTX": "Healthcare",
    "EXAS": "Healthcare",
    "ZTS": "Healthcare",
    "SYK": "Healthcare",
    "DXCM": "Healthcare",
    "ELV": "Healthcare",
    # Financials
    "JPM": "Financials",
    "BAC": "Financials",
    "WFC": "Financials",
    "GS": "Financials",
    "MS": "Financials",
    "BLK": "Financials",
    "AXP": "Financials",
    "V": "Financials",
    "MA": "Financials",
    "DFS": "Financials",
    "COF": "Financials",
    "AIG": "Financials",
    "PNC": "Financials",
    "USB": "Financials",
    "TFC": "Financials",
    "KEY": "Financials",
    "CME": "Financials",
    "ICE": "Financials",
    "PYPL": "Financials",
    "SQ": "Financials",
    # Consumer Discretionary
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "MCD": "Consumer Discretionary",
    "NKE": "Consumer Discretionary",
    "DIDI": "Consumer Discretionary",
    "LVMh": "Consumer Discretionary",
    "RCL": "Consumer Discretionary",
    "CCL": "Consumer Discretionary",
    "UAL": "Consumer Discretionary",
    "AAL": "Consumer Discretionary",
    "DAL": "Consumer Discretionary",
    "GM": "Consumer Discretionary",
    "F": "Consumer Discretionary",
    "TM": "Consumer Discretionary",
    "HWM": "Consumer Discretionary",
    # Consumer Staples
    "KO": "Consumer Staples",
    "PEP": "Consumer Staples",
    "WMT": "Consumer Staples",
    "CL": "Consumer Staples",
    "KMB": "Consumer Staples",
    "MO": "Consumer Staples",
    "PM": "Consumer Staples",
    "GIS": "Consumer Staples",
    "HSY": "Consumer Staples",
    "K": "Consumer Staples",
    "STZ": "Consumer Staples",
    "PG": "Consumer Staples",
    # Industrials
    "BA": "Industrials",
    "CAT": "Industrials",
    "LMT": "Industrials",
    "RTX": "Industrials",
    "GE": "Industrials",
    "MMM": "Industrials",
    "HON": "Industrials",
    "ITW": "Industrials",
    "PCAR": "Industrials",
    "NSC": "Industrials",
    "CSX": "Industrials",
    "UNP": "Industrials",
    "KSU": "Industrials",
    # Energy
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "EOG": "Energy",
    "SLB": "Energy",
    "MPC": "Energy",
    "VLO": "Energy",
    "PSX": "Energy",
    "HAL": "Energy",
    "OKE": "Energy",
    "KMI": "Energy",
    "TPL": "Energy",
    # Utilities
    "NEE": "Utilities",
    "DUK": "Utilities",
    "SO": "Utilities",
    "D": "Utilities",
    "AEP": "Utilities",
    "EXC": "Utilities",
    "XEL": "Utilities",
    "PPL": "Utilities",
    "AWK": "Utilities",
    "WEC": "Utilities",
    # Real Estate
    "PLD": "Real Estate",
    "AMT": "Real Estate",
    "DLR": "Real Estate",
    "EQIX": "Real Estate",
    "AVB": "Real Estate",
    "EQR": "Real Estate",
    "PSA": "Real Estate",
    "SPG": "Real Estate",
    "WY": "Real Estate",
    "URI": "Real Estate",
    # Materials
    "APD": "Materials",
    "LIN": "Materials",
    "NEM": "Materials",
    "FCX": "Materials",
    "DD": "Materials",
    "CTVA": "Materials",
    "ALB": "Materials",
    "SHW": "Materials",
    "STLD": "Materials",
    "X": "Materials",
    "RIO": "Materials",
    "NUE": "Materials",
    "PL": "Materials",
    "AU": "Materials",
    "AEM": "Materials",
    "SAN": "Materials",
    "BBVA": "Materials",
    # Communication Services
    "META": "Communication Services",
    "GOOGL": "Communication Services",
    "GOOG": "Communication Services",
    "NFLX": "Communication Services",
    "CMCSA": "Communication Services",
    "CHTR": "Communication Services",
    "NWSA": "Communication Services",
    "NWS": "Communication Services",
    "FOXA": "Communication Services",
    "FOX": "Communication Services",
    "VZ": "Communication Services",
    "T": "Communication Services",
    "TMUS": "Communication Services",
    # Additional stocks from portfolio
    "STX": "Technology",
    "TSM": "Technology",
    "GLW": "Technology",
    "BIDU": "Technology",
    "IONQ": "Technology",
    "ARM": "Technology",
    "SPOT": "Technology",
    "DDOG": "Technology",
    "SNDK": "Technology",
    "WDC": "Technology",
    "TOST": "Technology",
    # Consumer Discretionary
    "ONON": "Consumer Discretionary",
    "NKE": "Consumer Discretionary",
    "LYFT": "Consumer Discretionary",
    "JOBY": "Consumer Discretionary",
    "UBER": "Consumer Discretionary",
    "TOL": "Consumer Discretionary",
    "RCL": "Consumer Discretionary",
    "NCLH": "Consumer Discretionary",
    "LVS": "Consumer Discretionary",
    "DIS": "Consumer Discretionary",
    # Consumer Staples
    "BUD": "Consumer Staples",
    "TLRY": "Consumer Staples",
    # Healthcare
    "GILD": "Healthcare",
    "LLY": "Healthcare",
    "MRK": "Healthcare",
    "XBI": "Healthcare",
    "MRNA": "Healthcare",
    "ZS": "Healthcare",
    "EVR": "Healthcare",
    "GEV": "Healthcare",
    "WELL": "Healthcare",
    "SRTA": "Healthcare",
    "LAB": "Healthcare",
    # Financials
    "C": "Financials",
    "JPM": "Financials",
    "MS": "Financials",
    "GS": "Financials",
    "MTB": "Financials",
    "CME": "Financials",
    "HOOD": "Financials",
    "VST": "Financials",
    # Industrials
    "CAT": "Industrials",
    "BA": "Industrials",
    "LMT": "Industrials",
    "RTX": "Industrials",
    "ROK": "Industrials",
    "XLI": "Industrials",
    # Energy
    "CVX": "Energy",
    "VDE": "Energy",
    "HAL": "Energy",
    "SLB": "Energy",
    "DAR": "Energy",
    "EIX": "Energy",
    # Real Estate
    "O": "Real Estate",
    "CBRE": "Real Estate",
    "PLD": "Real Estate",
    "ITB": "Real Estate",
    # Utilities
    "NEE": "Utilities",
    "AEP": "Utilities",
    "PCG": "Utilities",
    "EWG": "Utilities",
    # ETFs and Index Funds
    "SPY": "Information Technology",
    "QQQ": "Information Technology",
    "DIA": "Information Technology",
    "IWM": "Information Technology",
    "VGT": "Information Technology",
    "PSQ": "Information Technology",
    "RSP": "Information Technology",
    "SQQQ": "Information Technology",
    "GLD": "Materials",
    "SLV": "Materials",
    "ETHA": "Consumer Discretionary",
    "IBIT": "Technology",
    "THNQ": "Technology",
    "GRNY": "Technology",
    "CWBHF": "Materials",
    "BYDIF": "Consumer Discretionary",
    "JETS": "Consumer Discretionary",
    "ACHR": "Healthcare",
    "OKLO": "Energy",
    "FLMX": "Technology",
    "RGTI": "Technology",
    "SRUUF": "Technology",
    "COLB": "Financials",
    "JKS": "Energy",
    "SHOP": "Consumer Discretionary",
    "BABA": "Consumer Discretionary",
    "PATH": "Healthcare",
    "QS": "Technology",
    "WRD": "Technology",
    "ULCC": "Consumer Discretionary",
    "AMAT": "Technology",
    "BBVA": "Financials",
    "LRCX": "Technology",
    "NI": "Materials",
    "CSCO": "Technology",
    "CRH": "Materials",
}


def get_sector(symbol: str) -> str:
    """Get sector for a given symbol.

    Args:
        symbol: Ticker symbol.

    Returns:
        Sector name, or "Other" if not found.
    """
    return SECTOR_MAPPING.get(symbol.upper(), "Other")


def get_risk_level(symbol: str) -> str:
    """Get financial risk level for a stock (determines stop loss width).

    Args:
        symbol: Ticker symbol.

    Returns:
        Risk level: "low" (2-3% stop), "moderate" (3-5% stop), "high" (5-8% stop).
    """
    # Blue-chip defensive stocks (2-3% stops)
    low_risk = {
        "JNJ", "PG", "KO", "PEP", "WMT", "MCD", "MSFT", "AAPL", "V", "MA",
        "JPM", "BAC", "GS", "WFC", "AXP", "MMM", "HON", "CAT", "NEE", "DUK",
        "SO", "XEL", "SCHW", "BUD", "KMB", "CL", "GIS", "HSY"
    }

    # Established companies with moderate volatility (3-5% stops)
    moderate_risk = {
        "ORCL", "CSCO", "IBM", "INTC", "AMD", "CRM", "ACN", "PSA", "SPG",
        "EQR", "AVB", "AMT", "PLD", "EQIX", "DLR", "XOM", "CVX", "COP",
        "EOG", "BA", "LMT", "RTX", "GE", "ITW", "UBER", "ALLY", "PYPL",
        "SQ", "AEP", "PPL", "AWK", "D", "NCLH", "RCL", "CCL", "UAL",
        "AAL", "DAL", "F", "GM", "TM"
    }

    # Growth & volatile stocks (5-8% stops)
    high_risk = {
        "TSLA", "META", "NVDA", "NFLX", "AMZN", "CRWD", "NET", "PANW",
        "SHOP", "DDOG", "SNPS", "CDNS", "ASML", "LRCX", "AMAT", "MU",
        "ARM", "IONQ", "QS", "JOBY", "LYFT", "RDDT", "SPOT", "HOOD",
        "MRNA", "BABA", "BIDU", "JKS", "GELD", "TLRY", "ULCC", "JETS",
        "OKLO", "TOST", "PATH", "ZS", "LAB", "EVR", "GEV", "SRTA",
        "ACHR", "RGTI", "BUDZ", "BZFD", "BRAXF", "TPICQ", "QBTS",
        "FLMX", "RR", "HTZWW", "HTZ", "ONON", "DAR", "WRD", "BTG",
        "NUE", "STLD", "X", "FCX", "NEM", "RIO", "AU", "AEM", "PL",
        "SLB", "HAL", "MPC", "VLO", "PSX", "OKE", "KMI"
    }

    symbol_upper = symbol.upper()

    if symbol_upper in low_risk:
        return "low"
    elif symbol_upper in moderate_risk:
        return "moderate"
    elif symbol_upper in high_risk:
        return "high"
    else:
        # Default to moderate for unknown stocks
        return "moderate"
