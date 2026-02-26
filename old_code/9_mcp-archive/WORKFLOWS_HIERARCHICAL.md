# Hierarchical Workflow Summaries for MCP Finance Tools

This document breaks each of the nine pro-user workflows into hierarchical
steps.  Every workflow is presented as a series of 2–4 primary actions, each
of which is further decomposed into 2–4 secondary steps for clarity.

---

### Workflow 1 – New‑idea generation
1. **Run initial market screen**
   - Select `screen_securities` filters (momentum, volume, exclude portfolio).
     * Open filter builder and choose momentum threshold (e.g. 70th percentile).
     * Add volume minimum and remove existing portfolio tickers.
   - Schedule overnight execution via the CLI.
     * Create a cron job or use the master script with `--run-screen` flag.
     * Confirm stdout logs and email summary will be generated.
   - Ensure filters respect current position exposures.
     * Load current positions from portfolio file.
     * Validate that no ticker in filter matches the held list.
2. **Refine candidates in scanning module**
   - Feed raw symbols into `scan_trades`.
     * Pass symbol list via command-line argument or config file.
     * Ensure data provider credentials are loaded.
   - Apply scoring rules and backtest historic performance.
     * Define scoring configuration (momentum, volatility, earnings).
     * Run backtest and review summary statistics for each symbol.
   - Discard symbols that repeatedly fail risk rules.
     * Mark symbols with high drawdown or poor Sharpe.
     * Remove them from the candidate pool before further analysis.
3. **Evaluate portfolio impact**
   - Use `portfolio_risk` to simulate adding each candidate.
     * Input current portfolio plus single candidate.
     * Choose VaR method (historical/parametric) for consistency.
   - Compute incremental VaR and concentration penalties.
     * Compare risk metrics with and without candidate.
     * Calculate change in concentration towards any sector.
   - Flag candidates exceeding risk thresholds.
     * Set alert if incremental VaR > 0.5% of NAV.
     * Notify user via email or dashboard about flagged items.
4. **Build trade plans for top picks**
   - Choose top three candidates by score and acceptable risk.
     * Rank candidates based on composite score and risk filter.
     * Select first three that pass validation.
   - Run `trade_plan` to size positions and set entry/exit.
     * Provide risk profile and budget constraints to the plan.
     * Review generated stop‑loss and target levels.
   - Export plans or queue for manual review.
     * Save plan JSON to a folder or mark for review in UI.
     * Optionally trigger `trade_plan --notify` to collaborators.

### Workflow 2 – Pre‑market preparation
1. **Consume daily briefing**
   - Open `morning_brief` at start of day.
     * Load the brief URL or run the CLI summary command.
     * Ensure data feeds have refreshed overnight.
   - Read headlines, gap analysis and movers list.
     * Skim for macro events and high‑volume names.
     * Mark any names already in the portfolio.
   - Note any economic calendar events.
     * Expand the calendar and flag FOMC, CPI, earnings.
     * Set reminders for key time slots.
2. **Identify fib events**
   - Highlight portfolio symbols with new `fibonacci` level
     crossings.
     * Filter brief movers by portfolio membership.
     * Use color‑coding to show levels crossed.
   - Record levels and timeframes for later trade decisions.
     * Write down level values in a notes file.
     * Attach charts or screenshots if desired.
3. **Drill into fundamentals & news**
   - Launch `security_analyzer` on marked symbols.
     * Supply tickers via command‑line or dashboard input.
     * Allow the analyzer to fetch the latest filings.
   - Review balance sheets, earnings, and recent news.
     * Check debt ratios, cashflow trends, revenue growth.
     * Read summaries of any news articles pulled.
   - Annotate any unusual items or risks.
     * Add comments using the tool’s annotation feature.
     * Tag other team members if collaboration supported.
4. **Check existing option positions**
   - Open `options_risk` for relevant tickers.
     * Load current contracts from the portfolio file.
     * Refresh quotes before analysis.
   - Analyse Greeks, IV and potential hedges.
     * View delta, gamma, vega across all legs.
     * Identify opportunities for protective spreads.
   - Decide whether to adjust or roll existing spreads.
     * Simulate roll costs and risk change.
     * Commit adjustments via broker integration or note them.

### Workflow 3 – Earnings play
1. **Benchmark peer performance**
   - Run `compare_securities` against peer group.
     * Select a list of industry peers or ETF components.
     * Configure time window (90‑day, 1‑year) for comparison.
   - Look for outliers in momentum or volatility.
     * Generate heatmap or table highlighting extremes.
     * Note any stocks significantly stronger or weaker.
   - Determine relative strength or weakness.
     * Compute percentile ranks within the group.
     * Export summary for later reference.
2. **Generate AI narrative**
   - Use `security_analyzer` to produce earnings summary.
     * Pass the ticker and request "earnings" context.
     * Wait for analysis to complete (may take seconds).
   - Include quantified metrics like surprise history.
     * Pull EPS/revenue surprise percentages.
     * Add prior‑quarter comparison for trend.
   - Save narrative for reference in trade notes.
     * Store output as a text file or database entry.
     * Tag it with date and event type for retrieval.
3. **Locate price zones**
   - Calculate `fibonacci` levels for target symbol.
     * Choose a window (e.g. 50 bars) based on volatility.
     * Run calculation and display resulting levels.
   - Identify support/resistance regions around event.
     * Map prior highs/lows near the earnings date.
     * Highlight overlaps with fib ratios.
   - Mark levels that align with peer technicals.
     * Check if peers share similar price zones.
     * Note collective thresholds that signal sector moves.
4. **Check option skew**
   - Run `screen_securities` focusing on options IV.
     * Filter for calls or puts with highest IV rank.
     * Include required volume or open interest minima.
   - Look for asymmetric pricing indicating fear.
     * Compare call vs. put IV to identify put skew.
     * Record any unusual option structures.
   - Flag candidates for potential strategies.
     * Add promising options to a watchlist.
     * Link them back to symbols with fib zones.
5. **Formulate trade plan**
   - Feed selected strike/price zones into `trade_plan`.
     * Provide the entry price, target, and stop range.
     * Choose a risk profile appropriate for earnings.
   - Evaluate Greeks and risk-reward via `options_risk`.
     * Calculate delta and vega for chosen strikes.
     * Ensure expected payoff is acceptable.
   - Finalise entry, exit and position size.
     * Commit the plan to system or export for execution.
     * Set alerts for level breaches or time-based exits.

### Workflow 4 – Risk audit
1. **Compute stress metrics**
   - Execute `portfolio_risk` VaR and -30 % tech shock.
     * Choose the appropriate historical window.
     * Select the tech sector or entire equity book.
   - Generate stress scenario reports.
     * Produce PDF or JSON output for each scenario.
     * Include charts showing PnL distribution.
   - Store results for compliance logs.
     * Save to a central repository with timestamp.
     * Tag with audit metadata (user, reason).
2. **Benchmark against peers**
   - Use `compare_securities` to see industry risk levels.
     * Pull peer portfolios or a relevant ETF.
     * Request the same VaR/stress metrics.
   - Identify areas where portfolio is unusually exposed.
     * Spot sectors or factors with higher risk.
     * Highlight differences in plots or tables.
3. **Screen for hedge opportunities**
   - Run `scan_trades` looking for inverse or defensive ideas.
     * Configure filters for low beta or inverse ETFs.
     * Include risk criteria from `portfolio_risk` output.
   - Prioritise candidates with low correlation.
     * Compute correlation matrix to current holdings.
     * Rank hedges by lowest correlation.
4. **Draft revised trade plan**
   - Create a `trade_plan` to reduce concentration.
     * Specify symbols to trim and target allocation.
     * Add hedging trades identified earlier.
   - Set new stop‑losses or allocate to hedging trades.
     * Choose stops based on updated risk levels.
     * Allocate capital to hedges as suggested.
   - Monitor plan execution over following days.
     * Track fills and adjust if market moves.
     * Re-run risk audit after execution.

### Workflow 5 – Momentum rotation
1. **Screen for momentum**
   - Build and run a momentum filter in `screen_securities`.
     * Set lookback period (e.g. 20‑day returns).
     * Include minimum volume and price criteria.
   - Export ticker list for further processing.
     * Save list as CSV or pass directly to next step.
     * Tag each with its momentum score.
2. **Compare to current holdings**
   - Pass results through `compare_securities` against portfolio.
     * Input candidate list and current symbols.
     * Receive side‑by‑side metrics.
   - Identify symbols with stronger momentum than holdings.
     * Highlight those exceeding portfolio avg momentum.
     * Mark them as rotation candidates.
3. **Compute technical entries**
   - Use `fibonacci` to calculate entry levels for candidates.
     * Determine swing high/low and compute levels.
     * Map levels to chart timeframes (1h, 4h, daily).
   - Choose levels that avoid current support/resistance.
     * Cross‑reference past price action.
     * Select entries slightly above consolidation tops.
4. **Verify fundamentals**
   - Run `security_analyzer` to check financial health.
     * Fetch latest ratios and news items.
     * Look for debt or cashflow red flags.
   - Drop any with weak balance sheets.
     * Remove tickers failing a minimum fundamental score.
     * Document reasons for removal.
5. **Risk‑check before buying**
   - Quickly rerun `portfolio_risk` with potential additions.
     * Input hypothetical positions with size estimates.
     * Observe change in VaR and concentration.
   - Approve or reject according to risk thresholds.
     * If above threshold, return to step 1 or adjust size.
     * Otherwise, prepare order execution plan.

### Workflow 6 – Long‑term thesis validation
1. **Review macro environment**
   - Read the monthly `morning_brief` for macro themes.
     * Pay attention to GDP, inflation, interest rate commentary.
     * Extract quotes or data points relevant to holdings.
   - Note any news that could affect long‑term holdings.
     * Identify regulatory, geopolitical or sector‑specific events.
     * Flag those for deeper company analysis.
2. **Re‑analyse fundamentals**
   - Use `security_analyzer` to refresh key ratios and earnings
     forecasts.
     * Run the analyzer with latest quarterly data.
     * Review trend lines for revenue and earnings.
   - Check for deteriorating metrics or management changes.
     * Look for rising debt/equity or dropping margins.
     * Note any CFO/CEO departures.
3. **Peer comparison**
   - Compare holdings to sector leaders with
     `compare_securities`.
     * Select a list of top performers in the sector.
     * Run comparison for valuation, growth, and momentum.
   - Verify thesis still out‑performs peers.
     * Determine if the holding remains in top quartile.
     * Document any cases where a peer now looks preferable.
4. **Technical alignment**
   - Update `fibonacci` levels to ensure price supports thesis.
     * Recompute swings using recent price action.
     * Identify whether price is still above key support.
   - Watch for breakdowns that may invalidate the trade.
     * Set alerts on level breaches.
     * Prepare an exit plan if breakdown occurs.
5. **Update risk posture**
   - Recalculate `portfolio_risk` including any thesis changes.
     * Input new weightings reflecting thesis adjustments.
     * Observe any shifts in overall risk profile.
   - Decide whether to rebalance or trim positions.
     * If risk increases beyond comfort, plan a trim.
     * Otherwise, leave allocation intact.

### Workflow 7 – Options hedge construction
1. **Find volatile position**
   - Scan `portfolio_risk` for high‑volatility outliers.
     * Sort holdings by their individual volatility scores.
     * Focus on those exceeding a set threshold (e.g. 30%).
   - Mark symbols needing downside protection.
     * Create a list for the options analysis step.
     * Assign priority based on notional size.
2. **Survey option chains**
   - Open `options_risk` and examine available strikes.
     * Pull the current chain for each candidate ticker.
     * Display implied volatility and open interest per strike.
   - Look for reasonable cost/IV trade‑offs.
     * Calculate cost per unit of protection (e.g. 1‑delta put).
     * Discard strikes with prohibitively high premiums.
3. **Select fib‑based strikes**
   - Use `fibonacci` to choose strikes near critical levels.
     * Compute levels using the holdings’ price history.
     * Overlay these levels on the option chain.
   - Prefer strikes just outside support zones for protection.
     * Choose a strike below the nearest fib level.
     * Ensure the strike is liquid enough to trade.
4. **Assess hedge impact**
   - Re‑run `portfolio_risk` with proposed hedge.
     * Add the hedge position to the simulated portfolio.
     * Observe reduction in VaR or drawdown.
   - Ensure overall risk metrics improve.
     * Confirm that cost of hedge justifies benefit.
     * If not, adjust strike or strategy (e.g. collar).
5. **Record hedge plan**
   - Store details in `trade_plan` for monitoring and alerts.
     * Include entry, size, and expiration in the plan.
     * Set alerts for when underlying approaches the strike.

### Workflow 8 – Research session
1. **Bulk calculate levels**
   - Run CLI job in `fibonacci` for entire watchlist.
     * Provide a list of all symbols to the script.
     * Choose timeframes to compute (1h, 4h, daily).
   - Cache results for easy lookup later.
     * Store in a local database or JSON files.
     * Tag data with timestamp and source.
2. **Execute options‑aware scan**
   - Launch `scan_trades` with options filters.
     * Configure to only include symbols with tradable options.
     * Set IV rank or skew criteria.
   - Look for patterns and favorable IV.
     * Detect classics like bull‑pennant or double‑bottom.
     * Flag unusual skew that may indicate event risk.
3. **Deep symbol analysis**
   - For the shortlist, run `security_analyzer`.
     * Pull full fundamental profile and recent news.
     * Retrieve analyst ratings and target prices.
   - Collate financials, news, and AI narratives.
     * Assemble a one‑page summary document.
     * Highlight red flags or catalysts.
4. **Prototype trade plans**
   - Feed picks into `trade_plan` with hypothetical entries.
     * Input assumed entry price and time horizon.
     * Let the plan size and set stops automatically.
   - Evaluate using past performance metrics.
     * Backtest the proposed plan over historical data.
     * Compute expected return and probability of profit.
5. **Summarise in mini‑brief**
   - Generate a short `morning_brief` style summary.
     * Include top 3 ideas, rationale, and risk points.
     * Format for email or Slack distribution.
   - Email or share with research collaborators.
     * Attach relevant charts and plan exports.
     * Request feedback or approval.

### Workflow 9 – End‑of‑day review
1. **Recap the day**
   - Read the evening `morning_brief` archive.
     * Open the archived brief in the system.
     * Check for any after‑hours news updates.
   - Note any major market moves or news.
     * List tickers that moved > 3%.
     * Record reasons if available.
2. **Update risk figures**
   - Recompute daily `portfolio_risk` metrics.
     * Run the risk script with updated prices.
     * Save the output with a date tag.
   - Compare to morning values for drift.
     * Highlight increases in VaR or concentration.
     * Investigate sources of change.
3. **Review open plans**
   - Check `trade_plan` items that triggered or partially
     filled.
     * Mark those that executed and note fill prices.
     * Cancel or adjust any incomplete plans.
   - Tag successes or failures.
     * Assign outcome labels (hit, miss, cancelled).
     * Store for later performance analysis.
4. **Gather sentiment summaries**
   - Ask `security_analyzer` for same‑day sentiment on movers.
     * Submit tickers and request sentiment report.
     * Wait for the analysis to finish.
   - Store results for pattern analysis.
     * Save sentiments alongside price moves.
     * Use in future research to correlate sentiment with outcomes.

### Workflow 9 – End‑of‑day review
1. **Recap the day**
   - Read the evening `morning_brief` archive.
   - Note any major market moves or news.
2. **Update risk figures**
   - Recompute daily `portfolio_risk` metrics.
   - Compare to morning values for drift.
3. **Review open plans**
   - Check `trade_plan` items that triggered or partially
     filled.
   - Tag successes or failures.
4. **Gather sentiment summaries**
   - Ask `security_analyzer` for same‑day sentiment on movers.
   - Store results for pattern analysis.

---

Each workflow is now expressed as a clear hierarchy with primary actions
and supporting steps, making it easier to translate into UI flows,
automation scripts or training material.