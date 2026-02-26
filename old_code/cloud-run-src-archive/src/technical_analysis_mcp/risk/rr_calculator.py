"""Risk-to-reward calculation.

Calculates R:R ratio from entry, stop, and target prices.
Determines if the risk/reward profile is favorable.
"""

from .models import RiskReward, StopLevel, TargetLevel
from ..config import MIN_RR_RATIO


class DefaultRRCalculator:
    """Calculates risk-to-reward ratio."""

    def __init__(self, min_rr: float = MIN_RR_RATIO):
        """Initialize R:R calculator.

        Args:
            min_rr: Minimum acceptable R:R ratio
        """
        self._min_rr = min_rr

    def calculate(
        self,
        entry_price: float,
        stop_price: float,
        target_price: float,
    ) -> RiskReward:
        """Calculate R:R ratio and assess favorability.

        Args:
            entry_price: Entry price for the trade
            stop_price: Stop-loss price
            target_price: Profit target price

        Returns:
            RiskReward with ratio and favorability assessment
        """
        risk_amount = abs(entry_price - stop_price)
        reward_amount = abs(target_price - entry_price)

        # Avoid division by zero
        if risk_amount <= 0:
            ratio = 0.0
        else:
            ratio = reward_amount / risk_amount

        is_favorable = ratio >= self._min_rr

        return RiskReward(
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            ratio=ratio,
            is_favorable=is_favorable,
        )
