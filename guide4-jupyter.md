# Technical Analysis Jupyter Notebook - Quick Guide

## 🚀 Quick Start (3 Minutes)

```bash
# 1. Install dependencies
pip install yfinance pandas numpy plotly google-generativeai openpyxl

# 2. Open notebook
jupyter notebook technical_analysis.ipynb

# 3. Run setup cells (1-7)
# 4. Analyze a stock (Cell 8)
result = analyze_and_save('AAPL', period='1mo')
```

---


## 📊 Notebook Structure (16 Cells)

### Setup Cells (1-7)

**Cell 1: Configuration**
```python
# Customize these
GEMINI_API_KEY = None  # Optional AI ranking
DATA_DIR = 'data'
USE_AI_RANKING = False  # Set True if you have API key
```

**Cell 2-6: Core Functions**
- Fetch data from yfinance
- Calculate 50+ indicators
- Detect 150+ signals
- AI ranking (optional)
- Save results

**Cell 7: Helper Functions**
- Export to Excel/CSV/JSON
- Visualization
- Data management

### Analysis Cells (8-16)

**Cell 8: Single Stock Analysis**
```python
result = analyze_and_save('AAPL', period='1mo')
# Generates: signals, indicators, exports
```

**Cell 9: Compare Multiple Stocks**
```python
compare_stocks(['AAPL', 'MSFT', 'GOOGL'])
```

**Cell 10: Screen for Opportunities**
```python
screen_stocks(
    symbols=['AAPL', 'MSFT', 'NVDA'],
    rsi_max=35,
    min_bullish_signals=5
)
```

**Cell 11: Interactive Dashboard**
```python
create_dashboard(result)  # Plotly visualization
```

**Cell 12-16: Batch Processing & Export**
- Analyze multiple stocks
- Historical tracking
- Custom screeners
- Advanced exports

---

## 🎯 Key Features

### 1. Comprehensive Analysis
- **50+ Indicators**: RSI, MACD, Bollinger Bands, ADX, Stochastic, etc.
- **150+ Signals**: Moving average crosses, volume spikes, trend patterns
- **AI Ranking**: Optional Gemini scoring (1-100)

### 2. Multiple Export Formats
```python
# JSON (detailed)
result['symbol']  # 'AAPL'
result['signals']  # All detected signals
result['indicators']  # All technical indicators

# Excel (formatted)
export_to_excel(result, 'AAPL_analysis')

# CSV (for spreadsheets)
export_to_csv(result, 'AAPL_signals')

# Dashboard (interactive)
create_dashboard(result)
```

### 3. Data Organization
```
data/
├── signals/
│   └── 2024-01-15/
│       ├── AAPL-signals.json
│       └── AAPL-ranked-signals.txt
├── indicators/
│   └── 2024-01-15/
│       └── AAPL-indicators.csv
└── exports/
    ├── AAPL_analysis.xlsx
    └── AAPL_signals.csv
```

---

## 💡 Common Use Cases

### Use Case 1: Daily Watchlist Analysis
```python
watchlist = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']

for symbol in watchlist:
    result = analyze_and_save(symbol, period='1mo')
    
    # Alert on strong signals
    top_signals = [s for s in result['signals'] if s['ai_score'] >= 85]
    if top_signals:
        print(f"🔥 {symbol}: {len(top_signals)} high-priority signals!")
```

### Use Case 2: Find Oversold Stocks
```python
candidates = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META']

oversold = screen_stocks(
    symbols=candidates,
    rsi_max=35,
    min_bullish_signals=5
)

print(oversold)  # Returns DataFrame of matches
```

### Use Case 3: Compare Sector Leaders
```python
tech_leaders = ['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'AMD']
comparison = compare_stocks(tech_leaders)

# Exports comparison table
comparison.to_excel('tech_comparison.xlsx')
```

### Use Case 4: Track Signal Changes
```python
# Analyze today
today = analyze_and_save('AAPL', period='1mo')

# Load yesterday's analysis
with open('data/signals/2024-01-14/AAPL-signals.json') as f:
    yesterday = json.load(f)

# Compare
print(f"Today: {today['summary']['bullish']} bullish signals")
print(f"Yesterday: {yesterday['summary']['bullish']} bullish signals")
```

---

## 🔧 Customization

### Add Custom Signals

Edit Cell 5 `detect_all_signals()`:

```python
# Add after existing signals:

# Custom: Price momentum + volume
if current['Price_Change'] > 2 and current['Volume'] > current['Volume_MA_20'] * 1.5:
    signals.append({
        'signal': 'MOMENTUM BREAKOUT',
        'desc': f"+{current['Price_Change']:.1f}% on high volume",
        'strength': 'STRONG BULLISH',
        'category': 'CUSTOM'
    })

# Custom: Reversal setup
if current['RSI'] < 30 and current['MACD'] > current['MACD_Signal']:
    signals.append({
        'signal': 'OVERSOLD REVERSAL SETUP',
        'desc': 'RSI oversold with MACD turning positive',
        'strength': 'BULLISH',
        'category': 'CUSTOM_REVERSAL'
    })
```

### Adjust AI Ranking

Edit Cell 6 `rank_with_gemini()` prompt:

```python
prompt = f"""
Score signals for {symbol} with emphasis on:
- Short-term trading (1-5 days)
- High probability setups
- Clear entry/exit points

Market Data: {market_data}
Signals: {signals}

Return JSON with scores 1-100.
"""
```

### Create Custom Screener

```python
def my_screener(symbols, **criteria):
    """Custom screening logic"""
    matches = []
    
    for symbol in symbols:
        result = analyze_and_save(symbol, period='1mo')
        
        # Your custom logic
        if (result['indicators']['rsi'] < criteria.get('rsi_max', 35) and
            result['indicators']['macd'] > 0 and
            result['summary']['bullish'] > criteria.get('min_bullish', 5)):
            
            matches.append({
                'symbol': symbol,
                'score': result['summary']['avg_score'],
                'rsi': result['indicators']['rsi']
            })
    
    return pd.DataFrame(matches)

# Use it
results = my_screener(['AAPL', 'MSFT'], rsi_max=30, min_bullish=7)
```

---

## 🐳 Docker Deployment

The notebook includes a Dockerfile for API deployment.

### Build and Run

```bash
# Build image
docker build -t technical-analysis-api .

# Run container
docker run -p 8080:8080 technical-analysis-api

# Test API
curl http://localhost:8080/analyze/AAPL
```

### API Endpoints

```python
# Analyze stock
GET /analyze/{symbol}?period=1mo

# Compare stocks
POST /compare
Body: {"symbols": ["AAPL", "MSFT", "GOOGL"]}

# Screen stocks
POST /screen
Body: {"symbols": [...], "rsi_max": 35}

# Health check
GET /health
```

### Docker Compose (Optional)

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - ./data:/app/data
```

---

## 📈 Output Examples

### Terminal Output
```
📊 Analyzing AAPL...
✅ Fetched 21 days of data
✅ Indicators calculated
✅ Detected 15 signals
🤖 AI ranking signals...
✅ AI ranked 15 signals

📊 AAPL Technical Analysis
🟢 Price: $185.23 (+1.2%)

📈 Signal Summary:
• Total: 15
• Bullish: 9 | Bearish: 6
• AI Score: 72.5/100

🎯 Top 10 Signals:
1. 🔥 [92] GOLDEN CROSS
   50 MA crossed above 200 MA
2. ⚡ [87] VOLUME ACCUMULATION
   Consistent volume + price increase
...

💾 Results saved to data/signals/2024-01-15/
```

### JSON Structure
```json
{
  "symbol": "AAPL",
  "timestamp": "2024-01-15T10:30:00",
  "price": 185.23,
  "change": 1.2,
  "signals": [
    {
      "rank": 1,
      "signal": "GOLDEN CROSS",
      "desc": "50 MA crossed above 200 MA",
      "strength": "STRONG BULLISH",
      "category": "MA_CROSS",
      "ai_score": 92,
      "ai_reasoning": "Strong momentum confirmed by volume"
    }
  ],
  "summary": {
    "total_signals": 15,
    "bullish": 9,
    "bearish": 6,
    "avg_score": 72.5
  },
  "indicators": {
    "rsi": 58.3,
    "macd": 0.0234,
    "adx": 28.5,
    "volume": 45234567
  }
}
```

### Excel Export
Formatted workbook with:
- **Summary** sheet: Key metrics
- **Signals** sheet: All signals ranked
- **Indicators** sheet: Technical data
- **Charts** sheet: Visual analysis

---

## 🔍 Signal Categories

### Moving Averages (MA_CROSS, MA_TREND)
- Golden Cross / Death Cross
- Price above/below key MAs
- MA alignment patterns
- MA slope changes

### Momentum (RSI, MACD, STOCHASTIC)
- Oversold/overbought conditions
- Momentum divergences
- Oscillator crossovers
- Momentum acceleration

### Volume (VOLUME, VOLUME_DIVERGENCE)
- Volume spikes
- Volume accumulation/distribution
- Volume divergences
- Climax volume

### Trend (TREND, ADX)
- Strong trend detection
- Trend reversals
- ADX trend strength
- DI crossovers

### Price Action (PRICE_ACTION, CANDLESTICK)
- Large moves
- Gap detection
- Candlestick patterns
- Support/resistance breaks

### Volatility (BOLLINGER, VOLATILITY)
- Bollinger Band touches
- BB squeeze
- Volatility expansion
- ATR-based stops

---

## ⚙️ Configuration Options

### Performance Settings
```python
# Cell 1: Adjust these for speed/detail tradeoff

# Faster: Use shorter period
period = '1mo'  # vs '1y'

# Fewer signals: Increase threshold
MIN_SCORE = 60  # Only show signals >= 60

# Skip AI ranking
USE_AI_RANKING = False

# Batch size for parallel processing
BATCH_SIZE = 5  # Process 5 at a time
```

### Memory Management
```python
# For large datasets
import gc

# After processing each stock
gc.collect()

# Limit data retention
MAX_HISTORY_DAYS = 7  # Keep only last week
```

### Cache Settings
```python
# Enable caching
ENABLE_CACHE = True
CACHE_TTL = 300  # 5 minutes

# Check cache before analyzing
cache_file = f'cache/{symbol}_{period}.json'
if os.path.exists(cache_file):
    with open(cache_file) as f:
        return json.load(f)
```

---

## 🐛 Troubleshooting

### Issue: No data found for symbol
```python
# Solution 1: Verify symbol
import yfinance as yf
ticker = yf.Ticker("AAPL")
print(ticker.info.get('longName'))

# Solution 2: Try different period
result = analyze_and_save('AAPL', period='6mo')
```

### Issue: Gemini API errors
```python
# Solution: Use rule-based ranking
USE_AI_RANKING = False

# Or check API key
print(f"API Key: {GEMINI_API_KEY[:10]}..." if GEMINI_API_KEY else "Not set")
```

### Issue: Slow performance
```python
# Solution 1: Reduce period
period = '1mo'  # Instead of '1y'

# Solution 2: Limit signals
signals = signals[:20]  # Top 20 only

# Solution 3: Add delays
import time
time.sleep(2)  # Between API calls
```

### Issue: Memory errors
```python
# Solution: Process in chunks
for chunk in chunked(symbols, 10):
    results = [analyze_and_save(s) for s in chunk]
    gc.collect()
```

---

## 📊 Indicator Reference

### Key Thresholds
- **RSI**: <30 oversold, >70 overbought, 50 = neutral
- **MACD**: Above signal = bullish, below = bearish
- **ADX**: >25 trending, >40 strong trend, <20 ranging
- **Stochastic**: <20 oversold, >80 overbought
- **Volume**: >2x average = significant

### Indicator Formulas
```python
# RSI (14-period)
rsi = 100 - (100 / (1 + rs))

# MACD (12, 26, 9)
macd = ema_12 - ema_26
signal = ema(macd, 9)

# Bollinger Bands (20-period, 2 std)
bb_middle = sma_20
bb_upper = sma_20 + (2 * std_20)
bb_lower = sma_20 - (2 * std_20)
```

---

## 🎓 Best Practices

### 1. Data Validation
```python
# Always verify data quality
if len(df) < 50:
    print("⚠️ Insufficient data for reliable signals")

# Check for gaps
if df.index.to_series().diff().max() > pd.Timedelta(days=7):
    print("⚠️ Data has large gaps")
```

### 2. Signal Confirmation
```python
# Use multiple timeframes
result_1mo = analyze_and_save('AAPL', period='1mo')
result_3mo = analyze_and_save('AAPL', period='3mo')

# Confirm signals match
if result_1mo['summary']['bullish'] > result_3mo['summary']['bullish']:
    print("✅ Short-term bullish confirmed by long-term trend")
```

### 3. Risk Management
```python
# Set stop-loss based on ATR
stop_loss = current_price - (2 * current_atr)

# Position sizing based on volatility
position_size = account_value * (target_risk / volatility)
```

### 4. Regular Review
```python
# Track signal accuracy
def track_outcomes():
    # Load signals from last week
    # Check if predictions were correct
    # Update confidence scores
    pass
```

---

## 🚀 Next Steps

### Immediate (Today)
1. ✅ Run setup cells (1-7)
2. ✅ Analyze your first stock (Cell 8)
3. ✅ Review exported files
4. ✅ Try the dashboard (Cell 11)

### Short Term (This Week)
- [ ] Build watchlist and analyze daily
- [ ] Export to Excel for tracking
- [ ] Try comparison and screening
- [ ] Add 1-2 custom signals

### Medium Term (This Month)
- [ ] Set up automated scheduling
- [ ] Deploy Docker API
- [ ] Track signal accuracy
- [ ] Integrate with trading platform

### Long Term (This Quarter)
- [ ] Backtest strategies
- [ ] ML signal prediction
- [ ] Portfolio optimization
- [ ] Community sharing

---

## 📚 Quick Reference

### Common Commands
```python
# Analyze single stock
analyze_and_save('AAPL', period='1mo')

# Compare stocks
compare_stocks(['AAPL', 'MSFT', 'GOOGL'])

# Screen for opportunities
screen_stocks(symbols=[...], rsi_max=35)

# Export to Excel
export_to_excel(result, 'AAPL_analysis')

# View dashboard
create_dashboard(result)
```

### File Locations
- **Signals**: `data/signals/YYYY-MM-DD/SYMBOL-signals.json`
- **Indicators**: `data/indicators/YYYY-MM-DD/SYMBOL-indicators.csv`
- **Exports**: `data/exports/SYMBOL_analysis.xlsx`

### Jupyter Shortcuts
- `Shift + Enter` - Run cell
- `Esc + A` - Insert cell above
- `Esc + B` - Insert cell below
- `Esc + D, D` - Delete cell
- `Esc + M` - Markdown mode

---

## 🎉 Ready to Start!

Your technical analysis system is ready:

✅ **150+ Signals** across 15 categories
✅ **50+ Indicators** 
✅ **AI Ranking** (optional)
✅ **Multiple Export Formats**
✅ **Interactive Dashboard**
✅ **Docker Deployment Ready**
✅ **100% Free & Local**

**Start now**: Run cells 1-7 for setup, then Cell 8 to analyze your first stock!
