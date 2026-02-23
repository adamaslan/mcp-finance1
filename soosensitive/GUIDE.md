# MCP Finance - User & Developer Guide

A comprehensive guide for running the MCP Finance application and customizing which stocks are analyzed.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Running the Application](#running-the-application)
   - [Local Development](#local-development-without-docker)
   - [Docker Development](#docker-development)
   - [Docker Production](#docker-production)
   - [Cloud Run Deployment](#cloud-run-deployment)
3. [Changing Stocks Analyzed](#changing-stocks-analyzed)
   - [Stock Universes](#1-stock-universes)
   - [Daily Analysis Watchlist](#2-daily-analysis-watchlist)
   - [Tier-Based Access](#3-tier-based-access-control)
   - [UI Popular Symbols](#4-ui-popular-symbols)
   - [API Analysis](#5-analyzing-custom-symbols-via-api)
   - [User Watchlists](#6-user-watchlists)
4. [Configuration Reference](#configuration-reference)
5. [Environment Variables](#environment-variables)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 20+ | Next.js frontend |
| Python | 3.11+ | FastAPI backend |
| Docker | Latest | Containerization (optional) |
| Google Cloud CLI | Latest | Cloud Run deployment |
| Clerk Account | - | Authentication |

### Quick Install Check

```bash
node --version    # v20.x.x
python --version  # Python 3.11.x
docker --version  # Docker version 24.x.x
gcloud --version  # Google Cloud SDK 4xx.x.x
```

---

## Running the Application

### Local Development (Without Docker)

Best for rapid development with hot-reload.

**Terminal 1: Start Backend**
```bash
cd mcp-finance1/cloud-run

# Create virtual environment (first time only)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GCP_PROJECT_ID=ttb-lang1

# Start server with hot-reload
uvicorn main:app --reload --port 8000
```

**Terminal 2: Start Frontend**
```bash
cd nextjs-mcp-finance

# Install dependencies (first time only)
npm install

# Start dev server
npm run dev
```

**Access Points:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Backend Health: http://localhost:8000/health

---

### Docker Development

Best for testing with GCP emulators (Firestore, Pub/Sub).

```bash
cd "gcp app w mcp"

# Start all services with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Or run in background
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker-compose logs -f frontend backend

# Stop all services
docker-compose down
```

**Services Started:**
| Service | Port | Description |
|---------|------|-------------|
| frontend | 3000 | Next.js with hot-reload |
| backend | 8080 | FastAPI with auto-reload |
| firestore | 8081 | Firestore emulator |
| pubsub | 8085 | Pub/Sub emulator |

---

### Docker Production

Best for testing production builds locally.

```bash
cd "gcp app w mcp"

# Build production images
docker-compose build

# Start production stack
docker-compose up

# Test health endpoints
curl http://localhost:3000
curl http://localhost:8080/health
```

---

### Cloud Run Deployment

Deploy to Google Cloud Run for production.

**Step 1: Deploy Backend**
```bash
cd "gcp app w mcp"
./scripts/deploy-backend.sh
```

This deploys to: `https://technical-analysis-api-xxx.us-central1.run.app`

**Step 2: Deploy Frontend**
```bash
# Set backend URL from Step 1
export MCP_CLOUD_RUN_URL=https://technical-analysis-api-1007181159506.us-central1.run.app

# Deploy frontend
./scripts/deploy-frontend.sh
```

**Verify Deployment:**
```bash
# Check backend health
curl https://technical-analysis-api-xxx.us-central1.run.app/health

# Check frontend
curl https://mcp-finance-frontend-xxx.us-central1.run.app
```

---

## Changing Stocks Analyzed

There are 6 configuration points for controlling which stocks are analyzed:

### 1. Stock Universes

**File:** `mcp-finance1/src/technical_analysis_mcp/universes.py`

Predefined lists of stocks organized by category:

```python
UNIVERSES = {
    # Major indices
    "sp500": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B",
        "UNH", "XOM", "JNJ", "JPM", "V", "PG", "MA", "HD", "CVX", "MRK",
        # ... ~500 symbols
    ],

    "nasdaq100": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "AVGO",
        # ... ~100 symbols
    ],

    # ETFs
    "etf_large_cap": [
        "SPY", "VOO", "IVV", "VTI", "QQQ", "DIA", "IWM", "VEA", "VWO",
    ],

    "etf_sector": [
        "XLK", "XLF", "XLV", "XLE", "XLY", "XLP", "XLI", "XLB", "XLU", "XLRE",
    ],

    # Crypto
    "crypto": [
        "BTC-USD", "ETH-USD", "BNB-USD", "XRP-USD", "ADA-USD",
    ],

    # Thematic
    "tech_leaders": [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
        "AMD", "INTC", "CRM", "ADBE", "ORCL",
    ],

    # Add your own custom universe
    "my_watchlist": [
        "AAPL", "TSLA", "NVDA",
    ],
}
```

**How to Add a New Universe:**

1. Edit `universes.py` and add your universe:
   ```python
   "biotech": ["MRNA", "BNTX", "PFE", "JNJ", "ABBV"],
   ```

2. Restart the backend:
   ```bash
   # Docker
   docker-compose restart backend

   # Local
   # Uvicorn auto-reloads on file change
   ```

3. Access via API:
   ```bash
   curl -X POST http://localhost:8080/api/screen \
     -H "Content-Type: application/json" \
     -d '{"symbols": [], "criteria": {}, "limit": 10}'
   ```

---

### 2. Daily Analysis Watchlist

**File:** `mcp-finance1/automation/functions/daily_analysis/main.py`

Stocks analyzed automatically at market close:

```python
DEFAULT_WATCHLIST = [
    # Tech leaders
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',

    # Semiconductors
    'MU', 'AMD',

    # Other large caps
    'TSLA', 'META',

    # ETFs for market overview
    'SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'DIA'
]
```

**To Modify:**

1. Edit the `DEFAULT_WATCHLIST` array
2. Redeploy the Cloud Function:
   ```bash
   cd mcp-finance1/automation/functions/daily_analysis
   gcloud functions deploy daily-stock-analysis \
     --runtime python311 \
     --trigger-topic daily-analysis-trigger \
     --project ttb-lang1
   ```

**Note:** Daily analysis runs via Cloud Scheduler at market close (4:00 PM ET).

---

### 3. Tier-Based Access Control

**File:** `nextjs-mcp-finance/src/lib/auth/tiers.ts`

Controls which universes each subscription tier can access:

```typescript
export const TIER_LIMITS: Record<UserTier, TierLimits> = {
  free: {
    analysesPerDay: 5,
    scansPerDay: 1,
    scanResultsLimit: 5,
    universes: ['sp500'],  // Only S&P 500
    timeframes: ['swing'],
    features: ['basic_analysis', 'signal_help'],
  },

  pro: {
    analysesPerDay: 50,
    scansPerDay: 10,
    scanResultsLimit: 25,
    universes: ['sp500', 'nasdaq100', 'etf_large_cap'],
    timeframes: ['swing', 'day', 'scalp'],
    features: ['full_analysis', 'portfolio_risk', 'trade_journal'],
  },

  max: {
    analysesPerDay: Infinity,
    scansPerDay: Infinity,
    scanResultsLimit: 50,
    universes: ['sp500', 'nasdaq100', 'etf_large_cap', 'etf_sector', 'crypto'],
    timeframes: ['swing', 'day', 'scalp'],
    features: ['all'],
  },
};
```

**To Add a New Universe to a Tier:**

1. Add the universe name to the `universes` array
2. Rebuild the frontend:
   ```bash
   cd nextjs-mcp-finance
   npm run build
   ```

---

### 4. UI Popular Symbols

**File:** `nextjs-mcp-finance/src/components/ui/command-palette.tsx`

Quick-access symbols shown in the search palette (Cmd+K):

```typescript
const POPULAR_SYMBOLS = [
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corporation' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.' },
  { symbol: 'TSLA', name: 'Tesla Inc.' },
  { symbol: 'NVDA', name: 'NVIDIA Corporation' },
  { symbol: 'META', name: 'Meta Platforms Inc.' },
  { symbol: 'JPM', name: 'JPMorgan Chase & Co.' },
  { symbol: 'V', name: 'Visa Inc.' },
  { symbol: 'SPY', name: 'S&P 500 ETF' },
  { symbol: 'QQQ', name: 'Nasdaq-100 ETF' },
  { symbol: 'IWM', name: 'Russell 2000 ETF' },
];
```

**To Modify:**

1. Edit the `POPULAR_SYMBOLS` array
2. Rebuild frontend or wait for hot-reload

---

### 5. Analyzing Custom Symbols via API

Analyze any stock directly via API, regardless of universe membership:

**Analyze Single Symbol**
```bash
curl -X POST http://localhost:8080/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "period": "1mo",
    "include_ai": true
  }'
```

**Compare Multiple Symbols**
```bash
curl -X POST http://localhost:8080/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN"],
    "period": "1mo"
  }'
```

**Screen Custom Symbol List**
```bash
curl -X POST http://localhost:8080/api/screen \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "TSLA", "NVDA", "AMD", "INTC"],
    "criteria": {
      "min_volume": 1000000,
      "min_signals": 3
    },
    "limit": 10
  }'
```

**Get Signals for Symbol**
```bash
curl http://localhost:8080/api/signals/AAPL
```

---

### 6. User Watchlists

Users can create custom watchlists stored in the database.

**Database Schema:** `nextjs-mcp-finance/src/lib/db/schema.ts`

```typescript
export const watchlists = pgTable('watchlists', {
  id: text('id').primaryKey(),
  userId: text('user_id').notNull(),
  name: text('name').notNull(),
  symbols: text('symbols').array().notNull(),
  isDefault: boolean('is_default').default(false),
  createdAt: timestamp('created_at').defaultNow(),
  updatedAt: timestamp('updated_at').defaultNow(),
});
```

Watchlists are managed through the frontend UI or via API.

---

## Configuration Reference

| What to Change | File | Location | Restart Required |
|----------------|------|----------|------------------|
| Stock universes | `universes.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |
| Daily watchlist | `main.py` | `mcp-finance1/automation/functions/daily_analysis/` | Redeploy Function |
| Tier access | `tiers.ts` | `nextjs-mcp-finance/src/lib/auth/` | Frontend |
| UI quick symbols | `command-palette.tsx` | `nextjs-mcp-finance/src/components/ui/` | Frontend |
| Cache TTL | `config.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |
| Rate limits | `config.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |
| Max signals | `config.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |

---

## Environment Variables

### Backend (.env)

```bash
# GCP Configuration
GCP_PROJECT_ID=ttb-lang1
GCP_REGION=us-central1

# AI Configuration
GEMINI_API_KEY=your-gemini-api-key

# Optional: Service Account
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### Frontend (.env)

```bash
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# Backend URL
MCP_CLOUD_RUN_URL=http://localhost:8000  # or Cloud Run URL

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Optional: Stripe
STRIPE_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx
```

### Docker (.env.docker)

```bash
GCP_PROJECT_ID=ttb-lang1
FIRESTORE_EMULATOR_HOST=firestore:8081
PUBSUB_EMULATOR_HOST=pubsub:8085
```

---

## Troubleshooting

### Symbol Not Found

**Error:** "No analysis found for SYMBOL"

**Solution:**
```bash
# Trigger analysis first
curl -X POST http://localhost:8080/api/analyze \
  -d '{"symbol": "SYMBOL"}'

# Wait 5-10 seconds, then fetch signals
curl http://localhost:8080/api/signals/SYMBOL
```

### Rate Limiting (429 Error)

**Error:** "Rate limit exceeded"

**Cause:** Gemini API has 10 requests/minute limit

**Solution:**
- Wait 60 seconds before retrying
- Reduce concurrent requests in scanner
- Check `config.py` for rate limit settings

### Stale Cache Data

**Problem:** Old signals returned

**Solution:**
```bash
# Clear cache for specific symbol
curl -X POST http://localhost:8080/api/admin/clear-cache?collection=signals

# Or wait for TTL (default 5 minutes)
```

### Docker Network Issues

**Error:** "Cannot connect to backend"

**Solution:**
```bash
# Check if services are running
docker-compose ps

# Check network
docker network ls
docker network inspect gcp-app-w-mcp_mcp-network

# Restart services
docker-compose down && docker-compose up
```

### GCP Emulator Connection Failed

**Error:** "Could not connect to Firestore emulator"

**Solution:**
```bash
# Verify emulator is running
curl http://localhost:8081

# Check environment variable
echo $FIRESTORE_EMULATOR_HOST

# Restart emulator
docker-compose restart firestore
```

### Build Errors

**Frontend:**
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run build
```

**Backend:**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Quick Reference Commands

```bash
# Start local dev
cd mcp-finance1/cloud-run && uvicorn main:app --reload --port 8000
cd nextjs-mcp-finance && npm run dev

# Start Docker dev
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Deploy to Cloud Run
./scripts/deploy-backend.sh
./scripts/deploy-frontend.sh

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:3000

# Analyze a stock
curl -X POST http://localhost:8080/api/analyze -d '{"symbol":"AAPL"}'
```

---

## Support

- **GitHub Issues:** Report bugs and feature requests
- **Documentation:** See `docs/` folder for detailed guides
- **API Reference:** `http://localhost:8080/docs` (Swagger UI)
