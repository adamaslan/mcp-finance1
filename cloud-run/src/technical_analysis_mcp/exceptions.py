"""Custom exception hierarchy for Technical Analysis MCP Server.

Defines domain-specific exceptions for clear error handling across the application.
"""


class TechnicalAnalysisError(Exception):
    """Base exception for all technical analysis errors."""

    pass


class DataFetchError(TechnicalAnalysisError):
    """Raised when fetching market data fails.

    Attributes:
        symbol: The ticker symbol that failed to fetch.
        period: The time period requested.
    """

    def __init__(self, symbol: str, period: str | None = None, message: str | None = None):
        self.symbol = symbol
        self.period = period
        if message:
            super().__init__(message)
        else:
            msg = f"Failed to fetch data for {symbol}"
            if period:
                msg += f" (period: {period})"
            super().__init__(msg)


class InsufficientDataError(TechnicalAnalysisError):
    """Raised when there's not enough data to calculate indicators.

    Attributes:
        symbol: The ticker symbol.
        required_periods: Minimum data points needed.
        available_periods: Data points actually available.
    """

    def __init__(self, symbol: str, required_periods: int, available_periods: int):
        self.symbol = symbol
        self.required_periods = required_periods
        self.available_periods = available_periods
        super().__init__(
            f"Insufficient data for {symbol}: "
            f"need {required_periods} periods, have {available_periods}"
        )


class RankingError(TechnicalAnalysisError):
    """Raised when signal ranking fails.

    Attributes:
        symbol: The ticker symbol being ranked.
        reason: Description of what went wrong.
    """

    def __init__(self, symbol: str, reason: str):
        self.symbol = symbol
        self.reason = reason
        super().__init__(f"Ranking failed for {symbol}: {reason}")


class InvalidSymbolError(TechnicalAnalysisError):
    """Raised when a ticker symbol is invalid or not found.

    Attributes:
        symbol: The invalid ticker symbol.
    """

    def __init__(self, symbol: str):
        self.symbol = symbol
        super().__init__(f"Invalid or unknown symbol: {symbol}")


class ConfigurationError(TechnicalAnalysisError):
    """Raised when there's a configuration issue.

    Attributes:
        parameter: The configuration parameter that's invalid.
        reason: Why the configuration is invalid.
    """

    def __init__(self, parameter: str, reason: str):
        self.parameter = parameter
        self.reason = reason
        super().__init__(f"Configuration error for '{parameter}': {reason}")
