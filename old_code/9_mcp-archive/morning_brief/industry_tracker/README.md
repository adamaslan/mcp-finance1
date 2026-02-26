# Industry Tracker Module

Standalone industry performance tracking and analysis tool that maps 50 US industries to their representative ETFs and calculates multi-horizon returns.

## Overview

This module is **completely independent** from the morning_brief logic. It can be used standalone or integrated into other tools.

### Key Features

- **50-Industry Mapping**: Static mapping of US economy sectors to liquid ETFs
- **Multi-Horizon Analysis**: Calculate returns across 11 time horizons:
  - `1w` (1 week, 5 trading days)
  - `2w` (2 weeks, 10 trading days)
  - `1m` (1 month, 21 trading days)
  - `2m`, `3m`, `6m`, `52w`, `2y`, `3y`, `5y`, `10y`
- **Real Data Fetching**: Uses yfinance for live ETF data (no mock data)
- **Performance Ranking**: Identify top/worst performing industries

## Usage

### Basic Example

```python
from industry_tracker import IndustryBrief

# Initialize
brief = IndustryBrief()

# Get top performers for last week
results = brief.generate_brief(horizon="1w", top_n=10)

# Access results
print(f"Average return: {results['metrics']['average_return']}%")
for perf in results['top_performers']:
    print(f"{perf['industry']}: {perf['returns']['1w']:+.2f}%")
```

### API Reference

#### IndustryBrief

```python
class IndustryBrief:
    def fetch_etf_data(etf_ticker: str, days: int = 2520) -> pd.DataFrame
    def calculate_all_industry_performance() -> list[dict]
    def get_top_performers(performances, horizon: str, top_n: int) -> list[dict]
    def get_worst_performers(performances, horizon: str, bottom_n: int) -> list[dict]
    def generate_brief(horizon: str = "1m", top_n: int = 10) -> dict
```

#### IndustryMapper

```python
class IndustryMapper:
    @classmethod
    def get_all_industries() -> list[str]

    @classmethod
    def get_etf(industry: str) -> Optional[str]

    @classmethod
    def get_industry(etf: str) -> Optional[str]

    @classmethod
    def get_all_etfs() -> list[str]
```

#### PerformanceCalculator

```python
class PerformanceCalculator:
    @classmethod
    def calculate_returns(df: pd.DataFrame) -> dict[str, Optional[float]]

    @classmethod
    def calculate_industry_performance(industry: str, etf: str, df: pd.DataFrame) -> dict

    @classmethod
    def get_best_performers(performances: list, horizon: str, top_n: int) -> list[dict]

    @classmethod
    def get_worst_performers(performances: list, horizon: str, bottom_n: int) -> list[dict]
```

## File Structure

```
industry_tracker/
├── __init__.py                 # Module exports
├── industry_mapper.py          # 50-industry to ETF mapping
├── performance_calculator.py   # Multi-horizon return calculations
├── industry_brief.py           # Main module with ETF fetching & analysis
├── README.md                   # This file
└── test_industry_brief.py      # Standalone test script
```

## Testing

Run the standalone test to see best performers for 1 week and 2 weeks:

```bash
cd /Users/adamaslan/code/gcp\ app\ w\ mcp/mcp-finance1/9_mcp/morning_brief
python industry_tracker/test_industry_brief.py
```

### Expected Output

```
================================================================================
INDUSTRY BRIEF TEST - Best Performers Analysis
================================================================================
Generated: 2026-02-24T...

📊 BEST PERFORMERS - LAST WEEK (1w)
────────────────────────────────────────────────────────────────────────────────
Time Horizon: Last Week (5 trading days)
Industries Analyzed: 47
Average Return: +1.23%
Positive: 38 | Negative: 9 | Neutral: 0

Top 10 Performers:

   1. Software                     (IGV)     +3.45%
   2. Cloud Computing              (CLOU)    +2.87%
   3. Semiconductors               (SOXX)    +2.34%
   ...
```

## Dependencies

- **yfinance**: Fetches historical ETF data
- **pandas**: Data manipulation and calculation

Install with mamba:

```bash
mamba activate fin-ai1
mamba install -c conda-forge yfinance pandas
```

## Integration

To use this module in other MCP tools:

```python
from morning_brief.industry_tracker import IndustryBrief, IndustryMapper, PerformanceCalculator

# Use independently - no morning_brief dependency
brief_gen = IndustryBrief()
analysis = brief_gen.generate_brief(horizon="2w", top_n=5)
```

## Notes

- ✅ Uses **real data** from yfinance (no mock data ever)
- ✅ Completely **independent** from morning_brief logic
- ✅ Can be used standalone or integrated into other tools
- ✅ Handles missing data gracefully (returns None for insufficient horizons)
- ✅ Comprehensive logging for debugging

## Error Handling

All methods handle failures gracefully:

```python
try:
    brief = IndustryBrief()
    results = brief.generate_brief(horizon="1w")
except IndustryBriefError as e:
    print(f"Industry brief generation failed: {e}")
```
