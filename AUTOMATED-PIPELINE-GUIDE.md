# Automated Technical Analysis Pipeline

A comprehensive guide to the GCP-powered stock analysis automation system.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Component Deep Dive](#component-deep-dive)
3. [Data Flow](#data-flow)
4. [Technical Indicators](#technical-indicators)
5. [Signal Detection](#signal-detection)
6. [AI Ranking System](#ai-ranking-system)
7. [Storage & Retrieval](#storage--retrieval)
8. [Usage Tips](#usage-tips)
9. [20 Ways to Expand](#20-ways-to-expand)

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AUTOMATED PIPELINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │    Cloud     │───▶│   Pub/Sub    │───▶│   Cloud Function     │  │
│  │  Scheduler   │    │    Topic     │    │  (Python 3.11)       │  │
│  │              │    │              │    │                      │  │
│  │ Mon-Fri      │    │ Message      │    │ • Fetch Data         │  │
│  │ 4:30 PM ET   │    │ Queue        │    │ • Calculate Indicators│  │
│  └──────────────┘    └──────────────┘    │ • Detect Signals     │  │
│                                          │ • AI Ranking         │  │
│                                          └──────────┬───────────┘  │
│                                                     │              │
│                    ┌────────────────────────────────┼──────────┐   │
│                    │                                │          │   │
│                    ▼                                ▼          │   │
│  ┌──────────────────────┐              ┌──────────────────┐   │   │
│  │      Firestore       │              │    Gemini AI     │   │   │
│  │                      │              │                  │   │   │
│  │ • analysis/{symbol}  │              │ • Score signals  │   │   │
│  │ • summaries/{date}   │              │ • Generate       │   │   │
│  │ • Historical data    │              │   insights       │   │   │
│  └──────────────────────┘              └──────────────────┘   │   │
│                                                               │   │
└───────────────────────────────────────────────────────────────────┘
```

### Components Summary

| Component | Purpose | Free Tier Limit |
|-----------|---------|-----------------|
| **Cloud Scheduler** | Triggers analysis on schedule | 3 jobs |
| **Pub/Sub** | Message queue for reliability | 10 GB/month |
| **Cloud Functions** | Serverless compute | 2M invocations/month |
| **Firestore** | NoSQL database for results | 1 GB storage |
| **Gemini AI** | Intelligent signal ranking | 1,500 requests/day |
| **yfinance** | Market data source | Unlimited (free) |

---

## Component Deep Dive

### 1. Cloud Scheduler

The scheduler acts as the automation trigger, firing at specified times.

**Configuration:**
```
Schedule: 30 16 * * 1-5  (cron format)
Timezone: America/New_York
Meaning:  Every weekday at 4:30 PM ET (30 min after market close)
```

**Why 4:30 PM ET?**
- Market closes at 4:00 PM ET
- 30-minute buffer ensures final prices are settled
- After-hours data excluded for consistency
- Weekdays only (Mon-Fri) to avoid empty market days

**Scheduler Message Payload:**
```json
{
  "trigger": "scheduled",
  "type": "daily",
  "timestamp": "2024-01-15T21:30:00Z"
}
```

### 2. Pub/Sub Topic

Provides reliable message delivery between scheduler and function.

**Benefits:**
- **Decoupling**: Scheduler and function operate independently
- **Retry Logic**: Failed messages are automatically retried
- **Durability**: Messages persist until acknowledged
- **Scalability**: Can handle burst traffic

**Message Flow:**
```
Scheduler → publishes message → Pub/Sub Topic → triggers → Cloud Function
```

### 3. Cloud Function

The core processing engine running serverless Python code.

**Runtime Configuration:**
```yaml
Runtime: Python 3.11
Memory: 512 MB
Timeout: 540 seconds (9 minutes)
Max Instances: 1 (cost control)
Trigger: Pub/Sub message
```

**Execution Lifecycle:**
```
1. Cold Start (if needed): ~2-5 seconds
2. Initialize clients (Firestore, Gemini)
3. Loop through watchlist:
   a. Fetch 3 months of price data
   b. Calculate 15+ technical indicators
   c. Detect trading signals
   d. Send to Gemini for AI scoring
   e. Store results in Firestore
4. Generate daily summary
5. Return success/failure
```

**Memory Usage Breakdown:**
```
Base Python runtime:     ~100 MB
pandas + numpy:          ~150 MB
yfinance data:           ~50 MB
Gemini client:           ~50 MB
Working memory:          ~100 MB
─────────────────────────────────
Total:                   ~450 MB (512 MB allocated)
```

### 4. Firestore Database

NoSQL document database storing all analysis results.

**Collection Structure:**
```
firestore/
├── analysis/                    # Individual stock analyses
│   ├── AAPL                     # Document per symbol
│   │   ├── symbol: "AAPL"
│   │   ├── price: 175.50
│   │   ├── change_pct: -0.31
│   │   ├── timestamp: "2024-01-15T21:35:00Z"
│   │   ├── indicators: {...}
│   │   ├── signals: [...]
│   │   ├── ai_score: 65
│   │   ├── ai_outlook: "NEUTRAL"
│   │   └── ai_summary: "..."
│   ├── MSFT
│   ├── GOOGL
│   └── ...
│
└── summaries/                   # Daily rollup summaries
    ├── 2024-01-15
    │   ├── date: "2024-01-15"
    │   ├── total_analyzed: 15
    │   ├── successful: 15
    │   ├── top_bullish: [...]
    │   └── top_bearish: [...]
    ├── 2024-01-14
    └── ...
```

**Document Size Limits:**
- Max document size: 1 MB
- Typical analysis document: ~2-5 KB
- Can store years of daily data within free tier

### 5. Gemini AI Integration

Large language model providing intelligent signal interpretation.

**Model Selection:**
```
Model: gemini-2.0-flash-exp
Purpose: Fast, cost-effective analysis
Latency: ~500ms per request
Token Usage: ~200-400 tokens per analysis
```

**Prompt Engineering:**
```
Input:
- Current price and % change
- Key indicators (RSI, MACD, ADX)
- Detected signals with strengths

Output (JSON):
- score: 1-100 actionability rating
- outlook: BULLISH/BEARISH/NEUTRAL
- action: BUY/SELL/HOLD
- confidence: HIGH/MEDIUM/LOW
- summary: One-sentence explanation
```

**Fallback Strategy:**
```python
try:
    result = gemini.analyze(signals)
except Exception:
    result = rule_based_scoring(signals)  # Never fails
```

---

## Data Flow

### Complete Request Lifecycle

```
Time: 4:30:00 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 1. TRIGGER PHASE                                                │
├─────────────────────────────────────────────────────────────────┤
│ Cloud Scheduler fires → Pub/Sub receives message                │
│ Latency: ~100ms                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:30:01 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 2. INITIALIZATION PHASE                                         │
├─────────────────────────────────────────────────────────────────┤
│ Cloud Function cold start (if needed)                           │
│ Initialize Firestore client                                     │
│ Configure Gemini AI                                             │
│ Latency: 2-5 seconds                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:30:05 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 3. DATA FETCH PHASE (per symbol)                                │
├─────────────────────────────────────────────────────────────────┤
│ yfinance.Ticker(symbol).history(period='3mo')                   │
│ Returns: ~63 trading days of OHLCV data                         │
│ Latency: 200-500ms per symbol                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:30:06 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 4. INDICATOR CALCULATION PHASE                                  │
├─────────────────────────────────────────────────────────────────┤
│ RSI(14), MACD(12,26,9), Bollinger(20,2)                        │
│ SMA(20,50), EMA(20), ADX(14), Stochastic(14,3)                 │
│ ATR(14), Volume Ratio                                           │
│ Latency: 10-50ms per symbol                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:30:06 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 5. SIGNAL DETECTION PHASE                                       │
├─────────────────────────────────────────────────────────────────┤
│ Check RSI thresholds (oversold < 30, overbought > 70)          │
│ Check MACD crossovers                                           │
│ Check price vs Bollinger Bands                                  │
│ Check trend alignment (Price > SMA20 > SMA50)                  │
│ Check volume anomalies (> 1.5x average)                        │
│ Latency: 5-10ms per symbol                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:30:07 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 6. AI RANKING PHASE                                             │
├─────────────────────────────────────────────────────────────────┤
│ Send indicators + signals to Gemini                             │
│ Receive: score, outlook, action, confidence, summary            │
│ Latency: 500-1000ms per symbol                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:30:08 PM ET
┌─────────────────────────────────────────────────────────────────┐
│ 7. STORAGE PHASE                                                │
├─────────────────────────────────────────────────────────────────┤
│ Batch write to Firestore                                        │
│ Update analysis/{symbol} document                               │
│ Latency: 50-100ms per batch                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
Time: 4:32:00 PM ET (for 15 stocks)
┌─────────────────────────────────────────────────────────────────┐
│ 8. SUMMARY PHASE                                                │
├─────────────────────────────────────────────────────────────────┤
│ Aggregate results                                               │
│ Identify top bullish/bearish                                    │
│ Store in summaries/{date}                                       │
│ Return success response                                         │
└─────────────────────────────────────────────────────────────────┘

Total Time: ~2 minutes for 15 stocks
```

---

## Technical Indicators

### Indicators Calculated

| Indicator | Formula | Period | Use Case |
|-----------|---------|--------|----------|
| **RSI** | 100 - (100 / (1 + RS)) | 14 | Overbought/Oversold |
| **MACD** | EMA(12) - EMA(26) | 12,26,9 | Trend momentum |
| **MACD Signal** | EMA(MACD, 9) | 9 | Crossover signals |
| **MACD Histogram** | MACD - Signal | - | Momentum strength |
| **SMA 20** | Mean(Close, 20) | 20 | Short-term trend |
| **SMA 50** | Mean(Close, 50) | 50 | Medium-term trend |
| **EMA 20** | Exp. weighted mean | 20 | Responsive trend |
| **Bollinger Upper** | SMA20 + 2*StdDev | 20 | Resistance |
| **Bollinger Lower** | SMA20 - 2*StdDev | 20 | Support |
| **ADX** | Directional Index | 14 | Trend strength |
| **+DI / -DI** | Directional indicators | 14 | Trend direction |
| **Stochastic %K** | (C-L14)/(H14-L14)*100 | 14 | Momentum |
| **Stochastic %D** | SMA(%K, 3) | 3 | Signal line |
| **ATR** | Average True Range | 14 | Volatility |
| **Volume Ratio** | Volume / SMA(Volume, 20) | 20 | Volume analysis |

### Indicator Interpretation

```
RSI Zones:
├── 0-30:   Oversold (potential buy)
├── 30-70:  Neutral
└── 70-100: Overbought (potential sell)

MACD Signals:
├── MACD > Signal: Bullish momentum
├── MACD < Signal: Bearish momentum
├── Histogram growing: Strengthening trend
└── Histogram shrinking: Weakening trend

Bollinger Bands:
├── Price > Upper: Overbought, potential reversal
├── Price < Lower: Oversold, potential bounce
└── Price at Middle: Fair value

ADX Interpretation:
├── 0-20:  Weak/No trend
├── 20-40: Developing trend
├── 40-60: Strong trend
└── 60+:   Extremely strong trend
```

---

## Signal Detection

### Signal Categories

```
CATEGORY        SIGNALS DETECTED
─────────────────────────────────────────────────────────
RSI             • RSI Oversold (< 30)
                • RSI Overbought (> 70)
                • RSI Approaching Oversold (30-40)
                • RSI Approaching Overbought (60-70)

MACD            • MACD Bullish (MACD > Signal, Hist > 0)
                • MACD Bearish (MACD < Signal, Hist < 0)
                • MACD Crossover (recent cross)

TREND           • Uptrend (Price > SMA20 > SMA50)
                • Downtrend (Price < SMA20 < SMA50)
                • Trend Reversal (alignment changing)

MA_CROSS        • Golden Cross Forming (SMA20 approaching SMA50 from below)
                • Death Cross Forming (SMA20 approaching SMA50 from above)

BOLLINGER       • Price Below Lower Band (oversold)
                • Price Above Upper Band (overbought)
                • Bollinger Squeeze (bands narrowing)

STOCHASTIC      • Stochastic Oversold (K,D < 20)
                • Stochastic Overbought (K,D > 80)
                • Stochastic Crossover

ADX             • Strong Bullish Trend (ADX > 25, +DI > -DI)
                • Strong Bearish Trend (ADX > 25, -DI > +DI)
                • Trend Developing (ADX rising)

VOLUME          • Volume Spike (> 2x average)
                • Above Average Volume (> 1.5x average)
                • Climactic Volume (> 3x average)
```

### Signal Strength Levels

```
STRENGTH            MEANING                    WEIGHT
────────────────────────────────────────────────────────
STRONG BULLISH      High conviction buy        +3
BULLISH             Moderate buy signal        +2
NOTABLE             Worth watching             +1
NEUTRAL             No clear direction          0
BEARISH             Moderate sell signal       -2
STRONG BEARISH      High conviction sell       -3
SIGNIFICANT         Important but directionless ±2
```

---

## AI Ranking System

### How Gemini Evaluates Signals

**Input Context Provided:**
```
1. Current price and daily change
2. Key indicator values (RSI, MACD, ADX)
3. List of detected signals with strengths
4. Signal categories for context
```

**Evaluation Criteria:**

| Criterion | Weight | Description |
|-----------|--------|-------------|
| **Actionability** | 30% | Can a trader act on this now? |
| **Reliability** | 25% | Historical accuracy of signal type |
| **Timing** | 25% | Is this the right moment? |
| **Risk/Reward** | 20% | Potential upside vs downside |

**Score Interpretation:**
```
90-100: Exceptional opportunity, high conviction
80-89:  Strong signal, consider action
70-79:  Good signal, worth monitoring
60-69:  Moderate signal, needs confirmation
50-59:  Neutral, no clear edge
40-49:  Weak signal, caution advised
30-39:  Poor setup, likely avoid
0-29:   Strong counter-signal, potential reversal
```

### Fallback Scoring (Rule-Based)

When AI is unavailable, rule-based scoring activates:

```python
def rule_based_score(signals):
    bullish_count = count(signals, "BULLISH")
    bearish_count = count(signals, "BEARISH")

    # Base score of 50 (neutral)
    score = 50 + (bullish_count - bearish_count) * 10

    # Clamp to valid range
    return max(10, min(90, score))
```

---

## Storage & Retrieval

### Firestore Document Schema

**Analysis Document:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-01-15T21:35:00Z",
  "price": 185.92,
  "change_pct": -0.31,

  "indicators": {
    "rsi": 54.23,
    "macd": 1.234,
    "macd_signal": 1.123,
    "adx": 28.5,
    "stoch_k": 65.4,
    "vol_ratio": 1.23
  },

  "signals": [
    {
      "signal": "MACD Bullish",
      "strength": "BULLISH",
      "category": "MACD",
      "value": 1.234
    }
  ],
  "signal_count": 4,

  "ai_score": 65,
  "ai_outlook": "NEUTRAL",
  "ai_action": "HOLD",
  "ai_confidence": "MEDIUM",
  "ai_summary": "Mixed signals with slight bullish bias",
  "ai_powered": true
}
```

### Query Patterns

```python
# Get latest analysis for a symbol
db.collection('analysis').document('AAPL').get()

# Get all bullish stocks
db.collection('analysis')
  .where('ai_outlook', '==', 'BULLISH')
  .stream()

# Get high-score stocks
db.collection('analysis')
  .where('ai_score', '>=', 70)
  .order_by('ai_score', 'DESCENDING')
  .stream()

# Get daily summary
db.collection('summaries')
  .order_by('date', 'DESCENDING')
  .limit(1)
  .stream()

# Get historical summaries (last 7 days)
db.collection('summaries')
  .order_by('date', 'DESCENDING')
  .limit(7)
  .stream()
```

---

## Usage Tips

### 1. Optimal Scheduling

```bash
# Market close analysis (recommended)
Schedule: "30 16 * * 1-5"  # 4:30 PM ET Mon-Fri

# Pre-market check
Schedule: "0 9 * * 1-5"    # 9:00 AM ET Mon-Fri

# Mid-day pulse
Schedule: "0 12 * * 1-5"   # 12:00 PM ET Mon-Fri
```

### 2. Watchlist Management

**Organize by Category:**
```python
WATCHLISTS = {
    "tech_leaders": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
    "semiconductors": ["MU", "AMD", "INTC", "AVGO", "QCOM"],
    "etfs": ["SPY", "QQQ", "IWM", "DIA", "VTI"],
    "sectors": ["XLF", "XLK", "XLE", "XLV", "XLI"],
    "high_volatility": ["TSLA", "COIN", "MARA", "RIOT"]
}
```

### 3. Interpreting Results

**Strong Buy Candidates:**
- AI Score > 75
- Outlook = BULLISH
- Multiple bullish signals
- RSI < 40 (not overbought)
- Volume confirming

**Strong Sell Candidates:**
- AI Score < 35
- Outlook = BEARISH
- Multiple bearish signals
- RSI > 60 (potentially overbought)
- Breakdown patterns

### 4. Alert Thresholds

```python
ALERT_THRESHOLDS = {
    "high_score": 80,      # Exceptional opportunity
    "low_score": 25,       # Strong warning
    "rsi_oversold": 25,    # Deep oversold
    "rsi_overbought": 80,  # Extreme overbought
    "volume_spike": 3.0,   # 3x normal volume
}
```

### 5. Combining with Other Data

```
Pipeline Output + External Data = Better Decisions

Examples:
├── + Earnings Calendar → Avoid before earnings
├── + Fed Meeting Dates → Expect volatility
├── + Sector Rotation → Context for moves
├── + News Sentiment → Confirm/deny signals
└── + Options Flow → Smart money direction
```

---

## 20 Ways to Expand

### Data & Coverage Expansions

#### 1. **Add More Markets**
```python
WATCHLISTS = {
    "us_stocks": ["AAPL", "MSFT", ...],
    "crypto": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "forex": ["EURUSD=X", "GBPUSD=X", "USDJPY=X"],
    "commodities": ["GC=F", "CL=F", "SI=F"],  # Gold, Oil, Silver
    "international": ["EWJ", "FXI", "VGK"],    # Japan, China, Europe ETFs
}
```

#### 2. **Extended Indicator Suite**
```python
# Add these indicators:
- Ichimoku Cloud (trend, support/resistance)
- Fibonacci Retracements (key levels)
- VWAP (volume-weighted average price)
- OBV (on-balance volume)
- Williams %R (momentum)
- CCI (commodity channel index)
- Parabolic SAR (trend reversal)
- Keltner Channels (volatility bands)
```

#### 3. **Multi-Timeframe Analysis**
```python
TIMEFRAMES = {
    "intraday": "1h",    # Hourly for day traders
    "short_term": "1d",  # Daily for swing traders
    "medium_term": "1wk", # Weekly for position traders
    "long_term": "1mo",  # Monthly for investors
}
# Combine signals across timeframes for higher conviction
```

#### 4. **Real-Time Data Integration**
```python
# Replace yfinance with:
- Alpha Vantage API (real-time quotes)
- Polygon.io (tick-level data)
- IEX Cloud (institutional-grade)
- Alpaca Markets (free real-time)
```

### Alert & Notification Expansions

#### 5. **Email Alerts**
```python
# Add to Cloud Function:
from sendgrid import SendGridAPIClient

def send_alert(subject, body, recipient):
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    message = Mail(
        from_email='alerts@yourdomain.com',
        to_emails=recipient,
        subject=subject,
        html_content=body
    )
    sg.send(message)
```

#### 6. **Slack Integration**
```python
# Add Slack webhook:
import requests

def notify_slack(message):
    webhook_url = SLACK_WEBHOOK_URL
    requests.post(webhook_url, json={"text": message})

# Trigger on high-score signals
if result['ai_score'] >= 80:
    notify_slack(f"🚨 High Score Alert: {symbol} - Score {score}")
```

#### 7. **SMS Alerts (Twilio)**
```python
from twilio.rest import Client

def send_sms(message):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE,
        to=USER_PHONE
    )
```

#### 8. **Mobile Push Notifications**
```python
# Using Firebase Cloud Messaging:
from firebase_admin import messaging

def send_push(title, body, token):
    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        token=token
    )
    messaging.send(message)
```

### Analysis Expansions

#### 9. **Backtesting Engine**
```python
def backtest_signal(symbol, signal_type, lookback_days=365):
    """
    Test how well a signal predicted future returns
    """
    historical_signals = get_historical_signals(symbol, signal_type)

    results = []
    for signal in historical_signals:
        entry_date = signal['date']
        future_return = calculate_return(symbol, entry_date, days=5)
        results.append({
            'date': entry_date,
            'signal_score': signal['score'],
            'actual_return': future_return
        })

    win_rate = sum(1 for r in results if r['actual_return'] > 0) / len(results)
    avg_return = mean([r['actual_return'] for r in results])

    return {'win_rate': win_rate, 'avg_return': avg_return}
```

#### 10. **Machine Learning Predictions**
```python
# Add sklearn/TensorFlow model:
from sklearn.ensemble import RandomForestClassifier

def train_prediction_model():
    # Features: indicators + signals
    # Target: 5-day forward return (positive/negative)

    features = prepare_features(historical_data)
    targets = prepare_targets(historical_data)

    model = RandomForestClassifier(n_estimators=100)
    model.fit(features, targets)

    return model

def predict_movement(symbol, model):
    current_features = get_current_features(symbol)
    prediction = model.predict_proba(current_features)
    return {
        'bullish_probability': prediction[0][1],
        'bearish_probability': prediction[0][0]
    }
```

#### 11. **Sentiment Analysis**
```python
# Add news sentiment:
def analyze_sentiment(symbol):
    news = fetch_news(symbol)  # NewsAPI, Finnhub, etc.

    sentiments = []
    for article in news:
        # Use Gemini or dedicated NLP
        sentiment = gemini.analyze_sentiment(article['title'])
        sentiments.append(sentiment)

    return {
        'overall_sentiment': mean(sentiments),
        'article_count': len(news),
        'bullish_articles': count(sentiments, positive),
        'bearish_articles': count(sentiments, negative)
    }
```

#### 12. **Options Flow Analysis**
```python
# Track unusual options activity:
def analyze_options_flow(symbol):
    options_data = fetch_options_data(symbol)

    return {
        'put_call_ratio': calculate_pcr(options_data),
        'unusual_volume': find_unusual_volume(options_data),
        'large_trades': find_block_trades(options_data),
        'implied_move': calculate_expected_move(options_data)
    }
```

### Infrastructure Expansions

#### 13. **Historical Data Warehouse**
```python
# Store all analyses in BigQuery for analytics:
from google.cloud import bigquery

def archive_to_bigquery(analysis):
    client = bigquery.Client()
    table_id = "project.dataset.analyses"

    rows = [flatten_analysis(analysis)]
    client.insert_rows_json(table_id, rows)

# Query historical patterns:
"""
SELECT symbol, AVG(ai_score) as avg_score,
       COUNT(*) as signal_count
FROM analyses
WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
GROUP BY symbol
ORDER BY avg_score DESC
"""
```

#### 14. **Dashboard (Looker Studio)**
```
Connect Firestore → BigQuery → Looker Studio

Dashboard Panels:
├── Daily Score Distribution (histogram)
├── Top Movers Table (sortable)
├── Signal Frequency by Category (pie chart)
├── Score Trends Over Time (line chart)
├── Win Rate by Signal Type (bar chart)
└── Sector Performance Heatmap
```

#### 15. **API Endpoint**
```python
# Add HTTP endpoint to Cloud Function:
@functions_framework.http
def api_handler(request):
    symbol = request.args.get('symbol')

    if request.path == '/analyze':
        return analyze_single(symbol)
    elif request.path == '/latest':
        return get_latest(symbol)
    elif request.path == '/history':
        return get_history(symbol, days=30)
    elif request.path == '/summary':
        return get_daily_summary()
```

#### 16. **Webhook Triggers**
```python
# Allow external services to trigger analysis:
def webhook_handler(request):
    event_type = request.json.get('type')

    if event_type == 'earnings_alert':
        symbols = request.json.get('symbols')
        return analyze_batch(symbols)

    elif event_type == 'price_alert':
        symbol = request.json.get('symbol')
        return analyze_single(symbol)
```

### User Experience Expansions

#### 17. **Custom Watchlists per User**
```python
# Firestore structure:
users/
├── user123/
│   ├── email: "user@example.com"
│   ├── watchlists/
│   │   ├── default: ["AAPL", "MSFT", ...]
│   │   ├── tech: ["NVDA", "AMD", ...]
│   │   └── dividends: ["JNJ", "PG", ...]
│   └── preferences/
│       ├── alert_threshold: 75
│       ├── notification_method: "email"
│       └── timezone: "America/New_York"
```

#### 18. **Mobile App (Flutter/React Native)**
```
Features:
├── Real-time analysis results
├── Push notifications
├── Custom watchlists
├── Interactive charts
├── Historical signal performance
└── Paper trading integration
```

#### 19. **Voice Assistant Integration**
```python
# Alexa/Google Assistant skill:
"Hey Google, what's the analysis for Apple stock?"

Response: "Apple has a neutral outlook with a score of 65.
Key signals include MACD bullish and RSI at 54.
The AI suggests holding current positions."
```

#### 20. **Trading Bot Integration**
```python
# Connect to broker API (Alpaca, Interactive Brokers):
def execute_on_signal(analysis):
    if analysis['ai_score'] >= 85 and analysis['ai_action'] == 'BUY':
        place_order(
            symbol=analysis['symbol'],
            side='buy',
            qty=calculate_position_size(analysis),
            type='limit',
            limit_price=analysis['price'] * 1.001
        )

    elif analysis['ai_score'] <= 25 and analysis['ai_action'] == 'SELL':
        close_position(analysis['symbol'])
```

---

## Cost Summary

### Current Setup (Free Tier)

| Component | Monthly Usage | Free Limit | Cost |
|-----------|--------------|------------|------|
| Cloud Functions | ~500 invocations | 2M | $0 |
| Gemini API | ~500 calls | 45,000 | $0 |
| Firestore | ~100 MB | 1 GB | $0 |
| Pub/Sub | ~1 MB | 10 GB | $0 |
| Scheduler | 1 job | 3 jobs | $0 |
| **Total** | | | **$0** |

### With All Expansions (~$10-50/month)

| Addition | Estimated Cost |
|----------|----------------|
| Real-time data API | $10-30/month |
| SMS alerts (100/month) | $1-2/month |
| BigQuery (10 GB) | $0.50/month |
| Additional AI calls | $2-5/month |
| Cloud Run (dashboard) | $5-10/month |

---

## Quick Reference

```bash
# Trigger analysis manually
gcloud scheduler jobs run daily-analysis-job --location=us-central1

# View recent logs
gcloud functions logs read daily-stock-analysis --limit=50

# View Firestore data
python view_firestore.py

# View specific stock
python view_firestore.py AAPL

# Redeploy after changes
cd automation && ./deploy.sh your-project-id
```

---

## Summary

This automated pipeline provides:

✅ **Daily Analysis**: 15+ stocks analyzed every market day
✅ **AI-Powered**: Gemini provides intelligent signal ranking
✅ **Reliable**: Cloud infrastructure with automatic retries
✅ **Scalable**: Easily add more stocks or indicators
✅ **Cost-Effective**: Runs entirely within GCP free tier
✅ **Extensible**: 20 expansion paths identified

The foundation is solid and production-ready. Each expansion builds on this base to create increasingly sophisticated analysis capabilities.
