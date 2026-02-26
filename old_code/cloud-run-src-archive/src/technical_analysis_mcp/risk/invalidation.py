"""Structure-based invalidation level detection.

Identifies price levels that would invalidate the trade thesis
(support breaks for bullish, resistance breaks for bearish).
"""

import pandas as pd
from .models import InvalidationLevel
from .protocols import InvalidationDetector


class StructureInvalidationDetector:
    """Detects structure-based invalidation levels."""

    def detect(
        self,
        df: pd.DataFrame,
        bias: str,
    ) -> InvalidationLevel | None:
        """Detect key price levels that would invalidate trade thesis.

        For bullish trades: Invalidation is a break below key support
        For bearish trades: Invalidation is a break above key resistance

        Args:
            df: DataFrame with OHLC and moving average data
            bias: Trade bias ("bullish" or "bearish")

        Returns:
            InvalidationLevel if detectable, None otherwise
        """
        if df.empty or len(df) < 10:
            return None

        current = df.iloc[-1]
        current_price = float(current["Close"])

        invalidation_candidates = []

        # For bullish trades, invalidation is below key support
        if bias == "bullish":
            # Primary support: 20 SMA
            if "SMA_20" in df.columns:
                sma20 = float(current["SMA_20"])
                if current_price > sma20:
                    invalidation_candidates.append(
                        InvalidationLevel(
                            price=sma20,
                            type="ma_support_break",
                            description="Price breaking below 20 SMA support",
                        )
                    )

            # Secondary support: 50 SMA
            if "SMA_50" in df.columns:
                sma50 = float(current["SMA_50"])
                if current_price > sma50:
                    invalidation_candidates.append(
                        InvalidationLevel(
                            price=sma50,
                            type="ma_support_break",
                            description="Price breaking below 50 SMA support",
                        )
                    )

            # Recent swing low (last 10 bars)
            recent_low = float(df["Low"].tail(10).min())
            if current_price > recent_low:
                invalidation_candidates.append(
                    InvalidationLevel(
                        price=recent_low,
                        type="support_break",
                        description="Price breaking recent swing low",
                    )
                )

        # For bearish trades, invalidation is above key resistance
        else:  # bearish
            # Primary resistance: 20 SMA
            if "SMA_20" in df.columns:
                sma20 = float(current["SMA_20"])
                if current_price < sma20:
                    invalidation_candidates.append(
                        InvalidationLevel(
                            price=sma20,
                            type="ma_resistance_break",
                            description="Price breaking above 20 SMA resistance",
                        )
                    )

            # Secondary resistance: 50 SMA
            if "SMA_50" in df.columns:
                sma50 = float(current["SMA_50"])
                if current_price < sma50:
                    invalidation_candidates.append(
                        InvalidationLevel(
                            price=sma50,
                            type="ma_resistance_break",
                            description="Price breaking above 50 SMA resistance",
                        )
                    )

            # Recent swing high (last 10 bars)
            recent_high = float(df["High"].tail(10).max())
            if current_price < recent_high:
                invalidation_candidates.append(
                    InvalidationLevel(
                        price=recent_high,
                        type="resistance_break",
                        description="Price breaking recent swing high",
                    )
                )

        if not invalidation_candidates:
            return None

        # Return closest invalidation level to current price
        invalidation_candidates.sort(
            key=lambda x: abs(x.price - current_price)
        )

        return invalidation_candidates[0]
