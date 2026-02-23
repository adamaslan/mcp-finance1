# Industry Data Visualization - Setup & Execution Guide

Quick start guide for building 3 months of historical industry data and generating economist-focused visualizations.

---

## 📦 What Was Built

### 1. **Data Collection Script**
[scripts/build_historical_industry_data.py](scripts/build_historical_industry_data.py)
- Fetches 90 days of historical performance for all 50 industries
- Stores daily snapshots in Firestore (`industry_history/{date}/`)
- Respects Alpha Vantage rate limits (12-second delays)
- **Expected Runtime**: ~3 hours for 90 days (10 minutes per day × 90 days)

### 2. **Visualization Script**
[scripts/visualize_industry_data.py](scripts/visualize_industry_data.py)
- Generates 3 core graphs from economist's perspective
- Creates markdown analysis summary
- **Output**: 4 files in `graphs/` directory

### 3. **Advanced Analysis Guide**
[INDUSTRY_DATA_ADVANCED_ANALYSIS.md](INDUSTRY_DATA_ADVANCED_ANALYSIS.md)
- 9 additional graph ideas
- 5 applications for the data
- Implementation roadmap

---

## 🚀 Quick Start (10 minutes)

### Step 1: Install Visualization Dependencies

```bash
# Activate environment
mamba activate fin-ai1

# Install matplotlib + seaborn
mamba install -c conda-forge matplotlib seaborn

# Verify
python -c "import matplotlib; import seaborn; print('OK')"
```

### Step 2: Set Environment Variables

```bash
# Already set from industry tracker setup
echo $ALPHA_VANTAGE_KEY    # Should be set
echo $GCP_PROJECT_ID       # Should be set

# If not set, add to .env
export ALPHA_VANTAGE_KEY=your-key
export GCP_PROJECT_ID=your-project
```

### Step 3: Build Historical Data (⚠️ SLOW - 3 hours)

```bash
cd nubackend1

# Run data collection (this will take ~3 hours)
python scripts/build_historical_industry_data.py
```

**What happens**:
- Fetches performance for all 50 industries
- Repeats for each of 90 days
- Stores in Firestore: `industry_history/2024-11-22/Software`, etc.
- Rate limited to avoid API quota

**Monitoring progress**:
```bash
# Tail the logs in another terminal
tail -f nubackend1.log  # If logging to file

# Or watch Firestore console:
# https://console.firebase.google.com/project/YOUR_PROJECT/firestore
```

### Step 4: Generate Visualizations (Fast - 2 minutes)

```bash
# After data collection completes
python scripts/visualize_industry_data.py --days 90
```

**Output**:
```
graphs/
├── sector_rotation_heatmap.png       # 1. Momentum across industries
├── economic_cycle_dashboard.png      # 2. Cyclical vs Defensive
├── correlation_matrix.png            # 3. Industry relationships
└── analysis_summary.md               # Markdown report
```

---

## 📊 The 3 Core Graphs

### Graph 1: Sector Rotation Heatmap

**Purpose**: Identify momentum shifts across all 50 industries over time.

**What it shows**:
- X-axis: Time (weekly snapshots)
- Y-axis: 50 industries
- Color: 1-month return (green = outperforming, red = underperforming)

**Economist's interpretation**:
- **Hot streaks** (consecutive green) = sustained sector leadership
- **Cold streaks** (consecutive red) = sustained underperformance
- **Color transitions** = inflection points / rotation events
- **Clusters** = related industries moving together

**Use cases**:
- Identify sector rotation opportunities
- Spot momentum persistence vs mean reversion
- Timing entry/exit for sector trades

---

### Graph 2: Economic Cycle Dashboard

**Purpose**: Track cyclical vs defensive sector performance to identify market regime.

**What it shows**:
- **Top panel**: 4 sector trend lines (Cyclical, Defensive, Financial, Commodity)
- **Bottom panel**: Cyclical - Defensive spread (risk appetite gauge)

**Economist's interpretation**:
- **Spread > +3%**: Strong **risk-on** (growth stocks, small caps, EM)
- **Spread -1% to +1%**: **Neutral** (balanced allocation)
- **Spread < -3%**: Strong **risk-off** (quality, dividends, defensive)

**Use cases**:
- Tactical asset allocation
- Portfolio tilts based on regime
- Risk management (reduce exposure in risk-off)

**Example**:
```
Current Spread: +4.2%
→ Interpretation: Risk-on environment
→ Action: Overweight cyclical growth, underweight defensives
```

---

### Graph 3: Correlation Matrix (Clustered)

**Purpose**: Show which industries move together (useful for diversification).

**What it shows**:
- Heatmap: Industries × Industries
- Color: Correlation coefficient (-1 to +1)
- Dendrograms: Hierarchical clustering showing sector groupings

**Economist's interpretation**:
- **Dark red clusters** (high correlation) = industries driven by common factors
- **Dark blue** (negative correlation) = natural hedges
- **Clustered groups** = sector families (e.g., all tech together)

**Use cases**:
- Portfolio diversification
- Risk factor analysis
- Identify pairs for relative value trades

**Example**:
```
Software ↔ Semiconductors: +0.85 (highly correlated)
→ Diversifying within tech provides little risk reduction
→ Need exposure to other sectors for true diversification
```

---

## 📈 Interpreting the Analysis Summary

The script also generates `graphs/analysis_summary.md` with:

### 1. Market Summary
- Average 1-month return across all industries
- Breadth (% advancing vs declining)
- Economic cycle indicator (cyclical vs defensive spread)

### 2. Top/Bottom Performers
- Tables of best and worst industries
- Helps identify rotation leaders

### 3. Key Insights
- Economist's perspective on current market regime
- Breadth analysis (strong/weak participation)
- Correlation insights (diversification opportunities)

### 4. Data Quality Notes
- Source verification
- Calculation methodology
- Timestamp and freshness

---

## ⚠️ Important Notes

### Data Collection Best Practices

**1. Run Once Daily** (Not every time you need data):
```bash
# Good: Run once at market close
0 18 * * * python scripts/build_historical_industry_data.py

# Bad: Running multiple times wastes API quota
```

**2. Alpha Vantage Rate Limits**:
- Free tier: 25 requests/day
- Script uses 5-10 requests per day with batch_size=5
- Full 90-day backfill: ~450 requests (spread over multiple days)

**3. Incremental Updates**:
```python
# Modify script to only fetch missing days
existing_dates = get_existing_dates_from_firestore()
dates_to_fetch = [d for d in all_dates if d not in existing_dates]
```

### Visualization Best Practices

**1. Refresh Graphs Daily**:
```bash
# After market close, regenerate visualizations
python scripts/visualize_industry_data.py --days 90
```

**2. Customize Time Periods**:
```bash
# Last 30 days only
python scripts/visualize_industry_data.py --days 30

# Full 90 days
python scripts/visualize_industry_data.py --days 90
```

**3. Export for Presentations**:
- Graphs saved as high-res PNG (300 DPI)
- Ready for PowerPoint, reports, client decks
- Analysis summary in markdown (convert to PDF with Pandoc)

---

## 🔧 Troubleshooting

### Issue: "No historical data found"

**Cause**: Data collection script hasn't run yet.

**Fix**:
```bash
python scripts/build_historical_industry_data.py
```

### Issue: "ModuleNotFoundError: No module named 'matplotlib'"

**Cause**: Visualization dependencies not installed.

**Fix**:
```bash
mamba install -c conda-forge matplotlib seaborn
```

### Issue: "Alpha Vantage rate limit exceeded"

**Cause**: Too many API calls in short period.

**Fix**:
- Wait 24 hours for quota reset
- Use `batch_size=5` in script (already default)
- Consider upgrading to Alpha Vantage premium ($50/month for 500 calls/day)

### Issue: Empty graphs / no data points

**Cause**: Firestore collections empty or wrong date range.

**Fix**:
```bash
# Check Firestore console
# Collection: industry_history
# Should have sub-collections like: 2024-11-22, 2024-11-23, etc.

# Verify locally
python -c "
from scripts.build_historical_industry_data import HistoricalDataBuilder
import asyncio
builder = HistoricalDataBuilder('key', 'project')
data = asyncio.run(builder.get_historical_snapshot('2024-11-22'))
print(len(data))  # Should be 50
"
```

---

## 📁 File Structure

```
nubackend1/
├── scripts/
│   ├── build_historical_industry_data.py   # Data collection
│   └── visualize_industry_data.py          # Graph generation
├── graphs/                                 # Output directory
│   ├── sector_rotation_heatmap.png
│   ├── economic_cycle_dashboard.png
│   ├── correlation_matrix.png
│   └── analysis_summary.md
├── INDUSTRY_DATA_ADVANCED_ANALYSIS.md      # 9 more graphs + 5 uses
└── VISUALIZATION_SETUP_GUIDE.md            # This file
```

---

## 🎯 Next Steps

1. ✅ Scripts created
2. ⏳ **Run data collection** (3 hours, one-time)
3. ⏳ **Generate initial graphs** (2 minutes)
4. ⏳ Review outputs and analysis
5. ⏳ Choose from 9 additional graphs to implement
6. ⏳ Explore 5 applications (trading signals, portfolio optimization, etc.)

---

## 📚 Additional Resources

- **Advanced Analysis**: [INDUSTRY_DATA_ADVANCED_ANALYSIS.md](INDUSTRY_DATA_ADVANCED_ANALYSIS.md)
- **Industry Tracker API**: [INDUSTRY_TRACKER_GUIDE.md](INDUSTRY_TRACKER_GUIDE.md)
- **Integration Guide**: [INDUSTRY_TRACKER_INTEGRATION.md](INDUSTRY_TRACKER_INTEGRATION.md)

---

**Ready to start?** Run the data collection script:

```bash
python scripts/build_historical_industry_data.py
```

Then generate visualizations:

```bash
python scripts/visualize_industry_data.py --days 90
```

**Results in**: `graphs/` directory 📊
