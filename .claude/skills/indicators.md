# /indicators - Technical Indicator Dashboard

Display all calculated technical indicators for a stock with color-coded thresholds.

## Usage

```
/indicators SYMBOL [OPTIONS]
```

**Options:**
- `/indicators AAPL` - Show all indicators for Apple
- `/indicators MU --compare SPY` - Compare MU indicators vs SPY benchmark
- `/indicators NVDA --history 5` - Show last 5 days of indicator values
- `/indicators TSLA --category momentum` - Show only momentum indicators
- `/indicators GOOGL --export` - Export to CSV file

**Examples:**
- `/indicators AAPL` - Full indicator dashboard
- `/indicators NVDA --compare QQQ` - Compare against tech ETF
- `/indicators META --category trend` - Trend indicators only

## Behavior

When this skill is invoked:

1. **Fetch data** for the symbol using CachedDataFetcher
2. **Calculate all indicators** using calculate_all_indicators()
3. **Extract current values** using calculate_indicators_dict()
4. **Apply thresholds** for color-coding
5. **Display dashboard** with interpretations

## Implementation

```python
import sys
sys.path.insert(0, 'src')

from technical_analysis_mcp.data import CachedDataFetcher
from technical_analysis_mcp.indicators import calculate_all_indicators, calculate_indicators_dict

def get_indicator_status(name: str, value: float) -> tuple[str, str]:
    """Get status and color for indicator value."""
    thresholds = {
        'rsi': [(30, 'OVERSOLD', 'green'), (40, 'APPROACHING OVERSOLD', 'yellow'),
                (60, 'NEUTRAL', 'white'), (70, 'APPROACHING OVERBOUGHT', 'yellow'),
                (100, 'OVERBOUGHT', 'red')],
        'stoch_k': [(20, 'OVERSOLD', 'green'), (80, 'NEUTRAL', 'white'),
                    (100, 'OVERBOUGHT', 'red')],
        'adx': [(20, 'WEAK TREND', 'yellow'), (25, 'TRENDING', 'white'),
                (50, 'STRONG TREND', 'green'), (100, 'VERY STRONG', 'green')],
        # ... more thresholds
    }

    if name in thresholds:
        for threshold, status, color in thresholds[name]:
            if value <= threshold:
                return status, color
    return 'N/A', 'white'

def display_indicators(symbol: str, period: str = '3mo'):
    """Fetch and display all indicators for a symbol."""
    fetcher = CachedDataFetcher()
    df = fetcher.fetch(symbol, period)
    df = calculate_all_indicators(df)
    indicators = calculate_indicators_dict(df)

    # Get price info
    price = float(df['Close'].iloc[-1])
    change = float((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100)

    return {
        'symbol': symbol,
        'price': price,
        'change_pct': change,
        'indicators': indicators
    }
```

## Indicator Categories

### Momentum Indicators

| Indicator | Range | Oversold | Neutral | Overbought |
|-----------|-------|----------|---------|------------|
| RSI(14) | 0-100 | < 30 | 30-70 | > 70 |
| Stoch %K | 0-100 | < 20 | 20-80 | > 80 |
| Stoch %D | 0-100 | < 20 | 20-80 | > 80 |

### Trend Indicators

| Indicator | Interpretation |
|-----------|----------------|
| MACD | > 0 = Bullish, < 0 = Bearish |
| MACD Signal | Crossover triggers |
| MACD Histogram | Momentum strength |
| ADX | < 20 = Weak, 20-25 = Emerging, > 25 = Strong |
| +DI / -DI | Trend direction |

### Moving Averages

| Indicator | Bullish | Bearish |
|-----------|---------|---------|
| Price vs SMA20 | Above | Below |
| Price vs SMA50 | Above | Below |
| SMA20 vs SMA50 | Above (uptrend) | Below (downtrend) |
| Price vs EMA20 | Above | Below |

### Volatility Indicators

| Indicator | Interpretation |
|-----------|----------------|
| ATR(14) | Average daily range |
| BB Width | Volatility measure |
| Price in BB | Position within bands |

### Volume Indicators

| Indicator | Interpretation |
|-----------|----------------|
| Volume Ratio | > 1.5 = High, < 0.5 = Low |
| OBV Trend | Rising = Accumulation |

## Output Format

### Full Dashboard

```
══════════════════════════════════════════════════════════════
  INDICATORS: AAPL
  Price: $267.26 (-1.38%)
  Period: 3 months (63 trading days)
══════════════════════════════════════════════════════════════

  MOMENTUM
  ──────────────────────────────────────────────────────────
  RSI(14)         45.3      [NEUTRAL]
  Stoch %K        62.1      [NEUTRAL]
  Stoch %D        58.4      [NEUTRAL]

  Interpretation: Momentum is neutral with no extreme readings.
                  Room for movement in either direction.

  TREND
  ──────────────────────────────────────────────────────────
  MACD            0.52      [BULLISH]     ▲
  MACD Signal     0.38
  MACD Histogram  0.14      [RISING]      ▲
  ADX             28.4      [TRENDING]
  +DI             24.2
  -DI             18.7      [BULLISH]     +DI > -DI

  Interpretation: Moderate uptrend with strengthening momentum.
                  MACD above signal line is bullish.

  MOVING AVERAGES
  ──────────────────────────────────────────────────────────
  SMA 20          $264.50   Price +1.0% above
  SMA 50          $258.20   Price +3.5% above
  EMA 20          $265.10   Price +0.8% above
  SMA 200         $242.30   Price +10.3% above

  Alignment: Price > SMA20 > SMA50 > SMA200 [BULLISH STACK]

  BOLLINGER BANDS
  ──────────────────────────────────────────────────────────
  Upper Band      $275.80
  Middle Band     $264.50   (SMA20)
  Lower Band      $253.20
  BB Width        8.5%      [NORMAL]
  Price Position  Upper 60% [BULLISH LEAN]

  Interpretation: Price in upper half of bands, no squeeze.

  VOLATILITY
  ──────────────────────────────────────────────────────────
  ATR(14)         $4.21     (1.6% of price)
  Volatility      24.5%     (annualized)

  Interpretation: Average volatility for this stock.

  VOLUME
  ──────────────────────────────────────────────────────────
  Current Vol     52.3M
  Avg Vol (20d)   48.1M
  Vol Ratio       1.09x     [NORMAL]
  OBV Trend       RISING    [ACCUMULATION]

  Interpretation: Normal volume with accumulation pattern.

══════════════════════════════════════════════════════════════
  SUMMARY
══════════════════════════════════════════════════════════════

  Overall Bias: BULLISH

  Key Points:
  ├─ ✓ Price above all major moving averages
  ├─ ✓ MACD bullish with rising histogram
  ├─ ✓ ADX shows trending market (28.4)
  ├─ ○ RSI neutral (45.3) - not overbought
  └─ ○ Volume normal - watching for confirmation

  Potential Actions:
  ├─ Support: $258.20 (SMA50)
  ├─ Resistance: $275.80 (BB Upper)
  └─ Stop Loss: $253.20 (BB Lower)

══════════════════════════════════════════════════════════════
```

### Comparison Mode (--compare)

```
══════════════════════════════════════════════════════════════
  INDICATOR COMPARISON: MU vs SPY
══════════════════════════════════════════════════════════════

  MOMENTUM
  ──────────────────────────────────────────────────────────
                  MU          SPY         Diff
  RSI(14)         38.2        52.4        -14.2  [MU weaker]
  Stoch %K        42.1        58.3        -16.2  [MU weaker]
  ADX             32.1        24.8        +7.3   [MU trending more]

  TREND
  ──────────────────────────────────────────────────────────
                  MU          SPY
  MACD            -0.82       0.45        [MU bearish, SPY bullish]
  vs SMA50        -2.3%       +1.8%       [MU below, SPY above]

  RELATIVE STRENGTH
  ──────────────────────────────────────────────────────────
  MU vs SPY (20d): -8.4%     [MU underperforming]
  MU vs SPY (50d): -12.1%    [MU underperforming]

  Interpretation: MU is underperforming the broader market.
                  Consider waiting for relative strength to improve.

══════════════════════════════════════════════════════════════
```

### Historical Mode (--history 5)

```
══════════════════════════════════════════════════════════════
  INDICATOR HISTORY: NVDA (Last 5 Days)
══════════════════════════════════════════════════════════════

  DATE        CLOSE     RSI     MACD    ADX     STOCH
  ─────────────────────────────────────────────────────────
  2026-01-06  $188.12   45.3    0.52    28.4    62.1
  2026-01-03  $190.45   48.2    0.61    27.8    65.4
  2026-01-02  $185.30   42.1    0.38    26.2    55.2
  2025-12-31  $182.90   38.5    0.15    24.5    48.3
  2025-12-30  $180.20   35.2   -0.12    23.1    42.1

  TREND ANALYSIS:
  ├─ RSI: Rising from 35.2 to 45.3 (+10.1)
  ├─ MACD: Turned positive, rising
  ├─ ADX: Strengthening (23.1 → 28.4)
  └─ Stoch: Rising from oversold

  Interpretation: Indicators improving across the board.
                  Momentum building for potential move higher.

══════════════════════════════════════════════════════════════
```

## Color Coding

| Color | Meaning |
|-------|---------|
| Green | Bullish / Oversold (buy opportunity) |
| Red | Bearish / Overbought (sell signal) |
| Yellow | Caution / Approaching extreme |
| White | Neutral |

## Error Handling

```
  ERROR: INVALID
  └─ Symbol not found or no data available

  Suggestions:
  - Verify the symbol is correct (e.g., AAPL not APPLE)
  - For crypto, use format: BTC-USD
  - Check if market is open
```

## Dependencies

- `src/technical_analysis_mcp/data.py` - Data fetching
- `src/technical_analysis_mcp/indicators.py` - All calculations
- yfinance, pandas, numpy

## Notes

- All indicators calculated from 3-month daily data
- Historical mode limited to available data
- Comparison mode requires valid benchmark symbol
- Export creates indicators_{symbol}.csv in current directory
- Use /signals for actionable trading signals
- Use /analyze for complete analysis with AI ranking
