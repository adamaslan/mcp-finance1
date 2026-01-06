"""Unified technical analysis orchestrator.

This module provides a single entry point for complete stock analysis,
combining data fetching, indicator calculation, signal detection, and ranking.

All analysis logic is centralized here to avoid duplication across different
deployment contexts (Cloud Functions, local scripts, MCP servers, etc.).
"""

import logging
from typing import Any

import pandas as pd

from .config import DEFAULT_PERIOD
from .data import CachedDataFetcher, YFinanceDataFetcher
from .exceptions import DataFetchError, InsufficientDataError, InvalidSymbolError
from .indicators import (
    calculate_bollinger_bands,
    calculate_indicators_dict,
    calculate_macd,
    calculate_moving_averages,
    calculate_rsi,
    calculate_stochastic,
    calculate_atr,
    calculate_adx,
)
from .models import MutableSignal, Signal
from .ranking import GeminiRanking, RuleBasedRanking
from .signals import detect_all_signals

logger = logging.getLogger(__name__)


class StockAnalyzer:
    """Complete technical analysis pipeline for a single stock.

    Provides a clean interface for analyzing stocks with technical indicators,
    signal detection, and AI-powered or rule-based ranking.
    """

    def __init__(
        self,
        use_cache: bool = True,
        use_ai: bool = True,
    ):
        """Initialize the analyzer.

        Args:
            use_cache: Whether to cache fetched data.
            use_ai: Whether to use AI-powered ranking (falls back to rule-based if unavailable).
        """
        self._data_fetcher = CachedDataFetcher() if use_cache else YFinanceDataFetcher()
        self._use_ai = use_ai
        self._rule_based_ranker = RuleBasedRanking()
        self._ai_ranker = GeminiRanking() if use_ai else None

        logger.info(
            "Initialized StockAnalyzer (cache=%s, ai=%s)",
            use_cache,
            use_ai,
        )

    def analyze(
        self,
        symbol: str,
        period: str = DEFAULT_PERIOD,
    ) -> dict[str, Any]:
        """Complete analysis for a single stock.

        Fetches data, calculates indicators, detects signals, and ranks them.

        Args:
            symbol: Ticker symbol (e.g., 'AAPL').
            period: Time period (e.g., '3mo', '1y').

        Returns:
            Dictionary with complete analysis results including:
            - symbol: Stock symbol
            - price: Current price
            - change_pct: Percent change
            - indicators: Dictionary of indicator values
            - signals: List of detected signals with ranks
            - ai_score: Overall score (0-100)
            - ai_outlook: BULLISH/BEARISH/NEUTRAL
            - ai_action: BUY/SELL/HOLD
            - ai_powered: Whether AI was used
            - timestamp: Analysis timestamp

        Raises:
            InvalidSymbolError: If symbol is invalid.
            DataFetchError: If data fetching fails.
            InsufficientDataError: If not enough data points.
        """
        try:
            # Step 1: Fetch data
            logger.info("Fetching data for %s (period: %s)", symbol, period)
            df = self._data_fetcher.fetch(symbol, period)

            # Step 2: Calculate indicators
            logger.debug("Calculating indicators for %s", symbol)
            indicators_dict = self._get_indicators(df)

            # Step 3: Detect signals
            logger.debug("Detecting signals for %s", symbol)
            signals = detect_all_signals(df)

            # Step 4: Rank signals
            logger.debug("Ranking signals for %s", symbol)
            market_data = {
                "price": float(df["Close"].iloc[-1]),
                "change_pct": float((df["Close"].iloc[-1] / df["Close"].iloc[-2] - 1) * 100),
                "volume": int(df["Volume"].iloc[-1]),
            }
            ranked_signals = self._rank_signals(symbol, signals, market_data)

            # Step 5: Generate score and outlook
            score_result = self._calculate_score(ranked_signals)

            # Compile result
            result = {
                "symbol": symbol.upper(),
                "timestamp": pd.Timestamp.utcnow().isoformat(),
                "price": market_data["price"],
                "change_pct": market_data["change_pct"],
                "indicators": {
                    "rsi": indicators_dict.get("rsi"),
                    "macd": indicators_dict.get("macd"),
                    "macd_signal": indicators_dict.get("macd_signal"),
                    "macd_hist": indicators_dict.get("macd_hist"),
                    "sma20": indicators_dict.get("sma20"),
                    "sma50": indicators_dict.get("sma50"),
                    "ema20": indicators_dict.get("ema20"),
                    "bb_upper": indicators_dict.get("bb_upper"),
                    "bb_lower": indicators_dict.get("bb_lower"),
                    "adx": indicators_dict.get("adx"),
                    "stoch_k": indicators_dict.get("stoch_k"),
                    "stoch_d": indicators_dict.get("stoch_d"),
                    "atr": indicators_dict.get("atr"),
                },
                "signals": [self._signal_to_dict(s) for s in ranked_signals[:10]],  # Top 10
                "signal_count": len(ranked_signals),
                "ai_score": score_result["score"],
                "ai_outlook": score_result["outlook"],
                "ai_action": score_result["action"],
                "ai_confidence": score_result.get("confidence", "MEDIUM"),
                "ai_summary": score_result.get("summary", ""),
                "ai_powered": score_result.get("ai_powered", False),
            }

            logger.info(
                "Analysis complete for %s: score=%d, outlook=%s",
                symbol,
                result["ai_score"],
                result["ai_outlook"],
            )
            return result

        except (InvalidSymbolError, DataFetchError, InsufficientDataError) as e:
            logger.error("Analysis failed for %s: %s", symbol, e)
            raise
        except Exception as e:
            logger.exception("Unexpected error analyzing %s", symbol)
            raise

    def _get_indicators(self, df: pd.DataFrame) -> dict[str, float]:
        """Extract all calculated indicator values from DataFrame.

        Args:
            df: DataFrame with all indicators calculated.

        Returns:
            Dictionary of indicator name -> value.
        """
        return calculate_indicators_dict(df)

    def _rank_signals(
        self,
        symbol: str,
        signals: list[MutableSignal],
        market_data: dict[str, Any],
    ) -> list[MutableSignal]:
        """Rank signals using AI or rule-based method.

        Args:
            symbol: Stock symbol.
            signals: List of signals to rank.
            market_data: Current market context.

        Returns:
            Ranked signals sorted by strength.
        """
        if self._use_ai and self._ai_ranker:
            try:
                return self._ai_ranker.rank(signals, symbol, market_data)
            except Exception as e:
                logger.warning("AI ranking failed for %s, falling back to rule-based: %s", symbol, e)
                return self._rule_based_ranker.rank(signals, symbol, market_data)
        else:
            return self._rule_based_ranker.rank(signals, symbol, market_data)

    def _calculate_score(self, signals: list[MutableSignal]) -> dict[str, Any]:
        """Calculate overall score and outlook from ranked signals.

        Args:
            signals: Ranked signals with scores.

        Returns:
            Dictionary with score, outlook, action, confidence, summary.
        """
        if not signals:
            return {
                "score": 50,
                "outlook": "NEUTRAL",
                "action": "HOLD",
                "confidence": "LOW",
                "summary": "No signals detected",
                "ai_powered": False,
            }

        # Use AI-provided scores if available, otherwise calculate from signals
        scores = [s.score for s in signals if s.score is not None]

        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            # Fallback: count bullish vs bearish
            bullish = sum(1 for s in signals if "BULLISH" in s.strength)
            bearish = sum(1 for s in signals if "BEARISH" in s.strength)
            avg_score = 50 + (bullish - bearish) * 5

        avg_score = max(10, min(90, avg_score))

        # Determine outlook
        if avg_score >= 65:
            outlook = "BULLISH"
            action = "BUY"
        elif avg_score <= 35:
            outlook = "BEARISH"
            action = "SELL"
        else:
            outlook = "NEUTRAL"
            action = "HOLD"

        return {
            "score": int(avg_score),
            "outlook": outlook,
            "action": action,
            "confidence": "HIGH" if abs(avg_score - 50) > 15 else "MEDIUM",
            "summary": f"Based on {len(signals)} detected signals",
            "ai_powered": bool(signals and signals[0].score is not None),
        }

    @staticmethod
    def _signal_to_dict(signal: MutableSignal) -> dict[str, Any]:
        """Convert signal object to dictionary.

        Args:
            signal: Signal object.

        Returns:
            Dictionary representation.
        """
        return {
            "signal": signal.signal,
            "strength": signal.strength,
            "category": signal.category.value if signal.category else None,
            "score": signal.score,
            "rank": signal.rank,
        }
