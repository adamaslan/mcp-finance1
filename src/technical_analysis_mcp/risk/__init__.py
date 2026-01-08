"""Risk-First Layer for Trade Plan Generation.

This module provides professional risk management and trade plan generation,
replacing 150+ signals with 1-3 actionable trade plans or suppression reasons.

Key components:
- RiskAssessor: Main orchestrator
- TradePlan: Primary output model
- SuppressionReason: Machine-readable suppression codes
- Volatility classification, timeframe selection, stop/target calculation
- Risk-to-reward validation and options vehicle selection
"""

from .models import (
    Timeframe,
    Bias,
    RiskQuality,
    VolatilityRegime,
    Vehicle,
    SuppressionCode,
    SuppressionReason,
    RiskMetrics,
    StopLevel,
    TargetLevel,
    RiskReward,
    InvalidationLevel,
    RiskAssessment,
    TradePlan,
    RiskAnalysisResult,
)
from .risk_assessor import RiskAssessor
from .volatility_regime import ATRVolatilityClassifier
from .timeframe_rules import DefaultTimeframeSelector
from .stop_distance import ATRStopCalculator
from .invalidation import StructureInvalidationDetector
from .rr_calculator import DefaultRRCalculator
from .suppression import DefaultSuppressionEvaluator
from .option_rules import DefaultVehicleSelector

__all__ = [
    # Enums
    "Timeframe",
    "Bias",
    "RiskQuality",
    "VolatilityRegime",
    "Vehicle",
    "SuppressionCode",
    # Models
    "SuppressionReason",
    "RiskMetrics",
    "StopLevel",
    "TargetLevel",
    "RiskReward",
    "InvalidationLevel",
    "RiskAssessment",
    "TradePlan",
    "RiskAnalysisResult",
    # Implementations
    "RiskAssessor",
    "ATRVolatilityClassifier",
    "DefaultTimeframeSelector",
    "ATRStopCalculator",
    "StructureInvalidationDetector",
    "DefaultRRCalculator",
    "DefaultSuppressionEvaluator",
    "DefaultVehicleSelector",
]
