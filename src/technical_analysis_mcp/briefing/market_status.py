"""Market status and futures tracking."""

from datetime import datetime, time, timedelta, timezone
from typing import Any

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # type: ignore


class MarketStatusChecker:
    """Check market status, futures, and volatility."""

    MARKET_TIMEZONES = {
        "US": "America/New_York",
        "EU": "Europe/London",
        "ASIA": "Asia/Tokyo",
    }

    MARKET_HOURS = {
        "US": (9, 30, 16, 0),  # 9:30 AM - 4:00 PM ET
        "EU": (8, 0, 16, 30),  # 8:00 AM - 4:30 PM GMT
        "ASIA": (9, 0, 15, 0),  # 9:00 AM - 3:00 PM JST
    }

    def __init__(self):
        """Initialize market status checker."""
        pass

    def get_market_status(self, market_region: str = "US") -> dict[str, Any]:
        """Get current market status.

        Args:
            market_region: Market region (US, EU, ASIA).

        Returns:
            Market status dict with open/closed status, futures, VIX.
        """
        # Get timezone-aware current time in market region
        tz_name = self.MARKET_TIMEZONES.get(market_region, "America/New_York")
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)

        # Get market hours for region
        market_hours = self.MARKET_HOURS.get(market_region, (9, 30, 16, 0))
        market_open = time(market_hours[0], market_hours[1])
        market_close = time(market_hours[2], market_hours[3])
        is_weekday = now.weekday() < 5

        # Check if market is open
        current_time = now.time()
        is_open = is_weekday and market_open <= current_time <= market_close

        if is_open:
            market_status = "OPEN"
            market_close_dt = datetime.combine(now.date(), market_close, tzinfo=tz)
            remaining = market_close_dt - now
            hours_remaining = remaining.total_seconds() / 3600
            status_text = f"{hours_remaining:.1f} hours remaining"
        elif is_weekday and current_time < market_open:
            market_status = "PRE_MARKET"
            market_open_dt = datetime.combine(now.date(), market_open, tzinfo=tz)
            remaining = market_open_dt - now
            hours_remaining = remaining.total_seconds() / 3600
            status_text = f"Opens in {hours_remaining:.1f} hours"
        elif is_weekday and current_time > market_close:
            market_status = "AFTER_HOURS"
            next_open_dt = datetime.combine(now.date() + timedelta(days=1), market_open, tzinfo=tz)
            remaining = next_open_dt - now
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
