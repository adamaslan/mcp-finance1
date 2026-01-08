# Next.js MCP Finance Integration Plan

## Overview

Build a Next.js 14+ application that serves as a **decision-explanation engine** for traders. Not a charting app - a system that tells you WHAT to do, WHY, and WHEN to exit.

**Core Philosophy:** Risk-First. No entry is shown until risk is defined. Every trade plan includes entry/stop/target/invalidation.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14+ (App Router, Server Components, Server Actions) |
| Auth | Clerk |
| Payments | Stripe (subscriptions) |
| Database | PostgreSQL + Drizzle ORM |
| MCP Client | Custom TypeScript wrapper around MCP server |
| Styling | Tailwind CSS + shadcn/ui |
| State | React Query (TanStack Query) for server state |
| Charts | Lightweight Charts (TradingView) - minimal, for context only |

---

## MCP Tools Available (from codebase)

| Tool | Purpose | Key Outputs |
|------|---------|-------------|
| `analyze_security` | Full technical analysis | 150+ signals, indicators, AI ranking |
| `get_trade_plan` | Risk-qualified trade plan | 1-3 plans OR suppression reasons |
| `scan_universe` | Scan SP500/NASDAQ100/ETFs | Qualified setups sorted by quality |
| `portfolio_risk` | Aggregate portfolio risk | Sector concentration, hedge suggestions |
| `morning_brief` | Daily market overview | Market status, events, themes |
| `indicator_help` | Indicator education | 18+ indicators explained |
| `signal_help` | Signal education | 21 signals explained |

---

## TypeScript Types (matching MCP outputs)

```typescript
interface TradePlan {
  symbol: string;
  timestamp: string;
  timeframe: "swing" | "day" | "scalp";
  bias: "bullish" | "bearish" | "neutral";
  risk_quality: "high" | "medium" | "low";
  entry_price: number;
  stop_price: number;
  target_price: number;
  invalidation_price: number;
  risk_reward_ratio: number;
  expected_move_percent: number;
  max_loss_percent: number;
  vehicle: "stock" | "option_call" | "option_put" | "option_spread";
  vehicle_notes: string | null;
  option_dte_range: [number, number] | null;
  option_delta_range: [number, number] | null;
  option_spread_width: number | null;
  primary_signal: string;
  supporting_signals: string[];
  is_suppressed: boolean;
  suppression_reasons: SuppressionReason[];
}

interface SuppressionReason {
  code: SuppressionCode;
  message: string;
  threshold: number | null;
  actual: number | null;
}

type SuppressionCode =
  | "STOP_TOO_WIDE"        // Stop > 3 ATR
  | "STOP_TOO_TIGHT"       // Stop < 0.5 ATR
  | "RR_UNFAVORABLE"       // R:R < 1.5:1
  | "NO_CLEAR_INVALIDATION"
  | "VOLATILITY_TOO_HIGH"  // ATR > 3% of price
  | "VOLATILITY_TOO_LOW"   // ATR < 1.5% of price
  | "NO_TREND"             // ADX < 20
  | "CONFLICTING_SIGNALS"  // >40% signals conflict
  | "INSUFFICIENT_DATA"
  | "NEAR_EARNINGS"
  | "MARKET_CLOSED";

interface RiskMetrics {
  atr: number;
  atr_percent: number;
  volatility_regime: "low" | "medium" | "high";
  adx: number;
  is_trending: boolean;
  bb_width_percent: number;
  volume_ratio: number;
}

interface ScanResult {
  universe: string;
  total_scanned: number;
  qualified_trades: TradePlan[];
  timestamp: string;
  duration_seconds: number;
}

interface PortfolioRiskResult {
  total_value: number;
  total_max_loss: number;
  risk_percent_of_portfolio: number;
  positions: PositionRisk[];
  sector_concentration: Record<string, number>;
  overall_risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  hedge_suggestions: string[];
  timestamp: string;
}

interface PositionRisk {
  symbol: string;
  shares: number;
  entry_price: number;
  current_price: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_percent: number;
  stop_level: number;
  max_loss_dollar: number;
  max_loss_percent: number;
  risk_quality: string;
  timeframe: string;
  sector: string;
}

interface MorningBrief {
  timestamp: string;
  market_status: MarketStatus;
  economic_events: EconomicEvent[];
  watchlist_signals: WatchlistSignal[];
  sector_leaders: SectorMove[];
  sector_losers: SectorMove[];
  key_themes: string[];
}

interface MarketStatus {
  status: "pre_market" | "open" | "post_market" | "closed";
  current_time: string;
  market_open_time: string;
  market_close_time: string;
  next_open_time: string | null;
  market_sentiment: "BULLISH" | "BEARISH" | "NEUTRAL";
}

interface WatchlistSignal {
  symbol: string;
  price: number;
  change_percent: number;
  top_signals: string[];
  risk_assessment: string;
  action: "BUY" | "HOLD" | "AVOID";
  key_support: number;
  key_resistance: number;
}
```

---

## Directory Structure

```
nextjs-mcp-finance/
├── src/
│   ├── app/
│   │   ├── (auth)/
│   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   └── sign-up/[[...sign-up]]/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx                      # Sidebar + header
│   │   │   ├── page.tsx                        # Dashboard home (morning brief)
│   │   │   ├── analyze/
│   │   │   │   └── [symbol]/page.tsx           # Deep analysis view
│   │   │   ├── scanner/
│   │   │   │   └── page.tsx                    # Universe scanner
│   │   │   ├── portfolio/
│   │   │   │   └── page.tsx                    # Portfolio risk view
│   │   │   ├── watchlist/
│   │   │   │   └── page.tsx                    # Watchlist management
│   │   │   ├── trade-journal/
│   │   │   │   └── page.tsx                    # Trade logging
│   │   │   ├── learn/
│   │   │   │   ├── signals/page.tsx            # Signal education
│   │   │   │   └── indicators/page.tsx         # Indicator education
│   │   │   └── settings/
│   │   │       └── page.tsx                    # User preferences
│   │   ├── api/
│   │   │   ├── mcp/
│   │   │   │   ├── analyze/route.ts
│   │   │   │   ├── trade-plan/route.ts
│   │   │   │   ├── scan/route.ts
│   │   │   │   ├── portfolio-risk/route.ts
│   │   │   │   └── morning-brief/route.ts
│   │   │   ├── webhooks/
│   │   │   │   ├── clerk/route.ts
│   │   │   │   └── stripe/route.ts
│   │   │   └── cron/
│   │   │       ├── morning-brief/route.ts
│   │   │       └── scan-alerts/route.ts
│   │   └── layout.tsx
│   ├── components/
│   │   ├── trade-plan/
│   │   │   ├── TradePlanCard.tsx
│   │   │   ├── EntryStopTarget.tsx
│   │   │   ├── RiskQualityBadge.tsx
│   │   │   └── SuppressionExplainer.tsx
│   │   ├── signals/
│   │   │   ├── SignalList.tsx
│   │   │   ├── SignalCard.tsx
│   │   │   └── SignalStrengthBadge.tsx
│   │   ├── indicators/
│   │   │   ├── IndicatorPanel.tsx
│   │   │   └── IndicatorExplainer.tsx
│   │   ├── portfolio/
│   │   │   ├── PositionCard.tsx
│   │   │   ├── SectorConcentration.tsx
│   │   │   └── HedgeSuggestions.tsx
│   │   ├── scanner/
│   │   │   ├── UniverseSelector.tsx
│   │   │   └── ScanResultsTable.tsx
│   │   └── ui/                                  # shadcn components
│   ├── lib/
│   │   ├── mcp/
│   │   │   ├── client.ts
│   │   │   └── types.ts
│   │   ├── db/
│   │   │   ├── schema.ts
│   │   │   └── queries.ts
│   │   └── stripe/
│   │       └── config.ts
│   └── server/
│       └── actions/
│           ├── analyze.ts
│           ├── scan.ts
│           └── portfolio.ts
├── drizzle/
│   └── migrations/
├── public/
├── .env.local
├── package.json
├── drizzle.config.ts
└── tailwind.config.ts
```

---

## Database Schema (Drizzle)

```typescript
// lib/db/schema.ts
import { pgTable, text, timestamp, jsonb, real, integer, boolean } from 'drizzle-orm/pg-core';

export const users = pgTable('users', {
  id: text('id').primaryKey(),                    // Clerk user ID
  email: text('email').notNull(),
  subscriptionTier: text('subscription_tier').default('free'),
  stripeCustomerId: text('stripe_customer_id'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const watchlists = pgTable('watchlists', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id),
  name: text('name').notNull(),
  symbols: text('symbols').array(),
  isDefault: boolean('is_default').default(false),
  createdAt: timestamp('created_at').defaultNow(),
});

export const positions = pgTable('positions', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id),
  symbol: text('symbol').notNull(),
  shares: real('shares').notNull(),
  entryPrice: real('entry_price').notNull(),
  entryDate: timestamp('entry_date').notNull(),
  notes: text('notes'),
  status: text('status').default('open'),         // open, closed
  createdAt: timestamp('created_at').defaultNow(),
});

export const tradeJournal = pgTable('trade_journal', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id),
  positionId: text('position_id').references(() => positions.id),
  symbol: text('symbol').notNull(),
  entryPrice: real('entry_price').notNull(),
  exitPrice: real('exit_price'),
  shares: real('shares').notNull(),
  pnl: real('pnl'),
  pnlPercent: real('pnl_percent'),
  tradePlanSnapshot: jsonb('trade_plan_snapshot'), // TradePlan at entry
  entryReason: text('entry_reason'),
  exitReason: text('exit_reason'),
  lessons: text('lessons'),
  entryDate: timestamp('entry_date').notNull(),
  exitDate: timestamp('exit_date'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const alerts = pgTable('alerts', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id),
  symbol: text('symbol').notNull(),
  alertType: text('alert_type').notNull(),        // price, signal, suppression_clear
  condition: jsonb('condition').notNull(),
  isActive: boolean('is_active').default(true),
  lastTriggered: timestamp('last_triggered'),
  createdAt: timestamp('created_at').defaultNow(),
});

export const scanHistory = pgTable('scan_history', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id),
  universe: text('universe').notNull(),
  results: jsonb('results').notNull(),            // ScanResult
  createdAt: timestamp('created_at').defaultNow(),
});

export const usageTracking = pgTable('usage_tracking', {
  id: text('id').primaryKey(),
  userId: text('user_id').references(() => users.id),
  date: text('date').notNull(),                   // YYYY-MM-DD
  analysisCount: integer('analysis_count').default(0),
  scanCount: integer('scan_count').default(0),
  createdAt: timestamp('created_at').defaultNow(),
});
```

---

## 50+ Features by Category

### Category 1: Core Trading Intelligence (12 features)

| # | Feature | Description | MCP Tool | Phase |
|---|---------|-------------|----------|-------|
| 1 | Trade Plan Generator | Primary trade plan with entry/stop/target | `get_trade_plan` | 1 |
| 2 | Risk Quality Badge | HIGH/MEDIUM/LOW visual indicator | `get_trade_plan` | 1 |
| 3 | Suppression Explainer | "No trade because..." with codes | `get_trade_plan` | 1 |
| 4 | Universe Scanner | Scan SP500/NASDAQ100/ETFs for setups | `scan_universe` | 1 |
| 5 | Watchlist Analysis | Analyze custom watchlist | `analyze_security` | 1 |
| 6 | Morning Brief | Daily market overview | `morning_brief` | 1 |
| 7 | Signal Ranking Display | Top signals with strength | `analyze_security` | 1 |
| 8 | Multi-Timeframe View | Swing/Day/Scalp perspectives | `get_trade_plan` | 2 |
| 9 | Bias Indicator | Bullish/Bearish/Neutral | `get_trade_plan` | 1 |
| 10 | Primary Signal Highlight | What's driving the trade | `get_trade_plan` | 1 |
| 11 | Supporting Signals | Secondary confirmations | `get_trade_plan` | 1 |
| 12 | Invalidation Level | When thesis is wrong | `get_trade_plan` | 1 |

### Category 2: Indicator & Signal Explainability (8 features)

| # | Feature | Description | MCP Tool | Phase |
|---|---------|-------------|----------|-------|
| 13 | Signal Education Cards | What each signal means | `signal_help` | 1 |
| 14 | Indicator Glossary | Learn all 18+ indicators | `indicator_help` | 1 |
| 15 | Signal Strength Breakdown | Why signal is STRONG/WEAK | `analyze_security` | 2 |
| 16 | Indicator Values Display | Current ATR, ADX, RSI, etc. | `analyze_security` | 1 |
| 17 | Volatility Regime Explainer | LOW/MEDIUM/HIGH meaning | `get_trade_plan` | 1 |
| 18 | Trend Status | ADX-based trending/ranging | `analyze_security` | 1 |
| 19 | Volume Analysis | Volume ratio interpretation | `analyze_security` | 2 |
| 20 | BB Width Context | Squeeze/expansion status | `analyze_security` | 2 |

### Category 3: Risk & Position Management (10 features)

| # | Feature | Description | MCP Tool | Phase |
|---|---------|-------------|----------|-------|
| 21 | Portfolio Risk Dashboard | Aggregate risk view | `portfolio_risk` | 1 |
| 22 | Position Tracker | Track open positions | `portfolio_risk` | 1 |
| 23 | Sector Concentration | Exposure by sector | `portfolio_risk` | 1 |
| 24 | Hedge Suggestions | "Add XLF put to hedge..." | `portfolio_risk` | 2 |
| 25 | Max Loss Calculator | Dollar risk per position | `portfolio_risk` | 1 |
| 26 | Overall Risk Level | LOW/MEDIUM/HIGH/CRITICAL | `portfolio_risk` | 1 |
| 27 | Stop Level Monitor | Distance to stop prices | `portfolio_risk` | 2 |
| 28 | P&L Tracking | Unrealized gains/losses | `portfolio_risk` | 1 |
| 29 | Risk-Adjusted Sizing | Position size suggestions | Calculated | 2 |
| 30 | Correlation Warning | Correlated positions alert | Future | 3 |

### Category 4: Options-Specific Intelligence (7 features)

| # | Feature | Description | MCP Tool | Phase |
|---|---------|-------------|----------|-------|
| 31 | Vehicle Recommendation | Stock vs options decision | `get_trade_plan` | 1 |
| 32 | DTE Range Suggestion | "30-45 DTE recommended" | `get_trade_plan` | 1 |
| 33 | Delta Range Suggestion | "0.40-0.60 delta calls" | `get_trade_plan` | 1 |
| 34 | Spread Width Suggestion | ATR-based spread sizing | `get_trade_plan` | 2 |
| 35 | Expected Move Display | % move for options sizing | `get_trade_plan` | 1 |
| 36 | Vehicle Notes | Why options over stock | `get_trade_plan` | 1 |
| 37 | Options Strategy Matcher | Match volatility to strategy | Calculated | 3 |

### Category 5: UX, Trust & Retention (7 features)

| # | Feature | Description | Phase |
|---|---------|-------------|-------|
| 38 | Trade Journal | Log entries/exits with snapshots | 2 |
| 39 | Journal Analytics | Win rate, avg R, best setups | 2 |
| 40 | Saved Scans | Save scanner configurations | 2 |
| 41 | Alert System | Price/signal/suppression alerts | 2 |
| 42 | Email Morning Brief | Daily brief to inbox | 2 |
| 43 | Mobile-Responsive UI | Works on all devices | 1 |
| 44 | Dark/Light Mode | Theme preference | 1 |

### Category 6: Platform & Scaling Foundations (6 features)

| # | Feature | Description | Phase |
|---|---------|-------------|-------|
| 45 | Clerk Authentication | Sign in/up, user management | 1 |
| 46 | Stripe Subscriptions | Free/Pro/Premium tiers | 1 |
| 47 | Rate Limiting | Protect MCP server | 1 |
| 48 | Caching Layer | Redis for frequent queries | 2 |
| 49 | Background Jobs | Scheduled scans, alerts | 2 |
| 50 | Usage Analytics | Track feature usage | 2 |

---

## Subscription Tiers

| Tier | Price | Limits |
|------|-------|--------|
| Free | $0/mo | 5 analyses/day, 1 scan/day, basic signals |
| Pro | $29/mo | 50 analyses/day, 10 scans/day, all signals, portfolio risk |
| Premium | $79/mo | Unlimited, priority scanning, alerts, API access |

---

## Phase 1: MVP (Weeks 1-4)

**Goal:** 10 core features that deliver immediate value and justify subscription.

### Week 1: Foundation
- [ ] Next.js project setup with App Router
- [ ] Clerk authentication integration
- [ ] Basic layout and navigation
- [ ] MCP client wrapper in TypeScript
- [ ] Environment setup

### Week 2: Core Trade Plan
- [ ] Trade plan page (`/analyze/[symbol]`)
- [ ] TradePlanCard component
- [ ] EntryStopTarget visualization
- [ ] RiskQualityBadge component
- [ ] SuppressionExplainer component
- [ ] Signal display components

### Week 3: Scanner & Dashboard
- [ ] Universe scanner page
- [ ] Morning brief dashboard
- [ ] Watchlist management
- [ ] Database schema + Drizzle setup
- [ ] Position entry form

### Week 4: Monetization & Education
- [ ] Portfolio risk page
- [ ] Stripe integration
- [ ] Usage limits enforcement
- [ ] Signal/indicator education pages
- [ ] Mobile responsive polish

---

## Phase 2: Engagement & Retention (Weeks 5-8)

- [ ] Trade Journal with snapshots
- [ ] Journal analytics (win rate, avg R)
- [ ] Alert system (email + in-app)
- [ ] Hedge suggestions display
- [ ] Multi-timeframe analysis
- [ ] Saved scans
- [ ] Email morning brief (Resend/SendGrid)
- [ ] Advanced indicator displays
- [ ] Redis caching
- [ ] Background jobs (Vercel Cron)

---

## Phase 3: Scale & Differentiation (Weeks 9-12)

- [ ] Options strategy matcher
- [ ] Correlation warnings
- [ ] API access for Premium
- [ ] Backtesting integration
- [ ] Social features (share trade plans)
- [ ] Advanced alerting (Telegram/Discord)

---

## Key Components

### TradePlanCard

```tsx
// components/trade-plan/TradePlanCard.tsx
interface TradePlanCardProps {
  plan: TradePlan;
}

export function TradePlanCard({ plan }: TradePlanCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold">{plan.symbol}</h2>
          <RiskQualityBadge quality={plan.risk_quality} />
        </div>
        <div className="flex gap-2">
          <Badge variant={plan.bias === 'bullish' ? 'success' : 'destructive'}>
            {plan.bias.toUpperCase()}
          </Badge>
          <Badge variant="outline">{plan.timeframe}</Badge>
          <Badge variant="secondary">{plan.vehicle}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <EntryStopTarget
          entry={plan.entry_price}
          stop={plan.stop_price}
          target={plan.target_price}
          invalidation={plan.invalidation_price}
        />
        <div className="mt-4 grid grid-cols-3 gap-4 text-center">
          <Stat label="R:R" value={`${plan.risk_reward_ratio.toFixed(1)}:1`} />
          <Stat label="Expected Move" value={`${plan.expected_move_percent.toFixed(1)}%`} />
          <Stat label="Max Loss" value={`${plan.max_loss_percent.toFixed(1)}%`} />
        </div>
        {plan.vehicle !== 'stock' && (
          <OptionSuggestion
            dte={plan.option_dte_range}
            delta={plan.option_delta_range}
            notes={plan.vehicle_notes}
          />
        )}
        <SignalSummary
          primary={plan.primary_signal}
          supporting={plan.supporting_signals}
        />
      </CardContent>
    </Card>
  );
}
```

### SuppressionExplainer

```tsx
// components/trade-plan/SuppressionExplainer.tsx
const SUPPRESSION_MESSAGES: Record<SuppressionCode, string> = {
  STOP_TOO_WIDE: "Stop loss is too far from entry (>3 ATR). Risk too high.",
  STOP_TOO_TIGHT: "Stop loss is too close (<0.5 ATR). High chance of getting stopped out.",
  RR_UNFAVORABLE: "Risk-to-reward ratio is below 1.5:1. Not worth the risk.",
  NO_CLEAR_INVALIDATION: "No clear price level that would invalidate the trade thesis.",
  VOLATILITY_TOO_HIGH: "Volatility is extreme (ATR >3%). Wait for calmer conditions.",
  VOLATILITY_TOO_LOW: "Volatility is too low for meaningful moves.",
  NO_TREND: "No clear trend (ADX <20). Avoid directional trades.",
  CONFLICTING_SIGNALS: "More than 40% of signals conflict. Mixed picture.",
  INSUFFICIENT_DATA: "Not enough historical data for reliable analysis.",
  NEAR_EARNINGS: "Earnings announcement approaching. High uncertainty.",
  MARKET_CLOSED: "Markets are closed. Analysis may be stale.",
};

export function SuppressionExplainer({ reasons }: { reasons: SuppressionReason[] }) {
  return (
    <Alert variant="warning">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle>No Trade Recommended</AlertTitle>
      <AlertDescription>
        <ul className="mt-2 space-y-2">
          {reasons.map((reason, i) => (
            <li key={i} className="flex items-start gap-2">
              <Badge variant="outline" className="shrink-0">{reason.code}</Badge>
              <span>{SUPPRESSION_MESSAGES[reason.code]}</span>
              {reason.threshold && reason.actual && (
                <span className="text-muted-foreground text-sm">
                  (Threshold: {reason.threshold}, Actual: {reason.actual})
                </span>
              )}
            </li>
          ))}
        </ul>
      </AlertDescription>
    </Alert>
  );
}
```

### RiskQualityBadge

```tsx
// components/trade-plan/RiskQualityBadge.tsx
const QUALITY_STYLES = {
  high: "bg-green-100 text-green-800 border-green-200",
  medium: "bg-yellow-100 text-yellow-800 border-yellow-200",
  low: "bg-red-100 text-red-800 border-red-200",
};

export function RiskQualityBadge({ quality }: { quality: "high" | "medium" | "low" }) {
  return (
    <Badge className={cn("font-semibold", QUALITY_STYLES[quality])}>
      {quality.toUpperCase()} QUALITY
    </Badge>
  );
}
```

---

## Server Actions

```typescript
// server/actions/analyze.ts
'use server';

import { auth } from '@clerk/nextjs';
import { MCPClient } from '@/lib/mcp/client';
import { checkUsageLimits, incrementUsage } from '@/lib/usage';

export async function getTradePlan(symbol: string) {
  const { userId } = auth();
  if (!userId) throw new Error('Unauthorized');

  const canProceed = await checkUsageLimits(userId, 'analysis');
  if (!canProceed) {
    throw new Error('Daily limit reached. Upgrade for more analyses.');
  }

  const mcp = new MCPClient();
  const result = await mcp.getTradePlan(symbol);

  await incrementUsage(userId, 'analysis');

  return result;
}

export async function scanUniverse(universe: string, maxResults = 10) {
  const { userId } = auth();
  if (!userId) throw new Error('Unauthorized');

  const canProceed = await checkUsageLimits(userId, 'scan');
  if (!canProceed) {
    throw new Error('Daily limit reached. Upgrade for more scans.');
  }

  const mcp = new MCPClient();
  const result = await mcp.scanUniverse(universe, maxResults);

  await incrementUsage(userId, 'scan');

  return result;
}

export async function assessPortfolioRisk(positions: Position[]) {
  const { userId } = auth();
  if (!userId) throw new Error('Unauthorized');

  // Portfolio risk requires Pro tier
  const tier = await getUserTier(userId);
  if (tier === 'free') {
    throw new Error('Portfolio risk requires Pro subscription.');
  }

  const mcp = new MCPClient();
  return mcp.assessPortfolioRisk(positions);
}

export async function getMorningBrief(watchlist?: string[]) {
  const { userId } = auth();
  if (!userId) throw new Error('Unauthorized');

  const mcp = new MCPClient();
  return mcp.getMorningBrief(watchlist);
}
```

---

## MCP Client Wrapper

```typescript
// lib/mcp/client.ts
import { spawn } from 'child_process';
import type {
  TradePlan,
  RiskAnalysisResult,
  ScanResult,
  PortfolioRiskResult,
  MorningBrief,
} from './types';

export class MCPClient {
  private serverPath: string;

  constructor() {
    this.serverPath = process.env.MCP_SERVER_PATH!;
  }

  async getTradePlan(symbol: string, period = '1mo'): Promise<RiskAnalysisResult> {
    return this.callTool('get_trade_plan', { symbol, period });
  }

  async analyzeSecurity(symbol: string, period = '1mo'): Promise<any> {
    return this.callTool('analyze_security', { symbol, period });
  }

  async scanUniverse(universe: string, maxResults = 10): Promise<ScanResult> {
    return this.callTool('scan_universe', { universe, max_results: maxResults });
  }

  async assessPortfolioRisk(positions: any[]): Promise<PortfolioRiskResult> {
    return this.callTool('portfolio_risk', { positions });
  }

  async getMorningBrief(watchlist?: string[], region = 'US'): Promise<MorningBrief> {
    return this.callTool('morning_brief', { watchlist, market_region: region });
  }

  async getIndicatorHelp(indicator?: string): Promise<any> {
    return this.callTool('indicator_help', { indicator });
  }

  async getSignalHelp(signal?: string): Promise<any> {
    return this.callTool('signal_help', { signal });
  }

  private async callTool(tool: string, args: Record<string, any>): Promise<any> {
    // Implementation depends on how MCP server is hosted
    // Option 1: Spawn process
    // Option 2: HTTP API if running as server
    // Option 3: Direct import if same runtime

    // Example using stdio transport:
    return new Promise((resolve, reject) => {
      const child = spawn('python', ['-m', 'technical_analysis_mcp'], {
        cwd: this.serverPath,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      // Send JSON-RPC request
      const request = {
        jsonrpc: '2.0',
        id: 1,
        method: 'tools/call',
        params: { name: tool, arguments: args },
      };

      child.stdin.write(JSON.stringify(request) + '\n');
      child.stdin.end();

      let output = '';
      child.stdout.on('data', (data) => {
        output += data.toString();
      });

      child.on('close', () => {
        try {
          const response = JSON.parse(output);
          resolve(response.result);
        } catch (e) {
          reject(e);
        }
      });
    });
  }
}
```

---

## API Routes

### Trade Plan API

```typescript
// app/api/mcp/trade-plan/route.ts
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';
import { MCPClient } from '@/lib/mcp/client';
import { checkAndIncrementUsage } from '@/lib/usage';

export async function GET(request: Request) {
  const { userId } = auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const symbol = searchParams.get('symbol');

  if (!symbol) {
    return NextResponse.json({ error: 'Symbol required' }, { status: 400 });
  }

  const canProceed = await checkAndIncrementUsage(userId, 'analysis');
  if (!canProceed) {
    return NextResponse.json(
      { error: 'Daily limit reached. Upgrade for more.' },
      { status: 429 }
    );
  }

  try {
    const mcp = new MCPClient();
    const result = await mcp.getTradePlan(symbol.toUpperCase());
    return NextResponse.json(result);
  } catch (error) {
    console.error('MCP error:', error);
    return NextResponse.json(
      { error: 'Analysis failed' },
      { status: 500 }
    );
  }
}
```

### Scanner API

```typescript
// app/api/mcp/scan/route.ts
import { auth } from '@clerk/nextjs';
import { NextResponse } from 'next/server';
import { MCPClient } from '@/lib/mcp/client';
import { checkAndIncrementUsage } from '@/lib/usage';

export async function GET(request: Request) {
  const { userId } = auth();
  if (!userId) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const universe = searchParams.get('universe') || 'sp500';
  const maxResults = parseInt(searchParams.get('maxResults') || '10');

  const canProceed = await checkAndIncrementUsage(userId, 'scan');
  if (!canProceed) {
    return NextResponse.json(
      { error: 'Daily scan limit reached.' },
      { status: 429 }
    );
  }

  try {
    const mcp = new MCPClient();
    const result = await mcp.scanUniverse(universe, maxResults);
    return NextResponse.json(result);
  } catch (error) {
    console.error('Scan error:', error);
    return NextResponse.json(
      { error: 'Scan failed' },
      { status: 500 }
    );
  }
}
```

---

## Environment Variables

```env
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_PRO_PRICE_ID=price_...
STRIPE_PREMIUM_PRICE_ID=price_...

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# MCP Server
MCP_SERVER_PATH=/path/to/mcp-finance1

# Redis (Phase 2)
REDIS_URL=redis://...

# Email (Phase 2)
RESEND_API_KEY=re_...
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to first trade plan | < 3 seconds |
| Scanner completion (500 symbols) | < 30 seconds |
| User activation (first analysis) | > 80% |
| Free → Pro conversion | > 5% |
| Pro retention (monthly) | > 85% |

---

## Key Architectural Decisions

1. **Server Components First**: All data fetching in Server Components, client components only for interactivity
2. **MCP as Backend**: No separate API layer - MCP server IS the backend
3. **Risk-First Display**: Always show risk before showing opportunity
4. **Education Built-In**: Every signal/indicator has inline explanation
5. **Mobile-First**: Design for mobile, enhance for desktop
6. **Subscription Gate**: Core value (trade plans) available on free tier with limits

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/app/(auth)/sign-in/[[...sign-in]]/page.tsx` | Clerk sign-in |
| `src/app/(auth)/sign-up/[[...sign-up]]/page.tsx` | Clerk sign-up |
| `src/app/(dashboard)/layout.tsx` | Dashboard layout with sidebar |
| `src/app/(dashboard)/page.tsx` | Morning brief dashboard |
| `src/app/(dashboard)/analyze/[symbol]/page.tsx` | Trade plan view |
| `src/app/(dashboard)/scanner/page.tsx` | Universe scanner |
| `src/app/(dashboard)/portfolio/page.tsx` | Portfolio risk |
| `src/app/(dashboard)/watchlist/page.tsx` | Watchlist management |
| `src/app/(dashboard)/trade-journal/page.tsx` | Trade journal |
| `src/app/(dashboard)/learn/signals/page.tsx` | Signal education |
| `src/app/(dashboard)/learn/indicators/page.tsx` | Indicator education |
| `src/app/(dashboard)/settings/page.tsx` | User settings |
| `src/app/api/mcp/analyze/route.ts` | Analysis API |
| `src/app/api/mcp/trade-plan/route.ts` | Trade plan API |
| `src/app/api/mcp/scan/route.ts` | Scanner API |
| `src/app/api/mcp/portfolio-risk/route.ts` | Portfolio risk API |
| `src/app/api/mcp/morning-brief/route.ts` | Morning brief API |
| `src/app/api/webhooks/clerk/route.ts` | Clerk webhook |
| `src/app/api/webhooks/stripe/route.ts` | Stripe webhook |
| `src/lib/mcp/client.ts` | MCP client wrapper |
| `src/lib/mcp/types.ts` | TypeScript types |
| `src/lib/db/schema.ts` | Drizzle schema |
| `src/lib/db/queries.ts` | Database queries |
| `src/lib/stripe/config.ts` | Stripe configuration |
| `src/lib/usage.ts` | Usage tracking |
| `src/components/trade-plan/TradePlanCard.tsx` | Trade plan card |
| `src/components/trade-plan/EntryStopTarget.tsx` | Entry/stop/target viz |
| `src/components/trade-plan/RiskQualityBadge.tsx` | Risk quality badge |
| `src/components/trade-plan/SuppressionExplainer.tsx` | Suppression explainer |
| `src/components/signals/SignalList.tsx` | Signal list |
| `src/components/signals/SignalCard.tsx` | Signal card |
| `src/components/portfolio/PositionCard.tsx` | Position card |
| `src/components/portfolio/SectorConcentration.tsx` | Sector chart |
| `src/components/portfolio/HedgeSuggestions.tsx` | Hedge suggestions |
| `src/components/scanner/UniverseSelector.tsx` | Universe selector |
| `src/components/scanner/ScanResultsTable.tsx` | Scan results table |
| `src/server/actions/analyze.ts` | Analysis server actions |
| `src/server/actions/scan.ts` | Scan server actions |
| `src/server/actions/portfolio.ts` | Portfolio server actions |
