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
from .sector_mapping import get_sector, get_risk_level

logger = logging.getLogger(__name__)

# Stop loss percentages based on financial risk assessment
STOP_LOSS_RANGES = {
    "low": (2.0, 3.0),          # Blue-chip, stable companies
    "moderate": (3.0, 5.0),     # Established with some volatility
    "high": (5.0, 8.0),         # Growth, volatile, emerging
}


class PortfolioRiskAssessor:
    """Assess aggregate risk across portfolio positions."""

    def __init__(self):
        """Initialize portfolio risk assessor."""
        self._fetcher = create_data_fetcher(use_cache=True)
        self._risk_assessor = RiskAssessor()

    def _calculate_intelligent_stop(
        self, current_price: float, symbol: str, df: Any
    ) -> float:
        """Calculate intelligent stop loss based on financial risk assessment.

        Uses a smart approach:
        1. Get stock's risk level (blue-chip, established, growth)
        2. Calculate volatility from historical data
        3. Adjust stop based on sector and stock characteristics
        4. Range: 2-8% depending on risk

        Args:
            current_price: Current stock price.
            symbol: Stock ticker.
            df: Historical price dataframe.

        Returns:
            Stop loss price (below current price).
        """
        risk_level = get_risk_level(symbol)
        min_pct, max_pct = STOP_LOSS_RANGES[risk_level]

        # Calculate historical volatility (daily returns standard deviation)
        try:
            df_copy = df.copy()
            if "Close" in df_copy.columns:
                returns = df_copy["Close"].pct_change()
                volatility = returns.std() * 100  # Convert to percentage

                # Adjust stop based on volatility
                # Higher volatility = wider stop within the range
                if volatility > 0:
                    # Normalize volatility to 0-1 scale (2% daily vol = ~0.5)
                    vol_factor = min(volatility / 4.0, 1.0)
                    adjusted_stop_pct = min_pct + (max_pct - min_pct) * vol_factor
                else:
                    adjusted_stop_pct = min_pct
            else:
                adjusted_stop_pct = (min_pct + max_pct) / 2
        except Exception:
            # Fallback to middle of range if volatility calculation fails
            adjusted_stop_pct = (min_pct + max_pct) / 2

        # Cap at the min/max range
        adjusted_stop_pct = max(min_pct, min(adjusted_stop_pct, max_pct))

        stop_price = current_price * (1 - adjusted_stop_pct / 100)
        return stop_price

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

        # Organize positions by sector
        positions_by_sector = self._organize_by_sectors(position_risks)

        # Sector concentration and summaries
        sector_concentration = self._calculate_sector_concentration(
            position_risks, total_value
        )

        # Generate sector summaries with risk breakdown
        sector_summaries = self._generate_sector_summaries(
            positions_by_sector, sector_concentration
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
            "overall_risk_level": overall_risk_level,
            "timestamp": datetime.now().isoformat(),
            # Organized by 11 sectors
            "sectors": sector_summaries,
            "sector_concentration": sector_concentration,
            "all_positions": position_risks,  # Flat list for backward compatibility
            "hedge_suggestions": hedge_suggestions,
        }

    async def _assess_single_position(self, position: dict[str, Any], period: str = DEFAULT_PERIOD) -> dict[str, Any]:
        """Assess risk for a single position.

        Args:
            position: Position dict with symbol, shares, entry_price.
            period: Time period for analysis.

        Returns:
            Position risk assessment with intelligent stop losses.
        """
        symbol = position.get("symbol", "").upper()
        shares = position.get("shares", 0)
        entry_price = position.get("entry_price", 0)

        # Fetch current data
        df = self._fetcher.fetch(symbol, period)
        df = calculate_all_indicators(df)

        current = df.iloc[-1]
        current_price = float(current.get("Close", entry_price))

        # Calculate intelligent stop loss based on financial risk
        stop_price = self._calculate_intelligent_stop(current_price, symbol, df)

        # Get risk assessment for additional signals
        signals = detect_all_signals(df)
        market_data = {"price": current_price, "change": 0}
        ranked_signals = rank_signals(
            signals=signals,
            symbol=symbol,
            market_data=market_data,
            use_ai=False,
        )
        risk_result = self._risk_assessor.assess(df, ranked_signals, symbol)

        # Use current price as the entry price (current snapshot)
        current_value = current_price * shares
        entry_value = current_price * shares  # Use current as base
        unrealized_pnl = 0  # No PnL since entry = current
        unrealized_percent = 0

        max_loss_dollar = abs(current_price - stop_price) * shares
        max_loss_percent = (abs(current_price - stop_price) / current_price * 100) if current_price > 0 else 0

        risk_level = get_risk_level(symbol)

        return {
            "symbol": symbol,
            "shares": shares,
            "entry_price": current_price,  # Current price is the entry
            "current_price": current_price,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_percent": unrealized_percent,
            "stop_level": stop_price,
            "stop_loss_percent": max_loss_percent,
            "max_loss_dollar": max_loss_dollar,
            "max_loss_percent": max_loss_percent,
            "risk_level": risk_level,  # low, moderate, high
            "risk_quality": risk_result.risk_assessment.risk_quality.value if risk_result.risk_assessment else "low",
            "timeframe": risk_result.trade_plans[0].timeframe.value if risk_result.trade_plans else "swing",
            "sector": get_sector(symbol),
        }

    def _organize_by_sectors(
        self, positions: list[dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Organize positions by their sectors.

        Args:
            positions: List of position assessments.

        Returns:
            Dictionary mapping sector names to lists of positions.
        """
        sectors_map: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for pos in positions:
            sector = pos.get("sector", "Other")
            sectors_map[sector].append(pos)

        # Sort sectors in a logical order
        sector_order = [
            "Information Technology",
            "Healthcare",
            "Financials",
            "Energy",
            "Consumer Discretionary",
            "Consumer Staples",
            "Industrials",
            "Materials",
            "Communication Services",
            "Utilities",
            "Real Estate",
            "Other",
        ]

        # Return sorted dictionary
        return {
            sector: sectors_map[sector]
            for sector in sector_order
            if sector in sectors_map
        }

    def _generate_sector_summaries(
        self,
        positions_by_sector: dict[str, list[dict[str, Any]]],
        sector_concentration: dict[str, float],
    ) -> dict[str, dict[str, Any]]:
        """Generate comprehensive summaries for each sector.

        Args:
            positions_by_sector: Positions organized by sector.
            sector_concentration: Sector concentration percentages.

        Returns:
            Dictionary of sector summaries with aggregated metrics.
        """
        sector_summaries = {}

        for sector, positions in positions_by_sector.items():
            total_value = sum(p["current_value"] for p in positions)
            total_max_loss = sum(p["max_loss_dollar"] for p in positions)
            avg_stop_loss_pct = sum(p["stop_loss_percent"] for p in positions) / len(
                positions
            )

            # Count risk levels
            low_risk_count = sum(1 for p in positions if p["risk_level"] == "low")
            moderate_risk_count = sum(
                1 for p in positions if p["risk_level"] == "moderate"
            )
            high_risk_count = sum(1 for p in positions if p["risk_level"] == "high")

            # Get hedge ETF for this sector
            hedge_etf = self._get_sector_hedge_etf(sector)

            sector_summaries[sector] = {
                "total_value": total_value,
                "percent_of_portfolio": sector_concentration.get(sector, 0),
                "position_count": len(positions),
                "positions": positions,
                "metrics": {
                    "total_max_loss_dollar": total_max_loss,
                    "max_loss_percent_of_sector": (
                        (total_max_loss / total_value * 100) if total_value > 0 else 0
                    ),
                    "avg_stop_loss_percent": avg_stop_loss_pct,
                },
                "risk_distribution": {
                    "low_risk_count": low_risk_count,
                    "moderate_risk_count": moderate_risk_count,
                    "high_risk_count": high_risk_count,
                },
                "hedge_etf": hedge_etf,
            }

        return sector_summaries

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
