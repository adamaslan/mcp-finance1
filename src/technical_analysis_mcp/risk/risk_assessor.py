"""Main risk assessment orchestrator.

Coordinates all risk assessment components to perform complete risk evaluation
and generate trade plans or suppression reasons.
"""

from typing import Any
import pandas as pd
from .models import (
    RiskAnalysisResult,
    RiskAssessment,
    TradePlan,
    RiskMetrics,
    RiskQuality,
    Bias,
)
from .volatility_regime import ATRVolatilityClassifier
from .timeframe_rules import DefaultTimeframeSelector
from .stop_distance import ATRStopCalculator
from .invalidation import StructureInvalidationDetector
from .rr_calculator import DefaultRRCalculator
from .suppression import DefaultSuppressionEvaluator
from .option_rules import DefaultVehicleSelector
from ..config import (
    ADX_TRENDING_THRESHOLD,
    PREFERRED_RR_RATIO,
)


class RiskAssessor:
    """Orchestrates complete risk assessment pipeline."""

    def __init__(
        self,
        volatility_classifier: Any | None = None,
        timeframe_selector: Any | None = None,
        stop_calculator: Any | None = None,
        invalidation_detector: Any | None = None,
        suppression_evaluator: Any | None = None,
        vehicle_selector: Any | None = None,
    ):
        """Initialize risk assessor with component dependencies.

        All components use dependency injection for testability.
        Defaults are provided if not supplied.

        Args:
            volatility_classifier: VolatilityClassifier implementation
            timeframe_selector: TimeframeSelector implementation
            stop_calculator: StopCalculator implementation
            invalidation_detector: InvalidationDetector implementation
            suppression_evaluator: SuppressionEvaluator implementation
            vehicle_selector: VehicleSelector implementation
        """
        self._volatility = (
            volatility_classifier or ATRVolatilityClassifier()
        )
        self._timeframe = timeframe_selector or DefaultTimeframeSelector()
        self._stop = stop_calculator or ATRStopCalculator()
        self._invalidation = (
            invalidation_detector or StructureInvalidationDetector()
        )
        self._suppression = (
            suppression_evaluator or DefaultSuppressionEvaluator()
        )
        self._vehicle = vehicle_selector or DefaultVehicleSelector()
        self._rr = DefaultRRCalculator()

    def assess(
        self,
        df: pd.DataFrame,
        signals: list[Any],
        symbol: str,
    ) -> RiskAnalysisResult:
        """Perform complete risk assessment and generate trade plans.

        Pipeline:
        1. Classify volatility regime
        2. Calculate risk metrics (ATR, ADX, trend, etc.)
        3. Determine trade bias from signals
        4. Select trading timeframe
        5. Calculate stop level
        6. Detect invalidation level
        7. Calculate target and R:R
        8. Create risk assessment
        9. Evaluate suppressions
        10. Build trade plan(s) or return suppression reasons

        Args:
            df: DataFrame with indicators calculated
            signals: Ranked signals from detection phase
            symbol: Ticker symbol

        Returns:
            RiskAnalysisResult with trade plans or suppression reasons
        """
        if df.empty:
            # Return error state
            return self._error_result(symbol, "Empty DataFrame provided")

        current = df.iloc[-1]
        price = float(current.get("Close", 0))
        timestamp = pd.Timestamp.utcnow().isoformat()

        if price <= 0:
            return self._error_result(symbol, "Invalid price data")

        # Step 1: Classify volatility
        volatility_regime = self._volatility.classify(df)

        # Step 2: Calculate risk metrics
        atr = float(current.get("ATR", price * 0.02))
        adx = float(current.get("ADX", 25))
        is_trending = adx >= ADX_TRENDING_THRESHOLD

        metrics = RiskMetrics(
            atr=atr,
            atr_percent=(atr / price) * 100 if price > 0 else 0,
            volatility_regime=volatility_regime,
            adx=adx,
            is_trending=is_trending,
            bb_width_percent=(
                float(current.get("BB_Width", 0) / price * 100)
                if price > 0
                else 0
            ),
            volume_ratio=(
                float(current.get("Volume", 1) / current.get("Volume_MA_20", 1))
                if current.get("Volume_MA_20", 0) > 0
                else 1.0
            ),
        )

        # Step 3: Determine bias from signals
        bias = self._determine_bias(signals)

        # Step 4: Select timeframe
        timeframe = self._timeframe.select(volatility_regime, adx, signals)

        # Step 5: Calculate stop level
        stop = self._stop.calculate(df, bias.value, timeframe)

        # Step 6: Detect invalidation level
        invalidation = self._invalidation.detect(df, bias.value)

        # Step 7: Calculate target and R:R
        target = self._calculate_target(df, bias, stop, metrics)
        risk_reward = self._rr.calculate(price, stop.price, target.price)

        # Step 8: Create assessment
        assessment = RiskAssessment(
            symbol=symbol,
            timestamp=timestamp,
            current_price=price,
            metrics=metrics,
            stop=stop,
            target=target,
            invalidation=invalidation,
            risk_reward=risk_reward,
            is_qualified=True,  # Will be updated after suppression
            risk_quality=self._assess_quality(risk_reward, metrics),
            suppressions=(),
        )

        # Step 9: Evaluate suppressions
        suppressions = self._suppression.evaluate(assessment, signals)

        # Step 10: Generate output
        if suppressions:
            # Suppressed - no trade plans
            return RiskAnalysisResult(
                symbol=symbol,
                timestamp=timestamp,
                trade_plans=(),
                has_trades=False,
                primary_suppression=suppressions[0] if suppressions else None,
                all_suppressions=suppressions,
                risk_assessment=RiskAssessment(
                    **{
                        **assessment.model_dump(),
                        "is_qualified": False,
                        "suppressions": suppressions,
                    }
                ),
                legacy_signals=self._format_legacy_signals(signals),
            )

        # Not suppressed - create trade plan
        expected_move = (
            abs(target.price - price) / price * 100 if price > 0 else 0
        )
        vehicle, vehicle_notes = self._vehicle.select(
            timeframe, volatility_regime, bias.value, expected_move
        )

        # Extract vehicle notes from suggestions dict if present
        vehicle_notes_str = None
        if isinstance(vehicle_notes, dict):
            vehicle_notes_str = vehicle_notes.get("reasoning", None)
        elif isinstance(vehicle_notes, str):
            vehicle_notes_str = vehicle_notes

        trade_plan = TradePlan(
            symbol=symbol,
            timestamp=timestamp,
            timeframe=timeframe,
            bias=bias,
            risk_quality=assessment.risk_quality,
            entry_price=price,
            stop_price=stop.price,
            target_price=target.price,
            invalidation_price=invalidation.price if invalidation else stop.price,
            risk_reward_ratio=risk_reward.ratio,
            expected_move_percent=expected_move,
            max_loss_percent=stop.distance_percent,
            vehicle=vehicle,
            vehicle_notes=vehicle_notes_str,
            primary_signal=(
                signals[0].signal if signals and hasattr(signals[0], 'signal') else "Market Setup"
            ),
            supporting_signals=tuple(
                s.signal for s in signals[1:4]
                if hasattr(s, 'signal')
            ),
            is_suppressed=False,
        )

        return RiskAnalysisResult(
            symbol=symbol,
            timestamp=timestamp,
            trade_plans=(trade_plan,),
            has_trades=True,
            primary_suppression=None,
            all_suppressions=(),
            risk_assessment=assessment,
            legacy_signals=self._format_legacy_signals(signals),
        )

    def _determine_bias(self, signals: list[Any]) -> Bias:
        """Determine directional bias from signals."""
        if not signals:
            return Bias.NEUTRAL

        bullish = sum(
            1 for s in signals
            if "BULLISH" in str(getattr(s, 'strength', ''))
        )
        bearish = sum(
            1 for s in signals
            if "BEARISH" in str(getattr(s, 'strength', ''))
        )

        if bullish > bearish + 2:
            return Bias.BULLISH
        elif bearish > bullish + 2:
            return Bias.BEARISH
        else:
            return Bias.NEUTRAL

    def _calculate_target(self, df, bias, stop, metrics):
        """Calculate target price for minimum preferred R:R."""
        from .models import TargetLevel

        current = df.iloc[-1]
        price = float(current["Close"])

        # Target = stop distance * preferred R:R
        stop_distance = abs(price - stop.price)
        target_distance = stop_distance * PREFERRED_RR_RATIO

        if bias == Bias.BULLISH:
            target_price = price + target_distance
        else:
            target_price = price - target_distance

        return TargetLevel(
            price=target_price,
            distance_percent=(
                (target_distance / price) * 100 if price > 0 else 0
            ),
            atr_multiple=(
                target_distance / metrics.atr if metrics.atr > 0 else 0
            ),
        )

    def _assess_quality(self, risk_reward, metrics) -> RiskQuality:
        """Assess overall risk quality."""
        from .models import RiskQuality

        score = 0

        # R:R scoring
        if risk_reward.ratio >= 2.5:
            score += 3
        elif risk_reward.ratio >= 2.0:
            score += 2
        elif risk_reward.ratio >= 1.5:
            score += 1

        # Trend scoring
        if metrics.adx >= 40:
            score += 2
        elif metrics.adx >= 25:
            score += 1

        # Volatility scoring (medium is ideal)
        if metrics.volatility_regime.value == "medium":
            score += 1

        if score >= 4:
            return RiskQuality.HIGH
        elif score >= 2:
            return RiskQuality.MEDIUM
        else:
            return RiskQuality.LOW

    def _format_legacy_signals(self, signals: list[Any]) -> tuple[dict, ...]:
        """Format signals for legacy compatibility."""
        result = []
        for signal in signals[:10]:
            if hasattr(signal, 'model_dump'):
                result.append(signal.model_dump())
            elif hasattr(signal, '__dict__'):
                result.append(signal.__dict__)
            else:
                result.append({"signal": str(signal)})
        return tuple(result)

    def _error_result(self, symbol: str, error: str) -> RiskAnalysisResult:
        """Return error state result."""
        from .models import SuppressionReason, SuppressionCode

        timestamp = pd.Timestamp.utcnow().isoformat()
        reason = SuppressionReason(
            code=SuppressionCode.INSUFFICIENT_DATA,
            message=error,
        )
        # Create minimal assessment for error case
        assessment = RiskAssessment(
            symbol=symbol,
            timestamp=timestamp,
            current_price=0,
            metrics=RiskMetrics(
                atr=0, atr_percent=0, volatility_regime="medium",
                adx=0, is_trending=False, bb_width_percent=0, volume_ratio=1.0
            ),
            stop=None,
            target=None,
            invalidation=None,
            risk_reward=None,
            is_qualified=False,
            risk_quality=RiskQuality.LOW,
            suppressions=(reason,),
        )
        return RiskAnalysisResult(
            symbol=symbol,
            timestamp=timestamp,
            trade_plans=(),
            has_trades=False,
            primary_suppression=reason,
            all_suppressions=(reason,),
            risk_assessment=assessment,
            legacy_signals=(),
        )
