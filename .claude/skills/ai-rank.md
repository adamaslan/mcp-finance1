# /ai-rank - AI-Powered Signal Ranking

Trigger Gemini AI to analyze and rank detected trading signals with confidence scores and reasoning.

## Usage

```
/ai-rank SYMBOL [OPTIONS]
```

**Options:**
- `/ai-rank AAPL` - AI analysis for single stock
- `/ai-rank --watchlist` - AI analysis for full default watchlist
- `/ai-rank NVDA TSLA META` - AI analysis for multiple stocks
- `/ai-rank AAPL --explain` - Include detailed AI reasoning
- `/ai-rank MU --compare` - Compare AI vs rule-based scores
- `/ai-rank --delay 8` - Custom delay between API calls (default: 6.5s)

**Examples:**
- `/ai-rank AAPL` - Quick AI ranking for Apple
- `/ai-rank --watchlist --explain` - Full watchlist with reasoning
- `/ai-rank NVDA --compare` - See how AI differs from rules

## Behavior

When this skill is invoked:

1. **Fetch data** and calculate indicators for each symbol
2. **Detect signals** using the signal detection system
3. **Call Gemini API** with signal context for AI ranking
4. **Parse AI response** for score, outlook, action, confidence
5. **Display results** with optional explanations
6. **Handle rate limits** with exponential backoff

## Implementation

```python
import sys
import os
import time
import json

sys.path.insert(0, 'src')

from technical_analysis_mcp.data import CachedDataFetcher
from technical_analysis_mcp.indicators import calculate_all_indicators, calculate_indicators_dict
from technical_analysis_mcp.signals import detect_all_signals
from technical_analysis_mcp.ranking import GeminiRanking, RuleBasedRanking

# Check for API key
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    print("ERROR: GEMINI_API_KEY not set in environment")
    print("Set it in .env or export GEMINI_API_KEY=your-key")
    sys.exit(1)

DEFAULT_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'MU', 'AMD', 'TSLA', 'META', 'SPY',
    'QQQ', 'IWM', 'XLF', 'XLK', 'DIA'
]

def ai_rank_symbol(symbol: str, fetcher, gemini_ranker, rule_ranker, explain: bool = False):
    """Get AI ranking for a single symbol."""
    try:
        # Fetch and calculate
        df = fetcher.fetch(symbol, '3mo')
        df = calculate_all_indicators(df)
        indicators = calculate_indicators_dict(df)
        signals = detect_all_signals(df)

        # Get price info
        price = float(df['Close'].iloc[-1])
        change = float((df['Close'].iloc[-1] / df['Close'].iloc[-2] - 1) * 100)

        market_data = {
            'price': price,
            'change_pct': change,
            'rsi': indicators.get('rsi'),
            'macd': indicators.get('macd'),
            'adx': indicators.get('adx'),
        }

        # Get AI ranking
        ai_signals = gemini_ranker.rank(signals.copy(), symbol, market_data)

        # Get rule-based for comparison
        rule_signals = rule_ranker.rank(signals.copy(), symbol, market_data)

        return {
            'symbol': symbol,
            'price': price,
            'change_pct': change,
            'indicators': indicators,
            'signal_count': len(signals),
            'ai_result': extract_ranking_result(ai_signals),
            'rule_result': extract_ranking_result(rule_signals),
        }

    except Exception as e:
        return {'symbol': symbol, 'error': str(e)}

def extract_ranking_result(ranked_signals):
    """Extract score and outlook from ranked signals."""
    if not ranked_signals:
        return {'score': 50, 'outlook': 'NEUTRAL', 'action': 'HOLD', 'confidence': 'LOW'}

    # Calculate from signal scores
    scores = [s.score for s in ranked_signals if s.score]
    if scores:
        avg_score = sum(scores) / len(scores)
    else:
        bullish = sum(1 for s in ranked_signals if 'BULLISH' in s.strength)
        bearish = sum(1 for s in ranked_signals if 'BEARISH' in s.strength)
        avg_score = 50 + (bullish - bearish) * 5

    avg_score = max(10, min(90, avg_score))

    if avg_score >= 65:
        outlook, action = 'BULLISH', 'BUY'
    elif avg_score <= 35:
        outlook, action = 'BEARISH', 'SELL'
    else:
        outlook, action = 'NEUTRAL', 'HOLD'

    return {
        'score': int(avg_score),
        'outlook': outlook,
        'action': action,
        'confidence': 'HIGH' if abs(avg_score - 50) > 15 else 'MEDIUM'
    }
```

## Gemini API Prompt

The skill sends this prompt to Gemini:

```
Analyze {SYMBOL} technical signals. Be concise.

PRICE: ${price:.2f} ({change_pct:+.2f}%)
RSI: {rsi:.1f} | MACD: {macd:.4f} | ADX: {adx:.1f}

SIGNALS DETECTED:
[
  {"signal": "RSI Oversold", "strength": "STRONG BULLISH"},
  {"signal": "MACD Bullish Crossover", "strength": "BULLISH"},
  ...
]

Return ONLY valid JSON (no markdown):
{
  "score": 1-100,
  "outlook": "BULLISH/BEARISH/NEUTRAL",
  "action": "BUY/SELL/HOLD",
  "confidence": "HIGH/MEDIUM/LOW",
  "summary": "1 sentence max"
}
```

For `--explain` mode, additional prompt:

```
Also include:
{
  ...
  "reasoning": "2-3 sentences explaining your analysis",
  "key_factors": ["factor1", "factor2", "factor3"],
  "risks": ["risk1", "risk2"],
  "support_level": price,
  "resistance_level": price
}
```

## Rate Limiting

Gemini API free tier: **10 requests per minute**

The skill handles this with:

```python
# Default delay between API calls
DELAY_SECONDS = 6.5  # ~9 requests/min, safely under limit

# Exponential backoff on 429 errors
def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if '429' in str(e):
                delay = 2 ** attempt  # 2s, 4s, 8s
                print(f"Rate limited, waiting {delay}s...")
                time.sleep(delay)
            else:
                raise
    raise Exception("Max retries exceeded")
```

## Output Format

### Single Stock Analysis

```
══════════════════════════════════════════════════════════════
  AI RANKING: AAPL
  Powered by Gemini AI
══════════════════════════════════════════════════════════════

  Price: $267.26 (-1.38%)
  Signals Detected: 5

  AI ANALYSIS
  ──────────────────────────────────────────────────────────
  Score:       72/100
  Outlook:     BULLISH
  Action:      BUY
  Confidence:  HIGH

  Summary:
  "Despite short-term weakness, AAPL shows strong technical
   support with RSI approaching oversold and price holding
   above key moving averages."

══════════════════════════════════════════════════════════════
```

### With Explanation (--explain)

```
══════════════════════════════════════════════════════════════
  AI RANKING: AAPL (Detailed Analysis)
══════════════════════════════════════════════════════════════

  Price: $267.26 (-1.38%)
  Signals Detected: 5

  AI ANALYSIS
  ──────────────────────────────────────────────────────────
  Score:       72/100
  Outlook:     BULLISH
  Action:      BUY
  Confidence:  HIGH

  Summary:
  "Despite short-term weakness, AAPL shows strong technical
   support with RSI approaching oversold and price holding
   above key moving averages."

  DETAILED REASONING
  ──────────────────────────────────────────────────────────
  "The combination of RSI at 38 (approaching oversold) with
   price still above the 50-day SMA suggests a potential
   bounce opportunity. MACD histogram is flattening, which
   often precedes a bullish crossover. Volume has been
   declining during the pullback, indicating weak selling
   pressure."

  Key Factors:
  ├─ RSI approaching oversold (38.2)
  ├─ Price above SMA50 (+3.5%)
  └─ Declining volume on pullback

  Risks:
  ├─ MACD still bearish
  └─ Broader market weakness

  Levels:
  ├─ Support:    $258.20 (SMA50)
  └─ Resistance: $275.80 (recent high)

══════════════════════════════════════════════════════════════
```

### Comparison Mode (--compare)

```
══════════════════════════════════════════════════════════════
  AI vs RULE-BASED COMPARISON: AAPL
══════════════════════════════════════════════════════════════

  Price: $267.26 (-1.38%)

                    AI          RULE-BASED      DIFF
  ──────────────────────────────────────────────────────────
  Score:            72          65              +7
  Outlook:          BULLISH     BULLISH         MATCH
  Action:           BUY         BUY             MATCH
  Confidence:       HIGH        MEDIUM          ▲

  AI Advantage:
  └─ AI detected accumulation pattern from volume analysis
     that rule-based system missed.

  Agreement Rate: 85%

══════════════════════════════════════════════════════════════
```

### Watchlist Mode (--watchlist)

```
══════════════════════════════════════════════════════════════
  AI RANKING: WATCHLIST (15 stocks)
  Processing time: ~110 seconds (rate limited)
══════════════════════════════════════════════════════════════

  Analyzing: AAPL... ✓
  Analyzing: MSFT... ✓
  Analyzing: GOOGL... ✓
  [... progress for each stock ...]

  RESULTS BY SCORE
  ──────────────────────────────────────────────────────────

  TOP BULLISH (Score >= 65)
  ├─ META    Score: 78  BULLISH   BUY   HIGH
  │  └─ "Strong uptrend with institutional accumulation"
  ├─ XLF     Score: 75  BULLISH   BUY   HIGH
  │  └─ "Sector rotation into financials continues"
  ├─ DIA     Score: 72  BULLISH   BUY   MEDIUM
  │  └─ "Blue chips showing relative strength"
  └─ NVDA    Score: 68  BULLISH   BUY   MEDIUM
     └─ "AI demand supporting semiconductor rally"

  NEUTRAL (Score 36-64)
  ├─ AAPL    Score: 58  NEUTRAL   HOLD  MEDIUM
  ├─ GOOGL   Score: 55  NEUTRAL   HOLD  MEDIUM
  ├─ AMZN    Score: 52  NEUTRAL   HOLD  LOW
  └─ [... more ...]

  TOP BEARISH (Score <= 35)
  ├─ MSFT    Score: 32  BEARISH   SELL  HIGH
  │  └─ "Breaking below key support, momentum fading"
  └─ TSLA    Score: 28  BEARISH   SELL  HIGH
     └─ "Death cross forming, high volatility ahead"

══════════════════════════════════════════════════════════════
  SUMMARY
══════════════════════════════════════════════════════════════

  Analyzed:     15 stocks
  AI Calls:     15 (0 errors)
  API Usage:    ~8.2 req/min (within quota)

  Distribution:
  ├─ Bullish:   4 stocks (27%)
  ├─ Neutral:   9 stocks (60%)
  └─ Bearish:   2 stocks (13%)

  Market Sentiment: NEUTRAL-BULLISH

══════════════════════════════════════════════════════════════
```

## Error Handling

### API Key Missing

```
══════════════════════════════════════════════════════════════
  ERROR: Gemini API Key Not Configured
══════════════════════════════════════════════════════════════

  GEMINI_API_KEY environment variable not set.

  Setup:
  1. Get API key: https://aistudio.google.com/app/apikey
  2. Add to .env file:
     GEMINI_API_KEY=your-key-here
  3. Or export:
     export GEMINI_API_KEY=your-key-here

  Fallback: Using rule-based ranking instead.

══════════════════════════════════════════════════════════════
```

### Rate Limit Error

```
══════════════════════════════════════════════════════════════
  WARNING: Rate Limit Reached
══════════════════════════════════════════════════════════════

  Gemini API quota exceeded (10 req/min).

  Actions taken:
  ├─ Waiting 10 seconds before retry...
  ├─ Retrying with exponential backoff...
  └─ ✓ Request succeeded after retry

  Tip: Use --delay 8 for larger watchlists to avoid rate limits.

══════════════════════════════════════════════════════════════
```

### Fallback to Rule-Based

```
  AAPL: AI analysis failed, using rule-based fallback
  ├─ Reason: API timeout
  └─ Score: 65 (rule-based)
```

## Cost Analysis

```
Gemini API Free Tier:
├─ Rate Limit: 10 requests/minute
├─ Daily Limit: Unlimited (within rate)
└─ Cost: $0

Typical Usage:
├─ Single stock: 1 API call
├─ Watchlist (15): 15 API calls (~2 minutes)
├─ Daily usage: ~30-50 calls
└─ Monthly: ~1000-1500 calls

Cost: $0 (within free tier)
```

## Dependencies

- `src/technical_analysis_mcp/ranking.py` - GeminiRanking class
- `google-generativeai` Python package
- GEMINI_API_KEY environment variable
- Internet connection for API calls

## Notes

- AI ranking adds ~1-2 seconds per stock (API latency)
- Rate limiting delays add ~6.5 seconds between stocks
- Full watchlist takes ~2 minutes due to rate limits
- Results are not cached (fresh AI analysis each time)
- Use `/analyze` for quick analysis without detailed AI reasoning
- Use `/signals` for signal detection without AI ranking
- Fallback to rule-based if API fails
