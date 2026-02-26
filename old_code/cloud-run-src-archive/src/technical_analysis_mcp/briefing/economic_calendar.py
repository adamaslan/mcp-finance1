"""Economic calendar and events."""

from typing import Any


class EconomicCalendar:
    """Fetch and parse economic events."""

    def __init__(self):
        """Initialize economic calendar."""
        pass

    def get_todays_events(self) -> list[dict[str, Any]]:
        """Get economic events scheduled for today.

        Returns:
            List of economic event dictionaries.
        """
        # Mock data - in production would fetch from API
        return [
            {
                "timestamp": "08:30",
                "event_name": "CPI Year-over-Year",
                "importance": "HIGH",
                "forecast": "3.2%",
                "previous": "3.1%",
                "actual": None,
            },
            {
                "timestamp": "10:00",
                "event_name": "Consumer Sentiment Index",
                "importance": "MEDIUM",
                "forecast": "72.0",
                "previous": "71.5",
                "actual": None,
            },
            {
                "timestamp": "14:00",
                "event_name": "Fed Speaker (Inflation Commentary)",
                "importance": "MEDIUM",
                "forecast": None,
                "previous": None,
                "actual": None,
            },
        ]

    def get_high_importance_events(self) -> list[dict[str, Any]]:
        """Get only high importance events.

        Returns:
            List of high importance events.
        """
        return [e for e in self.get_todays_events() if e.get("importance") == "HIGH"]

    def get_medium_importance_events(self) -> list[dict[str, Any]]:
        """Get only medium importance events.

        Returns:
            List of medium importance events.
        """
        return [e for e in self.get_todays_events() if e.get("importance") == "MEDIUM"]
