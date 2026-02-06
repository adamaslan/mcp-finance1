"""Price override system for what-if analysis.

Allows users to test trading strategies with hypothetical prices without
modifying the actual market data. Useful for scenario planning and backtesting.
"""

import logging
from typing import Any, Optional
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PriceOverrideManager:
    """Manages price overrides for what-if analysis."""

    def __init__(self):
        self._overrides: dict[str, float] = {}

    def set_override(self, symbol: str, price: float) -> None:
        """Set price override for a symbol.

        Args:
            symbol: Ticker symbol
            price: Override price

        Raises:
            ValueError: If price is non-positive
        """
        if price <= 0:
            raise ValueError(f"Price must be positive, got {price}")

        symbol = symbol.upper().strip()
        self._overrides[symbol] = price
        logger.info(f"Price override set: {symbol} = ${price:.2f}")

    def get_override(self, symbol: str) -> Optional[float]:
        """Get price override for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Override price or None if no override exists
        """
        return self._overrides.get(symbol.upper().strip())

    def clear_override(self, symbol: str) -> None:
        """Clear price override for a symbol.

        Args:
            symbol: Ticker symbol
        """
        symbol = symbol.upper().strip()
        if symbol in self._overrides:
            del self._overrides[symbol]
            logger.info(f"Price override cleared: {symbol}")

    def clear_all(self) -> None:
        """Clear all price overrides."""
        count = len(self._overrides)
        self._overrides.clear()
        logger.info(f"All price overrides cleared: {count} symbols")

    def apply_override(
        self,
        df: pd.DataFrame,
        symbol: str,
        price_override: Optional[float] = None,
    ) -> pd.DataFrame:
        """Apply price override to the last row of dataframe.

        Creates a synthetic current price by modifying the last row.
        Maintains relative relationships between OHLC values.

        Args:
            df: OHLC DataFrame with price data
            symbol: Ticker symbol
            price_override: Override price (uses stored override if None)

        Returns:
            Modified DataFrame with overridden last row

        Note:
            This creates a COPY of the DataFrame to avoid modifying the original.
            The override affects only the last row (current price).
        """
        # Use explicit override or check stored overrides
        override_price = price_override or self.get_override(symbol)

        if override_price is None:
            return df

        if len(df) == 0:
            logger.warning(f"Cannot apply override to empty DataFrame for {symbol}")
            return df

        # Create copy to avoid modifying original
        df = df.copy()

        # Get last row
        last_idx = df.index[-1]
        original_close = df.loc[last_idx, "Close"]

        if original_close <= 0:
            logger.warning(
                f"Invalid original close price {original_close} for {symbol}"
            )
            return df

        # Calculate price change ratio
        ratio = override_price / original_close

        # Apply override to OHLC maintaining relative relationships
        df.loc[last_idx, "Close"] = override_price
        df.loc[last_idx, "Open"] = df.loc[last_idx, "Open"] * ratio
        df.loc[last_idx, "High"] = max(
            df.loc[last_idx, "High"] * ratio,
            override_price,  # Ensure High >= Close
        )
        df.loc[last_idx, "Low"] = min(
            df.loc[last_idx, "Low"] * ratio,
            override_price,  # Ensure Low <= Close
        )

        # Recalculate derived values if they exist
        if "Price_Change" in df.columns and len(df) > 1:
            prev_close = df.iloc[-2]["Close"]
            df.loc[last_idx, "Price_Change"] = override_price - prev_close
            df.loc[last_idx, "Price_Change_Pct"] = (
                (override_price - prev_close) / prev_close * 100
            )

        logger.info(
            f"Price override applied: {symbol} ${original_close:.2f} → ${override_price:.2f} "
            f"({(ratio - 1) * 100:.1f}%)"
        )

        return df

    def get_override_info(self, symbol: str) -> Optional[dict[str, Any]]:
        """Get information about price override for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with override information or None
        """
        override = self.get_override(symbol)
        if override is None:
            return None

        return {
            "symbol": symbol.upper().strip(),
            "override_price": override,
            "override_active": True,
        }

    def list_all_overrides(self) -> dict[str, float]:
        """List all active price overrides.

        Returns:
            Dictionary mapping symbols to override prices
        """
        return self._overrides.copy()


# Global singleton
_price_override_manager = PriceOverrideManager()


def get_price_override_manager() -> PriceOverrideManager:
    """Get the global price override manager.

    Returns:
        PriceOverrideManager instance
    """
    return _price_override_manager
