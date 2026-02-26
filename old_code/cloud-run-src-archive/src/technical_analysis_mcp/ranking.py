"""Signal ranking strategies.

Implements the Strategy pattern for ranking signals using either
rule-based scoring or AI-powered ranking with Gemini.
"""

import json
import logging
from typing import Any, Protocol

from .config import (
    CATEGORY_BONUSES,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MAX_RULE_BASED_SCORE,
    STRENGTH_SCORES,
    SignalCategory,
)
from .exceptions import RankingError
from .models import MutableSignal

logger = logging.getLogger(__name__)


class RankingStrategy(Protocol):
    """Protocol for signal ranking strategies."""

    def rank(
        self,
        signals: list[MutableSignal],
        symbol: str,
        market_data: dict[str, Any],
    ) -> list[MutableSignal]:
        """Rank and score signals.

        Args:
            signals: List of signals to rank.
            symbol: Ticker symbol for context.
            market_data: Current market data for context.

        Returns:
            List of signals with scores and ranks assigned.
        """
        ...


class RuleBasedRanking:
    """Rule-based signal ranking using strength and category scores."""

    def rank(
        self,
        signals: list[MutableSignal],
        symbol: str,
        market_data: dict[str, Any],
    ) -> list[MutableSignal]:
        """Rank signals using predefined rules.

        Scores are based on signal strength keywords and category bonuses.

        Args:
            signals: List of signals to rank.
            symbol: Ticker symbol (not used in rule-based).
            market_data: Market data (not used in rule-based).

        Returns:
            List of signals with scores and ranks assigned.
        """
        logger.info("Ranking %d signals using rule-based strategy", len(signals))

        for signal in signals:
            score = self._calculate_score(signal)
            signal.ai_score = score
            signal.ai_reasoning = "Rule-based score"

        signals.sort(key=lambda x: x.ai_score or 0, reverse=True)

        for rank, signal in enumerate(signals, 1):
            signal.rank = rank

        logger.info("Completed rule-based ranking")
        return signals

    def _calculate_score(self, signal: MutableSignal) -> int:
        """Calculate score for a single signal.

        Args:
            signal: Signal to score.

        Returns:
            Score from 0-95.
        """
        score = 50
        strength = signal.strength.upper()

        for keyword, points in STRENGTH_SCORES.items():
            if keyword in strength:
                score = points
                break

        try:
            category = SignalCategory(signal.category)
            bonus = CATEGORY_BONUSES.get(category, 0)
            score += bonus
        except ValueError:
            pass

        return min(score, MAX_RULE_BASED_SCORE)


class GeminiRanking:
    """AI-powered signal ranking using Google's Gemini model."""

    def __init__(self, api_key: str | None = None):
        """Initialize Gemini ranking.

        Args:
            api_key: Gemini API key. Defaults to GEMINI_API_KEY from config.
        """
        self._api_key = api_key or GEMINI_API_KEY
        self._fallback = RuleBasedRanking()

    def rank(
        self,
        signals: list[MutableSignal],
        symbol: str,
        market_data: dict[str, Any],
    ) -> list[MutableSignal]:
        """Rank signals using Gemini AI.

        Falls back to rule-based ranking if AI fails.

        Args:
            signals: List of signals to rank.
            symbol: Ticker symbol for context.
            market_data: Current market data for context.

        Returns:
            List of signals with AI scores and reasoning.
        """
        if not self._api_key:
            logger.warning("No Gemini API key, falling back to rule-based ranking")
            return self._fallback.rank(signals, symbol, market_data)

        logger.info("Ranking %d signals using Gemini AI", len(signals))

        try:
            return self._rank_with_gemini(signals, symbol, market_data)
        except Exception as e:
            logger.warning("Gemini ranking failed: %s, falling back to rules", e)
            return self._fallback.rank(signals, symbol, market_data)

    def _rank_with_gemini(
        self,
        signals: list[MutableSignal],
        symbol: str,
        market_data: dict[str, Any],
    ) -> list[MutableSignal]:
        """Perform actual Gemini API call for ranking.

        Args:
            signals: Signals to rank.
            symbol: Ticker symbol.
            market_data: Market context.

        Returns:
            Ranked signals with AI scores.

        Raises:
            RankingError: If Gemini API call fails.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            raise RankingError(symbol, "google-generativeai package not installed")

        genai.configure(api_key=self._api_key)
        model = genai.GenerativeModel(GEMINI_MODEL)

        prompt = self._build_prompt(signals, symbol, market_data)

        try:
            response = model.generate_content(prompt)
            response_text = response.text.strip()
        except Exception as e:
            raise RankingError(symbol, f"Gemini API error: {e}")

        scores = self._parse_response(response_text)
        self._apply_scores(signals, scores)

        signals.sort(key=lambda x: x.ai_score or 0, reverse=True)

        for rank, signal in enumerate(signals, 1):
            signal.rank = rank

        logger.info("Completed Gemini AI ranking")
        return signals

    def _build_prompt(
        self,
        signals: list[MutableSignal],
        symbol: str,
        market_data: dict[str, Any],
    ) -> str:
        """Build the prompt for Gemini.

        Args:
            signals: Signals to include in prompt.
            symbol: Ticker symbol.
            market_data: Market context.

        Returns:
            Formatted prompt string.
        """
        prompt = f"""You are an expert technical analyst. Score these trading signals for {symbol}.

MARKET DATA:
- Price: ${market_data.get('price', 0):.2f} | Change: {market_data.get('change', 0):.2f}%
- RSI: {market_data.get('rsi', 0):.1f} | MACD: {market_data.get('macd', 0):.4f} | ADX: {market_data.get('adx', 0):.1f}

SIGNALS TO SCORE:
"""
        for i, sig in enumerate(signals, 1):
            prompt += f"{i}. {sig.signal}: {sig.description} [{sig.strength}]\n"

        prompt += """
Score each signal from 1-100 based on:
- Actionability: Can a trader act on this signal now?
- Reliability: How historically accurate is this signal type?
- Timing: Is this signal relevant at this moment?
- Risk/Reward: What's the potential upside vs downside?

Return ONLY valid JSON (no markdown, no explanations):
{
  "scores": [
    {"signal_number": 1, "score": 85, "reasoning": "Strong momentum confirmed by volume"},
    {"signal_number": 2, "score": 72, "reasoning": "Oversold but no reversal pattern yet"}
  ]
}

Make reasoning brief (under 60 chars). Score ALL signals.
"""
        return prompt

    def _parse_response(self, response_text: str) -> dict[str, Any]:
        """Parse Gemini response JSON.

        Args:
            response_text: Raw response from Gemini.

        Returns:
            Parsed scores dictionary.

        Raises:
            RankingError: If JSON parsing fails.
        """
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}")
        if start_idx != -1 and end_idx != -1:
            response_text = response_text[start_idx : end_idx + 1]

        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            raise RankingError("parsing", f"Invalid JSON from Gemini: {e}")

    def _apply_scores(
        self,
        signals: list[MutableSignal],
        scores_data: dict[str, Any],
    ) -> None:
        """Apply parsed scores to signals.

        Args:
            signals: Signals to update.
            scores_data: Parsed scores from Gemini.
        """
        for score_item in scores_data.get("scores", []):
            sig_num = score_item.get("signal_number", 0) - 1
            if 0 <= sig_num < len(signals):
                signals[sig_num].ai_score = score_item.get("score", 50)
                signals[sig_num].ai_reasoning = score_item.get("reasoning", "No reasoning")

        for signal in signals:
            if signal.ai_score is None:
                signal.ai_score = 50
                signal.ai_reasoning = "Score not provided by AI"


def get_ranking_strategy(use_ai: bool = False) -> RankingStrategy:
    """Get the appropriate ranking strategy.

    Args:
        use_ai: Whether to use AI ranking if available.

    Returns:
        Ranking strategy instance.
    """
    if use_ai and GEMINI_API_KEY:
        return GeminiRanking()
    return RuleBasedRanking()


def rank_signals(
    signals: list[MutableSignal],
    symbol: str,
    market_data: dict[str, Any],
    strategy: RankingStrategy | None = None,
    use_ai: bool = False,
) -> list[MutableSignal]:
    """Rank signals using the specified strategy.

    Convenience function that handles strategy selection.

    Args:
        signals: Signals to rank.
        symbol: Ticker symbol for context.
        market_data: Current market data.
        strategy: Specific strategy to use (optional).
        use_ai: Whether to use AI ranking if no strategy specified.

    Returns:
        Ranked signals with scores.
    """
    if strategy is None:
        strategy = get_ranking_strategy(use_ai)

    return strategy.rank(signals, symbol, market_data)
