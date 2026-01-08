"""Market status and futures tracking."""

from datetime import datetime, time, timedelta
from typing import Any


class MarketStatusChecker:
    """Check market status, futures, and volatility."""

    def __init__(self):
        """Initialize market status checker."""
        pass

    def get_market_status(self) -> dict[str, Any]:
        """Get current market status.

        Returns:
            Market status dict with open/closed status, futures, VIX.
        """
        now = datetime.now()
        market_open = time(9, 30)
        market_close = time(16, 0)
        is_weekday = now.weekday() < 5

        # Check if market is open
        current_time = now.time()
        is_open = is_weekday and market_open <= current_time <= market_close

        if is_open:
            market_status = "OPEN"
            remaining = datetime.combine(now.date(), market_close) - now
            hours_remaining = remaining.total_seconds() / 3600
            status_text = f"{hours_remaining:.1f} hours remaining"
        elif is_weekday and current_time < market_open:
            market_status = "PRE_MARKET"
            pre_market_close = datetime.combine(now.date(), market_open)
            remaining = pre_market_close - now
            hours_remaining = remaining.total_seconds() / 3600
            status_text = f"Opens in {hours_remaining:.1f} hours"
        elif is_weekday and current_time > market_close:
            market_status = "AFTER_HOURS"
            next_open = datetime.combine(now.date() + timedelta(days=1), market_open)
            remaining = next_open - now
            hours_remaining = remaining.total_seconds() / 3600
            status_text = f"Reopens in {hours_remaining:.1f} hours"
        else:
            market_status = "CLOSED"
            status_text = "Market closed (weekend)"

        return {
            "market_status": market_status,
            "current_time": now.isoformat(),
            "market_hours_remaining": status_text,
            "previous_close": 485.50,  # Mock data
            "futures_es": {
                "symbol": "ES",
                "last_price": 487.25,
                "change": 1.75,
                "change_percent": 0.36,
            },
            "futures_nq": {
                "symbol": "NQ",
                "last_price": 19450.00,
                "change": 85.00,
                "change_percent": 0.44,
            },
            "vix": 14.25,
            "put_call_ratio": 0.85,
            "market_sentiment": self._assess_sentiment(487.25, 485.50, 14.25),
        }

    def _assess_sentiment(self, futures: float, previous: float, vix: float) -> str:
        """Assess market sentiment.

        Args:
            futures: Current futures level.
            previous: Previous close.
            vix: VIX level.

        Returns:
            Sentiment: BULLISH, NEUTRAL, BEARISH.
        """
        change_pct = (futures - previous) / previous * 100

        if change_pct > 0.5 and vix < 15:
            return "BULLISH"
        elif change_pct < -0.5 or vix > 20:
            return "BEARISH"
        else:
            return "NEUTRAL"
