# /signals - Signal Detection Report

Generate comprehensive trading signal reports for stocks in your watchlist.

## Usage

```
/signals [SYMBOLS...] [OPTIONS]
```

**Options:**
- `/signals` - Analyze default watchlist (15 stocks)
- `/signals AAPL MSFT NVDA` - Analyze specific symbols
- `/signals --bullish` - Show only bullish signals
- `/signals --bearish` - Show only bearish signals
- `/signals --strong` - Show only STRONG signals
- `/signals --category RSI` - Filter by category (RSI, MACD, VOLUME, TREND, etc.)
- `/signals --export csv` - Export to CSV file
- `/signals --export json` - Export to JSON file

**Examples:**
- `/signals` - Full report for default watchlist
- `/signals --bullish --strong` - Strong bullish signals only
- `/signals AAPL NVDA --category MACD` - MACD signals for AAPL and NVDA
- `/signals --export csv` - Export all signals to signals_report.csv

## Behavior

When this skill is invoked:

1. **Fetch data** for each symbol using YFinanceDataFetcher
2. **Calculate indicators** using calculate_all_indicators()
3. **Detect signals** using detect_all_signals()
4. **Filter and sort** based on options
5. **Display report** grouped by strength/category

## Implementation

```python
import sys
sys.path.insert(0, 'src')

from technical_analysis_mcp.data import CachedDataFetcher
from technical_analysis_mcp.indicators import calculate_all_indicators
from technical_analysis_mcp.signals import detect_all_signals
from technical_analysis_mcp.config import DEFAULT_PERIOD

DEFAULT_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'MU', 'AMD', 'TSLA', 'META', 'SPY',
    'QQQ', 'IWM', 'XLF', 'XLK', 'DIA'
]

def get_signals_for_symbol(symbol: str, fetcher, period: str = '3mo'):
    """Detect all signals for a single symbol."""
    try:
        df = fetcher.fetch(symbol, period)
        df = calculate_all_indicators(df)
        signals = detect_all_signals(df)

        # Get current price
        price = float(df['Close'].iloc[-1])
        change = float((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100)

        return {
            'symbol': symbol,
            'price': price,
            'change_pct': change,
            'signals': signals,
            'signal_count': len(signals)
        }
    except Exception as e:
        return {'symbol': symbol, 'error': str(e), 'signals': []}

# Parse arguments
symbols = [arg.upper() for arg in args if not arg.startswith('--')]
if not symbols:
    symbols = DEFAULT_WATCHLIST

# Detect signals for each symbol
fetcher = CachedDataFetcher()
all_results = []
for symbol in symbols:
    result = get_signals_for_symbol(symbol, fetcher)
    all_results.append(result)
```

## Signal Categories

The system detects signals in these categories:

| Category | Signal Types |
|----------|--------------|
| **RSI** | Oversold, Overbought, Divergence |
| **MACD** | Bullish Crossover, Bearish Crossover, Histogram |
| **TREND** | Uptrend, Downtrend, Trend Reversal |
| **MA_CROSS** | Golden Cross, Death Cross, MA Alignment |
| **BOLLINGER** | Upper Band Touch, Lower Band Touch, Squeeze |
| **STOCHASTIC** | Overbought, Oversold, Crossover |
| **VOLUME** | Volume Spike 2x, Volume Spike 3x, Drying Up |
| **PRICE** | Large Move, Gap Up, Gap Down |

## Signal Strengths

| Strength | Description |
|----------|-------------|
| **STRONG BULLISH** | High-confidence buy signal |
| **BULLISH** | Moderate buy signal |
| **NOTABLE** | Worth watching |
| **BEARISH** | Moderate sell signal |
| **STRONG BEARISH** | High-confidence sell signal |

## Output Format

### Full Report

```
══════════════════════════════════════════════════════════════
  SIGNAL REPORT
  Generated: 2026-01-06 12:30:00 UTC
  Stocks Analyzed: 15
  Total Signals: 47
══════════════════════════════════════════════════════════════

  STRONG BULLISH (4 signals)
  ──────────────────────────────────────────────────────────
  META  $658.79 (+1.29%)
  ├─ RSI Oversold (28.3) - Strong reversal potential
  └─ Volume Spike 3x - Institutional accumulation

  NVDA  $188.12 (-0.39%)
  ├─ Golden Cross Forming - SMA20 crossing above SMA50
  └─ MACD Bullish Crossover - Momentum turning positive

  BULLISH (8 signals)
  ──────────────────────────────────────────────────────────
  AAPL  $267.26 (-1.38%)
  ├─ Price Above SMA50 - Uptrend intact
  ├─ RSI Approaching Oversold (38.2) - Potential bounce
  └─ Bollinger Lower Band Touch - Mean reversion setup

  AMD   $221.08 (-1.07%)
  ├─ MACD Histogram Rising - Momentum building
  └─ Volume Above Average (1.5x) - Confirmation

  [... more stocks ...]

  STRONG BEARISH (2 signals)
  ──────────────────────────────────────────────────────────
  MSFT  $472.85 (-0.02%)
  ├─ Death Cross Forming - SMA20 below SMA50
  └─ RSI Overbought (72.1) - Potential pullback

══════════════════════════════════════════════════════════════
  SUMMARY BY CATEGORY
══════════════════════════════════════════════════════════════

  RSI Signals:        12 (5 bullish, 7 bearish)
  MACD Signals:       8  (4 bullish, 4 bearish)
  Trend Signals:      10 (6 bullish, 4 bearish)
  Volume Signals:     7  (5 bullish, 2 bearish)
  Bollinger Signals:  6  (3 bullish, 3 bearish)
  Other:              4

══════════════════════════════════════════════════════════════
  ACTIONABLE SUMMARY
══════════════════════════════════════════════════════════════

  BUY Candidates:  META, NVDA, XLF
  SELL Candidates: MSFT, TSLA
  Watch List:      AAPL, AMD, GOOGL

══════════════════════════════════════════════════════════════
```

### Filtered Report (--bullish --strong)

```
══════════════════════════════════════════════════════════════
  SIGNAL REPORT: Strong Bullish Only
══════════════════════════════════════════════════════════════

  META  $658.79 (+1.29%)
  ├─ RSI Oversold (28.3)
  │   Strength: STRONG BULLISH
  │   Category: RSI
  │   Action: Consider buying - oversold with reversal signs
  └─ Volume Spike 3x (3.2x avg)
      Strength: STRONG BULLISH
      Category: VOLUME
      Action: Institutional interest detected

  NVDA  $188.12 (-0.39%)
  └─ Golden Cross Forming
      Strength: STRONG BULLISH
      Category: MA_CROSS
      Action: Major trend reversal - accumulate on dips

  Total: 4 strong bullish signals across 2 stocks

══════════════════════════════════════════════════════════════
```

### CSV Export Format

```csv
symbol,price,change_pct,signal,strength,category,value,timestamp
META,658.79,1.29,RSI Oversold,STRONG BULLISH,RSI,28.3,2026-01-06T12:30:00
META,658.79,1.29,Volume Spike 3x,STRONG BULLISH,VOLUME,3.2,2026-01-06T12:30:00
NVDA,188.12,-0.39,Golden Cross Forming,STRONG BULLISH,MA_CROSS,,2026-01-06T12:30:00
...
```

## Error Handling

```
  ERRORS (2 symbols)
  ──────────────────────────────────────────────────────────
  INVALID  - Invalid symbol or no data available
  CRYPTO   - Symbol not supported (use BTC-USD format for crypto)

  Successfully analyzed: 13/15 stocks
```

## Rate Limiting

- Uses cached data fetcher (5-minute TTL)
- Sequential processing to avoid API limits
- Large watchlists may take 30-60 seconds

## Dependencies

- `src/technical_analysis_mcp/data.py` - Data fetching
- `src/technical_analysis_mcp/indicators.py` - Indicator calculation
- `src/technical_analysis_mcp/signals.py` - Signal detection
- yfinance, pandas, numpy

## Notes

- Default period is 3 months for signal accuracy
- Signals are detected on the most recent data point
- Export creates file in current directory
- Use `/analyze` for deeper single-stock analysis
- Use `/ai-rank` for AI-powered signal ranking
