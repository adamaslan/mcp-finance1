"""Output formatting for Claude and other consumers.

Provides formatted text output for analysis results, comparisons,
and screening results suitable for display in Claude.
"""

from typing import Any

from .config import MAX_SIGNALS_RETURNED


def format_analysis(result: dict[str, Any]) -> str:
    """Format analysis result for Claude display.

    Args:
        result: Analysis result dictionary containing symbol, price,
                change, signals, summary, and indicators.

    Returns:
        Formatted string for display.
    """
    change = result.get("change", 0)
    price_emoji = "🟢" if change > 0 else "🔴" if change < 0 else "⚪"

    output = f"""
📊 {result['symbol']} Technical Analysis
{price_emoji} Price: ${result['price']:.2f} ({change:+.2f}%)

📈 Summary:
• Total Signals: {result['summary']['total_signals']}
• Bullish: {result['summary']['bullish']} | Bearish: {result['summary']['bearish']}
• Avg Score: {result['summary']['avg_score']:.1f}/100

🎯 Top 10 Signals:
"""

    signals = result.get("signals", [])[:10]
    for i, sig in enumerate(signals, 1):
        score = sig.get("ai_score", "N/A")

        if isinstance(score, (int, float)):
            if score >= 80:
                indicator = "🔥"
            elif score >= 60:
                indicator = "⚡"
            else:
                indicator = "📊"
        else:
            indicator = "📊"

        output += f"\n{i}. {indicator} [{score}] {sig['signal']}\n"
        output += f"   {sig.get('desc', sig.get('description', ''))}\n"

    if result.get("cached"):
        output += "\n💾 (Cached result)"

    return output


def format_comparison(result: dict[str, Any]) -> str:
    """Format comparison result for Claude display.

    Args:
        result: Comparison result with list of compared securities.

    Returns:
        Formatted string for display.
    """
    output = "📊 Security Comparison\n"

    if result.get("winner"):
        winner = result["winner"]
        output += f"🏆 Top Pick: {winner['symbol']} (Score: {winner['score']:.1f})\n"

    output += "\n"

    for i, item in enumerate(result.get("comparison", []), 1):
        change = item.get("change", 0)
        change_str = f"{change:+.2f}%" if change else "N/A"

        output += f"{i}. {item['symbol']} - Score: {item['score']:.1f}\n"
        output += f"   Price: ${item['price']:.2f} ({change_str})\n"
        output += f"   Signals: {item['bullish']} bullish / {item['bearish']} bearish\n\n"

    return output


def format_screening(result: dict[str, Any]) -> str:
    """Format screening result for Claude display.

    Args:
        result: Screening result with matches and criteria.

    Returns:
        Formatted string for display.
    """
    matches = result.get("matches", [])

    output = f"🔍 Screened {result.get('total_screened', 0)} securities\n"
    output += f"✅ Found {len(matches)} matches\n\n"

    if not matches:
        output += "No securities matched the criteria.\n"
        return output

    for i, match in enumerate(matches[:10], 1):
        output += f"{i}. {match['symbol']} - Score: {match['score']:.1f}\n"
        output += f"   Price: ${match['price']:.2f} | RSI: {match['rsi']:.1f}\n"

    if len(matches) > 10:
        output += f"\n... and {len(matches) - 10} more matches"

    return output


def format_signals_list(signals: list[dict[str, Any]], max_signals: int = MAX_SIGNALS_RETURNED) -> str:
    """Format a list of signals for display.

    Args:
        signals: List of signal dictionaries.
        max_signals: Maximum number of signals to display.

    Returns:
        Formatted string of signals.
    """
    if not signals:
        return "No signals detected."

    output = f"Detected {len(signals)} signals:\n\n"

    for i, sig in enumerate(signals[:max_signals], 1):
        score = sig.get("ai_score", "N/A")
        output += f"{i}. [{score}] {sig['signal']}\n"
        output += f"   {sig.get('desc', sig.get('description', ''))}\n"
        output += f"   Strength: {sig['strength']} | Category: {sig['category']}\n\n"

    if len(signals) > max_signals:
        output += f"... and {len(signals) - max_signals} more signals"

    return output


def format_indicators(indicators: dict[str, Any]) -> str:
    """Format indicator values for display.

    Args:
        indicators: Dictionary of indicator values.

    Returns:
        Formatted string of indicators.
    """
    output = "📈 Key Indicators:\n"

    key_indicators = [
        ("RSI", "rsi", ".1f"),
        ("MACD", "macd", ".4f"),
        ("ADX", "adx", ".1f"),
        ("Volume", "volume", ",d"),
    ]

    for label, key, fmt in key_indicators:
        if key in indicators:
            value = indicators[key]
            output += f"• {label}: {value:{fmt}}\n"

    return output


def format_error(error: Exception, symbol: str | None = None) -> str:
    """Format an error for display.

    Args:
        error: The exception that occurred.
        symbol: Optional symbol context.

    Returns:
        Formatted error message.
    """
    output = "❌ Error"

    if symbol:
        output += f" analyzing {symbol}"

    output += f": {error}\n"

    return output


# ============================================================================
# Risk Layer Formatters (Trade Plans and Risk Analysis)
# ============================================================================


def format_trade_plan(plan: Any) -> str:
    """Format a single trade plan for display.

    Args:
        plan: TradePlan object from risk assessment.

    Returns:
        Formatted trade plan string.
    """
    from .risk.models import TradePlan, Bias, RiskQuality

    # Determine emoji based on bias and quality
    bias_emoji = {
        "bullish": "🟢",
        "bearish": "🔴",
        "neutral": "⚪",
    }.get(plan.bias.value if isinstance(plan.bias, Bias) else plan.bias, "⚪")

    quality_emoji = {
        "high": "🔥",
        "medium": "⚡",
        "low": "⚠️",
    }.get(
        plan.risk_quality.value if isinstance(plan.risk_quality, RiskQuality) else plan.risk_quality,
        "⚠️",
    )

    output = f"""
{quality_emoji} {plan.symbol} Trade Plan ({plan.timeframe.value.upper()})
{bias_emoji} Bias: {plan.bias.value.upper() if isinstance(plan.bias, Bias) else plan.bias.upper()}

📍 Levels:
• Entry: ${plan.entry_price:.2f}
• Stop: ${plan.stop_price:.2f} ({plan.max_loss_percent:.1f}% risk)
• Target: ${plan.target_price:.2f} ({plan.expected_move_percent:.1f}% move)
• Invalidation: ${plan.invalidation_price:.2f}

📊 Risk Profile:
• R:R Ratio: {plan.risk_reward_ratio:.2f}:1
• Quality: {plan.risk_quality.value.upper() if isinstance(plan.risk_quality, RiskQuality) else plan.risk_quality.upper()}

🎯 Vehicle: {plan.vehicle.value.upper() if hasattr(plan.vehicle, 'value') else str(plan.vehicle).upper()}
"""

    if plan.vehicle_notes:
        output += f"   Note: {plan.vehicle_notes}\n"

    # Add option details if present
    if hasattr(plan, 'option_dte_range') and plan.option_dte_range:
        output += f"   • DTE Range: {plan.option_dte_range[0]}-{plan.option_dte_range[1]} days\n"
    if hasattr(plan, 'option_delta_range') and plan.option_delta_range:
        output += f"   • Delta Range: {plan.option_delta_range[0]:.2f} to {plan.option_delta_range[1]:.2f}\n"
    if hasattr(plan, 'option_spread_width') and plan.option_spread_width:
        output += f"   • Spread Width: ${plan.option_spread_width:.2f}\n"

    output += f"""
📈 Signal Basis:
• Primary: {plan.primary_signal}
"""

    for sig in plan.supporting_signals:
        output += f"• Supporting: {sig}\n"

    return output


def format_risk_analysis(result: Any) -> str:
    """Format complete risk analysis output.

    Args:
        result: RiskAnalysisResult from risk assessor.

    Returns:
        Formatted analysis string.
    """
    from .risk.models import RiskAnalysisResult

    if result.has_trades:
        output = f"📊 {result.symbol} Risk Analysis - Trade Opportunities\n\n"
        output += f"Found {len(result.trade_plans)} actionable trade plan(s)\n\n"

        for i, plan in enumerate(result.trade_plans, 1):
            output += f"--- Trade Plan {i} ---\n"
            output += format_trade_plan(plan)
            output += "\n"
    else:
        output = f"❌ {result.symbol}: No Trades\n\n"
        output += "Suppression Reasons:\n"

        for reason in result.all_suppressions:
            output += f"• [{reason.code.value}] {reason.message}\n"
            if reason.threshold is not None and reason.actual is not None:
                output += (
                    f"  (Threshold: {reason.threshold:.2f}, "
                    f"Actual: {reason.actual:.2f})\n"
                )

    return output


def format_suppression_summary(suppressions: tuple[Any, ...]) -> str:
    """Format suppression reasons for display.

    Args:
        suppressions: Tuple of SuppressionReason objects.

    Returns:
        Formatted suppression summary.
    """
    if not suppressions:
        return "✅ No suppressions - setup qualifies for trading"

    output = "❌ Setup suppressed for the following reasons:\n\n"

    for i, reason in enumerate(suppressions, 1):
        code = reason.code.value if hasattr(reason.code, 'value') else str(reason.code)
        output += f"{i}. [{code}] {reason.message}\n"

        if reason.threshold is not None and reason.actual is not None:
            output += (
                f"   Threshold: {reason.threshold:.2f}, "
                f"Actual: {reason.actual:.2f}\n"
            )

    return output


def format_scan_results(result: dict[str, Any]) -> str:
    """Format scan results for display.

    Args:
        result: Scan results from TradeScanner.

    Returns:
        Formatted scan results string.
    """
    universe = result.get("universe", "unknown")
    total_scanned = result.get("total_scanned", 0)
    qualified_trades = result.get("qualified_trades", [])
    duration = result.get("duration_seconds", 0)

    output = f"🔍 Smart Trade Scan - {universe.upper()}\n\n"
    output += f"Found {len(qualified_trades)} qualified setup(s) "
    output += f"(scanned {total_scanned} securities in {duration:.1f} seconds)\n\n"

    if not qualified_trades:
        output += "No qualified trades found in this universe.\n"
        return output

    # Group by quality
    high_quality = [t for t in qualified_trades if t.get("risk_quality") == "high"]
    medium_quality = [t for t in qualified_trades if t.get("risk_quality") == "medium"]
    low_quality = [t for t in qualified_trades if t.get("risk_quality") == "low"]

    if high_quality:
        output += f"🔥 HIGH QUALITY TRADES ({len(high_quality)}):\n"
        for i, trade in enumerate(high_quality, 1):
            output += _format_scan_trade(i, trade)
        output += "\n"

    if medium_quality:
        output += f"⚡ MEDIUM QUALITY TRADES ({len(medium_quality)}):\n"
        for i, trade in enumerate(medium_quality, 1):
            output += _format_scan_trade(i, trade)
        output += "\n"

    if low_quality:
        output += f"⚠️ LOW QUALITY TRADES ({len(low_quality)}):\n"
        for i, trade in enumerate(low_quality, 1):
            output += _format_scan_trade(i, trade)
        output += "\n"

    output += f"Scan completed in {duration:.1f} seconds"

    return output


def _format_scan_trade(index: int, trade: dict[str, Any]) -> str:
    """Format a single scan trade result.

    Args:
        index: Trade index in results.
        trade: Trade result dictionary.

    Returns:
        Formatted trade string.
    """
    output = f"{index}. {trade.get('symbol', 'N/A')} - "
    output += f"${trade.get('entry_price', 0):.2f} entry | "
    output += f"${trade.get('stop_price', 0):.2f} stop | "
    output += f"${trade.get('target_price', 0):.2f} target\n"
    output += f"   R:R: {trade.get('risk_reward_ratio', 0):.2f}:1 | "
    output += f"Bias: {trade.get('bias', 'NEUTRAL').upper()} | "
    output += f"Timeframe: {trade.get('timeframe', 'SWING').upper()}\n"
    output += f"   Signal: {trade.get('primary_signal', 'N/A')}\n\n"

    return output


def format_portfolio_risk(result: dict[str, Any]) -> str:
    """Format portfolio risk assessment for display.

    Args:
        result: Portfolio risk assessment from PortfolioRiskAssessor.

    Returns:
        Formatted portfolio risk string.
    """
    total_value = result.get("total_value", 0)
    total_max_loss = result.get("total_max_loss", 0)
    risk_percent = result.get("risk_percent_of_portfolio", 0)
    overall_risk = result.get("overall_risk_level", "UNKNOWN")
    positions = result.get("positions", [])
    sector_concentration = result.get("sector_concentration", {})
    hedge_suggestions = result.get("hedge_suggestions", [])

    # Risk level emoji
    risk_emoji = {
        "LOW": "🟢",
        "MEDIUM": "🟡",
        "HIGH": "🔴",
        "CRITICAL": "🚨",
    }.get(overall_risk, "⚪")

    output = f"📊 Portfolio Risk Assessment\n\n"
    output += f"Portfolio Value: ${total_value:,.2f}\n"
    output += f"Maximum Loss: ${total_max_loss:,.2f} ({risk_percent:.1f}% of portfolio)\n"
    output += f"Risk Level: {risk_emoji} {overall_risk}\n\n"

    # Position breakdown
    output += "POSITION BREAKDOWN:\n"
    for i, pos in enumerate(positions, 1):
        symbol = pos.get("symbol", "N/A")
        shares = pos.get("shares", 0)
        entry = pos.get("entry_price", 0)
        current = pos.get("current_price", 0)
        current_value = pos.get("current_value", 0)
        max_loss = pos.get("max_loss_dollar", 0)
        max_loss_pct = pos.get("max_loss_percent", 0)
        risk_quality = pos.get("risk_quality", "unknown").upper()
        stop = pos.get("stop_level", 0)

        output += f"{i}. {symbol} ({shares:.0f} shares @ ${entry:.2f})\n"
        output += f"   Current: ${current_value:,.2f} | Max Loss: ${max_loss:,.2f} | Risk: {max_loss_pct:.1f}%\n"
        output += f"   Stop: ${stop:.2f} | Quality: {risk_quality}\n\n"

    # Sector concentration
    if sector_concentration:
        output += "SECTOR CONCENTRATION:\n"
        for sector, pct in sorted(
            sector_concentration.items(), key=lambda x: x[1], reverse=True
        ):
            conc_indicator = "⚠️ Concentrated" if pct > 40 else ""
            output += f"• {sector}: {pct:.1f}% {conc_indicator}\n"
        output += "\n"

    # Hedge suggestions
    if hedge_suggestions:
        output += "HEDGING SUGGESTIONS:\n"
        for suggestion in hedge_suggestions:
            output += f"• {suggestion}\n"
    else:
        output += "No immediate hedging needed - portfolio is well-diversified\n"

    return output


def format_morning_brief(result: dict[str, Any]) -> str:
    """Format morning market briefing for display.

    Args:
        result: Morning brief from MorningBriefGenerator.

    Returns:
        Formatted morning brief string.
    """
    market_status = result.get("market_status", {})
    economic_events = result.get("economic_events", [])
    watchlist_signals = result.get("watchlist_signals", [])
    sector_leaders = result.get("sector_leaders", [])
    sector_losers = result.get("sector_losers", [])
    key_themes = result.get("key_themes", [])

    # Market status
    market_open = market_status.get("market_status", "UNKNOWN")
    status_emoji = {
        "OPEN": "🟢",
        "PRE_MARKET": "🔵",
        "AFTER_HOURS": "🟠",
        "CLOSED": "⚪",
    }.get(market_open, "❓")

    output = f"# 📈 Morning Market Brief\n\n"
    output += f"**Market Status**: {status_emoji} {market_open}"
    output += f" ({market_status.get('market_hours_remaining', '')})\n"

    # Futures
    futures_es = market_status.get("futures_es", {})
    futures_nq = market_status.get("futures_nq", {})
    output += f"- Futures: ES {futures_es.get('change_percent', 0):+.2f}% | "
    output += f"NQ {futures_nq.get('change_percent', 0):+.2f}% | "
    output += f"VIX {market_status.get('vix', 0):.2f}\n\n"

    # Economic calendar
    if economic_events:
        output += "## 📊 Economic Calendar\n\n"

        high_importance = [e for e in economic_events if e.get("importance") == "HIGH"]
        if high_importance:
            output += "**HIGH IMPORTANCE (Today)**\n"
            for event in high_importance:
                output += f"• {event.get('timestamp')} ET - {event.get('event_name')}"
                output += f" (Forecast: {event.get('forecast')} | Previous: {event.get('previous')})\n"
            output += "\n"

        medium_importance = [e for e in economic_events if e.get("importance") == "MEDIUM"]
        if medium_importance:
            output += "**MEDIUM IMPORTANCE**\n"
            for event in medium_importance:
                output += f"• {event.get('timestamp')} ET - {event.get('event_name')}\n"
            output += "\n"

    # Watchlist signals
    if watchlist_signals:
        output += "## 🎯 Watchlist Signals (Top Picks)\n\n"
        for signal in watchlist_signals[:5]:
            symbol = signal.get("symbol", "N/A")
            price = signal.get("price", 0)
            change = signal.get("change_percent", 0)
            action = signal.get("action", "HOLD")
            risk_assess = signal.get("risk_assessment", "HOLD")
            signals = signal.get("top_signals", [])
            support = signal.get("key_support", 0)
            resistance = signal.get("key_resistance", 0)

            # Action emoji
            action_emoji = {
                "BUY": "🟢",
                "HOLD": "⚡",
                "AVOID": "🔴",
            }.get(action, "⚪")

            output += f"### {action_emoji} {action} - {symbol} (${price:.2f} {change:+.1f}%)\n"
            output += f"- Signals: {', '.join(signals[:3]) if signals else 'N/A'}\n"
            output += f"- Risk Assessment: {risk_assess}\n"
            output += f"- Support: ${support:.2f} | Resistance: ${resistance:.2f}\n"
            output += f"- Action: **{action}**\n\n"

    # Sector movers
    if sector_leaders or sector_losers:
        output += "## 🏆 Sector Leaders/Losers\n\n"

        if sector_leaders:
            output += "**Top Gainers**: "
            output += ", ".join(
                f"{s.get('sector')} {s.get('change_percent', 0):+.1f}%"
                for s in sector_leaders
            )
            output += "\n"

        if sector_losers:
            output += "**Top Losers**: "
            output += ", ".join(
                f"{s.get('sector')} {s.get('change_percent', 0):+.1f}%"
                for s in sector_losers
            )
            output += "\n\n"

    # Key themes
    if key_themes:
        output += "## 🎪 Key Market Themes\n\n"
        for i, theme in enumerate(key_themes, 1):
            output += f"{i}. **{theme}**\n"

    return output
