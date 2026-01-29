"""Morning market briefing generator."""

import asyncio
import logging
from typing import Any

from ..data import CachedDataFetcher
from ..indicators import calculate_all_indicators
from ..ranking import rank_signals
from ..risk import RiskAssessor
from ..signals import detect_all_signals
from .economic_calendar import EconomicCalendar
from .market_status import MarketStatusChecker

logger = logging.getLogger(__name__)


class MorningBriefGenerator:
    """Generate daily morning market briefings."""

    def __init__(self):
        """Initialize briefing generator."""
        self._fetcher = CachedDataFetcher()
        self._risk_assessor = RiskAssessor()
        self._market_checker = MarketStatusChecker()
        self._calendar = EconomicCalendar()

    async def generate_brief(
        self,
        watchlist: list[str] | None = None,
        market_region: str = "US",
        period: str = "1mo",
    ) -> dict[str, Any]:
        """Generate morning market briefing.

        Args:
            watchlist: Optional list of symbols (default: top 10 S&P 500).
            market_region: Market region (US, EU, ASIA).
            period: Time period for analysis.

        Returns:
            Morning brief with market status, signals, events, and themes.
        """
        if watchlist is None:
            # Default watchlist - top tech and finance stocks
            watchlist = ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "JPM", "BAC", "V", "MA", "TSLA"]
        else:
            watchlist = watchlist[:10]  # Limit to 10 symbols

        logger.info("Generating morning brief for %d watchlist symbols in %s (period: %s)", len(watchlist), market_region, period)

        # Gather market info in parallel
        market_status = self._market_checker.get_market_status(market_region)
        economic_events = self._calendar.get_todays_events()

        # Analyze watchlist symbols
        watchlist_signals = await self._analyze_watchlist(watchlist, period=period)

        # Get sector movers (mock)
        sector_leaders = self._get_sector_leaders()
        sector_losers = self._get_sector_losers()

        # Detect market themes
        market_themes = self._detect_market_themes(
            market_status, watchlist_signals, sector_leaders
        )

        return {
            "timestamp": market_status.get("current_time", ""),
            "market_status": market_status,
            "economic_events": economic_events,
            "watchlist_signals": watchlist_signals,
            "sector_leaders": sector_leaders,
            "sector_losers": sector_losers,
            "key_themes": market_themes,
        }

    async def _analyze_watchlist(self, symbols: list[str], period: str = "1mo") -> list[dict[str, Any]]:
        """Analyze watchlist symbols for signals.

        Args:
            symbols: List of ticker symbols.
            period: Time period for analysis.

        Returns:
            List of watchlist signal analyses.
        """
        semaphore = asyncio.Semaphore(5)
        results = []

        async def analyze_symbol(symbol: str) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    return await self._analyze_single(symbol, period=period)
                except Exception as e:
                    logger.warning("Error analyzing %s: %s", symbol, e)
                    return None

        task_results = await asyncio.gather(
            *[analyze_symbol(sym) for sym in symbols],
            return_exceptions=False,
        )

        for result in task_results:
            if result is not None:
                results.append(result)

        return results

    async def _analyze_single(self, symbol: str, period: str = "1mo") -> dict[str, Any]:
        """Analyze single symbol for watchlist.

        Args:
            symbol: Ticker symbol.
            period: Time period for analysis.

        Returns:
            Watchlist signal analysis.
        """
        symbol = symbol.upper().strip()

        df = self._fetcher.fetch(symbol, period)
        df = calculate_all_indicators(df)

        current = df.iloc[-1]
        price = float(current.get("Close", 0))
        change = float(current.get("Price_Change", 0))

        signals = detect_all_signals(df)
        market_data = {"price": price, "change": change}
        ranked_signals = rank_signals(
            signals=signals,
            symbol=symbol,
            market_data=market_data,
            use_ai=False,
        )

        # Get top 3 signals
        top_signals = [s.signal for s in ranked_signals[:3] if hasattr(s, "signal")]

        # Get risk assessment
        risk_result = self._risk_assessor.assess(df, ranked_signals, symbol)

        # Determine action
        if risk_result.has_trades:
            action = "BUY"
            risk_assess = "TRADE"
        elif risk_result.risk_assessment and risk_result.risk_assessment.metrics.is_trending:
            action = "HOLD"
            risk_assess = "HOLD"
        else:
            action = "AVOID"
            risk_assess = "AVOID"

        # Calculate key levels
        support = price * 0.97
        resistance = price * 1.03

        return {
            "symbol": symbol,
            "price": price,
            "change_percent": change,
            "top_signals": top_signals,
            "risk_assessment": risk_assess,
            "action": action,
            "key_support": support,
            "key_resistance": resistance,
        }

    def _get_sector_leaders(self) -> list[dict[str, Any]]:
        """Get top sector gainers.

        Returns:
            List of sector leader information.
        """
        return [
            {"sector": "Technology", "change_percent": 2.1, "drivers": ["AI stocks rallying", "Earnings optimism"]},
            {"sector": "Financials", "change_percent": 1.5, "drivers": ["Rate expectations", "Bank earnings"]},
            {"sector": "Healthcare", "change_percent": 0.8, "drivers": ["Biotech strength"]},
        ]

    def _get_sector_losers(self) -> list[dict[str, Any]]:
        """Get top sector losers.

        Returns:
            List of sector loser information.
        """
        return [
            {"sector": "Energy", "change_percent": -1.2, "drivers": ["Crude oil weakness"]},
            {"sector": "Utilities", "change_percent": -0.5, "drivers": ["Rate sensitivity"]},
            {"sector": "Consumer", "change_percent": -0.3, "drivers": ["Mixed earnings"]},
        ]

    def _detect_market_themes(
        self,
        market_status: dict[str, Any],
        watchlist_signals: list[dict[str, Any]],
        sector_leaders: list[dict[str, Any]],
    ) -> list[str]:
        """Detect major market themes.

        Args:
            market_status: Market status information.
            watchlist_signals: Watchlist signal analyses.
            sector_leaders: Sector leader information.

        Returns:
            List of key market themes.
        """
        themes = []

        # Check for tech strength
        tech_symbols = ["AAPL", "MSFT", "NVDA", "GOOGL", "META"]
        tech_bullish = sum(
            1 for w in watchlist_signals
            if w.get("symbol") in tech_symbols and w.get("action") == "BUY"
        )
        if tech_bullish >= 3:
            themes.append("Tech Strength - AI enthusiasm and earnings optimism")

        # Check for financial strength
        if sector_leaders and sector_leaders[0].get("sector") == "Financials":
            themes.append("Financials Rallying - Bank stocks outperforming")

        # Market sentiment
        sentiment = market_status.get("market_sentiment", "NEUTRAL")
        if sentiment == "BULLISH":
            themes.append("Positive Sentiment - Futures up, VIX compressed")
        elif sentiment == "BEARISH":
            themes.append("Risk-Off - High volatility, negative futures")

        # Default theme if none detected
        if not themes:
            themes.append("Mixed Market - No dominant theme detected")

        return themes
