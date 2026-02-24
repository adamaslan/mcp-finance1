# MCP Finance - Enhanced Developer Guide with Skills & Automation

A comprehensive guide for running the MCP Finance application, customizing stocks, and leveraging Claude Skills for rapid development.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Running the Application](#running-the-application)
4. [Claude Skills System](#claude-skills-system)
5. [20+ Recommended Skills](#20-recommended-skills)
6. [Webhook Integration](#webhook-integration)
7. [Changing Stocks Analyzed](#changing-stocks-analyzed)
8. [Configuration Reference](#configuration-reference)
9. [Environment Variables](#environment-variables)
10. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Clone and install
cd "gcp app w mcp"
npm install

# 2. Set up environment (see Environment Variables section)
cp .env.example .env.local

# 3. Start development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 4. Access
Frontend: http://localhost:3000
Backend: http://localhost:8080
```

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Node.js | 20+ | Next.js frontend |
| Python | 3.11+ | FastAPI backend |
| Docker | Latest | Containerization |
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

**Terminal 1: Backend**
```bash
cd mcp-finance1/cloud-run
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export GCP_PROJECT_ID=ttb-lang1
uvicorn main:app --reload --port 8000
```

**Terminal 2: Frontend**
```bash
cd nextjs-mcp-finance
npm install
npm run dev
```

**Access:** Frontend at http://localhost:3000, Backend at http://localhost:8000

---

### Docker Development

```bash
# Start all services with hot-reload
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# View logs
docker-compose logs -f frontend backend

# Stop services
docker-compose down
```

**Services:**
- Frontend: 3000
- Backend: 8080
- Firestore: 8081
- Pub/Sub: 8085

---

### Cloud Run Deployment

```bash
# Deploy backend
./scripts/deploy-backend.sh

# Deploy frontend (set backend URL first)
export MCP_CLOUD_RUN_URL=https://technical-analysis-api-xxx.us-central1.run.app
./scripts/deploy-frontend.sh
```

---

## Claude Skills System

Claude Skills are reusable automation patterns that accelerate development. They combine file templates, validation checks, and best practices into executable workflows.

### What are Skills?

Skills are structured, documented patterns for common development tasks:
- Authentication setup
- Component creation
- API endpoint generation
- Database migrations
- Testing setup
- Webhook integration

### Skill Structure

```json
{
  "name": "skill-name",
  "version": "1.0.0",
  "displayName": "Human Readable Name",
  "description": "What this skill does",
  "category": "frontend|backend|devops|testing",
  "triggers": ["phrases that invoke this skill"],
  "prerequisites": {
    "required": [],
    "optional": []
  },
  "files": {
    "create": [],
    "modify": []
  },
  "hooks": {
    "pre": "Command to run before execution",
    "post": "Command to run after execution"
  }
}
```

### Using Skills

**Via Natural Language:**
```
"Create a new API endpoint for stock alerts"
"Add Clerk authentication pages"
"Set up webhook integration for Discord"
```

**Via Skill Command:**
```
/skill create-api-endpoint --entity=stock-alert
/skill add-auth-pages --provider=clerk
/skill setup-webhook --type=discord
```

---

## 20+ Recommended Skills

### Frontend Skills

#### 1. **Create Component with Tests**
**Category:** Frontend
**Description:** Generate a new React component with TypeScript, tests, and Storybook story
**Triggers:** "Create component", "Add new component"
**Files Created:**
- `src/components/[category]/[Name].tsx`
- `src/components/[category]/[Name].test.tsx`
- `src/components/[category]/[Name].stories.tsx`

**Subskills:**
- `create-component:basic` - Component only
- `create-component:with-state` - With useState hooks
- `create-component:form` - Form component with validation

---

#### 2. **Add API Route Handler**
**Category:** Frontend (Next.js)
**Description:** Create Next.js API route with validation, error handling, and TypeScript
**Triggers:** "Add API route", "Create endpoint"
**Files Created:**
- `src/app/api/[route]/route.ts`
- `src/app/api/[route]/route.test.ts`

**Example:**
```
Create API route for fetching user watchlists
→ Creates: src/app/api/watchlists/route.ts
```

---

#### 3. **Setup Dashboard Page**
**Category:** Frontend
**Description:** Create authenticated dashboard page with layout, header, and navigation
**Triggers:** "Create dashboard", "Add dashboard page"
**Files Created:**
- `src/app/(dashboard)/[page]/page.tsx`
- `src/app/(dashboard)/[page]/layout.tsx`
- `src/components/dashboard/[Page]Header.tsx`

**Subskills:**
- `dashboard:analytics` - With chart components
- `dashboard:table` - With data table
- `dashboard:cards` - With stat cards

---

#### 4. **Add Form with Validation**
**Category:** Frontend
**Description:** Create form component with Zod validation, error handling, and submission
**Triggers:** "Create form", "Add form component"
**Stack:** React Hook Form + Zod
**Files Created:**
- `src/components/forms/[Name]Form.tsx`
- `src/lib/validations/[name]-schema.ts`

---

#### 5. **Create Modal Dialog**
**Category:** Frontend (UI)
**Description:** Generate modal with animations, backdrop, and accessibility
**Triggers:** "Create modal", "Add dialog"
**Files Created:**
- `src/components/modals/[Name]Modal.tsx`
- Uses Radix UI Dialog primitives

---

#### 6. **Add Chart Component**
**Category:** Frontend (Data Visualization)
**Description:** Create interactive chart with Recharts or Chart.js
**Triggers:** "Add chart", "Create graph"
**Options:** Line, Bar, Candlestick, Area, Pie
**Files Created:**
- `src/components/charts/[Type]Chart.tsx`

**Subskills:**
- `chart:line` - Line chart
- `chart:candlestick` - Stock candlestick chart
- `chart:heatmap` - Correlation heatmap

---

#### 7. **Setup Data Table**
**Category:** Frontend (Tables)
**Description:** Create data table with sorting, filtering, pagination
**Triggers:** "Create table", "Add data table"
**Stack:** TanStack Table
**Files Created:**
- `src/components/tables/[Name]Table.tsx`
- `src/components/tables/[Name]Columns.tsx`

---

### Backend Skills

#### 8. **Create FastAPI Endpoint**
**Category:** Backend (Python)
**Description:** Generate FastAPI endpoint with Pydantic models, validation, and docs
**Triggers:** "Create FastAPI endpoint", "Add API route"
**Files Created:**
- `mcp-finance1/cloud-run/routers/[name].py`
- `mcp-finance1/cloud-run/models/[name].py`
- `mcp-finance1/cloud-run/services/[name]_service.py`

**Example Structure:**
```python
# routers/alerts.py
from fastapi import APIRouter, Depends
from models.alert import AlertCreate, AlertResponse
from services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])

@router.post("/", response_model=AlertResponse)
async def create_alert(
    alert: AlertCreate,
    service: AlertService = Depends()
):
    return await service.create_alert(alert)
```

---

#### 9. **Add Pydantic Model**
**Category:** Backend (Validation)
**Description:** Create Pydantic model with validation and serialization
**Triggers:** "Create Pydantic model", "Add data model"
**Files Created:**
- `mcp-finance1/cloud-run/models/[name].py`

**Subskills:**
- `model:request` - Request model
- `model:response` - Response model
- `model:nested` - Nested models

---

#### 10. **Setup Background Task**
**Category:** Backend (Async)
**Description:** Create background task with FastAPI BackgroundTasks
**Triggers:** "Add background task", "Create async job"
**Files Created:**
- `mcp-finance1/cloud-run/tasks/[name]_task.py`

---

#### 11. **Create Service Layer**
**Category:** Backend (Architecture)
**Description:** Generate service class with business logic and error handling
**Triggers:** "Create service", "Add business logic"
**Files Created:**
- `mcp-finance1/cloud-run/services/[name]_service.py`

**Pattern:**
```python
class AlertService:
    def __init__(self, db: Database, gemini_client: GeminiClient):
        self.db = db
        self.gemini = gemini_client

    async def create_alert(self, alert: AlertCreate) -> Alert:
        # Business logic here
        pass
```

---

#### 12. **Add Gemini AI Integration**
**Category:** Backend (AI)
**Description:** Integrate Gemini API for analysis or generation
**Triggers:** "Add AI feature", "Integrate Gemini"
**Files Created:**
- `mcp-finance1/cloud-run/ai/[feature]_analyzer.py`

**Example:**
```python
class StockSentimentAnalyzer:
    async def analyze_news(self, symbol: str) -> SentimentResult:
        prompt = f"Analyze recent news sentiment for {symbol}"
        response = await self.gemini.generate_content(prompt)
        return self.parse_sentiment(response)
```

---

#### 13. **Setup Firestore Collection**
**Category:** Backend (Database)
**Description:** Create Firestore collection with schema and CRUD operations
**Triggers:** "Add Firestore collection", "Create database schema"
**Files Created:**
- `mcp-finance1/cloud-run/db/[collection]_repo.py`

---

#### 14. **Add Rate Limiting**
**Category:** Backend (Middleware)
**Description:** Implement rate limiting with Redis or in-memory store
**Triggers:** "Add rate limiting", "Implement throttling"
**Files Created:**
- `mcp-finance1/cloud-run/middleware/rate_limiter.py`

---

### DevOps & Infrastructure Skills

#### 15. **Create Cloud Function**
**Category:** DevOps (GCP)
**Description:** Generate Cloud Function with deployment script
**Triggers:** "Create Cloud Function", "Add serverless function"
**Files Created:**
- `mcp-finance1/automation/functions/[name]/main.py`
- `mcp-finance1/automation/functions/[name]/requirements.txt`
- `scripts/deploy-[name]-function.sh`

**Example:**
```python
# Daily portfolio analysis function
def analyze_portfolios(event, context):
    """Cloud Function triggered by Pub/Sub"""
    portfolios = fetch_user_portfolios()
    for portfolio in portfolios:
        analysis = analyze_risk(portfolio)
        send_alert_if_needed(portfolio, analysis)
```

---

#### 16. **Setup Cloud Scheduler**
**Category:** DevOps (Automation)
**Description:** Create scheduled job with Cloud Scheduler
**Triggers:** "Add scheduled job", "Create cron job"
**Files Created:**
- `infrastructure/scheduler/[job-name].yaml`
- Deployment script

---

#### 17. **Add Docker Service**
**Category:** DevOps (Containers)
**Description:** Add new service to docker-compose with networking
**Triggers:** "Add Docker service", "Create container"
**Files Modified:**
- `docker-compose.yml`
- `docker-compose.dev.yml`

---

#### 18. **Create Deployment Script**
**Category:** DevOps
**Description:** Generate deployment script for Cloud Run or GKE
**Triggers:** "Create deployment script"
**Files Created:**
- `scripts/deploy-[service].sh`

---

### Testing & Quality Skills

#### 19. **Add E2E Test**
**Category:** Testing (Playwright)
**Description:** Create end-to-end test with Playwright
**Triggers:** "Add E2E test", "Create Playwright test"
**Files Created:**
- `nextjs-mcp-finance/e2e/[feature]/[test-name].spec.ts`

**Example:**
```typescript
test('user can create watchlist', async ({ page }) => {
  await page.goto('/dashboard/watchlists');
  await page.click('button:has-text("New Watchlist")');
  await page.fill('input[name="name"]', 'Tech Stocks');
  await page.click('button:has-text("Create")');
  await expect(page.locator('text=Tech Stocks')).toBeVisible();
});
```

---

#### 20. **Setup Integration Test**
**Category:** Testing (Backend)
**Description:** Create API integration test with pytest
**Triggers:** "Add integration test", "Create API test"
**Files Created:**
- `mcp-finance1/tests/integration/test_[feature].py`

---

#### 21. **Add Performance Test**
**Category:** Testing (Performance)
**Description:** Create load test with k6 or locust
**Triggers:** "Add performance test", "Create load test"
**Files Created:**
- `tests/performance/[test-name].js` (k6)

---

### Database & Schema Skills

#### 22. **Create Drizzle Schema**
**Category:** Database (Frontend DB)
**Description:** Add Drizzle ORM schema with relations
**Triggers:** "Add database table", "Create schema"
**Files Created:**
- `nextjs-mcp-finance/src/lib/db/schema/[table].ts`

**Example:**
```typescript
export const alerts = pgTable('alerts', {
  id: serial('id').primaryKey(),
  userId: text('user_id').notNull(),
  symbol: text('symbol').notNull(),
  condition: text('condition').notNull(),
  targetPrice: decimal('target_price'),
  isActive: boolean('is_active').default(true),
  createdAt: timestamp('created_at').defaultNow(),
});
```

---

#### 23. **Add Migration**
**Category:** Database
**Description:** Create database migration with rollback
**Triggers:** "Add migration", "Create database migration"
**Commands:**
```bash
npm run drizzle:generate  # Generate migration
npm run drizzle:migrate   # Apply migration
```

---

#### 24. **Create Repository Pattern**
**Category:** Database (Architecture)
**Description:** Generate repository with CRUD operations
**Triggers:** "Create repository", "Add data access layer"
**Files Created:**
- `src/lib/repositories/[entity]-repository.ts`

---

### Webhook & Integration Skills

#### 25. **Setup Slack Webhook**
**Category:** Integration
**Description:** Create Slack webhook integration for alerts
**Triggers:** "Add Slack integration", "Setup Slack webhook"
**Files Created:**
- `src/lib/integrations/slack.ts`
- `src/app/api/webhooks/slack/route.ts`

**Example:**
```typescript
export async function sendSlackAlert(webhook: string, alert: Alert) {
  const message = {
    text: `🚨 Alert: ${alert.symbol}`,
    blocks: [
      {
        type: "section",
        text: {
          type: "mrkdwn",
          text: `*${alert.symbol}* hit target price of $${alert.targetPrice}`
        }
      }
    ]
  };

  await fetch(webhook, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(message)
  });
}
```

---

#### 26. **Setup Discord Webhook**
**Category:** Integration
**Description:** Create Discord webhook for notifications
**Triggers:** "Add Discord integration", "Setup Discord webhook"
**Files Created:**
- `src/lib/integrations/discord.ts`

---

#### 27. **Add Stripe Payment**
**Category:** Integration (Payments)
**Description:** Setup Stripe checkout and webhook handling
**Triggers:** "Add Stripe", "Setup payments"
**Files Created:**
- `src/app/api/stripe/checkout/route.ts`
- `src/app/api/webhooks/stripe/route.ts`

---

#### 28. **Create Webhook Handler**
**Category:** Backend (Webhooks)
**Description:** Generic webhook receiver with signature validation
**Triggers:** "Create webhook endpoint"
**Files Created:**
- `src/app/api/webhooks/[service]/route.ts`

---

### Utility & Helper Skills

#### 29. **Add Logging Middleware**
**Category:** Observability
**Description:** Setup structured logging with Winston or Pino
**Triggers:** "Add logging", "Setup logger"
**Files Created:**
- `src/lib/logger.ts`
- `mcp-finance1/cloud-run/utils/logger.py`

---

#### 30. **Create Custom Hook**
**Category:** Frontend (Hooks)
**Description:** Generate React custom hook with tests
**Triggers:** "Create custom hook", "Add React hook"
**Files Created:**
- `src/hooks/use[Name].ts`
- `src/hooks/use[Name].test.ts`

**Examples:**
- `useStockData` - Fetch and cache stock data
- `useWebSocket` - WebSocket connection manager
- `useInfiniteScroll` - Infinite scroll pagination

---

## Webhook Integration

### Webhook Types

The MCP Finance app supports three webhook types:

1. **Slack Webhooks** - Channel notifications
2. **Discord Webhooks** - Server notifications
3. **Custom Webhooks** - Any HTTP endpoint

### Available Events

Configure webhooks to trigger on these events:

| Event ID | Description | Payload |
|----------|-------------|---------|
| `price_target` | Price target hit | `{ symbol, currentPrice, targetPrice }` |
| `trade_signal` | New trade signal | `{ symbol, signal, confidence, timeframe }` |
| `volume_spike` | Unusual volume | `{ symbol, volume, avgVolume, percentChange }` |
| `earnings_reminder` | Earnings date approaching | `{ symbol, earningsDate, daysUntil }` |
| `portfolio_alert` | Portfolio risk change | `{ userId, riskScore, change, reason }` |

### Setup Webhooks

**1. Via UI:**
Navigate to Settings → Integrations → Webhooks

**2. Via API:**
```bash
curl -X POST http://localhost:3000/api/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Trading Alerts",
    "type": "slack",
    "url": "https://hooks.slack.com/services/...",
    "events": ["price_target", "trade_signal"]
  }'
```

**3. Test Webhook:**
```bash
curl -X POST http://localhost:3000/api/webhooks/test/[webhook-id]
```

### Webhook Payload Format

All webhooks receive this standard format:

```json
{
  "event": "price_target",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "symbol": "AAPL",
    "currentPrice": 175.50,
    "targetPrice": 175.00,
    "percentChange": 0.29
  },
  "metadata": {
    "userId": "user_xxx",
    "triggerId": "alert_123"
  }
}
```

### Slack Message Examples

**Price Alert:**
```
🎯 Price Target Hit!
AAPL reached $175.50 (target: $175.00)
+0.29% above target
```

**Trade Signal:**
```
📈 New Trade Signal
TSLA - BUY Signal (Day Trading)
Confidence: 82%
Entry: $242.50 | Target: $248.00
```

---

## Changing Stocks Analyzed

### 1. Stock Universes

**File:** `mcp-finance1/src/technical_analysis_mcp/universes.py`

Add custom universe:

```python
UNIVERSES = {
    # ... existing universes

    "biotech": [
        "MRNA", "BNTX", "PFE", "JNJ", "ABBV", "GILD", "REGN"
    ],

    "ev_sector": [
        "TSLA", "RIVN", "LCID", "NIO", "XPEV", "F", "GM"
    ],
}
```

### 2. Daily Analysis Watchlist

**File:** `mcp-finance1/automation/functions/daily_analysis/main.py`

```python
DEFAULT_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA',
    'MU', 'AMD', 'TSLA', 'META',
    'SPY', 'QQQ', 'IWM', 'XLF', 'XLK', 'DIA'
]
```

Redeploy function:
```bash
cd mcp-finance1/automation/functions/daily_analysis
gcloud functions deploy daily-stock-analysis \
  --runtime python311 \
  --trigger-topic daily-analysis-trigger \
  --project ttb-lang1
```

### 3. Tier-Based Access

**File:** `nextjs-mcp-finance/src/lib/auth/tiers.ts`

```typescript
export const TIER_LIMITS: Record<UserTier, TierLimits> = {
  free: {
    analysesPerDay: 5,
    universes: ['sp500'],
    features: ['basic_analysis'],
  },
  pro: {
    analysesPerDay: 50,
    universes: ['sp500', 'nasdaq100', 'etf_large_cap'],
    features: ['full_analysis', 'portfolio_risk'],
  },
  max: {
    analysesPerDay: Infinity,
    universes: ['sp500', 'nasdaq100', 'etf_large_cap', 'etf_sector', 'crypto'],
    features: ['all'],
  },
};
```

### 4. Popular Symbols (UI)

**File:** `nextjs-mcp-finance/src/components/ui/command-palette.tsx`

```typescript
const POPULAR_SYMBOLS = [
  { symbol: 'AAPL', name: 'Apple Inc.' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.' },
  { symbol: 'MSFT', name: 'Microsoft Corporation' },
  // Add more...
];
```

---

## Configuration Reference

| What to Change | File | Location | Restart Required |
|----------------|------|----------|------------------|
| Stock universes | `universes.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |
| Daily watchlist | `main.py` | `mcp-finance1/automation/functions/daily_analysis/` | Redeploy Function |
| Tier access | `tiers.ts` | `nextjs-mcp-finance/src/lib/auth/` | Frontend |
| UI symbols | `command-palette.tsx` | `nextjs-mcp-finance/src/components/ui/` | Frontend |
| Cache TTL | `config.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |
| Rate limits | `config.py` | `mcp-finance1/src/technical_analysis_mcp/` | Backend |

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

### Frontend (.env.local)

```bash
# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxx
CLERK_SECRET_KEY=sk_test_xxx

# Backend URL
MCP_CLOUD_RUN_URL=http://localhost:8000

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Stripe (Optional)
STRIPE_SECRET_KEY=sk_test_xxx
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_xxx

# Webhooks
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/xxx
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxx
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

# Wait 5-10 seconds, then fetch
curl http://localhost:8080/api/signals/SYMBOL
```

### Rate Limiting (429 Error)

**Cause:** Gemini API limit (10 requests/minute)

**Solution:**
- Wait 60 seconds
- Reduce concurrent requests
- Check `config.py` rate limit settings

### Webhook Not Firing

**Debug:**
```bash
# Check webhook logs
curl http://localhost:3000/api/webhooks/[id]/logs

# Test webhook manually
curl -X POST http://localhost:3000/api/webhooks/test/[id]

# Verify event subscription
curl http://localhost:3000/api/webhooks/[id]
```

### Docker Network Issues

```bash
# Check services
docker-compose ps

# Inspect network
docker network ls
docker network inspect gcp-app-w-mcp_mcp-network

# Restart
docker-compose down && docker-compose up
```

---

## Skill Development Guide

### Creating a Custom Skill

1. **Define Skill JSON:**

```json
{
  "skill": {
    "name": "my-custom-skill",
    "version": "1.0.0",
    "displayName": "My Custom Skill",
    "description": "What it does",
    "category": "frontend",
    "triggers": ["create xyz", "add xyz"],
    "prerequisites": {
      "required": []
    },
    "files": {
      "create": [
        {
          "path": "src/components/[Name].tsx",
          "template": "component-template"
        }
      ]
    }
  }
}
```

2. **Create Templates:**

```typescript
// templates/component-template.ts
export const componentTemplate = (name: string) => `
'use client';

import { useState } from 'react';

export function ${name}() {
  const [state, setState] = useState();

  return (
    <div>
      {/* Component implementation */}
    </div>
  );
}
`;
```

3. **Add Tests:**

```typescript
// templates/component-test-template.ts
export const testTemplate = (name: string) => `
import { render, screen } from '@testing-library/react';
import { ${name} } from './${name}';

describe('${name}', () => {
  it('renders correctly', () => {
    render(<${name} />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });
});
`;
```

4. **Register Skill:**

Add to `docs/skills/` directory and reference in main skills registry.

---

## Quick Reference Commands

```bash
# Development
npm run dev                          # Start frontend
uvicorn main:app --reload            # Start backend
docker-compose up                    # Start all services

# Testing
npm run test:e2e                     # E2E tests
npm run test:e2e:ui                  # Interactive mode
pytest tests/                        # Backend tests

# Deployment
./scripts/deploy-backend.sh          # Deploy backend
./scripts/deploy-frontend.sh         # Deploy frontend

# Database
npm run drizzle:generate             # Generate migration
npm run drizzle:migrate              # Run migration
npm run drizzle:studio               # Open Drizzle Studio

# Skills (via Claude)
"Create API endpoint for alerts"
"Add Slack webhook integration"
"Setup E2E test for watchlist feature"
```

---

## Additional Resources

- **API Documentation:** http://localhost:8080/docs (Swagger UI)
- **GitHub Issues:** Report bugs and features
- **Skills Library:** `docs/skills/` directory
- **Webhook Examples:** `docs/webhooks/` directory

---

## Support

For questions or issues:
1. Check this guide's Troubleshooting section
2. Review skill documentation in `docs/skills/`
3. Open a GitHub issue with reproduction steps
4. Check backend logs: `docker-compose logs backend`
5. Check frontend logs: Browser DevTools console

---

**Version:** 2.0 (Enhanced with Skills & Webhooks)
**Last Updated:** 2024-01-18
**Maintained by:** MCP Finance Team
