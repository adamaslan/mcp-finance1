# 🚀 Firestore Database - Quick Start Guide

**Project**: ttb-lang1 | **Status**: ✅ Fully Operational | **Last Verified**: 2026-02-11

---

## ⚡ 30-Second Summary

Your Firestore database `ttb-lang1` contains:
- **5 stock symbols** (AEM, CRM, IGV, JPM, QBTS)
- **4,288 options contracts** with full Greeks and volatility data
- **8,500+ historical candles** (daily, weekly, monthly)
- **Free tier active** - no charges, no quota concerns

---

## 🔹 Quick Connect (Python)

```python
from google.cloud import firestore

# Connect to database
db = firestore.Client(project="ttb-lang1")

# Get AEM options chain
aem = db.collection("options_chains").document("AEM").get().to_dict()
print(f"AEM: {aem['total_calls']} calls, {aem['total_puts']} puts")

# Get current price
quote = db.collection("options_quotes").document("AEM").get().to_dict()
print(f"Price: ${quote['current']} ({quote['change_percent']:+.2f}%)")

# Get 1-day candles
candles = db.collection("candle_data")\
    .document("AEM")\
    .collection("intervals")\
    .document("1day")\
    .get().to_dict()
print(f"Candles: {candles['num_candles']}")
```

---

## 🛠️ Common Tasks

### View All Symbols
```python
symbols = [doc.id for doc in db.collection("options_chains").stream()]
print(f"Symbols: {symbols}")
# Output: Symbols: ['AEM', 'CRM', 'IGV', 'JPM', 'QBTS']
```

### Get All Expirations for a Symbol
```python
expirations = db.collection("options_chains")\
    .document("AEM")\
    .collection("expirations")\
    .stream()

dates = [doc.id for doc in expirations]
print(f"Expirations: {dates}")
```

### Find Calls Above/Below Strike
```python
symbol = "AEM"
expiration = "2026-02-13"

calls = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .document(expiration)\
    .collection("calls")\
    .stream()

for call in calls:
    data = call.to_dict()
    print(f"Strike ${data['strike']}: ${data['last_price']} (IV: {data['implied_volatility']:.2f}%)")
```

### Get Implied Volatility Surface
```python
symbol = "AEM"

expirations = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .stream()

for exp in expirations:
    exp_data = exp.to_dict()
    print(f"{exp.id}: IV={exp_data['implied_volatility']:.2f}%")
```

### Get Historical Prices
```python
symbol = "AEM"

candles = db.collection("candle_data")\
    .document(symbol)\
    .collection("intervals")\
    .document("1week")\
    .get().to_dict()

# Last 10 candles
for candle in candles['candles'][-10:]:
    print(f"{candle['datetime']}: Close ${candle['close']:.2f}")
```

---

## 📊 Data Structure Overview

```
options_chains/AEM
├─ symbol, exchange, last_trade_price
├─ num_expirations, total_calls, total_puts
└─ expirations/2026-02-13
   ├─ implied_volatility, put_volume, call_volume
   ├─ calls/150 -> {strike, last_price, IV, greeks...}
   └─ puts/150 -> {strike, last_price, IV, greeks...}

options_quotes/AEM
├─ current, change, change_percent
└─ OHLC snapshot

candle_data/AEM/intervals/1day
├─ status, num_candles
└─ candles[] -> {datetime, open, high, low, close, volume}
```

---

## 🔄 Running the Pipeline

```bash
# Activate environment
mamba activate fin-ai1

# Set API keys
export FINHUB_API_KEY=your-key
export ALPHA_VANTAGE_KEY=your-key

# Run pipeline (fetches all 5 symbols)
python run_pipeline.py

# Specific symbols
python run_pipeline.py --symbols AEM CRM

# Without candles (faster)
python run_pipeline.py --no-candles
```

**Duration**: 2-3 minutes for all 5 symbols with candles

---

## 📈 Available Data per Symbol

### Options Chain
- 14-20 expiration dates
- 550-1,000 options contracts per symbol
- **Fields**: Strike, bid/ask, IV, Greeks, volume, OI, theoretical value

### Historical Candles
- ✅ **1 day** - 100 candles (always available)
- ✅ **1 week** - 183-1,371 candles (depends on IPO date)
- ✅ **1 month** - 42-315 candles
- ❌ **Intraday** (1m-1h) - Requires paid API

### Current Quote
- Price, change, change%
- OHLC
- Timestamp

---

## 🔍 Useful Queries

### Highest Implied Volatility
```python
symbol = "AEM"
expirations = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .stream()

highest_iv = max(
    (doc.to_dict()['implied_volatility'], doc.id)
    for doc in expirations
)
print(f"Highest IV: {highest_iv[0]:.2f}% on {highest_iv[1]}")
```

### Put/Call Ratio (Market Sentiment)
```python
symbol = "AEM"
expiration = "2026-02-13"

exp = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .document(expiration)\
    .get().to_dict()

ratio = exp['put_call_volume_ratio']
sentiment = "Bearish 📉" if ratio > 1 else "Bullish 📈"
print(f"{symbol} P/C Ratio: {ratio:.2f} - {sentiment}")
```

### Find Deep ITM Calls
```python
symbol = "AEM"
expiration = "2026-02-13"
current_price = 215.50

calls = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .document(expiration)\
    .collection("calls")\
    .stream()

deep_itm = [
    doc.to_dict() for doc in calls
    if float(doc.id) < current_price - 10  # 10+ ITM
]

for call in deep_itm[:5]:
    intrinsic = current_price - call['strike']
    time_value = call['last_price'] - intrinsic
    print(f"Strike ${call['strike']}: "
          f"Price ${call['last_price']:.2f} "
          f"(Intrinsic: ${intrinsic:.2f}, Time: ${time_value:.2f})")
```

### Greeks Analysis (Risk Exposure)
```python
symbol = "AEM"
expiration = "2026-02-13"
strike = "210"

call = db.collection("options_chains")\
    .document(symbol)\
    .collection("expirations")\
    .document(expiration)\
    .collection("calls")\
    .document(strike)\
    .get().to_dict()

print(f"Strike ${call['strike']}: ${call['last_price']}")
print(f"  Delta: {call.get('delta', 0):.4f} (price sensitivity)")
print(f"  Gamma: {call.get('gamma', 0):.6f} (delta acceleration)")
print(f"  Theta: {call.get('theta', 0):.4f} (time decay)")
print(f"  Vega:  {call.get('vega', 0):.4f} (volatility sensitivity)")
print(f"  Rho:   {call.get('rho', 0):.4f} (rate sensitivity)")
```

---

## 🔐 Authentication

**Current Auth**: Application Default Credentials (ADC)
**User**: chillcoders@gmail.com
**Status**: ✅ Authenticated

```bash
# Re-authenticate if needed
gcloud auth application-default login

# Verify auth
gcloud auth list
gcloud config get-value project
```

---

## 📊 Quota Status

```
Daily Limit    │ Current Usage   │ % Used
───────────────┼─────────────────┼────────
50,000 reads   │    ~100         │  0.2%
20,000 writes  │    ~100         │  0.5%
 1 GB storage  │   ~85 MB        │  8.5%
20,000 docs    │  ~4,500         │ 22.5%
```

**Status**: ✅ Well within limits - Free tier active, no charges

---

## 🔗 Documentation Files

| File | Purpose |
|------|---------|
| [FIRESTORE_DB_REPORT.md](./FIRESTORE_DB_REPORT.md) | Complete database documentation |
| [FIRESTORE_CLI_REFERENCE.md](./FIRESTORE_CLI_REFERENCE.md) | GCloud & Python commands |
| [FIRESTORE_STATUS_DASHBOARD.md](./FIRESTORE_STATUS_DASHBOARD.md) | Current status & metrics |
| [FINNHUB_OPTIONS_PIPELINE.md](./nubackend1/FINNHUB_OPTIONS_PIPELINE.md) | Pipeline details |

---

## ⚠️ Important Notes

### Real Data Only
- ✅ All data is **real, live market data** from Finnhub
- ✅ Updated daily when pipeline runs
- ❌ No mock data - ever
- ❌ Errors if APIs are unavailable

### Free Tier Limits
- Still have 49,900 read operations today
- Still have 19,900 write operations today
- Plenty of storage (915 MB free)
- No expiration on free tier

### Upgrade for Intraday Data
To get 1-minute through 1-hour candles:
- Option A: Upgrade Finnhub ($129+/month)
- Option B: Upgrade Alpha Vantage ($20+/month)
- No code changes needed - pipeline auto-upgrades

---

## 🆘 Troubleshooting

### Connection Issues
```python
from google.cloud import firestore
import google.auth

# Check auth
creds, proj = google.auth.default()
print(f"Project: {proj}")

# Test connection
db = firestore.Client(project="ttb-lang1")
doc = db.collection("_health_check").document("test").get()
print("Connected!" if doc.exists else "Connection failed")
```

### "Document not found"
```python
# Check if document exists before accessing
doc = db.collection("options_chains").document("INVALID").get()
if doc.exists:
    print(doc.to_dict())
else:
    print("Not found - try: AEM, CRM, IGV, JPM, or QBTS")
```

### "Permission Denied"
```bash
# Re-authenticate
gcloud auth application-default login

# Or check GCP project
gcloud config get-value project
# Should be: ttb-lang1
```

---

## 🎯 Next Steps

### 1. Explore Data
```python
from google.cloud import firestore
db = firestore.Client(project="ttb-lang1")

# See all symbols
symbols = [d.id for d in db.collection("options_chains").stream()]
print(f"Available: {symbols}")
```

### 2. Build Analytics
```python
# Find implied volatility trends
# Calculate Greeks exposure
# Identify options strategies
# Build option pricing models
```

### 3. Automate Tasks
```python
# Schedule pipeline runs
# Monitor quotes in real-time
# Alert on IV changes
# Analyze P/C ratios
```

### 4. Integrate Elsewhere
```python
# Use in FastAPI endpoints
# Feed into ML models
# Build dashboards
# Export to analytics tools
```

---

## 💬 Common Questions

**Q: How often is data updated?**
A: When the pipeline runs (typically daily). Manual trigger available.

**Q: Can I modify the data?**
A: Yes, you have full read/write access to ttb-lang1 project.

**Q: What if APIs are down?**
A: Pipeline fails gracefully and returns HTTP 503. No mock data.

**Q: How long is data retained?**
A: Indefinitely. No auto-delete. Manual cleanup available.

**Q: Can I scale this?**
A: Yes, free tier can handle ~20k documents. Upgrade easily if needed.

**Q: How do I backup?**
A: Firestore has built-in backups. Manual exports available.

---

## 🚀 Ready to Use!

Your database is fully operational and ready for:
- ✅ Real-time options analysis
- ✅ Historical price analysis
- ✅ Volatility studies
- ✅ Greeks calculations
- ✅ Options strategies
- ✅ Machine learning models
- ✅ Custom dashboards

**Get started**: See Python examples above or read full documentation.

---

**Last Updated**: 2026-02-11
**Database**: ttb-lang1 (us-east1)
**Status**: ✅ Fully Operational
