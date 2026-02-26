"""Trade scanner for identifying qualified setups across universes."""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

from ..config import DEFAULT_PERIOD
from ..data import create_data_fetcher
from ..indicators import calculate_all_indicators
from ..ranking import rank_signals
from ..risk import RiskAssessor
from ..signals import detect_all_signals
from ..universes import UNIVERSES

logger = logging.getLogger(__name__)


class TradeScanner:
    """Scans universes for qualified trade setups."""

    def __init__(self, max_concurrent: int = 10):
        """Initialize trade scanner.

        Args:
            max_concurrent: Maximum concurrent scan operations.
        """
        self._max_concurrent = max_concurrent
        self._fetcher = create_data_fetcher(use_cache=True)
        self._risk_assessor = RiskAssessor()

    async def scan_universe(
        self,
        universe: str = "sp500",
        max_results: int = 10,
        period: str = DEFAULT_PERIOD,
    ) -> dict[str, Any]:
        """Scan universe for qualified trade setups.

        Args:
            universe: Universe name (sp500, nasdaq100, etf_large_cap, crypto).
            max_results: Maximum results to return (1-50).
            period: Data period for analysis.

        Returns:
            Scan results with qualified setups.
        """
        max_results = min(max(1, max_results), 50)
        symbols = UNIVERSES.get(universe, [])

        if not symbols:
            logger.warning("Unknown universe: %s", universe)
            return {
                "universe": universe,
                "total_scanned": 0,
                "qualified_trades": [],
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": 0,
            }

        logger.info("Scanning %d symbols from %s universe", len(symbols), universe)
        start_time = time.time()

        # Scan with rate limiting
        semaphore = asyncio.Semaphore(self._max_concurrent)
        qualified_trades = []

        async def scan_symbol(symbol: str) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    return await self._scan_single(symbol, period)
                except Exception as e:
                    logger.warning("Error scanning %s: %s", symbol, e)
                    return None

        # Parallel scanning
        results = await asyncio.gather(
            *[scan_symbol(sym) for sym in symbols],
            return_exceptions=False,
        )

        # Filter to qualified trades and sort by quality
        for result in results:
            if result and result.get("has_trades"):
                qualified_trades.append(result)

        # Sort by quality (HIGH > MEDIUM > LOW) then by R:R ratio
        quality_order = {"high": 0, "medium": 1, "low": 2}
        qualified_trades.sort(
            key=lambda x: (
                quality_order.get(
                    x.get("risk_quality", "low").lower(), 99
                ),
                -(x.get("risk_reward_ratio", 1.0)),
            )
        )

        duration = time.time() - start_time

        return {
            "universe": universe,
            "total_scanned": len(symbols),
            "qualified_trades": qualified_trades[:max_results],
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration,
        }

    async def _scan_single(self, symbol: str, period: str) -> dict[str, Any]:
        """Scan a single symbol for trade setup.

        Args:
            symbol: Ticker symbol.
            period: Data period.

        Returns:
            Trade plan result if qualified, None otherwise.
        """
        symbol = symbol.upper().strip()

        try:
            # Fetch data
            df = self._fetcher.fetch(symbol, period)

            # Calculate indicators
            df = calculate_all_indicators(df)

            # Detect signals
            signals = detect_all_signals(df)

            # Rank signals
            current = df.iloc[-1]
            market_data = {
                "price": float(current["Close"]),
                "change": float(current.get("Price_Change", 0)),
            }

            ranked_signals = rank_signals(
                signals=signals,
                symbol=symbol,
                market_data=market_data,
                use_ai=False,
            )

            # Get risk assessment
            result = self._risk_assessor.assess(df, ranked_signals, symbol)

            # Return qualified trades only
            if result.has_trades and result.trade_plans:
                plan = result.trade_plans[0]  # Return best plan
                return {
                    "symbol": symbol,
                    "entry_price": float(plan.entry_price),
                    "stop_price": float(plan.stop_price),
                    "target_price": float(plan.target_price),
                    "risk_reward_ratio": float(plan.risk_reward_ratio),
                    "risk_quality": plan.risk_quality.value,
                    "timeframe": plan.timeframe.value,
                    "bias": plan.bias.value,
                    "primary_signal": plan.primary_signal,
                    "has_trades": True,
                }

            return None

        except Exception as e:
            logger.debug("Error processing %s: %s", symbol, e)
            return None
