"""Morning summary generator for industry performance.

Generates daily market rotation insights and momentum narratives
based on 50-industry performance data.
"""

import logging
from typing import Optional
from datetime import datetime
from .performance_calculator import PerformanceCalculator

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """Generate morning market summaries from industry performance."""

    def __init__(self):
        """Initialize summary generator."""
        self._calculator = PerformanceCalculator()

    def generate_morning_summary(
        self,
        performances: list[dict],
        horizon: str = "1m",
    ) -> dict:
        """Generate morning summary JSON.

        Args:
            performances: List of cached industry performance dicts.
            horizon: Time horizon for analysis (default: 1 month).

        Returns:
            Morning summary dict:
            {
                "timestamp": ISO timestamp,
                "horizon": "1m",
                "top_performers": [...],  # Top 5
                "worst_performers": [...],  # Bottom 5
                "extremes": {
                    "highs": [...],  # 52-week highs
                    "lows": [...]   # 52-week lows
                },
                "narrative": "3-5 sentence market analysis",
                "metrics": {
                    "average_return": float,
                    "positive_count": int,
                    "negative_count": int,
                    "neutral_count": int,
                }
            }
        """
        logger.info("Generating morning summary for %d industries", len(performances))

        # Get top/bottom performers
        top_performers = self._calculator.get_best_performers(
            performances, horizon=horizon, top_n=5
        )
        worst_performers = self._calculator.get_worst_performers(
            performances, horizon=horizon, bottom_n=5
        )

        # Find 52-week extremes
        extremes = self._calculator.find_52week_extremes(performances)

        # Calculate metrics
        metrics = self._calculate_metrics(performances, horizon)

        # Generate narrative
        narrative = self._generate_narrative(
            top_performers,
            worst_performers,
            extremes,
            metrics,
            horizon,
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "horizon": horizon,
            "top_performers": top_performers,
            "worst_performers": worst_performers,
            "extremes": extremes,
            "narrative": narrative,
            "metrics": metrics,
        }

    def _calculate_metrics(
        self,
        performances: list[dict],
        horizon: str,
    ) -> dict:
        """Calculate summary metrics.

        Args:
            performances: Industry performance dicts.
            horizon: Time horizon.

        Returns:
            Metrics dict with average return and sentiment counts.
        """
        valid_returns = [
            p["returns"][horizon]
            for p in performances
            if p.get("returns", {}).get(horizon) is not None
        ]

        if not valid_returns:
            return {
                "average_return": 0.0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "total_industries": len(performances),
                "industries_with_data": 0,
            }

        average_return = round(sum(valid_returns) / len(valid_returns), 2)

        # Count sentiment distribution
        positive = sum(1 for r in valid_returns if r > 0.5)
        negative = sum(1 for r in valid_returns if r < -0.5)
        neutral = len(valid_returns) - positive - negative

        return {
            "average_return": average_return,
            "positive_count": positive,
            "negative_count": negative,
            "neutral_count": neutral,
            "total_industries": len(performances),
            "industries_with_data": len(valid_returns),
        }

    def _generate_narrative(
        self,
        top_performers: list[dict],
        worst_performers: list[dict],
        extremes: dict,
        metrics: dict,
        horizon: str,
    ) -> str:
        """Generate 3-5 sentence market narrative.

        Args:
            top_performers: Top 5 best performers.
            worst_performers: Bottom 5 worst performers.
            extremes: 52-week highs/lows dict.
            metrics: Summary metrics.
            horizon: Time horizon.

        Returns:
            Natural language market analysis.
        """
        sentences = []

        # Overall market sentiment
        avg_return = metrics["average_return"]
        pos_count = metrics["positive_count"]
        neg_count = metrics["negative_count"]
        total = metrics["industries_with_data"]

        if avg_return > 1.0:
            sentiment = "strong bullish momentum"
        elif avg_return > 0.3:
            sentiment = "modest gains"
        elif avg_return > -0.3:
            sentiment = "mixed performance"
        elif avg_return > -1.0:
            sentiment = "moderate weakness"
        else:
            sentiment = "significant selling pressure"

        sentences.append(
            f"The US economy is showing {sentiment} over the past {self._horizon_label(horizon)}, "
            f"with an average industry return of {avg_return:+.1f}%."
        )

        # Winners and losers
        if pos_count > neg_count * 1.5:
            sentences.append(
                f"Broad-based strength is evident with {pos_count} of {total} industries positive, "
                f"indicating healthy market breadth."
            )
        elif neg_count > pos_count * 1.5:
            sentences.append(
                f"Weakness is widespread with {neg_count} of {total} industries declining, "
                f"suggesting defensive positioning may be warranted."
            )
        else:
            sentences.append(
                f"Market breadth is balanced with {pos_count} industries advancing and "
                f"{neg_count} declining, reflecting sector rotation rather than directional trend."
            )

        # Top sector rotation
        if top_performers:
            leaders = [p["industry"] for p in top_performers[:3]]
            leaders_str = ", ".join(leaders)
            sentences.append(
                f"Leadership is concentrated in {leaders_str}, "
                f"with the top performer up {top_performers[0]['returns'][horizon]:+.1f}%."
            )

        # Worst sectors
        if worst_performers:
            laggards = [p["industry"] for p in worst_performers[:3]]
            laggards_str = ", ".join(laggards)
            sentences.append(
                f"Underperformers include {laggards_str}, "
                f"with the weakest sector down {worst_performers[0]['returns'][horizon]:.1f}%."
            )

        # 52-week extremes
        highs = extremes.get("highs", [])
        lows = extremes.get("lows", [])

        if highs:
            high_names = [h["industry"] for h in highs[:2]]
            sentences.append(
                f"Notable momentum: {', '.join(high_names)} reaching 52-week highs, "
                f"signaling sustained uptrends."
            )
        elif lows:
            low_names = [l["industry"] for l in lows[:2]]
            sentences.append(
                f"Caution warranted in {', '.join(low_names)}, which are testing 52-week lows."
            )

        # Combine into narrative (max 5 sentences)
        return " ".join(sentences[:5])

    def _horizon_label(self, horizon: str) -> str:
        """Convert horizon key to human-readable label.

        Args:
            horizon: Horizon key (e.g., '1m', '3m').

        Returns:
            Human-readable label.
        """
        labels = {
            "2w": "two weeks",
            "1m": "month",
            "2m": "two months",
            "3m": "quarter",
            "6m": "six months",
            "52w": "year",
            "2y": "two years",
            "3y": "three years",
            "5y": "five years",
            "10y": "decade",
        }
        return labels.get(horizon, horizon)

    def generate_email_summary(
        self,
        performances: list[dict],
        horizon: str = "1m",
    ) -> str:
        """Generate plain-text email summary.

        Args:
            performances: Industry performance dicts.
            horizon: Time horizon.

        Returns:
            Multi-line plain-text email summary.
        """
        summary = self.generate_morning_summary(performances, horizon)

        lines = [
            "=" * 60,
            "MORNING INDUSTRY PERFORMANCE BRIEF",
            f"Generated: {summary['timestamp']}",
            f"Time Horizon: {self._horizon_label(horizon).title()}",
            "=" * 60,
            "",
            "MARKET NARRATIVE",
            "-" * 60,
            summary["narrative"],
            "",
            "TOP 5 PERFORMERS",
            "-" * 60,
        ]

        for i, perf in enumerate(summary["top_performers"], 1):
            ret = perf["returns"][horizon]
            lines.append(
                f"{i}. {perf['industry']:<25} ({perf['etf']:<6}) {ret:+6.2f}%"
            )

        lines.extend([
            "",
            "BOTTOM 5 PERFORMERS",
            "-" * 60,
        ])

        for i, perf in enumerate(summary["worst_performers"], 1):
            ret = perf["returns"][horizon]
            lines.append(
                f"{i}. {perf['industry']:<25} ({perf['etf']:<6}) {ret:+6.2f}%"
            )

        # Add extremes if any
        if summary["extremes"]["highs"]:
            lines.extend([
                "",
                "52-WEEK HIGHS",
                "-" * 60,
            ])
            for h in summary["extremes"]["highs"]:
                ret = h["returns"]["52w"]
                lines.append(f"  {h['industry']:<25} ({h['etf']:<6}) {ret:+6.2f}%")

        if summary["extremes"]["lows"]:
            lines.extend([
                "",
                "52-WEEK LOWS",
                "-" * 60,
            ])
            for l in summary["extremes"]["lows"]:
                ret = l["returns"]["52w"]
                lines.append(f"  {l['industry']:<25} ({l['etf']:<6}) {ret:+6.2f}%")

        lines.extend([
            "",
            "MARKET METRICS",
            "-" * 60,
            f"Average Return: {summary['metrics']['average_return']:+.2f}%",
            f"Industries Advancing: {summary['metrics']['positive_count']}",
            f"Industries Declining: {summary['metrics']['negative_count']}",
            f"Industries Neutral: {summary['metrics']['neutral_count']}",
            "=" * 60,
        ])

        return "\n".join(lines)
