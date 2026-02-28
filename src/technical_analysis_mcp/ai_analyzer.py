"""
Gemini AI Analyzer for All MCP Tools

Provides natural language explanations and insights for all 8 MCP tool outputs.
Similar to options_ai_analyzer.py but tailored for stock technical analysis.
"""

import os
import json
import logging
from typing import Any
from datetime import datetime

from .config import GEMINI_MODEL

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("⚠️ google-generativeai not installed. AI analysis disabled.")
    print("Install with: mamba install -c conda-forge google-generativeai")

logger = logging.getLogger(__name__)


class MCPToolAIAnalyzer:
    """Use Gemini to analyze and explain MCP tool outputs with natural language insights."""

    MODEL_NAME = GEMINI_MODEL

    def __init__(self, api_key: str | None = None):
        """Initialize Gemini AI analyzer.

        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.

        Raises:
            ValueError: If API key not provided and not in environment.
            ImportError: If google-generativeai package not installed.
        """
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package not installed")

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.MODEL_NAME)
        logger.info("AI Analyzer initialized with %s", self.MODEL_NAME)

    def _perform_analysis(
        self,
        result: dict[str, Any],
        prompt_builder: callable,
    ) -> dict[str, Any]:
        """Generic analysis helper to eliminate code duplication.

        Args:
            result: Original tool output dictionary
            prompt_builder: Function that takes result and returns prompt string

        Returns:
            Enhanced result with AI analysis
        """
        prompt = prompt_builder(result)
        response = self.model.generate_content(prompt)
        ai_analysis = self._parse_ai_response(response.text)

        enhanced = result.copy()
        enhanced["ai_analysis"] = ai_analysis
        return enhanced

    # ============================================================================
    # ANALYZE_SECURITY TOOL
    # ============================================================================

    def analyze_security_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze output from analyze_security MCP tool.

        Args:
            result: Output from analyze_security() function

        Returns:
            Enhanced result with AI analysis
        """
        return self._perform_analysis(result, self._build_analyze_security_prompt)

    def _build_analyze_security_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for analyze_security AI analysis."""
        symbol = result.get("symbol", "UNKNOWN")
        price = result.get("price", 0)
        change = result.get("change", 0)
        summary = result.get("summary", {})
        indicators = result.get("indicators", {})
        signals = result.get("signals", [])

        prompt = f"""You are an expert technical analyst. Analyze this stock's technical signals and provide clear, actionable insights.

# STOCK OVERVIEW
- Symbol: {symbol}
- Price: ${price:.2f} ({change:+.2f}%)
- Total Signals: {summary.get('total_signals', 0)}
- Bullish Signals: {summary.get('bullish', 0)}
- Bearish Signals: {summary.get('bearish', 0)}
- Average Signal Score: {summary.get('avg_score', 0):.1f}/100

# KEY INDICATORS
- RSI: {indicators.get('rsi', 0):.1f}
- MACD: {indicators.get('macd', 0):.2f}
- ADX: {indicators.get('adx', 0):.1f}
- Volume: {indicators.get('volume', 0):,}

# TOP 10 SIGNALS
"""
        for i, sig in enumerate(signals[:10], 1):
            prompt += f"{i}. [{sig.get('ai_score', 'N/A')}] {sig.get('signal', 'N/A')}\n"
            prompt += f"   {sig.get('desc', 'N/A')}\n"

        prompt += """

# YOUR TASK

Provide a comprehensive analysis in JSON format with these sections:

1. **market_bias**: Clear statement: Is this bullish, bearish, or neutral? Why?

2. **key_drivers**: Top 3 signals driving the current setup (what's most important)

3. **indicator_analysis**: Explain what RSI, MACD, and ADX are telling us:
   - Is RSI overbought/oversold or neutral?
   - What does MACD trend indicate?
   - Is ADX showing a strong trend?

4. **signal_quality**: Assessment of signal reliability:
   - Are signals confirming each other?
   - Any conflicting signals?
   - Overall conviction level (HIGH/MEDIUM/LOW)

5. **trading_implications**: Practical guidance:
   - What type of setup is this? (breakout, reversal, continuation, range-bound)
   - Timeframe suitability (day trade, swing, position)
   - Entry considerations

6. **risk_factors**: Top 3 risks or concerns to watch

7. **action_items**: 3-5 specific next steps for a trader:
   - What to monitor today/this week
   - Entry/exit considerations
   - Stop placement ideas

8. **plain_english_summary**: 2-3 sentence summary for someone who doesn't know technical analysis

Return ONLY valid JSON (no markdown, no code blocks). Use this exact structure:

{
  "market_bias": "BULLISH|BEARISH|NEUTRAL",
  "bias_explanation": "string",
  "key_drivers": [
    {"signal": "string", "importance": "HIGH|MEDIUM", "explanation": "string"}
  ],
  "indicator_analysis": {
    "rsi": "string",
    "macd": "string",
    "adx": "string",
    "volume": "string"
  },
  "signal_quality": {
    "confirmation_level": "HIGH|MEDIUM|LOW",
    "conflicting_signals": ["string"],
    "conviction": "HIGH|MEDIUM|LOW",
    "explanation": "string"
  },
  "trading_implications": {
    "setup_type": "string",
    "timeframe": "string",
    "entry_considerations": "string"
  },
  "risk_factors": [
    {"risk": "string", "severity": "HIGH|MEDIUM|LOW", "mitigation": "string"}
  ],
  "action_items": [
    {
      "priority": 1,
      "timeframe": "TODAY|THIS_WEEK|THIS_MONTH",
      "action": "string"
    }
  ],
  "plain_english_summary": "string"
}
"""
        return prompt

    # ============================================================================
    # COMPARE_SECURITIES TOOL
    # ============================================================================

    def analyze_comparison_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """
        Analyze output from compare_securities MCP tool.

        Args:
            result: Output from compare_securities() function

        Returns:
            Enhanced result with AI analysis
        """
        return self._perform_analysis(result, self._build_comparison_prompt)

    def _build_comparison_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for compare_securities AI analysis."""
        comparison = result.get("comparison", [])
        winner = result.get("winner")

        prompt = f"""You are an expert stock analyst. Compare these securities and recommend the best pick.

# SECURITIES COMPARISON
"""
        for i, item in enumerate(comparison, 1):
            prompt += f"""
{i}. {item['symbol']}
   - Score: {item['score']:.1f}/100
   - Price: ${item['price']:.2f} ({item['change']:+.2f}%)
   - Signals: {item['bullish']} bullish / {item['bearish']} bearish
"""

        # Handle case where all symbols failed to analyze
        if winner:
            winner_text = f"{winner.get('symbol', 'NONE')} with score {winner.get('score', 0):.1f}"
        else:
            winner_text = "NONE - All symbols failed to analyze"

        prompt += f"""

# CURRENT WINNER
{winner_text}

# YOUR TASK

Provide analysis in JSON format:

1. **ranking_rationale**: Why is the winner ranked #1?

2. **detailed_comparison**: Compare top 3 securities:
   - Relative strengths
   - Key differences
   - Risk/reward profiles

3. **recommendation**: Clear trading recommendation:
   - Best pick for aggressive traders
   - Best pick for conservative traders
   - Best pick for current market conditions

4. **sector_insights**: If any sector patterns emerge

5. **action_plan**: Specific steps to act on this comparison

Return ONLY valid JSON:

{{
  "ranking_rationale": "string",
  "detailed_comparison": [
    {{
      "symbol": "string",
      "rank": 1,
      "strengths": ["string"],
      "weaknesses": ["string"],
      "profile": "AGGRESSIVE|MODERATE|CONSERVATIVE"
    }}
  ],
  "recommendation": {{
    "aggressive_pick": "string",
    "conservative_pick": "string",
    "current_market_pick": "string",
    "explanation": "string"
  }},
  "sector_insights": "string",
  "action_plan": ["string"]
}}
"""
        return prompt

    # ============================================================================
    # SCREEN_SECURITIES TOOL
    # ============================================================================

    def analyze_screening_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from screen_securities MCP tool."""
        return self._perform_analysis(result, self._build_screening_prompt)

    def _build_screening_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for screen_securities AI analysis."""
        universe = result.get("universe", "UNKNOWN")
        total_screened = result.get("total_screened", 0)
        matches = result.get("matches", [])
        criteria = result.get("criteria", {})

        prompt = f"""You are an expert stock screener. Analyze these screening results and provide insights.

# SCREENING RESULTS
- Universe: {universe}
- Total Screened: {total_screened}
- Matches Found: {len(matches)}
- Criteria: {json.dumps(criteria, indent=2)}

# TOP MATCHES
"""
        for i, match in enumerate(matches[:10], 1):
            prompt += f"""
{i}. {match['symbol']}
   - Score: {match['score']:.1f}/100
   - Total Signals: {match['signals']}
   - Price: ${match['price']:.2f}
   - RSI: {match['rsi']:.1f}
"""

        prompt += """

# YOUR TASK

Provide analysis in JSON format:

1. **screening_effectiveness**: How good were the results?

2. **top_picks**: Highlight top 3 picks with reasoning

3. **pattern_recognition**: Any patterns in the matches?

4. **criteria_assessment**: Were the screening criteria good?

5. **refinement_suggestions**: How to improve the screen?

Return ONLY valid JSON:

{
  "screening_effectiveness": {
    "hit_rate": "HIGH|MEDIUM|LOW",
    "quality_assessment": "string"
  },
  "top_picks": [
    {
      "symbol": "string",
      "why": "string",
      "confidence": "HIGH|MEDIUM|LOW"
    }
  ],
  "pattern_recognition": {
    "common_characteristics": ["string"],
    "market_environment": "string"
  },
  "criteria_assessment": "string",
  "refinement_suggestions": ["string"]
}
"""
        return prompt

    # ============================================================================
    # GET_TRADE_PLAN TOOL
    # ============================================================================

    def analyze_trade_plan_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from get_trade_plan MCP tool."""
        return self._perform_analysis(result, self._build_trade_plan_prompt)

    def _build_trade_plan_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for get_trade_plan AI analysis."""
        symbol = result.get("symbol", "UNKNOWN")
        has_trades = result.get("has_trades", False)
        trade_plans = result.get("trade_plans", [])
        suppressions = result.get("all_suppressions", [])

        prompt = f"""You are an expert trade planner. Analyze this risk-qualified trade plan.

# TRADE PLAN FOR {symbol}
- Has Tradeable Setups: {has_trades}
- Number of Plans: {len(trade_plans)}
- Suppressions: {len(suppressions)}

"""
        if trade_plans:
            for i, plan in enumerate(trade_plans, 1):
                prompt += f"""
## Trade Plan {i}
- Timeframe: {plan.get('timeframe', 'N/A')}
- Bias: {plan.get('bias', 'N/A')}
- Entry: ${plan.get('entry_price', 0):.2f}
- Stop: ${plan.get('stop_price', 0):.2f}
- Target: ${plan.get('target_price', 0):.2f}
- R:R Ratio: {plan.get('risk_reward_ratio', 0):.2f}
- Risk Quality: {plan.get('risk_quality', 'N/A')}
- Primary Signal: {plan.get('primary_signal', 'N/A')}
"""

        if suppressions:
            prompt += "\n## Suppression Reasons (Why No Trade):\n"
            for supp in suppressions:
                prompt += f"- {supp}\n"

        prompt += """

# YOUR TASK

Provide analysis in JSON format:

1. **trade_assessment**: Overall evaluation of the trade setup

2. **risk_analysis**: Detailed risk evaluation:
   - Stop loss placement quality
   - R:R ratio assessment
   - Position sizing considerations

3. **execution_plan**: Step-by-step execution guide

4. **monitoring_checklist**: What to watch while in the trade

5. **exit_strategy**: Both profit-taking and stop-loss guidance

6. **if_suppressed**: If no tradeable setup, explain why and what to wait for

Return ONLY valid JSON:

{
  "trade_assessment": {
    "quality": "EXCELLENT|GOOD|FAIR|POOR",
    "conviction": "HIGH|MEDIUM|LOW",
    "explanation": "string"
  },
  "risk_analysis": {
    "stop_placement": "string",
    "rr_assessment": "string",
    "position_size_guidance": "string",
    "max_loss_acceptable": "string"
  },
  "execution_plan": [
    {"step": 1, "action": "string", "timing": "string"}
  ],
  "monitoring_checklist": ["string"],
  "exit_strategy": {
    "profit_targets": ["string"],
    "stop_loss_rules": ["string"],
    "time_stops": "string"
  },
  "if_suppressed": {
    "reasons": ["string"],
    "what_to_wait_for": ["string"],
    "alternative_symbols": ["string"]
  }
}
"""
        return prompt

    # ============================================================================
    # SCAN_TRADES TOOL
    # ============================================================================

    def analyze_scan_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from scan_trades MCP tool."""
        return self._perform_analysis(result, self._build_scan_prompt)

    def _build_scan_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for scan_trades AI analysis."""
        universe = result.get("universe", "UNKNOWN")
        total_scanned = result.get("total_scanned", 0)
        qualified = result.get("qualified_trades", [])
        duration = result.get("duration_seconds", 0)

        prompt = f"""You are an expert trade scanner analyst. Analyze these scanning results.

# SCAN RESULTS
- Universe: {universe}
- Total Scanned: {total_scanned}
- Qualified Trades Found: {len(qualified)}
- Scan Duration: {duration:.1f} seconds

# QUALIFIED TRADES
"""
        for i, trade in enumerate(qualified[:10], 1):
            prompt += f"""
{i}. {trade.get('symbol', 'N/A')}
   - Bias: {trade.get('bias', 'N/A')}
   - Entry: ${trade.get('entry_price', 0):.2f}
   - Stop: ${trade.get('stop_price', 0):.2f}
   - Target: ${trade.get('target_price', 0):.2f}
   - R:R: {trade.get('risk_reward_ratio', 0):.2f}
   - Quality: {trade.get('risk_quality', 'N/A')}
"""

        prompt += """

# YOUR TASK

Provide analysis in JSON format:

1. **scan_quality**: Overall assessment of scan results

2. **best_opportunities**: Top 3 trades with detailed reasoning

3. **market_themes**: What themes/patterns emerge?

4. **portfolio_construction**: How to combine these trades

5. **prioritization**: How to prioritize if can't take all trades

6. **risk_management**: Aggregate risk guidance

Return ONLY valid JSON:

{
  "scan_quality": {
    "hit_rate": "string",
    "overall_quality": "EXCELLENT|GOOD|FAIR|POOR",
    "assessment": "string"
  },
  "best_opportunities": [
    {
      "symbol": "string",
      "rank": 1,
      "why_best": "string",
      "confidence": "HIGH|MEDIUM|LOW"
    }
  ],
  "market_themes": {
    "dominant_bias": "BULLISH|BEARISH|MIXED",
    "sector_concentration": "string",
    "timeframe_preference": "string",
    "themes": ["string"]
  },
  "portfolio_construction": {
    "suggested_allocation": "string",
    "diversification_notes": "string",
    "correlation_warning": "string"
  },
  "prioritization": {
    "if_choose_1": "string",
    "if_choose_3": ["string"],
    "if_choose_5": ["string"]
  },
  "risk_management": {
    "aggregate_risk": "string",
    "position_sizing": "string",
    "max_concurrent": "string"
  }
}
"""
        return prompt

    # ============================================================================
    # PORTFOLIO_RISK TOOL
    # ============================================================================

    def analyze_portfolio_risk_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from portfolio_risk MCP tool."""
        return self._perform_analysis(result, self._build_portfolio_risk_prompt)

    def _build_portfolio_risk_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for portfolio_risk AI analysis."""
        total_value = result.get("total_value", 0)
        max_loss = result.get("total_max_loss", 0)
        risk_pct = result.get("risk_percent_of_portfolio", 0)
        risk_level = result.get("overall_risk_level", "UNKNOWN")
        positions = result.get("positions", [])
        sector_conc = result.get("sector_concentration", {})
        hedges = result.get("hedge_suggestions", [])

        prompt = f"""You are an expert portfolio risk manager. Analyze this portfolio's risk profile.

# PORTFOLIO OVERVIEW
- Total Value: ${total_value:,.2f}
- Total Max Loss: ${max_loss:,.2f}
- Risk as % of Portfolio: {risk_pct:.1f}%
- Overall Risk Level: {risk_level}
- Number of Positions: {len(positions)}

# SECTOR CONCENTRATION
{json.dumps(sector_conc, indent=2)}

# POSITIONS
"""
        for pos in positions:
            prompt += f"""
- {pos['symbol']}: {pos['shares']} shares @ ${pos.get('entry_price', 0):.2f}
  Current Value: ${pos.get('current_value', 0):,.2f}
"""

        prompt += "\n# HEDGE SUGGESTIONS\n"
        if hedges:
            for hedge in hedges:
                prompt += f"- {hedge}\n"
        else:
            prompt += "- No hedges suggested\n"

        prompt += """

# YOUR TASK

Provide analysis in JSON format:

1. **risk_assessment**: Overall portfolio risk evaluation

2. **position_analysis**: Individual position risks

3. **concentration_analysis**: Sector/correlation risks

4. **hedge_recommendations**: Hedging strategy

5. **rebalancing_suggestions**: How to improve the portfolio

6. **stress_scenarios**: What could go wrong?

7. **action_items**: Prioritized steps to manage risk

Return ONLY valid JSON:

{
  "risk_assessment": {
    "overall_level": "TOO_HIGH|APPROPRIATE|TOO_LOW",
    "explanation": "string",
    "risk_score": 1-10
  },
  "position_analysis": [
    {
      "symbol": "string",
      "risk_contribution": "HIGH|MEDIUM|LOW",
      "concerns": ["string"],
      "suggestions": ["string"]
    }
  ],
  "concentration_analysis": {
    "sector_risk": "HIGH|MEDIUM|LOW",
    "correlation_risk": "HIGH|MEDIUM|LOW",
    "diversification_score": 1-10,
    "explanation": "string"
  },
  "hedge_recommendations": {
    "urgency": "HIGH|MEDIUM|LOW",
    "strategies": [
      {
        "type": "string",
        "why": "string",
        "how": "string"
      }
    ]
  },
  "rebalancing_suggestions": [
    {
      "priority": 1,
      "action": "string",
      "expected_impact": "string"
    }
  ],
  "stress_scenarios": [
    {
      "scenario": "string",
      "impact": "string",
      "probability": "HIGH|MEDIUM|LOW",
      "mitigation": "string"
    }
  ],
  "action_items": [
    {
      "priority": 1,
      "timeframe": "TODAY|THIS_WEEK|THIS_MONTH",
      "action": "string"
    }
  ]
}
"""
        return prompt

    # ============================================================================
    # MORNING_BRIEF TOOL
    # ============================================================================

    def analyze_morning_brief_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from morning_brief MCP tool."""
        return self._perform_analysis(result, self._build_morning_brief_prompt)

    def _build_morning_brief_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for morning_brief AI analysis."""
        market_status = result.get("market_status", {})
        events = result.get("economic_events", [])
        watchlist = result.get("watchlist_signals", [])
        themes = result.get("key_themes", [])

        prompt = f"""You are an expert market analyst. Synthesize this morning brief into actionable insights.

# MARKET STATUS
{json.dumps(market_status, indent=2)}

# ECONOMIC EVENTS TODAY
"""
        for event in events:
            prompt += f"- {event}\n"

        prompt += "\n# WATCHLIST SIGNALS\n"
        for sig in watchlist:
            prompt += f"- {sig.get('symbol', 'N/A')}: {sig.get('action', 'N/A')}\n"

        prompt += "\n# KEY THEMES\n"
        for theme in themes:
            prompt += f"- {theme}\n"

        prompt += """

# YOUR TASK

Provide analysis in JSON format:

1. **market_outlook**: Today's market bias and reasoning

2. **top_opportunities**: Best trades for today

3. **key_risks**: What could disrupt the market today?

4. **sector_rotation**: Any sector trends?

5. **trading_strategy**: How to approach today's session

6. **time_specific_guidance**: Pre-market, open, midday, close strategies

Return ONLY valid JSON:

{
  "market_outlook": {
    "bias": "BULLISH|BEARISH|NEUTRAL",
    "confidence": "HIGH|MEDIUM|LOW",
    "reasoning": "string",
    "volatility_expectation": "HIGH|MEDIUM|LOW"
  },
  "top_opportunities": [
    {
      "symbol": "string",
      "setup": "string",
      "timing": "string"
    }
  ],
  "key_risks": [
    {
      "risk": "string",
      "likelihood": "HIGH|MEDIUM|LOW",
      "mitigation": "string"
    }
  ],
  "sector_rotation": {
    "leaders": ["string"],
    "laggards": ["string"],
    "explanation": "string"
  },
  "trading_strategy": {
    "approach": "AGGRESSIVE|MODERATE|CONSERVATIVE",
    "focus": "string",
    "avoid": "string"
  },
  "time_specific_guidance": {
    "pre_market": "string",
    "market_open": "string",
    "midday": "string",
    "power_hour": "string"
  }
}
"""
        return prompt

    # ============================================================================
    # ANALYZE_FIBONACCI TOOL
    # ============================================================================

    def analyze_fibonacci_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from analyze_fibonacci MCP tool."""
        return self._perform_analysis(result, self._build_fibonacci_prompt)

    def _build_fibonacci_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for analyze_fibonacci AI analysis."""
        symbol = result.get("symbol", "UNKNOWN")
        price = result.get("price", 0)
        swing_high = result.get("swingHigh", 0)
        swing_low = result.get("swingLow", 0)
        levels = result.get("levels", [])
        signals = result.get("signals", [])
        clusters = result.get("clusters", [])
        summary = result.get("summary", {})

        prompt = f"""You are an expert Fibonacci trader. Analyze these Fibonacci levels and signals.

# FIBONACCI ANALYSIS FOR {symbol}
- Current Price: ${price:.2f}
- Swing High: ${swing_high:.2f}
- Swing Low: ${swing_low:.2f}
- Total Levels: {len(levels)}
- Total Signals: {summary.get('totalSignals', 0)}
- Confluence Zones: {summary.get('confluenceZones', 0)}

# TOP 10 FIBONACCI LEVELS
"""
        for i, level in enumerate(levels[:10], 1):
            prompt += f"{i}. {level['name']} @ ${level['price']:.2f}\n"
            prompt += f"   Type: {level['type']}, Strength: {level['strength']}\n"

        prompt += "\n# TOP 10 SIGNALS\n"
        for i, sig in enumerate(signals[:10], 1):
            prompt += f"{i}. [{sig['strength']}] {sig['signal']}\n"

        prompt += f"\n# CLUSTERS ({len(clusters)} found)\n"
        for cluster in clusters[:5]:
            prompt += f"- ${cluster['centerPrice']:.2f}: {cluster['levelCount']} levels ({cluster['strength']})\n"

        prompt += """

# YOUR TASK

Provide analysis in JSON format:

1. **fibonacci_setup**: What type of Fibonacci setup is this?

2. **key_levels**: Most important levels to watch

3. **price_action_context**: Where is price relative to Fibonacci structure?

4. **trading_zones**: Entry, stop, and target zones

5. **confluence_analysis**: Strongest confluence zones

6. **setup_quality**: Overall quality of the Fibonacci setup

7. **execution_guide**: How to trade this Fibonacci setup

Return ONLY valid JSON:

{
  "fibonacci_setup": {
    "type": "string",
    "quality": "EXCELLENT|GOOD|FAIR|POOR",
    "explanation": "string"
  },
  "key_levels": [
    {
      "level": "string",
      "price": 0.0,
      "significance": "HIGH|MEDIUM|LOW",
      "what_it_means": "string"
    }
  ],
  "price_action_context": {
    "current_position": "string",
    "bias_from_structure": "BULLISH|BEARISH|NEUTRAL",
    "next_major_level": "string"
  },
  "trading_zones": {
    "buy_zones": [{"price": 0.0, "strength": "HIGH|MEDIUM|LOW"}],
    "sell_zones": [{"price": 0.0, "strength": "HIGH|MEDIUM|LOW"}],
    "stop_zones": [{"price": 0.0, "reasoning": "string"}]
  },
  "confluence_analysis": [
    {
      "price": 0.0,
      "what_converges": ["string"],
      "strength": "VERY_STRONG|STRONG|MODERATE",
      "action": "string"
    }
  ],
  "setup_quality": {
    "score": 1-10,
    "pros": ["string"],
    "cons": ["string"]
  },
  "execution_guide": {
    "if_bullish": "string",
    "if_bearish": "string",
    "wait_for": ["string"]
  }
}
"""
        return prompt

    # ============================================================================
    # OPTIONS_RISK_ANALYSIS TOOL
    # ============================================================================

    def analyze_options_risk_output(self, result: dict[str, Any]) -> dict[str, Any]:
        """Analyze output from options_risk_analysis MCP tool."""
        return self._perform_analysis(result, self._build_options_risk_prompt)

    def _build_options_risk_prompt(self, result: dict[str, Any]) -> str:
        """Build prompt for options_risk_analysis AI analysis."""
        symbol = result.get("symbol", "UNKNOWN")
        price = result.get("current_price", 0)
        dte = result.get("days_to_expiration", 0)
        calls = result.get("calls", {})
        puts = result.get("puts", {})
        pcr = result.get("put_call_ratio", {})
        warnings = result.get("risk_warnings", [])
        opportunities = result.get("opportunities", [])

        prompt = f"""You are an expert options trader. Analyze this options chain data and provide actionable insights.

# OPTIONS CHAIN FOR {symbol}
- Current Stock Price: ${price:.2f}
- Expiration Date: {result.get('expiration_date', 'N/A')}
- Days to Expiration: {dte}

# CALLS ANALYSIS
"""
        if calls:
            prompt += f"""
- Total Contracts: {calls.get('total_contracts', 0)}
- Liquid Contracts: {calls.get('liquid_contracts', 0)}
- Total Volume: {calls.get('total_volume', 0):,}
- Total Open Interest: {calls.get('total_open_interest', 0):,}
- Average IV: {calls.get('avg_implied_volatility', 0):.1f}%
- ATM Strike: ${calls.get('atm_strike', 0):.2f}
- ATM IV: {calls.get('atm_iv', 0):.1f}%
"""
            if calls.get('top_volume_strikes'):
                prompt += "\n## Top Call Strikes by Volume:\n"
                for strike in calls['top_volume_strikes'][:3]:
                    prompt += f"- ${strike['strike']:.2f}: {strike['volume']:,} vol, IV {strike['iv']:.1f}%\n"

        # PUTS ANALYSIS
        prompt += "\n# PUTS ANALYSIS\n"
        if puts:
            prompt += f"""
- Total Contracts: {puts.get('total_contracts', 0)}
- Liquid Contracts: {puts.get('liquid_contracts', 0)}
- Total Volume: {puts.get('total_volume', 0):,}
- Total Open Interest: {puts.get('total_open_interest', 0):,}
- Average IV: {puts.get('avg_implied_volatility', 0):.1f}%
- ATM Strike: ${puts.get('atm_strike', 0):.2f}
- ATM IV: {puts.get('atm_iv', 0):.1f}%
"""
            if puts.get('top_volume_strikes'):
                prompt += "\n## Top Put Strikes by Volume:\n"
                for strike in puts['top_volume_strikes'][:3]:
                    prompt += f"- ${strike['strike']:.2f}: {strike['volume']:,} vol, IV {strike['iv']:.1f}%\n"

        # PUT/CALL RATIO
        prompt += "\n# PUT/CALL RATIO\n"
        if pcr.get('volume'):
            prompt += f"- Volume Ratio: {pcr['volume']:.2f}\n"
        if pcr.get('open_interest'):
            prompt += f"- Open Interest Ratio: {pcr['open_interest']:.2f}\n"

        # WARNINGS AND OPPORTUNITIES
        if warnings:
            prompt += "\n# RISK WARNINGS\n"
            for warning in warnings:
                prompt += f"- {warning}\n"

        if opportunities:
            prompt += "\n# OPPORTUNITIES\n"
            for opp in opportunities:
                prompt += f"- {opp}\n"

        prompt += """

# YOUR TASK

Provide comprehensive options trading analysis in JSON format:

1. **market_sentiment**: What does the options flow tell us about sentiment?

2. **iv_analysis**: Interpret the implied volatility levels:
   - Is IV high, medium, or low historically?
   - What does this mean for premium buyers vs sellers?
   - Any IV skew between calls and puts?

3. **liquidity_assessment**: Evaluate the tradability:
   - Are there enough liquid contracts?
   - What strikes have the best liquidity?
   - Any liquidity concerns?

4. **strategy_recommendations**: Specific trading strategies:
   - For bullish bias
   - For bearish bias
   - For neutral/income strategies
   - Consider DTE, IV, and liquidity

5. **risk_factors**: Top risks to be aware of:
   - Time decay considerations
   - Volatility risks
   - Liquidity risks
   - Event risks

6. **optimal_strikes**: Recommended strike selection:
   - For directional plays
   - For spreads
   - For income strategies

7. **position_sizing**: Guidance on how much to allocate:
   - Based on IV levels
   - Based on DTE
   - Based on liquidity

8. **action_plan**: Step-by-step execution guide:
   - What to check before entering
   - How to structure the trade
   - When to enter
   - How to manage risk

Return ONLY valid JSON:

{{
  "market_sentiment": {{
    "bias": "BULLISH|BEARISH|NEUTRAL",
    "confidence": "HIGH|MEDIUM|LOW",
    "reasoning": "string",
    "key_flow_signals": ["string"]
  }},
  "iv_analysis": {{
    "level": "HIGH|MEDIUM|LOW",
    "historical_context": "string",
    "buyer_vs_seller_edge": "string",
    "skew_analysis": "string"
  }},
  "liquidity_assessment": {{
    "overall_quality": "EXCELLENT|GOOD|FAIR|POOR",
    "best_liquid_strikes_calls": ["string"],
    "best_liquid_strikes_puts": ["string"],
    "concerns": ["string"]
  }},
  "strategy_recommendations": [
    {{
      "bias": "BULLISH|BEARISH|NEUTRAL",
      "strategy_name": "string",
      "strikes": "string",
      "reasoning": "string",
      "risk_reward": "string",
      "suitability": "AGGRESSIVE|MODERATE|CONSERVATIVE"
    }}
  ],
  "risk_factors": [
    {{
      "factor": "string",
      "severity": "HIGH|MEDIUM|LOW",
      "mitigation": "string"
    }}
  ],
  "optimal_strikes": {{
    "for_directional": "string",
    "for_spreads": "string",
    "for_income": "string"
  }},
  "position_sizing": {{
    "recommended_allocation": "string",
    "max_risk_per_contract": "string",
    "scaling_guidance": "string"
  }},
  "action_plan": [
    {{
      "step": 1,
      "action": "string",
      "timing": "BEFORE_ENTRY|AT_ENTRY|AFTER_ENTRY"
    }}
  ]
}}
"""
        return prompt

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _parse_ai_response(self, response_text: str) -> dict[str, Any]:
        """Parse JSON response from Gemini."""
        cleaned = response_text.strip()

        # Remove markdown code blocks if present
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.debug(f"Raw response:\n{response_text}")

            # Return fallback structure
            return {
                "error": "AI response parsing failed",
                "raw_response": response_text,
                "parse_error": str(e),
            }

    def format_analysis_report(
        self,
        tool_name: str,
        original_result: dict[str, Any],
        enhanced_result: dict[str, Any],
    ) -> str:
        """Format AI-enhanced analysis as a readable report.

        Args:
            tool_name: Name of the MCP tool (e.g., "analyze_security")
            original_result: Original tool output
            enhanced_result: Enhanced output with AI analysis

        Returns:
            Formatted string report
        """
        ai = enhanced_result.get("ai_analysis", {})

        report = []
        report.append("=" * 80)
        report.append(f"  AI-ENHANCED {tool_name.upper().replace('_', ' ')} ANALYSIS")
        report.append("=" * 80)
        report.append("")

        # Pretty print the AI analysis
        report.append(json.dumps(ai, indent=2))
        report.append("")
        report.append("=" * 80)

        return "\n".join(report)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    import sys

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY not set")
        print("\nSet it with:")
        print("  export GEMINI_API_KEY='your-key-here'")
        print("\nOr add to .env file")
        sys.exit(1)

    if not GEMINI_AVAILABLE:
        print("ERROR: google-generativeai not installed")
        print("\nInstall with:")
        print("  mamba install -c conda-forge google-generativeai")
        sys.exit(1)

    print("\n" + "=" * 80)
    print("  MCP TOOLS AI ANALYZER - EXAMPLE")
    print("=" * 80 + "\n")

    analyzer = MCPToolAIAnalyzer()

    # Example: Analyze a mock analyze_security result
    mock_result = {
        "symbol": "AAPL",
        "price": 150.25,
        "change": 2.5,
        "summary": {
            "total_signals": 45,
            "bullish": 30,
            "bearish": 15,
            "avg_score": 72.5,
        },
        "indicators": {
            "rsi": 65.5,
            "macd": 1.25,
            "adx": 28.0,
            "volume": 50000000,
        },
        "signals": [
            {"signal": "Bullish MACD Crossover", "desc": "MACD crossed above signal line", "ai_score": 85},
            {"signal": "RSI Bullish Divergence", "desc": "Price made lower low but RSI made higher low", "ai_score": 78},
        ],
    }

    print("Analyzing mock analyze_security result for AAPL...")
    enhanced = analyzer.analyze_security_output(mock_result)

    report = analyzer.format_analysis_report("analyze_security", mock_result, enhanced)
    print(report)

    print("\n✓ Example complete\n")
