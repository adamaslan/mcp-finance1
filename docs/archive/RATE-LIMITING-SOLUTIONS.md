# Gemini API Rate Limiting Solutions

## Current Situation

Your pipeline is hitting Gemini API rate limits (429 errors) because:

- **Free Tier Quota**: 10 requests per minute per model
- **Watchlist Size**: 15 stocks analyzed daily
- **Analysis Frequency**: Daily at 4:30 PM ET
- **Issue**: Processing 15 stocks sequentially with default delays exceeds quota

## Solutions (Ranked by Cost-Effectiveness)

### 1. **Reduce Watchlist Size** ⭐ Recommended (Free)

**Pro**: No additional cost, immediate improvement
**Con**: Analyzes fewer stocks

```python
# Update DEFAULT_WATCHLIST to core holdings
DEFAULT_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'SPY', 'QQQ'  # 7 stocks = ~43 seconds at 6.5s delays
]
```

**Time calculation**: 7 stocks × 6.5s = ~46 seconds (under 1 minute quota)

**Deploy**:
```bash
cd automation/functions/daily_analysis
# Edit main.py and change DEFAULT_WATCHLIST
gcloud functions deploy daily-stock-analysis \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=daily_analysis_pubsub \
  --trigger-topic=daily-analysis-trigger --quiet
```

---

### 2. **Implement Results Caching** ⭐ Recommended (Free)

**Pro**: Reduces API calls by avoiding redundant analyses
**Con**: Adds complexity, requires Firestore reads

Cache AI scores for 24 hours and only re-analyze on significant price changes:

```python
def should_reanalyze(symbol: str, current_price: float) -> bool:
    """Check if stock price changed enough to warrant new analysis."""
    doc = db.collection('analysis').document(symbol).get()
    if not doc.exists:
        return True

    cached_data = doc.to_dict()
    cached_price = cached_data.get('price', 0)
    cached_time = cached_data.get('timestamp', '')

    # Price change threshold: 2%
    price_change = abs((current_price - cached_price) / cached_price)
    if price_change > 0.02:
        return True

    # Time threshold: 24 hours
    from datetime import datetime, timedelta
    cached_dt = datetime.fromisoformat(cached_time)
    if datetime.utcnow() - cached_dt > timedelta(days=1):
        return True

    return False

def analyze_symbol(symbol: str) -> dict:
    """Skip AI ranking if cache is fresh."""
    # ... existing code ...

    if should_reanalyze(symbol, indicators['price']):
        ai_result = rank_with_gemini(symbol, indicators, signals)
    else:
        doc = db.collection('analysis').document(symbol).get()
        cached = doc.to_dict()
        ai_result = {
            'score': cached.get('ai_score'),
            'outlook': cached.get('ai_outlook'),
            'action': cached.get('ai_action'),
            'confidence': cached.get('ai_confidence'),
            'summary': cached.get('ai_summary'),
            'ai_powered': cached.get('ai_powered', True)
        }
        print(f"  [CACHED] Using cached AI result for {symbol}")
```

**Result**: First run analyzes 15 stocks; subsequent runs only re-analyze ~2-3 stocks with significant changes.

---

### 3. **Upgrade Gemini API Model** ($0-20/month)

**Pro**: Higher quotas (100+ requests/min on paid tier)
**Con**: Requires billing setup

Use Gemini 2.5 Flash Image as suggested in error messages:

```python
# Update model selection in main.py
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')  # Changed from gemini-2.0-flash-exp
```

**Cost**:
- Free tier: 10 req/min (current)
- Paid tier: ~$0.075 per 1M input tokens
- Daily analysis: ~15KB tokens = ~$0.000013/day = negligible

**Setup**: Add billing to your GCP project and upgrade API quota.

---

### 4. **Process Multiple Watchlists Sequentially** (Advanced)

**Pro**: Analyze all 15 stocks without hitting rate limits
**Con**: Longer execution time

Split analysis across multiple daily runs:

```python
# automation/functions/daily_analysis/main.py

WATCHLISTS = {
    'morning': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'],      # 9:30 AM ET
    'midday': ['MU', 'AMD', 'TSLA', 'META', 'SPY'],              # 1:00 PM ET
    'afternoon': ['QQQ', 'IWM', 'XLF', 'XLK', 'DIA']            # 4:30 PM ET
}

def run_analysis_scheduled(schedule_id: str):
    """Analyze specific watchlist."""
    watchlist = WATCHLISTS.get(schedule_id, DEFAULT_WATCHLIST)
    # ... rest of analysis ...
```

Then create 3 scheduler jobs (one per watchlist).

---

### 5. **Batch Process with Higher Concurrency** (Advanced)

**Pro**: Faster processing
**Con**: Complex implementation, may still hit rate limits

Use asyncio with semaphore to control concurrency:

```python
import asyncio

async def analyze_with_semaphore(symbol: str, semaphore: asyncio.Semaphore):
    """Analyze symbol with concurrency limit."""
    async with semaphore:
        return analyze_symbol(symbol)

async def run_analysis_concurrent():
    """Analyze multiple stocks with controlled concurrency."""
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent analyses
    tasks = [analyze_with_semaphore(s, semaphore) for s in DEFAULT_WATCHLIST]
    return await asyncio.gather(*tasks)
```

---

## Recommended Approach: Hybrid Strategy

1. **Immediate** (Today): Reduce watchlist to 7 core stocks (Solution #1)
2. **Short-term** (Week 1): Implement caching (Solution #2)
3. **Medium-term** (Month 1): If needed, upgrade to paid Gemini tier (Solution #3)

**Expected Results**:
- Core stocks: No rate limiting issues
- With caching: 80%+ reduction in API calls
- Cost: $0/month (stays free tier)

---

## Monitoring

Check for rate limiting issues:

```bash
# View logs for 429 errors
gcloud functions logs read daily-stock-analysis \
  --region us-central1 --limit 100 | grep -i "429\|quota\|rate"

# Count successful analyses
gcloud functions logs read daily-stock-analysis \
  --region us-central1 --limit 100 | grep "Analyzed:"
```

---

## Implementation Steps

### For Solution #1 (Reduce Watchlist):

```bash
# 1. Edit the function
cat > automation/functions/daily_analysis/main.py << 'EOF'
# ... paste updated file with smaller watchlist ...
EOF

# 2. Redeploy
cd automation/functions/daily_analysis
gcloud functions deploy daily-stock-analysis \
  --gen2 --runtime=python311 --region=us-central1 \
  --source=. --entry-point=daily_analysis_pubsub \
  --trigger-topic=daily-analysis-trigger --quiet
cd ../../..

# 3. Test
gcloud scheduler jobs run daily-analysis-job --location=us-central1
```

### For Solution #2 (Add Caching):

```bash
# Add should_reanalyze() function to main.py
# Modify analyze_symbol() to check cache first
# Redeploy same way as above
```

---

## Cost Comparison

| Solution | Setup | Monthly Cost | API Calls/Day | Issues |
|----------|-------|-------------|---------------|--------|
| Current | Done | $0 | 15 | Rate limiting |
| #1: Reduce | 5 min | $0 | 7 | Fewer insights |
| #2: Caching | 30 min | $0 | 2-3 | Added complexity |
| #3: Upgrade | 10 min | $0.40 | 15 | Billing setup |
| #4: Multi-run | 20 min | $0 | 15 (split) | More scheduler jobs |

---

## FAQ

**Q: Will the current fix (exponential backoff) work?**
A: Partially. It will retry failed requests, but with 15 stocks in ~100 seconds, you'll still exceed the 10/min quota. The backoff helps but isn't a complete solution.

**Q: How do I know if caching is working?**
A: Look for `[CACHED]` messages in logs. Track cache hit rate over time.

**Q: Can I use multiple API keys?**
A: Yes, but you'd need to distribute them across function instances. Not recommended for this use case.

**Q: What if I upgrade later?**
A: All solutions are compatible. Start with #1, add #2, then upgrade if needed.

---

## Next Steps

1. Choose a solution above (recommend #1 + #2)
2. Implement the code changes
3. Redeploy using `gcloud functions deploy`
4. Monitor logs for rate limiting errors
5. Adjust watchlist or cache thresholds based on results
