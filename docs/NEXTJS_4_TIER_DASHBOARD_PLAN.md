# Next.js MCP Finance - 4-Tier Dashboard Plan

## Overview

A Next.js 14+ application with **4 distinct dashboard experiences** designed to maximize conversion and showcase the full power of the MCP Finance technical analysis pipeline.

**Philosophy:** Each tier reveals progressively more data, creating a natural upgrade path. The landing page demonstrates value; free tier hooks users; pro tier enables serious trading; max tier delivers everything.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | Next.js 14+ (App Router, Server Components, Server Actions) |
| Auth | Clerk (with tier-based middleware) |
| Styling | Tailwind CSS + shadcn/ui |
| Theme | next-themes (light/dark mode) |
| Database | PostgreSQL + Drizzle ORM |
| MCP | Custom TypeScript client |
| State | React Query (TanStack Query) |

---

## 4 Dashboard Tiers

### Tier 1: Landing Page (Public)
**Goal:** Showcase power, drive signups

| Feature | Data Source | Purpose |
|---------|-------------|---------|
| Live Market Pulse | `morning_brief` | Real-time market status |
| Sample Trade Plan | `get_trade_plan` (AAPL only) | Show what users get |
| Scanner Preview | `scan_universe` (top 3 only) | Tease the scanner |
| Signal Showcase | `signal_help` | Educate on signals |
| Indicator Gallery | `indicator_help` | Show technical depth |
| Social Proof | Static | Testimonials, stats |
| Pricing Cards | Static | Tier comparison |

**Blurred/Locked Content:**
- Full trade plans (show entry, blur stop/target)
- Full scanner results (show 3, blur rest)
- Real-time alerts
- Portfolio risk

---

### Tier 2: Free Dashboard ($0/mo)
**Goal:** Hook users, demonstrate value, create upgrade desire

| Feature | Data Access | Limit |
|---------|-------------|-------|
| Trade Plans | `get_trade_plan` | **Swing timeframe ONLY** |
| Analysis | `analyze_security` | 5/day |
| Scanner | `scan_universe` | 1/day, top 5 results |
| Morning Brief | `morning_brief` | Daily (limited watchlist) |
| Signal Help | `signal_help` | Full access |
| Indicator Help | `indicator_help` | Full access |
| Watchlist | Database | 1 watchlist, 10 symbols max |

**Locked (shown blurred with upgrade CTA):**
- Day/Scalp timeframes
- Full scanner results
- Portfolio risk assessment
- Hedge suggestions
- Option DTE/delta suggestions
- Trade journal
- Alerts

---

### Tier 3: Pro Dashboard ($29/mo)
**Goal:** Enable serious trading with all timeframes

| Feature | Data Access | Limit |
|---------|-------------|-------|
| Trade Plans | `get_trade_plan` | **ALL timeframes (Swing/Day/Scalp)** |
| Analysis | `analyze_security` | 50/day |
| Scanner | `scan_universe` | 10/day, top 25 results |
| Morning Brief | `morning_brief` | Full watchlist |
| Portfolio Risk | `portfolio_risk` | Full access |
| Sector Concentration | `portfolio_risk` | Full access |
| Position Tracking | Database | Unlimited positions |
| Trade Journal | Database | Full logging |
| Watchlists | Database | 5 watchlists, 50 symbols each |
| Option Suggestions | `get_trade_plan` | DTE/Delta ranges |

**Locked (shown with upgrade CTA):**
- Hedge suggestions
- Spread width suggestions
- Full suppression analytics
- Raw indicator data export
- API access
- Priority scanning

---

### Tier 4: Max Dashboard ($79/mo)
**Goal:** Full pipeline access - everything the system produces

| Feature | Data Access | Limit |
|---------|-------------|-------|
| **ALL Pro features** | All tools | Unlimited |
| Hedge Suggestions | `portfolio_risk` | Full suggestions |
| Spread Width Calc | `get_trade_plan` | ATR-based spreads |
| Raw Signal Data | `analyze_security` | All 150+ signals |
| Raw Indicator Data | `analyze_security` | All 18+ indicators |
| Suppression Analytics | `get_trade_plan` | Full breakdown |
| Correlation Matrix | Future | Cross-position analysis |
| Multi-Universe Scan | `scan_universe` | All universes parallel |
| Alert System | Database + Cron | Price/signal/suppression |
| Email Briefs | Resend | Daily + weekly |
| API Access | REST API | Programmatic access |
| Priority Scanning | Queue | Faster results |
| Export (CSV/JSON) | All data | Full export |
| Backtesting | Future | Historical analysis |

---

## Complete Data Utilization Map

### From `get_trade_plan`

| Data Field | Free | Pro | Max |
|------------|------|-----|-----|
| symbol | ✅ | ✅ | ✅ |
| timestamp | ✅ | ✅ | ✅ |
| timeframe (swing) | ✅ | ✅ | ✅ |
| timeframe (day/scalp) | ❌ | ✅ | ✅ |
| bias | ✅ | ✅ | ✅ |
| risk_quality | ✅ | ✅ | ✅ |
| entry_price | ✅ | ✅ | ✅ |
| stop_price | Blurred | ✅ | ✅ |
| target_price | Blurred | ✅ | ✅ |
| invalidation_price | ❌ | ✅ | ✅ |
| risk_reward_ratio | ❌ | ✅ | ✅ |
| expected_move_percent | ❌ | ✅ | ✅ |
| max_loss_percent | ❌ | ✅ | ✅ |
| vehicle | ✅ | ✅ | ✅ |
| vehicle_notes | ❌ | ✅ | ✅ |
| option_dte_range | ❌ | ✅ | ✅ |
| option_delta_range | ❌ | ✅ | ✅ |
| option_spread_width | ❌ | ❌ | ✅ |
| primary_signal | ✅ | ✅ | ✅ |
| supporting_signals | ❌ | ✅ | ✅ |
| suppression_reasons (summary) | ✅ | ✅ | ✅ |
| suppression_reasons (full) | ❌ | ❌ | ✅ |

### From `analyze_security`

| Data Field | Free | Pro | Max |
|------------|------|-----|-----|
| Top 3 signals | ✅ | ✅ | ✅ |
| Top 10 signals | ❌ | ✅ | ✅ |
| All 150+ signals | ❌ | ❌ | ✅ |
| Signal strength | ❌ | ✅ | ✅ |
| Signal categories | ❌ | ✅ | ✅ |
| Key indicators (5) | ✅ | ✅ | ✅ |
| All indicators (18+) | ❌ | ✅ | ✅ |
| Raw indicator values | ❌ | ❌ | ✅ |
| AI ranking score | ❌ | ✅ | ✅ |
| Confluence score | ❌ | ❌ | ✅ |

### From `scan_universe`

| Data Field | Free | Pro | Max |
|------------|------|-----|-----|
| Top 5 results | ✅ | ✅ | ✅ |
| Top 25 results | ❌ | ✅ | ✅ |
| All results (50) | ❌ | ❌ | ✅ |
| SP500 universe | ✅ | ✅ | ✅ |
| NASDAQ100 universe | ❌ | ✅ | ✅ |
| ETF universe | ❌ | ✅ | ✅ |
| Crypto universe | ❌ | ❌ | ✅ |
| Custom universe | ❌ | ❌ | ✅ |
| Parallel multi-scan | ❌ | ❌ | ✅ |

### From `portfolio_risk`

| Data Field | Free | Pro | Max |
|------------|------|-----|-----|
| Total value | ❌ | ✅ | ✅ |
| Total max loss | ❌ | ✅ | ✅ |
| Risk percent | ❌ | ✅ | ✅ |
| Position details | ❌ | ✅ | ✅ |
| Sector concentration | ❌ | ✅ | ✅ |
| Overall risk level | ❌ | ✅ | ✅ |
| Hedge suggestions | ❌ | ❌ | ✅ |
| Correlation matrix | ❌ | ❌ | ✅ (Future) |

### From `morning_brief`

| Data Field | Free | Pro | Max |
|------------|------|-----|-----|
| Market status | ✅ | ✅ | ✅ |
| Market sentiment | ✅ | ✅ | ✅ |
| Economic events (3) | ✅ | ✅ | ✅ |
| Economic events (all) | ❌ | ✅ | ✅ |
| Watchlist signals (5) | ✅ | ✅ | ✅ |
| Watchlist signals (all) | ❌ | ✅ | ✅ |
| Sector leaders | ✅ | ✅ | ✅ |
| Sector losers | ✅ | ✅ | ✅ |
| Key themes | ✅ | ✅ | ✅ |
| Email delivery | ❌ | ❌ | ✅ |

---

## Directory Structure

```
nextjs-mcp-finance/
├── src/
│   ├── app/
│   │   ├── (marketing)/
│   │   │   ├── layout.tsx              # Marketing layout (no sidebar)
│   │   │   ├── page.tsx                # Landing page (Tier 1)
│   │   │   ├── pricing/page.tsx        # Pricing page
│   │   │   └── demo/page.tsx           # Interactive demo
│   │   ├── (auth)/
│   │   │   ├── sign-in/[[...sign-in]]/page.tsx
│   │   │   └── sign-up/[[...sign-up]]/page.tsx
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx              # Dashboard layout with sidebar
│   │   │   ├── page.tsx                # Dashboard home (tier-aware)
│   │   │   ├── analyze/[symbol]/page.tsx
│   │   │   ├── scanner/page.tsx
│   │   │   ├── portfolio/page.tsx
│   │   │   ├── watchlist/page.tsx
│   │   │   ├── journal/page.tsx
│   │   │   ├── alerts/page.tsx         # Max only
│   │   │   ├── export/page.tsx         # Max only
│   │   │   ├── learn/
│   │   │   │   ├── signals/page.tsx
│   │   │   │   └── indicators/page.tsx
│   │   │   └── settings/page.tsx
│   │   ├── api/
│   │   │   ├── mcp/[...tool]/route.ts  # Dynamic MCP routes
│   │   │   ├── webhooks/
│   │   │   │   ├── clerk/route.ts
│   │   │   │   └── stripe/route.ts
│   │   │   └── export/route.ts         # Max only - CSV/JSON export
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── landing/
│   │   │   ├── Hero.tsx
│   │   │   ├── LiveMarketPulse.tsx
│   │   │   ├── SampleTradePlan.tsx
│   │   │   ├── ScannerPreview.tsx
│   │   │   ├── FeatureShowcase.tsx
│   │   │   ├── PricingCards.tsx
│   │   │   └── CTASection.tsx
│   │   ├── dashboard/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   ├── ThemeToggle.tsx
│   │   │   ├── UpgradePrompt.tsx
│   │   │   └── TierBadge.tsx
│   │   ├── trade-plan/
│   │   │   ├── TradePlanCard.tsx
│   │   │   ├── TradePlanBlurred.tsx    # Free tier version
│   │   │   ├── EntryStopTarget.tsx
│   │   │   ├── TimeframeSelector.tsx
│   │   │   ├── RiskQualityBadge.tsx
│   │   │   ├── SuppressionExplainer.tsx
│   │   │   └── OptionSuggestion.tsx
│   │   ├── scanner/
│   │   │   ├── UniverseSelector.tsx
│   │   │   ├── ScanResultsTable.tsx
│   │   │   ├── ScanResultsLimited.tsx  # Free tier
│   │   │   └── MultiUniverseScan.tsx   # Max tier
│   │   ├── portfolio/
│   │   │   ├── RiskDashboard.tsx
│   │   │   ├── PositionCard.tsx
│   │   │   ├── SectorConcentration.tsx
│   │   │   ├── HedgeSuggestions.tsx    # Max tier
│   │   │   └── CorrelationMatrix.tsx   # Max tier (future)
│   │   ├── signals/
│   │   │   ├── SignalList.tsx
│   │   │   ├── SignalCard.tsx
│   │   │   ├── SignalListFull.tsx      # Max tier
│   │   │   └── RawSignalExport.tsx     # Max tier
│   │   ├── indicators/
│   │   │   ├── IndicatorPanel.tsx
│   │   │   ├── IndicatorExplainer.tsx
│   │   │   └── RawIndicatorPanel.tsx   # Max tier
│   │   ├── alerts/                     # Max tier
│   │   │   ├── AlertManager.tsx
│   │   │   ├── AlertCard.tsx
│   │   │   └── AlertHistory.tsx
│   │   ├── gating/
│   │   │   ├── TierGate.tsx            # HOC for tier checks
│   │   │   ├── BlurredContent.tsx
│   │   │   ├── UpgradeCTA.tsx
│   │   │   └── FeatureLock.tsx
│   │   └── ui/                         # shadcn components
│   ├── lib/
│   │   ├── mcp/
│   │   │   ├── client.ts
│   │   │   └── types.ts
│   │   ├── db/
│   │   │   ├── schema.ts
│   │   │   └── queries.ts
│   │   ├── auth/
│   │   │   ├── tiers.ts                # Tier logic
│   │   │   └── limits.ts               # Usage limits
│   │   ├── stripe/
│   │   │   └── config.ts
│   │   └── theme/
│   │       └── config.ts
│   ├── hooks/
│   │   ├── useTier.ts
│   │   ├── useUsage.ts
│   │   └── useTheme.ts
│   └── middleware.ts                   # Clerk + tier routing
├── drizzle/
├── public/
├── tailwind.config.ts
└── next.config.js
```

---

## Theme Configuration (Light/Dark Mode)

### Tailwind Config

```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: 'class',
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        // Custom trading colors
        bullish: {
          DEFAULT: '#22c55e',
          dark: '#16a34a',
        },
        bearish: {
          DEFAULT: '#ef4444',
          dark: '#dc2626',
        },
        neutral: {
          DEFAULT: '#6b7280',
          dark: '#4b5563',
        },
        // Risk quality
        'risk-high': '#22c55e',
        'risk-medium': '#eab308',
        'risk-low': '#ef4444',
        // Tier colors
        'tier-free': '#6b7280',
        'tier-pro': '#3b82f6',
        'tier-max': '#8b5cf6',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
```

### Theme Toggle Component

```tsx
// components/dashboard/ThemeToggle.tsx
'use client';

import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      className="relative"
    >
      <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
```

### Theme Provider Setup

```tsx
// app/layout.tsx
import { ThemeProvider } from 'next-themes';
import { ClerkProvider } from '@clerk/nextjs';

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            {children}
          </ThemeProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}
```

---

## Tier Gating System

### Tier Configuration

```typescript
// lib/auth/tiers.ts
export type UserTier = 'free' | 'pro' | 'max';

export interface TierLimits {
  analysesPerDay: number;
  scansPerDay: number;
  scanResultsLimit: number;
  watchlistCount: number;
  watchlistSymbolLimit: number;
  timeframes: ('swing' | 'day' | 'scalp')[];
  universes: string[];
  features: string[];
}

export const TIER_LIMITS: Record<UserTier, TierLimits> = {
  free: {
    analysesPerDay: 5,
    scansPerDay: 1,
    scanResultsLimit: 5,
    watchlistCount: 1,
    watchlistSymbolLimit: 10,
    timeframes: ['swing'],
    universes: ['sp500'],
    features: [
      'basic_trade_plan',
      'signal_help',
      'indicator_help',
      'morning_brief_limited',
    ],
  },
  pro: {
    analysesPerDay: 50,
    scansPerDay: 10,
    scanResultsLimit: 25,
    watchlistCount: 5,
    watchlistSymbolLimit: 50,
    timeframes: ['swing', 'day', 'scalp'],
    universes: ['sp500', 'nasdaq100', 'etf_large_cap'],
    features: [
      'full_trade_plan',
      'all_timeframes',
      'portfolio_risk',
      'sector_concentration',
      'position_tracking',
      'trade_journal',
      'option_suggestions',
      'signal_help',
      'indicator_help',
      'morning_brief_full',
    ],
  },
  max: {
    analysesPerDay: Infinity,
    scansPerDay: Infinity,
    scanResultsLimit: 50,
    watchlistCount: Infinity,
    watchlistSymbolLimit: Infinity,
    timeframes: ['swing', 'day', 'scalp'],
    universes: ['sp500', 'nasdaq100', 'etf_large_cap', 'crypto'],
    features: [
      'full_trade_plan',
      'all_timeframes',
      'portfolio_risk',
      'sector_concentration',
      'position_tracking',
      'trade_journal',
      'option_suggestions',
      'hedge_suggestions',
      'spread_width',
      'raw_signals',
      'raw_indicators',
      'suppression_analytics',
      'alerts',
      'email_briefs',
      'api_access',
      'export',
      'priority_scanning',
      'multi_universe_scan',
      'signal_help',
      'indicator_help',
      'morning_brief_full',
    ],
  },
};

export function canAccessFeature(tier: UserTier, feature: string): boolean {
  return TIER_LIMITS[tier].features.includes(feature);
}

export function canAccessTimeframe(tier: UserTier, timeframe: string): boolean {
  return TIER_LIMITS[tier].timeframes.includes(timeframe as any);
}
```

### Tier Gate Component

```tsx
// components/gating/TierGate.tsx
'use client';

import { useTier } from '@/hooks/useTier';
import { canAccessFeature } from '@/lib/auth/tiers';
import { BlurredContent } from './BlurredContent';
import { UpgradeCTA } from './UpgradeCTA';

interface TierGateProps {
  feature: string;
  requiredTier?: 'pro' | 'max';
  children: React.ReactNode;
  fallback?: React.ReactNode;
  blurContent?: boolean;
}

export function TierGate({
  feature,
  requiredTier,
  children,
  fallback,
  blurContent = true,
}: TierGateProps) {
  const { tier } = useTier();

  const hasAccess = canAccessFeature(tier, feature);

  if (hasAccess) {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  if (blurContent) {
    return (
      <BlurredContent>
        {children}
        <UpgradeCTA
          currentTier={tier}
          requiredTier={requiredTier || 'pro'}
          feature={feature}
        />
      </BlurredContent>
    );
  }

  return (
    <UpgradeCTA
      currentTier={tier}
      requiredTier={requiredTier || 'pro'}
      feature={feature}
    />
  );
}
```

### Blurred Content Component

```tsx
// components/gating/BlurredContent.tsx
interface BlurredContentProps {
  children: React.ReactNode;
}

export function BlurredContent({ children }: BlurredContentProps) {
  return (
    <div className="relative">
      <div className="pointer-events-none select-none blur-sm">
        {children}
      </div>
      <div className="absolute inset-0 flex items-center justify-center bg-background/50 backdrop-blur-sm">
        {/* UpgradeCTA will be overlaid here */}
      </div>
    </div>
  );
}
```

---

## Landing Page (Tier 1 - Public)

```tsx
// app/(marketing)/page.tsx
import { Hero } from '@/components/landing/Hero';
import { LiveMarketPulse } from '@/components/landing/LiveMarketPulse';
import { SampleTradePlan } from '@/components/landing/SampleTradePlan';
import { ScannerPreview } from '@/components/landing/ScannerPreview';
import { FeatureShowcase } from '@/components/landing/FeatureShowcase';
import { PricingCards } from '@/components/landing/PricingCards';
import { CTASection } from '@/components/landing/CTASection';

export default async function LandingPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-muted">
      <Hero />

      {/* Real-time market pulse - shows system is live */}
      <section className="py-16">
        <LiveMarketPulse />
      </section>

      {/* Sample trade plan with blurred stop/target */}
      <section className="py-16 bg-muted/50">
        <div className="container">
          <h2 className="text-3xl font-bold text-center mb-8">
            See What You Get
          </h2>
          <SampleTradePlan symbol="AAPL" showBlurred />
        </div>
      </section>

      {/* Scanner preview - top 3 only */}
      <section className="py-16">
        <div className="container">
          <h2 className="text-3xl font-bold text-center mb-8">
            Find Trades in Seconds
          </h2>
          <ScannerPreview limit={3} />
        </div>
      </section>

      {/* Feature showcase */}
      <section className="py-16 bg-muted/50">
        <FeatureShowcase />
      </section>

      {/* Pricing */}
      <section className="py-16">
        <PricingCards />
      </section>

      {/* Final CTA */}
      <CTASection />
    </main>
  );
}
```

### Sample Trade Plan Component

```tsx
// components/landing/SampleTradePlan.tsx
import { MCPClient } from '@/lib/mcp/client';
import { TradePlanCard } from '@/components/trade-plan/TradePlanCard';

interface SampleTradePlanProps {
  symbol: string;
  showBlurred?: boolean;
}

export async function SampleTradePlan({ symbol, showBlurred }: SampleTradePlanProps) {
  const mcp = new MCPClient();
  const result = await mcp.getTradePlan(symbol);

  if (!result.has_trades) {
    return (
      <div className="text-center text-muted-foreground">
        Check back later for live trade setups
      </div>
    );
  }

  const plan = result.trade_plans[0];

  return (
    <div className="max-w-2xl mx-auto relative">
      <TradePlanCard
        plan={plan}
        blurredFields={showBlurred ? ['stop_price', 'target_price', 'risk_reward_ratio'] : []}
      />
      {showBlurred && (
        <div className="absolute bottom-4 left-0 right-0 text-center">
          <p className="text-sm text-muted-foreground mb-2">
            Sign up to see stop, target, and R:R
          </p>
          <a
            href="/sign-up"
            className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground shadow transition-colors hover:bg-primary/90"
          >
            Get Started Free
          </a>
        </div>
      )}
    </div>
  );
}
```

---

## Dashboard Pages

### Tier-Aware Dashboard Home

```tsx
// app/(dashboard)/page.tsx
import { auth } from '@clerk/nextjs';
import { redirect } from 'next/navigation';
import { getUserTier } from '@/lib/auth/tiers';

// Tier-specific components
import { FreeDashboard } from '@/components/dashboard/FreeDashboard';
import { ProDashboard } from '@/components/dashboard/ProDashboard';
import { MaxDashboard } from '@/components/dashboard/MaxDashboard';

export default async function DashboardPage() {
  const { userId } = auth();
  if (!userId) redirect('/sign-in');

  const tier = await getUserTier(userId);

  switch (tier) {
    case 'free':
      return <FreeDashboard />;
    case 'pro':
      return <ProDashboard />;
    case 'max':
      return <MaxDashboard />;
    default:
      return <FreeDashboard />;
  }
}
```

### Free Dashboard

```tsx
// components/dashboard/FreeDashboard.tsx
import { MorningBriefLimited } from '@/components/morning-brief/MorningBriefLimited';
import { QuickAnalyze } from '@/components/analyze/QuickAnalyze';
import { UpgradePrompt } from '@/components/dashboard/UpgradePrompt';
import { UsageMeter } from '@/components/dashboard/UsageMeter';

export function FreeDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <UsageMeter />
      </div>

      {/* Upgrade prompt */}
      <UpgradePrompt
        title="Unlock All Timeframes"
        description="Free tier only includes Swing trades. Upgrade to Pro for Day and Scalp analysis."
        targetTier="pro"
      />

      {/* Limited morning brief */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Market Overview</h2>
        <MorningBriefLimited />
      </section>

      {/* Quick analyze (swing only) */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Analyze a Stock</h2>
        <p className="text-sm text-muted-foreground mb-4">
          Swing timeframe only. {5 - usedToday} analyses remaining today.
        </p>
        <QuickAnalyze timeframe="swing" />
      </section>

      {/* Blurred scanner preview */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Today's Top Setups</h2>
        <TierGate feature="full_scanner" blurContent>
          <ScannerPreview limit={10} />
        </TierGate>
      </section>
    </div>
  );
}
```

### Pro Dashboard

```tsx
// components/dashboard/ProDashboard.tsx
import { MorningBrief } from '@/components/morning-brief/MorningBrief';
import { PortfolioSummary } from '@/components/portfolio/PortfolioSummary';
import { WatchlistQuickView } from '@/components/watchlist/WatchlistQuickView';
import { RecentScans } from '@/components/scanner/RecentScans';
import { TimeframeSelector } from '@/components/trade-plan/TimeframeSelector';
import { TierGate } from '@/components/gating/TierGate';

export function ProDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Pro Dashboard</h1>
        <TimeframeSelector allowedTimeframes={['swing', 'day', 'scalp']} />
      </div>

      {/* Full morning brief */}
      <section>
        <MorningBrief />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Portfolio summary */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Portfolio Risk</h2>
          <PortfolioSummary />
        </section>

        {/* Watchlist quick view */}
        <section>
          <h2 className="text-lg font-semibold mb-4">Watchlist</h2>
          <WatchlistQuickView />
        </section>
      </div>

      {/* Recent scans */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Recent Scans</h2>
        <RecentScans limit={25} />
      </section>

      {/* Blurred hedge suggestions */}
      <TierGate feature="hedge_suggestions" requiredTier="max">
        <section>
          <h2 className="text-lg font-semibold mb-4">Hedge Suggestions</h2>
          <HedgeSuggestions />
        </section>
      </TierGate>
    </div>
  );
}
```

### Max Dashboard

```tsx
// components/dashboard/MaxDashboard.tsx
import { MorningBrief } from '@/components/morning-brief/MorningBrief';
import { PortfolioRiskFull } from '@/components/portfolio/PortfolioRiskFull';
import { HedgeSuggestions } from '@/components/portfolio/HedgeSuggestions';
import { AlertsSummary } from '@/components/alerts/AlertsSummary';
import { MultiUniverseScan } from '@/components/scanner/MultiUniverseScan';
import { RawDataPanel } from '@/components/data/RawDataPanel';
import { ExportButton } from '@/components/export/ExportButton';

export function MaxDashboard() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Max Dashboard</h1>
          <p className="text-sm text-tier-max">Full Pipeline Access</p>
        </div>
        <ExportButton />
      </div>

      {/* Active alerts */}
      <section>
        <AlertsSummary />
      </section>

      {/* Full morning brief with email option */}
      <section>
        <MorningBrief showEmailOption />
      </section>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Full portfolio risk */}
        <div className="lg:col-span-2">
          <PortfolioRiskFull />
        </div>

        {/* Hedge suggestions */}
        <div>
          <HedgeSuggestions />
        </div>
      </div>

      {/* Multi-universe parallel scan */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Multi-Universe Scan</h2>
        <MultiUniverseScan universes={['sp500', 'nasdaq100', 'etf_large_cap', 'crypto']} />
      </section>

      {/* Raw data panel */}
      <section>
        <h2 className="text-lg font-semibold mb-4">Raw Data Access</h2>
        <RawDataPanel />
      </section>
    </div>
  );
}
```

---

## Pricing Page

```tsx
// app/(marketing)/pricing/page.tsx
import { Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';

const tiers = [
  {
    name: 'Free',
    price: '$0',
    description: 'Get started with swing trading analysis',
    features: [
      { text: '5 analyses per day', included: true },
      { text: '1 scan per day (top 5 results)', included: true },
      { text: 'Swing timeframe only', included: true },
      { text: 'Basic trade plans', included: true },
      { text: 'Signal & indicator education', included: true },
      { text: 'Day & Scalp timeframes', included: false },
      { text: 'Portfolio risk tracking', included: false },
      { text: 'Trade journal', included: false },
      { text: 'Alerts', included: false },
    ],
    cta: 'Get Started',
    href: '/sign-up',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '$29',
    period: '/month',
    description: 'All timeframes for serious traders',
    features: [
      { text: '50 analyses per day', included: true },
      { text: '10 scans per day (top 25 results)', included: true },
      { text: 'All timeframes (Swing, Day, Scalp)', included: true },
      { text: 'Full trade plans with R:R', included: true },
      { text: 'Portfolio risk dashboard', included: true },
      { text: 'Sector concentration analysis', included: true },
      { text: 'Trade journal', included: true },
      { text: 'Option DTE & delta suggestions', included: true },
      { text: 'Hedge suggestions', included: false },
      { text: 'API access', included: false },
    ],
    cta: 'Start Pro Trial',
    href: '/sign-up?tier=pro',
    highlighted: true,
  },
  {
    name: 'Max',
    price: '$79',
    period: '/month',
    description: 'Full pipeline access for professionals',
    features: [
      { text: 'Unlimited analyses', included: true },
      { text: 'Unlimited scans (all results)', included: true },
      { text: 'All timeframes', included: true },
      { text: 'Hedge suggestions', included: true },
      { text: 'Raw signal data (150+)', included: true },
      { text: 'Raw indicator data (18+)', included: true },
      { text: 'Price & signal alerts', included: true },
      { text: 'Email morning briefs', included: true },
      { text: 'API access', included: true },
      { text: 'CSV/JSON export', included: true },
      { text: 'Multi-universe parallel scan', included: true },
    ],
    cta: 'Start Max Trial',
    href: '/sign-up?tier=max',
    highlighted: false,
  },
];

export default function PricingPage() {
  return (
    <div className="py-16">
      <div className="container">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold mb-4">Simple, Transparent Pricing</h1>
          <p className="text-xl text-muted-foreground">
            Start free. Upgrade when you're ready for more power.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {tiers.map((tier) => (
            <Card
              key={tier.name}
              className={tier.highlighted ? 'border-primary shadow-lg scale-105' : ''}
            >
              <CardHeader>
                <CardTitle className="text-2xl">{tier.name}</CardTitle>
                <CardDescription>{tier.description}</CardDescription>
                <div className="mt-4">
                  <span className="text-4xl font-bold">{tier.price}</span>
                  {tier.period && (
                    <span className="text-muted-foreground">{tier.period}</span>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {tier.features.map((feature, i) => (
                    <li key={i} className="flex items-center gap-2">
                      {feature.included ? (
                        <Check className="h-5 w-5 text-green-500" />
                      ) : (
                        <X className="h-5 w-5 text-muted-foreground" />
                      )}
                      <span className={!feature.included ? 'text-muted-foreground' : ''}>
                        {feature.text}
                      </span>
                    </li>
                  ))}
                </ul>
              </CardContent>
              <CardFooter>
                <Button
                  asChild
                  className="w-full"
                  variant={tier.highlighted ? 'default' : 'outline'}
                >
                  <a href={tier.href}>{tier.cta}</a>
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
```

---

## Middleware (Clerk + Tier Routing)

```typescript
// middleware.ts
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isPublicRoute = createRouteMatcher([
  '/',
  '/pricing',
  '/demo',
  '/sign-in(.*)',
  '/sign-up(.*)',
  '/api/webhooks/(.*)',
]);

const isMaxOnlyRoute = createRouteMatcher([
  '/alerts(.*)',
  '/export(.*)',
  '/api/export(.*)',
]);

const isProOnlyRoute = createRouteMatcher([
  '/portfolio(.*)',
  '/journal(.*)',
]);

export default clerkMiddleware(async (auth, req) => {
  if (isPublicRoute(req)) {
    return NextResponse.next();
  }

  const { userId, sessionClaims } = auth();

  if (!userId) {
    return auth().redirectToSignIn();
  }

  const tier = sessionClaims?.metadata?.tier || 'free';

  // Check Max-only routes
  if (isMaxOnlyRoute(req) && tier !== 'max') {
    return NextResponse.redirect(new URL('/pricing?upgrade=max', req.url));
  }

  // Check Pro-only routes
  if (isProOnlyRoute(req) && tier === 'free') {
    return NextResponse.redirect(new URL('/pricing?upgrade=pro', req.url));
  }

  return NextResponse.next();
});

export const config = {
  matcher: ['/((?!.*\\..*|_next).*)', '/', '/(api|trpc)(.*)'],
};
```

---

## Environment Variables

```env
# Clerk
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_...
CLERK_SECRET_KEY=sk_...
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up

# Stripe
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_FREE_PRICE_ID=
STRIPE_PRO_PRICE_ID=price_...
STRIPE_MAX_PRICE_ID=price_...

# Database
DATABASE_URL=postgresql://...

# MCP Server
MCP_SERVER_PATH=/path/to/mcp-finance1

# Redis (for rate limiting)
REDIS_URL=redis://...

# Email (Max tier)
RESEND_API_KEY=re_...
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Next.js project with App Router
- [ ] Clerk auth with tier metadata
- [ ] Tailwind + shadcn/ui setup
- [ ] next-themes (light/dark mode)
- [ ] MCP client wrapper
- [ ] Landing page with live data
- [ ] Tier gating system
- [ ] Basic dashboard layouts (all 3 tiers)

### Phase 2: Core Features (Week 3-4)
- [ ] Trade plan page (tier-aware)
- [ ] Scanner page (tier-aware limits)
- [ ] Morning brief (tier-aware)
- [ ] Watchlist management
- [ ] Stripe integration
- [ ] Usage tracking

### Phase 3: Pro Features (Week 5-6)
- [ ] Portfolio risk dashboard
- [ ] Position tracking
- [ ] Trade journal
- [ ] All timeframe support
- [ ] Option suggestions

### Phase 4: Max Features (Week 7-8)
- [ ] Hedge suggestions
- [ ] Alert system
- [ ] Email briefs
- [ ] Raw data access
- [ ] Export functionality
- [ ] API access

---

## Files to Create

| File | Purpose |
|------|---------|
| `src/app/(marketing)/page.tsx` | Landing page |
| `src/app/(marketing)/pricing/page.tsx` | Pricing page |
| `src/app/(dashboard)/page.tsx` | Tier-aware dashboard |
| `src/components/landing/*.tsx` | Landing components |
| `src/components/dashboard/*.tsx` | Dashboard components |
| `src/components/gating/*.tsx` | Tier gating components |
| `src/lib/auth/tiers.ts` | Tier configuration |
| `src/lib/auth/limits.ts` | Usage limits |
| `src/hooks/useTier.ts` | Tier hook |
| `src/middleware.ts` | Auth + tier routing |
| `tailwind.config.ts` | Theme config |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Landing → Sign Up | > 15% |
| Free → Pro conversion | > 8% |
| Pro → Max conversion | > 20% |
| Theme toggle usage | Track |
| Feature unlock attempts | Track for upgrade prompts |
