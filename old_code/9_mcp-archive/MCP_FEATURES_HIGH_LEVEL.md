# MCP Finance Tools – High-Level Feature Roadmap

This document captures high-level feature ideas for the nine MCP analysis
modules.  It is intended to serve as a living brainstorming space, not an
implementation spec.  The goal is to ensure each tool has a rich, extensible
set of capabilities like the Fibonacci module and that all tools play nicely
together.

---

## Shared Integration Features
To ensure the nine MCP tools interoperate smoothly, each module should
implement the following common capabilities:

1. **Unified Context Interface** – provide a `get_context()` factory that
   returns a standard object with `symbol`, `interval`, `df`, `current`,
   `prev`, etc.
2. **Signal Registry** – all tools register their output signals with a
   central `SignalDirectory` so cross-tool dashboards can subscribe easily.
3. **Standard Output Format** – every handler returns a JSON object with
   `{signal,value,strength,category,timeframe}` plus metadata.
4. **Cross‑Tool Dependency Injection** – allow one tool to call another’s
   analysis for enrichment (e.g. portfolio risk invites fibonacci levels).
5. **Master CLI/Script** – a script that can run all tools sequentially or in
   parallel and aggregate results into a single report.

These five features will be mentioned again in each per‑tool section.

---

## 1.  Compare Securities
A module for quantitative comparison of multiple symbols.

1. Side-by-side price charting with normalized scales.
2. Correlation matrix calculation over arbitrary lookbacks.
3. Pair‑trade opportunity scanner based on cointegration.
4. Benchmarking against indices or custom portfolios.
5. Volatility comparison (historical/VaR/expected shortfall).
6. Event‑driven performance (earnings, splits, dividend dates).
7. Sector/industry weighting analysis using metadata.
8. Relative strength rankings with percentiles.
9. Rolling Sharpe ratio comparison.
10. Price momentum heatmap.
11. Multi‑symbol Fibonacci overlay support.
12. Trade‑cost estimator between securities.
13. Cross‑currency conversion for ADRs/forex.
14. Sentiment‑based comparison using news/alerts.
15. Liquidity metrics (average spread, depth) side‑by‑side.
16. Fund flow comparison for ETFs.
17. Risk parity optimizer to equalize volatility.
18. Machine‑learning similarity score (autoencoder).
19. Exportable comparison reports (PDF/CSV).
20. API for hooking into third‑party analytics.

Add the five shared integration features to this list for inter‑tool use.

---

## 2.  Security Analyzer (AI‑assisted)
Provides deep, possibly ML‑powered analysis of a single security.

1. Fundamental data ingest and ratio calculator.
2. AI narrative generation based on earnings transcripts.
3. Technical indicator library wrapper (RSI, MACD, Bollinger).
4. News sentiment feed integration.
5. Insider trading / filings alerting.
6. Analyst estimate tracking and surprise calculations.
7. Options skew and implied volatility surface visualization.
8. ESG score aggregator.
9. Customizable watchlist rules with alerting.
10. Forecasting interface (ARIMA, Prophet, ML models).
11. Peer group comparison built in.
12. Real‑time price streaming support.
13. Risk‑adjusted return projections.
14. Scenario analysis (shock events).
15. Price‑target distribution generator.
16. Dataset export for external ML training.
17. Backtesting harness for user‑defined strategies.
18. Historical annotation layer (dividends, splits).
19. Versioned model metadata for reproducibility.
20. Plug‑in architecture for additional AI models.

Include the five integration items enabling system‑wide data sharing.

---

## 3.  Morning Brief
Daily market summary and headlines.

1. Opening gap analysis for major indexes.
2. Pre‑market movers list with catalysts.
3. Overnight news digest with sentiment scores.
4. Economic calendar event impact tracker.
5. Heatmap of sector performance.
6. Overnight option volume spike list.
7. Currency / commodity overnight move summary.
8. Top gainers/losers in watchlists.
9. Daily Fibonacci level update for key symbols.
10. Automated alpha (signal) grade for the day.
11. Datafeed health check report.
12. Earnings schedule with surprising results.
13. Pre‑market technical signals (breakouts, fills).
14. Alert configuration interface (email/slack).
15. Customizable brief templates per user.
16. Audio/voice briefing generation.
17. Integration with calendar apps.
18. Historical brief archive search.
19. Mobile‑friendly digest delivery.
20. API for other systems to consume brief data.

Also add the 5 inter‑tool features to ensure the morning brief can pull
signals from all other modules and vice‑versa.

---

## 4.  Options Risk Analysis
Suite for analysing derivatives portfolios.

1. Greeks calculator for individual legs and entire portfolio.
2. Risk‑surface visualization (delta, gamma heatmaps).
3. Scenario stress‑testing (price moves, volatility shocks).
4. Max‑loss / max‑profit analysis per strategy.
5. Assignment probability estimator.
6. Option chain scanner based on custom criteria.
7. Implied volatility rank and percentile.
8. Real‑time Greeks using streaming quotes.
9. Monte‑Carlo simulation engine.
10. Volatility skew/search (call/put parity).
11. Event‑driven risk change tracker (earnings, FOMC).
12. Margin requirement estimator.
13. Probability of profit (POP) bootstrapped.
14. Synthetic position builder (delta‑neutral, etc.).
15. Strategy template library (iron condors, butterflies).
16. PnL visualization over time with Greeks overlay.
17. Trade recommendation engine based on risk appetite.
18. Alerts for crossing risk thresholds.
19. Exportable risk report for compliance.
20. Historical re‑pricing for held positions.

Integrate the 5 shared features so portfolio risk can ingest data from
every other tool (e.g. support cross‑tool aggregate reporting).

---

## 5.  Portfolio Risk
Assessment of whole‑account risk metrics.

1. Value at Risk (VaR) using historical, parametric, and MC methods.
2. Expected shortfall (CVaR) calculation.
3. Asset‑class correlation matrix.
4. Stress‑test scenarios (2008, 2020, custom).
5. Drawdown analysis and recovery times.
6. Position‑level PnL attribution.
7. Liquidity risk scoring (based on volume and market depth).
8. Concentration risk alert (single asset > x% of NAV).
9. Risk parity optimizer.
10. Beta vs major indices.
11. Return‑volatility profile plot.
12. Monte‑Carlo walk forward simulation.
13. Custom risk factor builder (interest rates, FX, etc.).
14. Regulatory reporting templates (FRTB, etc.).
15. Rebalancing suggestion engine.
16. Portfolio carry and funding cost calculation.
17. Co‑var and marginal VaR metrics.
18. Event‑driven shock analysis from external feeds.
19. Historical risk report archive.
20. Integration with trading logs for realized/unrealized risk.

Include the standard five shared features for seamless cross‑tool use.

---

## 6.  Scan Trades
Search for opportunities across the market.

1. Customizable filter builder (price, volume, indicators, etc.).
2. Pre‑built screens (momentum, value, breakouts).
3. Real‑time screen execution with alerts.
4. Historical backtest of screens.
5. Watchlist based scanning.
6. Pattern recognition (head‑and‑shoulders, flags, etc.).
7. Options‑aware scanning (IV rank, skew, unusual activity).
8. Insider‑activity screen.
9. Social‑media sentiment filter.
10. Fundamental metric filters (P/E, ROE, debt/equity).
11. Technical divergence alert (price vs. RSI/MACD).
12. Multi‑symbol correlation exclusion.
13. Sector/industry filters.
14. Volume spike detector with catalyst lookup.
15. AI‑suggested screens based on historical success.
16. Portfolio overlay to avoid conflicted trades.
17. Export results to brokerage API.
18. Alerts via email/Slack/mobile.
19. Performance leaderboard for screens.
20. Auto‑indexing of results for quick search.

Supply the five shared integration points so a screen can feed other
tools and vice‑versa.

---

## 7.  Screen Securities
Parallel processing engine for bulk screening.

1. Distributed job runner over multiple CPU cores.
2. Pluggable rule modules using same `Signal` format.
3. Caching of symbol data between runs.
4. Output normalization across data providers.
5. Dynamic resource allocation (scale based on queue).
6. Historical backfill capability.
7. Result deduplication with expiration policies.
8. API interface for external callers.
9. On‑the‑fly rule editing via UI/CLI.
10. Load balancing across worker machines.
11. Monitoring dashboard with job metrics.
12. Multi‑tenant support for different user sets.
13. Time zone aware scheduling.
14. Integration with message queues (Kafka/Rabbit).
15. Alert gateway to push results into other tools.
16. Audit trail for compliance.
17. Pre‑configured common screen templates.
18. Rate‑limit handling for data providers.
19. Persistence layer for scan results.
20. Auto‑scale when run in cloud environments.

Add the five cross‑tool features to make screen results consumable by
Fibonacci, Portfolio Risk, etc., and to allow other tools to submit
screen jobs.

---

## 8.  Trade Plan
Generates actionable strategies for a given symbol.

1. Risk profile selector (conservative, moderate, aggressive).
2. Suggest entry/exit based on multi‑factor model.
3. Money management rules (position sizing, stop‑loss).
4. Scenario optimizer using Monte‑Carlo paths.
5. Dynamic plan adjustments when market conditions change.
6. Integration with Fibonacci levels, trendlines, and support/resistance.
7. Option strategy chooser if underlying has tradable options.
8. Probability‑weighted outcome estimates.
9. Backtest performance of generated plans.
10. Export plan as JSON/CSV for order management systems.
11. Alerts when plan deviates (slippage, partial fills).
12. User‑editable strategy templates.
13. Plan history and versioning.
14. Tax lot tracking integration.
15. Multi‑symbol portfolio planning.
16. Collaborative sharing of plans between users.
17. Visual timeline of planned trades.
18. Compliance rules enforcement (pattern day trading, etc.).
19. Integration with broker APIs for one‑click execution.
20. Post‑trade analysis and plan refinement suggestions.

Include the five standard integration features so the trade plan can call
portfolio risk, signal directories, etc., and to allow other tools to
trigger plan generation.

---

## 9.  Fibonacci Expansion
Currently the most developed module; add another 20 high‑impact
capabilities to continue its growth.

1. **User‑configurable ratio sets** loaded from external JSON/YAML.
2. **Customisable swing detection algorithms** (zigzag, fractal).
3. **Time‑based Fibonacci analysis** with dynamic time‑zone support.
4. **Harmonic pattern recognition engine** that emits pattern-specific
   signals.
5. **Multi‑symbol confluence scanner** that finds symbols sharing the same
   level.
6. **Backtester for fib‑based strategies** with performance metrics.
7. **WebSocket stream for real‑time level crossing alerts.**
8. **Visualisation helpers** that output drawing coordinates for a charting
   library.
9. **Auto‑scale tolerances to account for tick size or fractional pricing.
10. **Machine‑learning model to weight levels by historical hit rate.**
11. **Custom signal strength calibration by symbol or sector.**
12. **Futures term‑structure adjustment** (carry & contango) for commodity
    symbols.
13. **Multi‑interval analysis** (1m, 5m, 1h, 1d) combined into composite
    signals.
14. **External data feed hooks** (economic releases, earnings) that adjust
    level priority.
15. **Drift detection** to invalidate old swing data automatically.
16. **Confidence intervals around levels** based on volatility.
17. **Auto‑export of level tables to Google Sheets/Excel.**
18. **CLI tool to bulk‑calculate levels for watchlists.**
19. **Integration with brokerage OCO orders using fib level triggers.**
20. **Historical level animation for visual back‑play.**

Plus, of course, the five “inter‑tool” features described earlier, which
will allow Fibonacci to feed and consume shared context and signals.

---

## Next Steps
1. Review this roadmap with stakeholders and prioritise feature sets.
2. Use the Fibonacci directory as a template when building out each tool:
   create `core/`, `analysis/`, `signals/`, `tests/` and implement the
   shared integration features first.
3. Establish a project‑wide documentation standard so every tool’s
   features are tracked and discussed in a similar markdown file.
4. Begin by fleshing out one of the simpler tools (e.g. `compare_securities`)
   with a handful of the suggested features and expand based on feedback.

The intention is not to implement all 180+ features at once, but to give
each module a clear set of directions for growth and to ensure they all
contribute to a cohesive, interoperable analytics platform.