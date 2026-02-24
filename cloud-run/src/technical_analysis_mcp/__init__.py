"""Technical Analysis MCP Server.

A modular technical analysis system for stocks, ETFs, and crypto
with 150+ signals and optional AI-powered ranking.

Example usage:
    from technical_analysis_mcp import TechnicalAnalyzer

    analyzer = TechnicalAnalyzer()
    result = analyzer.analyze("AAPL")
    print(result.summary)
"""

from datetime import datetime
from typing import Any

from .config import (
    DEFAULT_PERIOD,
    MAX_SIGNALS_RETURNED,
    SignalCategory,
    SignalStrength,
)
from .data import CachedDataFetcher, DataFetcher, FinnhubAlphaDataFetcher
from .exceptions import (
    DataFetchError,
    InsufficientDataError,
    InvalidSymbolError,
    RankingError,
    TechnicalAnalysisError,
)
from .indicators import calculate_all_indicators
from .models import (
    AnalysisResult,
    AnalysisSummary,
    ComparisonResult,
    Indicators,
    IndicatorsSummary,
    MutableSignal,
    ScreeningResult,
    Signal,
)
from .ranking import GeminiRanking, RankingStrategy, RuleBasedRanking, rank_signals
from .signals import detect_all_signals
from .universes import UNIVERSES, get_universe, list_universes

__version__ = "2.0.0"
__all__ = [
    # Main class
    "TechnicalAnalyzer",
    # Models
    "Signal",
    "Indicators",
    "IndicatorsSummary",
    "AnalysisSummary",
    "AnalysisResult",
    "ComparisonResult",
    "ScreeningResult",
    # Enums
    "SignalStrength",
    "SignalCategory",
    # Exceptions
    "TechnicalAnalysisError",
    "DataFetchError",
    "InsufficientDataError",
    "InvalidSymbolError",
    "RankingError",
    # Data fetching
    "DataFetcher",
    "FinnhubAlphaDataFetcher",
    "CachedDataFetcher",
    # Ranking
    "RankingStrategy",
    "RuleBasedRanking",
    "GeminiRanking",
    # Universes
    "UNIVERSES",
    "get_universe",
    "list_universes",
    # Version
    "__version__",
]


class TechnicalAnalyzer:
    """Facade class for the technical analysis system.

    Provides a simple interface to the complete analysis pipeline:
    data fetching, indicator calculation, signal detection, and ranking.

    Attributes:
        data_fetcher: The data fetcher to use.
        ranking_strategy: The ranking strategy to use.

    Example:
        >>> analyzer = TechnicalAnalyzer()
        >>> result = analyzer.analyze("AAPL", period="1mo")
        >>> print(f"Found {result['summary']['total_signals']} signals")
    """

    def __init__(
        self,
        data_fetcher: DataFetcher | None = None,
        ranking_strategy: RankingStrategy | None = None,
        use_cache: bool = True,
    ):
        """Initialize the analyzer.

        Args:
            data_fetcher: Custom data fetcher. Defaults to CachedDataFetcher.
            ranking_strategy: Custom ranking strategy. Defaults to RuleBasedRanking.
            use_cache: Whether to use caching for data fetching.
        """
        if data_fetcher is None:
            if use_cache:
                self._data_fetcher = CachedDataFetcher()
            else:
                self._data_fetcher = FinnhubAlphaDataFetcher()
        else:
            self._data_fetcher = data_fetcher

        self._ranking_strategy = ranking_strategy or RuleBasedRanking()

    def analyze(
        self,
        symbol: str,
        period: str = DEFAULT_PERIOD,
        use_ai: bool = False,
    ) -> dict[str, Any]:
        """Analyze a security.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL').
            period: Time period (e.g., '1mo', '3mo').
            use_ai: Whether to use AI ranking (requires API key).

        Returns:
            Analysis result dictionary with signals, indicators, and summary.

        Raises:
            DataFetchError: If data fetching fails.
            InsufficientDataError: If not enough data points.
        """
        symbol = symbol.upper().strip()

        df = self._data_fetcher.fetch(symbol, period)

        df = calculate_all_indicators(df)

        signals = detect_all_signals(df)

        current = df.iloc[-1]
        market_data = {
            "price": float(current["Close"]),
            "change": float(current.get("Price_Change", 0)),
            "rsi": float(current.get("RSI", 50)),
            "macd": float(current.get("MACD", 0)),
            "adx": float(current.get("ADX", 0)),
        }

        if use_ai:
            strategy = GeminiRanking()
        else:
            strategy = self._ranking_strategy

        ranked_signals = strategy.rank(signals, symbol, market_data)

        bullish_count = sum(1 for s in ranked_signals if "BULLISH" in s.strength)
        bearish_count = sum(1 for s in ranked_signals if "BEARISH" in s.strength)
        avg_score = (
            sum(s.ai_score or 50 for s in ranked_signals) / len(ranked_signals)
            if ranked_signals
            else 0
        )

        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "price": market_data["price"],
            "change": market_data["change"],
            "signals": [s.to_dict() for s in ranked_signals[:MAX_SIGNALS_RETURNED]],
            "summary": {
                "total_signals": len(ranked_signals),
                "bullish": bullish_count,
                "bearish": bearish_count,
                "avg_score": avg_score,
            },
            "indicators": {
                "rsi": market_data["rsi"],
                "macd": market_data["macd"],
                "adx": market_data["adx"],
                "volume": int(current["Volume"]),
            },
            "cached": False,
        }

    def compare(
        self,
        symbols: list[str],
        period: str = DEFAULT_PERIOD,
    ) -> dict[str, Any]:
        """Compare multiple securities.

        Args:
            symbols: List of ticker symbols.
            period: Time period for analysis.

        Returns:
            Comparison result with ranked securities.
        """
        results: list[dict[str, Any]] = []

        for symbol in symbols:
            try:
                analysis = self.analyze(symbol, period)
                results.append({
                    "symbol": symbol,
                    "score": analysis["summary"]["avg_score"],
                    "bullish": analysis["summary"]["bullish"],
                    "bearish": analysis["summary"]["bearish"],
                    "price": analysis["price"],
                    "change": analysis["change"],
                })
            except TechnicalAnalysisError:
                continue

        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "comparison": results,
            "winner": results[0] if results else None,
        }

    def screen(
        self,
        universe: str | list[str],
        criteria: dict[str, Any] | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Screen securities against criteria.

        Args:
            universe: Universe name or list of symbols.
            criteria: Screening criteria.
            limit: Maximum results.

        Returns:
            Screening result with matches.
        """
        if isinstance(universe, str):
            symbols = get_universe(universe)
            universe_name = universe
        else:
            symbols = universe
            universe_name = "custom"

        criteria = criteria or {}
        matches: list[dict[str, Any]] = []

        for symbol in symbols:
            try:
                analysis = self.analyze(symbol)

                if self._meets_criteria(analysis, criteria):
                    matches.append({
                        "symbol": symbol,
                        "score": analysis["summary"]["avg_score"],
                        "signals": analysis["summary"]["total_signals"],
                        "price": analysis["price"],
                        "rsi": analysis["indicators"]["rsi"],
                    })
            except TechnicalAnalysisError:
                continue

        matches.sort(key=lambda x: x["score"], reverse=True)

        return {
            "universe": universe_name,
            "total_screened": len(symbols),
            "matches": matches[:limit],
            "criteria": criteria,
        }

    def _meets_criteria(
        self,
        analysis: dict[str, Any],
        criteria: dict[str, Any],
    ) -> bool:
        """Check if analysis meets screening criteria."""
        indicators = analysis.get("indicators", {})

        if "rsi_max" in criteria:
            if indicators.get("rsi", 100) > criteria["rsi_max"]:
                return False

        if "rsi_min" in criteria:
            if indicators.get("rsi", 0) < criteria["rsi_min"]:
                return False

        if "min_score" in criteria:
            if analysis["summary"]["avg_score"] < criteria["min_score"]:
                return False

        if "min_bullish" in criteria:
            if analysis["summary"]["bullish"] < criteria["min_bullish"]:
                return False

        return True
