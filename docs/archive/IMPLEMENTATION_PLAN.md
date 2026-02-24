# Next.js 4-Tier Dashboard - Implementation Plan

## Project Overview
Build a Next.js 14+ SaaS application with 4 distinct dashboard tiers (Landing/Free/Pro/Max) that progressively unlock access to MCP Finance financial analysis features.

**Pricing Model:**
- Free: $0/mo (swing analysis only, 5 analyses/day, 1 scan/day)
- Pro: $29/mo (all timeframes, 50 analyses/day, portfolio risk)
- Max: $79/mo (unlimited access, API access, alerts, exports)

---

## Phase 1: Foundation & Auth (Days 1-3)

### Core Setup
- [ ] Initialize Next.js 14+ project with App Router
- [ ] Install dependencies: Clerk, Tailwind CSS, shadcn/ui, next-themes, React Query
- [ ] Set up Tailwind config with custom trading colors
- [ ] Configure Clerk authentication with tier metadata
- [ ] Set up next-themes for light/dark mode support
- [ ] Create environment variables template (.env.example)

### Authentication & Tier System
- [ ] Create tier configuration (lib/auth/tiers.ts)
- [ ] Create usage limits tracking (lib/auth/limits.ts)
- [ ] Implement useTier() hook
- [ ] Implement useUsage() hook
- [ ] Set up Clerk middleware with tier routing

### Layout & Navigation
- [ ] Create marketing layout (app/(marketing)/layout.tsx)
- [ ] Create auth layout (app/(auth)/)
- [ ] Create dashboard layout (app/(dashboard)/layout.tsx)
  - Sidebar navigation
  - Header with theme toggle
  - Responsive design

---

## Phase 2: Landing Page & Public Features (Days 4-6)

### Landing Page Components
- [ ] LiveMarketPulse component (call morning_brief)
- [ ] SampleTradePlan component (fetch AAPL, blur sensitive data)
- [ ] ScannerPreview component (scan_universe SP500, top 3)
- [ ] FeatureShowcase component (signal/indicator education)
- [ ] PricingCards component (tier comparison)
- [ ] Hero section (value prop + CTA)

### Pages
- [ ] Landing page (app/(marketing)/page.tsx)
- [ ] Pricing page (app/(marketing)/pricing/page.tsx)

---

## Phase 3: Tier Gating System (Days 7-8)

### Gating Components
- [ ] TierGate wrapper (check access, show blurred or fallback)
- [ ] BlurredContent component (blur effect + overlay)
- [ ] UpgradeCTA component (contextual upgrade button)
- [ ] FeatureLock component (locked state display)

### Dashboard Common Components
- [ ] Sidebar navigation (tier-aware menu)
- [ ] Header (logo, theme toggle, user menu)
- [ ] TierBadge (display tier label)
- [ ] UpgradePrompt (sticky banner with feature CTA)
- [ ] UsageMeter (show daily limits remaining)

---

## Phase 4: Free Dashboard (Days 9-11)

### Free Tier Features
- [ ] Quick trade plan analyzer (swing only, 5/day limit)
- [ ] Morning brief (limited: top 3 events, top 5 signals)
- [ ] Scanner preview (SP500 top 5, blur rest)
- [ ] Usage meter component

### Pages
- [ ] FreeDashboard component

---

## Phase 5: Pro Dashboard & Features (Days 12-15)

### Pro Components
- [ ] TimeframeSelector (Swing/Day/Scalp)
- [ ] PortfolioSummary (portfolio_risk basic)
- [ ] SectorConcentration chart
- [ ] PositionCard (individual position)
- [ ] WatchlistQuickView
- [ ] RecentScans

### Pro Pages
- [ ] Analyze page (analyze/[symbol]/page.tsx - top 10 signals, 5 indicators)
- [ ] Scanner page (scanner/page.tsx - max 25 results)
- [ ] Watchlist page (watchlist/page.tsx - max 5 lists, 50 symbols each)
- [ ] Portfolio page (portfolio/page.tsx - full risk dashboard)
- [ ] Journal page (journal/page.tsx - trade logging)
- [ ] Settings page (settings/page.tsx)
- [ ] ProDashboard component

---

## Phase 6: Max Dashboard & Features (Days 16-19)

### Max Components
- [ ] HedgeSuggestions (from portfolio_risk)
- [ ] MultiUniverseScan (parallel scan all universes)
- [ ] RawSignalExport (all 150+ signals)
- [ ] RawIndicatorPanel (all 18+ with raw values)
- [ ] AlertManager (create/manage alerts)
- [ ] AlertCard + AlertHistory
- [ ] ExportButton (CSV/JSON download)

### Max Pages
- [ ] Alerts page (alerts/page.tsx)
- [ ] Export page (export/page.tsx)
- [ ] Learn pages expanded (all signals/indicators searchable)
- [ ] MaxDashboard component

---

## Phase 7: Database & Persistence (Days 20-22)

### Drizzle Schema
- [ ] Users table (Clerk ID, tier, Stripe info)
- [ ] Watchlists table
- [ ] Positions table (for portfolio)
- [ ] Trade journal table
- [ ] Alerts table
- [ ] Usage logs table

### Database Queries
- [ ] Watchlist CRUD
- [ ] Position CRUD
- [ ] Trade journal CRUD
- [ ] Alert CRUD
- [ ] Usage tracking

---

## Phase 8: MCP Integration (Days 23-24)

### MCP Client
- [ ] Create MCPClient wrapper (lib/mcp/client.ts)
- [ ] Implement type definitions (lib/mcp/types.ts)
- [ ] Error handling + retry logic
- [ ] Caching strategy (React Query)
- [ ] API routes for tier-based rate limiting

### API Routes
- [ ] Dynamic MCP router (api/mcp/[...tool]/route.ts)
- [ ] Auth check + rate limiting
- [ ] Usage tracking

---

## Phase 9: Stripe Integration (Days 25-26)

### Stripe Setup
- [ ] Configure price IDs
- [ ] Webhook secrets

### Webhooks
- [ ] Clerk webhook (user.created → free tier, metadata updates)
- [ ] Stripe webhook (checkout.session.completed → tier update, subscription.deleted → downgrade)

### Checkout
- [ ] Generate checkout links
- [ ] Success/cancel redirects

---

## Phase 10: Testing & Optimization (Days 27-28)

### Testing
- [ ] Unit tests (tier logic)
- [ ] Integration tests (API routes)
- [ ] Component tests (TierGate, BlurredContent)
- [ ] E2E tests (auth + upgrade flow)

### Optimization
- [ ] Image optimization (next/image)
- [ ] Code splitting for pages
- [ ] Client-side caching (React Query)
- [ ] Server-side caching
- [ ] Database query optimization
- [ ] Rate limiting

### Security
- [ ] SQL injection prevention
- [ ] XSS prevention
- [ ] CSRF protection
- [ ] Secure session handling

---

## Phase 11: Deployment (Day 29-30)

### Deployment
- [ ] Environment variables in production
- [ ] Deploy to Vercel
- [ ] Custom domain + SSL
- [ ] Database backups

### Monitoring
- [ ] Error tracking (Sentry optional)
- [ ] Conversion metrics (landing → signup → upgrade)
- [ ] Feature usage analytics
- [ ] API latency monitoring

---

## Key Files & Components Summary

**Total Components:** ~60+ components across landing, dashboard, gating, trade-plan, scanner, portfolio, signals, indicators, alerts

**Total Pages:** 13+ pages (marketing, auth, dashboard, analyze, scanner, watchlist, portfolio, journal, settings, learn, alerts, export)

**Total API Routes:** 3 main routes (dynamic MCP, Clerk webhook, Stripe webhook) + export endpoint

**Core Libraries:** 4 (auth/tiers, auth/limits, mcp/client, mcp/types, db/schema, db/queries, stripe/config, theme/config)

**Hooks:** 3 (useTier, useUsage, useTheme via next-themes)

---

## Dependencies

- Next.js 14+, Clerk, Tailwind CSS, shadcn/ui, next-themes
- React Query, Drizzle ORM, Stripe, Zod, Lucide icons

---

## Success Metrics

- Landing → Signup: > 15%
- Free → Pro conversion: > 8%
- Pro → Max conversion: > 20%
- Dashboard load time: < 1 second
- API response time: < 500ms
