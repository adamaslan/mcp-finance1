# /analyze - Quick Stock Analysis

Run instant technical analysis on any stock symbol using the unified StockAnalyzer.

## Usage

```
/analyze SYMBOL [--period PERIOD]
```

**Examples:**
- `/analyze AAPL` - Analyze Apple with default 3-month period
- `/analyze MU --period 6mo` - Analyze Micron with 6-month history
- `/analyze NVDA TSLA META` - Analyze multiple stocks

## Behavior

When this skill is invoked:

1. **Parse the input** to extract symbol(s) and optional period
2. **Run the analysis** using the StockAnalyzer from `src/technical_analysis_mcp/analysis.py`
3. **Display results** in a clean, actionable format

## Implementation

Execute this Python code to run the analysis:

```python
import sys
sys.path.insert(0, 'src')

from technical_analysis_mcp.analysis import StockAnalyzer
from technical_analysis_mcp.exceptions import InvalidSymbolError, DataFetchError, InsufficientDataError

def analyze_stock(symbol: str, period: str = '3mo'):
    """Run complete technical analysis on a stock."""
    analyzer = StockAnalyzer(use_cache=True, use_ai=False)  # AI optional

    try:
        result = analyzer.analyze(symbol, period=period)
        return result
    except (InvalidSymbolError, DataFetchError, InsufficientDataError) as e:
        return {'error': str(e), 'symbol': symbol}

# Parse arguments from skill invocation
symbols = [arg.upper() for arg in args if not arg.startswith('--')]
period = '3mo'  # default
if '--period' in args:
    idx = args.index('--period')
    if idx + 1 < len(args):
        period = args[idx + 1]

# Analyze each symbol
for symbol in symbols:
    result = analyze_stock(symbol, period)
    # Display results...
```

## Output Format

Display results like this:

```
══════════════════════════════════════════════════════════════
  ANALYSIS: {SYMBOL}
══════════════════════════════════════════════════════════════

  Price: ${price:.2f} ({change_pct:+.2f}%)

  SCORE: {score}/100 | Outlook: {outlook} | Action: {action}
  Confidence: {confidence}

  TOP SIGNALS ({signal_count} detected):
  ├─ {signal_1} - {strength_1}
  ├─ {signal_2} - {strength_2}
  └─ {signal_3} - {strength_3}

  KEY INDICATORS:
  ├─ RSI(14):    {rsi:.1f}  [{rsi_status}]
  ├─ MACD:       {macd:.4f} [{macd_status}]
  ├─ ADX:        {adx:.1f}  [{trend_status}]
  └─ Vol Ratio:  {vol_ratio:.1f}x

  AI Summary: {ai_summary}

══════════════════════════════════════════════════════════════
```

## Color Coding (for terminal)

- **BULLISH/BUY**: Green indicators
- **BEARISH/SELL**: Red indicators
- **NEUTRAL/HOLD**: Yellow indicators
- **Score >= 65**: Green
- **Score <= 35**: Red
- **Score 36-64**: Yellow

## Error Handling

If analysis fails, show:

```
  ERROR: {symbol}
  └─ {error_message}

  Suggestions:
  - Verify the symbol is valid (e.g., AAPL not APPLE)
  - Check internet connection
  - Try a shorter period if data is insufficient
```

## Dependencies

- Uses `src/technical_analysis_mcp/analysis.py` (StockAnalyzer)
- Requires yfinance, pandas, numpy
- Optional: Gemini API key for AI-powered ranking

## Notes

- Default period is 3 months (sufficient for most indicators)
- Results are cached for 5 minutes
- Multiple symbols are analyzed sequentially
- AI ranking is disabled by default for speed (use /ai-rank for AI analysis)
