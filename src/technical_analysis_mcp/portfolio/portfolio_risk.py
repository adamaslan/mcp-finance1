"""Portfolio risk assessment."""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

from ..config import DEFAULT_PERIOD
from ..data import create_data_fetcher
from ..indicators import calculate_all_indicators
from ..ranking import rank_signals
from ..risk import RiskAssessor
from ..signals import detect_all_signals
from .sector_mapping import get_sector

logger = logging.getLogger(__name__)


class PortfolioRiskAssessor:
    """Assess aggregate risk across portfolio positions."""

    def __init__(self):
        """Initialize portfolio risk assessor."""
        self._fetcher = create_data_fetcher(use_cache=True)
        self._risk_assessor = RiskAssessor()

    async def assess_positions(
        self,
        positions: list[dict[str, Any]],
        period: str = DEFAULT_PERIOD,
    ) -> dict[str, Any]:
        """Assess aggregate risk across positions.

        Args:
            positions: List of position dicts with symbol, shares, entry_price.
            period: Time period for analysis.

        Returns:
            Portfolio risk assessment with positions, aggregate metrics.
        """
        if not positions:
            return {
                "total_value": 0,
                "total_max_loss": 0,
                "risk_percent_of_portfolio": 0,
                "positions": [],
                "sector_concentration": {},
                "correlation_matrix": None,
                "overall_risk_level": "LOW",
                "hedge_suggestions": [],
                "timestamp": datetime.now().isoformat(),
            }

        logger.info("Assessing %d positions (period: %s)", len(positions), period)

        # Assess each position in parallel
        semaphore = asyncio.Semaphore(5)
        position_risks = []

        async def assess_position(pos: dict[str, Any]) -> dict[str, Any] | None:
            async with semaphore:
                try:
                    return await self._assess_single_position(pos, period=period)
                except Exception as e:
                    logger.warning("Error assessing %s: %s", pos.get("symbol"), e)
                    return None

        results = await asyncio.gather(
            *[assess_position(pos) for pos in positions],
            return_exceptions=False,
        )

        position_risks = [r for r in results if r is not None]

        if not position_risks:
            return {
                "total_value": 0,
                "total_max_loss": 0,
                "risk_percent_of_portfolio": 0,
                "positions": [],
                "sector_concentration": {},
                "correlation_matrix": None,
                "overall_risk_level": "LOW",
                "hedge_suggestions": [],
                "timestamp": datetime.now().isoformat(),
            }

        # Calculate aggregate metrics
        total_value = sum(p["current_value"] for p in position_risks)
        total_max_loss = sum(p["max_loss_dollar"] for p in position_risks)

        # Sector concentration
        sector_concentration = self._calculate_sector_concentration(
            position_risks, total_value
        )

        # Hedge suggestions
        hedge_suggestions = self._generate_hedge_suggestions(
            position_risks, sector_concentration
        )

        # Overall risk level
        risk_percent = (total_max_loss / total_value * 100) if total_value > 0 else 0
        overall_risk_level = self._assess_overall_risk(risk_percent, position_risks)

        return {
            "total_value": total_value,
            "total_max_loss": total_max_loss,
            "risk_percent_of_portfolio": risk_percent,
            "positions": position_risks,
            "sector_concentration": sector_concentration,
            "correlation_matrix": None,  # Simplified: skip correlation for now
            "overall_risk_level": overall_risk_level,
            "hedge_suggestions": hedge_suggestions,
            "timestamp": datetime.now().isoformat(),
        }

    async def _assess_single_position(self, position: dict[str, Any], period: str = DEFAULT_PERIOD) -> dict[str, Any]:
        """Assess risk for a single position.

        Args:
            position: Position dict with symbol, shares, entry_price.
            period: Time period for analysis.

        Returns:
            Position risk assessment.
        """
        symbol = position.get("symbol", "").upper()
        shares = position.get("shares", 0)
        entry_price = position.get("entry_price", 0)

        # Fetch current data
        df = self._fetcher.fetch(symbol, period)
        df = calculate_all_indicators(df)

        current = df.iloc[-1]
        current_price = float(current.get("Close", entry_price))

        # Get risk assessment
        signals = detect_all_signals(df)
        market_data = {"price": current_price, "change": 0}
        ranked_signals = rank_signals(
            signals=signals,
            symbol=symbol,
            market_data=market_data,
            use_ai=False,
        )
        risk_result = self._risk_assessor.assess(df, ranked_signals, symbol)

        # Extract stop level from risk assessment
        if risk_result.risk_assessment and risk_result.risk_assessment.stop:
            stop_price = float(risk_result.risk_assessment.stop.price)
        else:
            stop_price = entry_price * 0.95  # Default 5% stop

        # Calculate position metrics
        current_value = current_price * shares
        entry_value = entry_price * shares
        unrealized_pnl = current_value - entry_value
        unrealized_percent = (unrealized_pnl / entry_value * 100) if entry_value > 0 else 0

        max_loss_dollar = abs(current_price - stop_price) * shares
        max_loss_percent = (abs(current_price - stop_price) / current_price * 100) if current_price > 0 else 0

        return {
            "symbol": symbol,
            "shares": shares,
            "entry_price": entry_price,
            "current_price": current_price,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_percent": unrealized_percent,
            "stop_level": stop_price,
            "max_loss_dollar": max_loss_dollar,
            "max_loss_percent": max_loss_percent,
            "risk_quality": risk_result.risk_assessment.risk_quality.value if risk_result.risk_assessment else "low",
            "timeframe": risk_result.trade_plans[0].timeframe.value if risk_result.trade_plans else "swing",
            "sector": get_sector(symbol),
        }

    def _calculate_sector_concentration(
        self,
        positions: list[dict[str, Any]],
        total_value: float,
    ) -> dict[str, float]:
        """Calculate sector concentration.

        Args:
            positions: List of position assessments.
            total_value: Total portfolio value.

        Returns:
            Sector concentration as percentage of portfolio.
        """
        sector_values: defaultdict[str, float] = defaultdict(float)

        for pos in positions:
            sector = pos.get("sector", "Other")
            sector_values[sector] += pos.get("current_value", 0)

        if total_value <= 0:
            return {}

        return {
            sector: (value / total_value * 100)
            for sector, value in sector_values.items()
        }

    def _generate_hedge_suggestions(
        self,
        positions: list[dict[str, Any]],
        sector_concentration: dict[str, float],
    ) -> list[str]:
        """Generate hedge suggestions based on portfolio.

        Args:
            positions: List of position assessments.
            sector_concentration: Sector concentration map.

        Returns:
            List of hedge suggestions.
        """
        suggestions = []

        # Check for high sector concentration
        for sector, pct in sector_concentration.items():
            if pct > 40:
                etf = self._get_sector_hedge_etf(sector)
                if etf:
                    suggestions.append(
                        f"Add {etf} put to hedge {sector} exposure ({pct:.1f}%)"
                    )

        # Check for positions with low quality
        low_quality_positions = [
            p for p in positions if p.get("risk_quality") == "low"
        ]
        if len(low_quality_positions) >= 2:
            suggestions.append(
                f"Review stop levels for {len(low_quality_positions)} low-quality positions"
            )

        return suggestions

    def _get_sector_hedge_etf(self, sector: str) -> str | None:
        """Get hedge ETF for a sector.

        Args:
            sector: Sector name.

        Returns:
            ETF ticker for hedging, or None.
        """
        sector_etf_map = {
            "Technology": "QQQ",
            "Healthcare": "XBI",
            "Financials": "XLF",
            "Energy": "XLE",
            "Consumer Discretionary": "XLY",
            "Consumer Staples": "XLP",
            "Industrials": "XLI",
            "Materials": "XLB",
            "Utilities": "XLU",
            "Real Estate": "XLRE",
            "Communication Services": "XLC",
        }
        return sector_etf_map.get(sector)

    def _assess_overall_risk(
        self,
        risk_percent: float,
        positions: list[dict[str, Any]],
    ) -> str:
        """Assess overall portfolio risk level.

        Args:
            risk_percent: Risk as % of portfolio.
            positions: List of position assessments.

        Returns:
            Risk level: LOW, MEDIUM, HIGH, CRITICAL.
        """
        if risk_percent > 20:
            return "CRITICAL"
        elif risk_percent > 15:
            return "HIGH"
        elif risk_percent > 10:
            return "MEDIUM"
        else:
            return "LOW"
