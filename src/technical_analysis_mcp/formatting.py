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
