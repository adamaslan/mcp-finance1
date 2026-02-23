# Industry Tracker Integration with Morning Brief

Quick guide for integrating the Industry Tracker module with your existing morning_brief API.

## Option 1: Direct Integration (Recommended)

The Industry Tracker is already integrated into your main.py as a standalone module. The morning_brief endpoint can simply call it:

### In your morning_brief handler:

```python
from fastapi import FastAPI, HTTPException

@app.get("/api/morning-brief")
async def morning_brief_endpoint(
    watchlist: list[str] | None = None,
    include_industry_summary: bool = True,
):
    """Generate comprehensive morning market briefing.

    Combines:
    - Watchlist analysis (existing logic)
    - Industry rotation summary (new Industry Tracker)
    - Economic calendar events
    - Market status
    """

    # Your existing morning brief logic
    watchlist_data = await analyze_watchlist(watchlist)

    # Add industry rotation summary
    industry_summary = None
    if include_industry_summary:
        try:
            # Call the Industry Tracker morning summary
            response = await morning_summary_endpoint(horizon="1m")
            industry_summary = response.get("data")
        except Exception as e:
            logger.warning("Industry summary unavailable: %s", e)
            # Degrade gracefully - morning brief works without it

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "watchlist": watchlist_data,
        "industry_rotation": industry_summary,  # NEW
        "economic_events": get_economic_events(),
        "market_status": get_market_status(),
    }
```

## Option 2: Using IndustryService Directly

```python
from industry_tracker.api_service import IndustryService, IndustryServiceError
import os

@app.get("/api/morning-brief")
async def morning_brief_endpoint():
    """Morning brief with industry rotation."""

    # Initialize service
    try:
        industry_service = IndustryService(
            alpha_vantage_key=os.getenv("ALPHA_VANTAGE_KEY"),
            gcp_project_id=os.getenv("GCP_PROJECT_ID"),
        )

        # Get industry summary
        industry_summary = await industry_service.get_morning_summary(
            horizon="1m",
            force_refresh=False,  # Use cached data
        )
    except IndustryServiceError as e:
        logger.error("Industry summary failed: %s", e)
        industry_summary = None

    # Combine with existing brief logic
    return {
        "watchlist": await analyze_watchlist(),
        "industry_rotation": industry_summary,  # NEW
        "economic_events": get_economic_events(),
    }
```

## Option 3: Separate Endpoints (Current Implementation)

Keep the endpoints separate (already implemented in main.py):

- `GET /api/summary/morning` → Industry rotation summary
- `GET /api/morning-brief` → Your existing watchlist brief

Then combine them in the frontend:

```typescript
// Frontend integration
const [watchlistBrief, industryBrief] = await Promise.all([
  fetch('/api/morning-brief'),
  fetch('/api/summary/morning?horizon=1m'),
]);

const combinedBrief = {
  ...watchlistBrief,
  industryRotation: industryBrief.data,
};
```

---

## Recommended Daily Workflow

### 1. Scheduled Cache Refresh (6 AM EST)

```bash
# Cloud Scheduler job
curl -X POST https://your-backend.run.app/api/refresh-all \
  -H "Content-Type: application/json" \
  -d '{"batch_size": 10}'
```

### 2. Morning Brief Generation (8 AM EST)

```bash
# Frontend calls this when user opens app
curl "https://your-backend.run.app/api/summary/morning?horizon=1m"
```

**Result**: Sub-100ms response using cached Firebase data.

---

## Frontend Integration Example

### Display Industry Rotation in Morning Brief

```tsx
// components/MorningBrief.tsx
import { Card } from '@/components/ui/card';

interface IndustryRotation {
  top_performers: Array<{
    industry: string;
    etf: string;
    returns: { [key: string]: number | null };
  }>;
  worst_performers: Array<{ ... }>;
  narrative: string;
  metrics: {
    average_return: number;
    positive_count: number;
    negative_count: number;
  };
}

export function IndustryRotationSection({ data }: { data: IndustryRotation }) {
  return (
    <Card className="p-6">
      <h2 className="text-xl font-bold mb-4">Industry Rotation</h2>

      {/* Market Narrative */}
      <p className="text-gray-700 mb-6">{data.narrative}</p>

      {/* Top Performers */}
      <div className="mb-4">
        <h3 className="font-semibold mb-2">🚀 Top Performers</h3>
        <div className="space-y-2">
          {data.top_performers.slice(0, 5).map((perf) => (
            <div key={perf.industry} className="flex justify-between">
              <span>{perf.industry} ({perf.etf})</span>
              <span className="text-green-600 font-mono">
                +{perf.returns['1m']?.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Worst Performers */}
      <div>
        <h3 className="font-semibold mb-2">📉 Underperformers</h3>
        <div className="space-y-2">
          {data.worst_performers.slice(0, 5).map((perf) => (
            <div key={perf.industry} className="flex justify-between">
              <span>{perf.industry} ({perf.etf})</span>
              <span className="text-red-600 font-mono">
                {perf.returns['1m']?.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Market Breadth */}
      <div className="mt-4 p-4 bg-gray-50 rounded">
        <div className="text-sm text-gray-600">
          Market Breadth: {data.metrics.positive_count} advancing,
          {data.metrics.negative_count} declining
        </div>
        <div className="text-sm text-gray-600">
          Average Return: {data.metrics.average_return > 0 ? '+' : ''}
          {data.metrics.average_return.toFixed(2)}%
        </div>
      </div>
    </Card>
  );
}
```

---

## Testing Integration

### 1. Verify Backend Health

```bash
curl http://localhost:8080/ | jq .industry_tracker_available
# Should return: true
```

### 2. Test Morning Summary

```bash
curl "http://localhost:8080/api/summary/morning?horizon=1m" | jq .
```

### 3. Test Full Integration

```bash
# If you implemented Option 1
curl http://localhost:8080/api/morning-brief | jq .industry_rotation
```

---

## Error Handling

### Graceful Degradation

```python
@app.get("/api/morning-brief")
async def morning_brief_endpoint():
    """Morning brief with graceful degradation."""

    # Always return core brief
    brief = {
        "timestamp": datetime.utcnow().isoformat(),
        "watchlist": await analyze_watchlist(),
        "economic_events": get_economic_events(),
    }

    # Try to add industry rotation (optional)
    try:
        industry_summary = await get_industry_summary()
        brief["industry_rotation"] = industry_summary
    except Exception as e:
        logger.warning("Industry rotation unavailable: %s", e)
        brief["industry_rotation"] = None
        brief["warnings"] = ["Industry rotation data unavailable"]

    return brief
```

---

## Performance Optimization

### Cache TTL Strategy

```python
# In your morning brief endpoint
from datetime import datetime, timedelta

CACHE_TTL = timedelta(hours=1)  # Refresh every hour during market hours

async def get_cached_industry_summary():
    """Get industry summary with 1-hour cache."""
    cache_key = "industry_summary_1m"

    # Check in-memory cache
    cached = memory_cache.get(cache_key)
    if cached and cached["expires_at"] > datetime.utcnow():
        return cached["data"]

    # Fetch fresh from Industry Tracker API
    summary = await fetch_industry_summary()

    # Cache for 1 hour
    memory_cache.set(cache_key, {
        "data": summary,
        "expires_at": datetime.utcnow() + CACHE_TTL,
    })

    return summary
```

---

## Monitoring

### Key Metrics to Track

```python
# Add to your logging/monitoring
logger.info(
    "Morning brief generated",
    extra={
        "watchlist_symbols": len(watchlist),
        "industry_rotation_included": industry_summary is not None,
        "response_time_ms": response_time,
    }
)
```

### Alerts

Set up alerts for:
- Industry Tracker API errors > 5% of requests
- Cache age > 24 hours (stale data)
- Alpha Vantage rate limit hits

---

## Next Steps

1. ✅ Industry Tracker module is complete
2. ✅ API endpoints are live in main.py
3. ⏳ Integrate with morning_brief endpoint (choose Option 1, 2, or 3)
4. ⏳ Set up daily cache refresh (Cloud Scheduler)
5. ⏳ Build frontend UI components
6. ⏳ Deploy to Cloud Run

---

**Need Help?** See [INDUSTRY_TRACKER_GUIDE.md](./INDUSTRY_TRACKER_GUIDE.md) for full API documentation.
