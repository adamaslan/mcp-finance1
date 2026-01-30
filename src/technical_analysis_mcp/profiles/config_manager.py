"""Central configuration management with caching and validation."""

from typing import Optional, Dict, Any
import logging

from .base_config import UserConfig, RiskProfile
from .risk_profiles import get_profile, get_profile_with_overrides

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages user configurations with caching and validation."""

    def __init__(self):
        self._cache: Dict[str, UserConfig] = {}
        self._session_overrides: Dict[str, Dict[str, Any]] = {}

    def get_config(
        self,
        user_id: Optional[str] = None,
        risk_profile: RiskProfile | str = RiskProfile.NEUTRAL,
        session_overrides: Optional[Dict[str, Any]] = None,
    ) -> UserConfig:
        """Get effective configuration for a user/session.

        Priority:
        1. Session overrides (temporary, per-request)
        2. User saved preferences (from database - not yet implemented)
        3. Risk profile preset
        4. Default config

        Args:
            user_id: User identifier for saved preferences
            risk_profile: Base risk profile to use ("risky", "neutral", "averse")
            session_overrides: Temporary overrides for this request

        Returns:
            Complete UserConfig with all overrides applied
        """
        # Start with risk profile preset
        config = get_profile(risk_profile)

        # Apply user saved preferences (if user_id provided)
        # TODO: Implement database integration
        if user_id:
            user_prefs = self._load_user_preferences(user_id)
            if user_prefs:
                config = get_profile_with_overrides(risk_profile, user_prefs)

        # Apply session overrides (temporary, per-request)
        if session_overrides:
            all_overrides = {**config.custom_overrides, **session_overrides}
            config = get_profile_with_overrides(config.risk_profile, all_overrides)

        return config

    def set_session_override(
        self,
        session_id: str,
        key: str,
        value: Any,
    ) -> None:
        """Set a temporary session override.

        Args:
            session_id: Session identifier
            key: Configuration parameter name
            value: Override value
        """
        if session_id not in self._session_overrides:
            self._session_overrides[session_id] = {}
        self._session_overrides[session_id][key] = value
        logger.info(f"Session override set: {session_id}.{key} = {value}")

    def clear_session_overrides(self, session_id: str) -> None:
        """Clear all session overrides for a session.

        Args:
            session_id: Session identifier
        """
        self._session_overrides.pop(session_id, None)
        logger.info(f"Session overrides cleared: {session_id}")

    def _load_user_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Load user preferences from database/cache.

        Args:
            user_id: User identifier

        Returns:
            Dictionary of user preferences or None if not found

        Note:
            TODO: Implement actual database integration
            Currently returns cached overrides or None
        """
        if user_id in self._cache:
            return self._cache[user_id].custom_overrides
        return None

    def save_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> None:
        """Save user preferences.

        Args:
            user_id: User identifier
            preferences: Dictionary of preferences to save

        Note:
            TODO: Implement actual database persistence
            Currently only caches in memory
        """
        logger.info(f"Saving preferences for user {user_id}: {preferences}")
        # For now, just cache
        if user_id not in self._cache:
            self._cache[user_id] = get_profile(RiskProfile.NEUTRAL)

    def validate_overrides(
        self,
        overrides: Dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """Validate user-provided overrides.

        Args:
            overrides: Dictionary of overrides to validate

        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []

        # RSI bounds check
        if "rsi_oversold" in overrides:
            val = overrides["rsi_oversold"]
            if not (0 < val < 50):
                errors.append("rsi_oversold must be between 0 and 50")

        if "rsi_overbought" in overrides:
            val = overrides["rsi_overbought"]
            if not (50 < val < 100):
                errors.append("rsi_overbought must be between 50 and 100")

        # R:R bounds check
        if "min_rr_ratio" in overrides:
            val = overrides["min_rr_ratio"]
            if not (0.5 <= val <= 5.0):
                errors.append("min_rr_ratio must be between 0.5 and 5.0")

        # Stop ATR bounds
        if "stop_max_atr" in overrides:
            val = overrides["stop_max_atr"]
            if not (1.0 <= val <= 10.0):
                errors.append("stop_max_atr must be between 1.0 and 10.0")

        if "stop_min_atr" in overrides:
            val = overrides["stop_min_atr"]
            if not (0.1 <= val <= 2.0):
                errors.append("stop_min_atr must be between 0.1 and 2.0")

        # Momentum weight
        if "momentum_weight_in_score" in overrides:
            val = overrides["momentum_weight_in_score"]
            if not (0.0 <= val <= 0.5):
                errors.append("momentum_weight must be between 0 and 0.5")

        # ADX thresholds
        if "adx_trending" in overrides:
            val = overrides["adx_trending"]
            if not (10 <= val <= 50):
                errors.append("adx_trending must be between 10 and 50")

        # Position sizing
        if "max_position_risk_pct" in overrides:
            val = overrides["max_position_risk_pct"]
            if not (0.1 <= val <= 5.0):
                errors.append("max_position_risk_pct must be between 0.1 and 5.0")

        return (len(errors) == 0, errors)

    def export_config(self, config: UserConfig) -> Dict[str, Any]:
        """Export configuration as dictionary for API responses.

        Args:
            config: Configuration to export

        Returns:
            Dictionary representation of config
        """
        return config.to_dict()


# Global singleton
_config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager singleton.

    Returns:
        ConfigManager instance
    """
    return _config_manager
