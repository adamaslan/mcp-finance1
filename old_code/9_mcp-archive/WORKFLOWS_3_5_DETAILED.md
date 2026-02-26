# Detailed Workflows 3–5 with Expanded Elements

This document provides a deeper dive into Workflows 3, 4 and 5 from the
pro‑user series.  Each workflow is broken down into primary actions along
with extensive sub‑steps.  Ten additional elements have been added to each
workflow to provide even more operational detail.

---

## Workflow 3 – Earnings play (expanded)

1. **Benchmark peer performance**
   - Select peer list via industry tag or custom ETF.
   - Choose time windows (30‑, 90‑, 365‑day) for metrics.
   - Pull comparative charts and correlation matrices.
   - Calculate average EPS surprise for the group.
   - Identify momentum outliers (top / bottom 5%).
   - Check implied volatility percentile for each peer.
   - Download data into spreadsheet for manual inspection.
   - Flag peers with upcoming earnings dates.
   - Visualise sector map with relative strength colours.
   - Store results in research database for later retrieval.

2. **Generate AI narrative**
   - Launch `security_analyzer` with ticker and context tag "earnings".
   - Wait for natural‑language summary and sentiment scores.
   - Request breakdown of revenue/earnings/forecast surprises.
   - Ask for analyst comments or conference‑call highlights.
   - Fetch historical price moves around past earnings.
   - Save narrative to a named note in the system.
   - Append any unusual items (mergers, guidance cuts).
   - Tag narrative with event date and version.
   - Send narrative snippet to Slack research channel.
   - Link narrative to the final trade plan for audit trail.

3. **Locate price zones**
   - Compute fib levels using 50‑, 100‑, 200‑bar windows.
   - Overlay levels on intraday and daily charts.
   - Mark which levels were respected in past earnings reactions.
   - Note overlapping pivot points and moving averages.
   - Store identified zones with confidence rating.
   - Colour‑code levels by strength (major/minor).
   - Publish levels to shared Google Sheets for team.
   - Add alert triggers at crossing of major zones.
   - Compare zones with those of peers (group confluence).
   - Recalculate if overnight price gap occurs before market open.

4. **Check option skew**
   - Query option chain using `screen_securities` options filters.
   - Compute put/call ratio and IV difference.
   - Identify strikes with extreme open interest.
   - Calculate expected move using straddle pricing.
   - Plot skew curve and note its slope.
   - Compare skew to historical distribution.
   - Search for unusual block trades or volume spikes.
   - Evaluate cost of buying protection vs. selling premium.
   - Add top 3 candidate structures to watchlist.
   - Document any implied volatility crush risk after earnings.

5. **Formulate trade plan**
   - Provide entry price, target price, stop‑loss, time horizon.
   - Choose risk profile (earnings‑specific, e.g. aggressive).
   - Model plan with and without options overlay.
   - Calculate Greeks for selected strikes/legs.
   - Compute probability of profit using historical returns.
   - Generate PnL chart and value‑at‑risk for the plan.
   - Export JSON to OMS or save in system repository.
   - Set automated alerts for price reaching stop/target.
   - Schedule a review of the plan post‑earnings to assess outcome.
   - Tag plan as "earnings" and associate with narrative notes.

## Workflow 4 – Risk audit (expanded)

1. **Compute stress metrics**
   - Select portfolio snapshot and specify stress scenarios.
   - Run VaR (historical, Monte‑Carlo, parametric) for all methods.
   - Apply sector‑specific shocks (tech -30%, energy -20%).
   - Generate scenario charts, including worst‑case drawdowns.
   - Produce a PDF report with executive summary.
   - Store outputs in compliance folder with metadata.
   - Email report to compliance team and save to Slack channel.
   - Log the timestamp and user who ran the audit.
   - Archive results for quarterly audit comparisons.
   - Tag the database entry with the reason e.g. "pre‑reallocation".

2. **Benchmark against peers**
   - Identify a relevant peer portfolio or index.
   - Pull same risk metrics for the peer set.
   - Compare VaR, CVaR, concentration, beta.
   - Highlight areas where our portfolio deviates significantly.
   - Generate a side‑by‑side table with colour‑coded risk levels.
   - Check if peer portfolio uses similar hedge strategies.
   - Note any risk factors we are over‑ or under‑exposed to.
   - Save benchmarking results in research notebook.
   - Flag any structural differences in asset allocation.
   - Use benchmarking to inform rebalancing decisions.

3. **Screen for hedge opportunities**
   - Use `scan_trades` with inverse ETFs and low‑correlation ideas.
   - Filter results by liquidity and cost.
   - Score hedges by expected reduction in portfolio VaR.
   - Rank hedges by cost‑benefit ratio.
   - Visualise correlation matrix with candidates vs holdings.
   - Check for hedges available in options markets as well.
   - Create a short list of preferred hedging instruments.
   - Document rationale for selecting each hedge.
   - Determine notional amount needed for effective coverage.
   - Add hedges to a provisional `trade_plan` for comparison.

4. **Draft revised trade plan**
   - Create a `trade_plan` incorporating hedges and trims.
   - Input new target exposures and stop levels.
   - Generate expected PnL and risk metrics for the revised plan.
   - Validate that the new plan keeps VaR within limits.
   - Determine execution schedule for trimming or hedging.
   - Export plan to OMS for implementation or manual review.
   - Set alerts for execution progress and plan deviations.
   - After execution, run a follow‑up risk audit to verify outcome.
   - Record the audit in the compliance log with comments.
   - Archive final plan version for future reference.

## Workflow 5 – Momentum rotation (expanded)

1. **Screen for momentum**
   - Define momentum criteria (e.g. 20‑day, 5‑day crossovers).
   - Include volume filters and minimum ATR requirement.
   - Run scan and export raw results as CSV.
   - Compute percentile ranks for each symbol.
   - Tag symbols by sector for later comparison.
   - Filter out penny stocks or illiquid names.
   - Save candidate list with timestamp in database.
   - Automatically schedule next run for the following day.
   - Notify user of top 10 momentum movers via email.
   - Archive scan parameters for reproducibility.

2. **Compare to current holdings**
   - Use `compare_securities` to evaluate candidates vs portfolio.
   - Pull momentum, volatility, distance from 52‑week high.
   - Identify candidates with stronger momentum than any holding.
   - Create a shortlist by excluding names already held.
   - Compute expected turnover cost if rotated.
   - Visualise overlap with existing sector weights.
   - Flag candidates with earnings/events soon (risk factor).
   - Export comparison report to Google Sheets.
   - Add notes explaining why each candidate was selected.
   - Store the shortlist for review in the next step.

3. **Compute technical entries**
   - For each shortlisted candidate, calculate fib levels.
   - Determine swing points and derive entry/exit levels.
   - Overlay moving averages and pivot points.
   - Identify confluence zones where multiple indicators agree.
   - Record level strength scores and confidence intervals.
   - Set automatic alerts at entry levels using the app.
   - Draw potential trade plans with multiple entry scenarios.
   - Compare technical levels across different timeframes.
   - Create chart snapshots for inclusion in research notes.
   - Save technical analysis results to the database.

4. **Verify fundamentals**
   - For each candidate, pull latest financial statements.
   - Compute key ratios (P/E, ROE, debt/equity, cashflow).
   - Check analyst rating changes or upgrades/downgrades.
   - Scan news for any recent negative headlines.
   - Remove any candidate failing a minimum fundamental score.
   - Document the reason for removal in notes.
   - For surviving names, rate fundamentals on a 1‑5 scale.
   - Attach AI‑generated summaries for quick reference.
   - Save fundamental checks with timestamp and user.
   - Aggregate final fundamental ratings into the shortlist.

5. **Risk‑check before buying**
   - Input hypothetical positions into `portfolio_risk`.
   - Choose position sizes based on momentum score.
   - Observe changes in overall VaR, drawdown, concentration.
   - Ensure new additions do not exceed risk limits.
   - Adjust sizes downward if certain thresholds are breached.
   - Calculate potential worst‑case loss for the proposed trades.
   - Flag any candidate that causes unacceptable risk spikes.
   - Export the risk report with annotated comments.
   - Send report to inner‑circle for a quick second opinion.
   - Finalise execution plan or defer if risk is too high.

---

This document provides a richer, more actionable set of steps for each
workflow.  It is intended for use by developers planning implementing each
workflow and by power users looking to understand every detail of the
process.