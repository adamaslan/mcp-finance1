# Pro User Profile & Advanced Workflows for MCP Finance Tools

This document imagines a power user of the MCP Finance suite.  It
outlines their characteristics, the top ways they benefit from the platform,
and suggests full workflows utilising four to eight of the nine tools in
concert.  Altogether there are 81 specific actions or use cases.

---

## User Profile

- **Name (fictional)**: Alex Mercer
- **Trader Type**: Semi‑quantitative swing/trend trader with a bias
  toward mid‑cap equities and options.  Alex combines technical analysis,
  fundamental screening and risk management with occasional algorithmic
  scans.
- **Portfolio Size**: Roughly 120 positions spread across equities and
  several covered‑call and iron‑condor option structures on 30 tickers.
- **Time Commitment**: Checks the platform twice daily (pre‑market and
  late afternoon) and runs bespoke scans on demand.
- **Data Philosophy**: Believes strongly in using real data and avoids
  any mock or placeholder information.  Relies on the app for actionable
  insight, not just charts.
- **Tech Stack**: Runs MCP Finance locally and on a small cloud VM; uses
  the CLI for automation and the web UI for visual review.

---

## Top 5 Best Ways to Use the App

1. **Integrated Signal Hub** – Alex fires up the master CLI at 8 a.m.
   which executes all nine tools and aggregates signals into a daily
   dashboard.  Fib levels, risk metrics and morning brief headlines appear
   together, giving a comprehensive view of the market before the bell.

2. **Portfolio‑Aware Scanning** – a nightly job runs `screen_securities`
   filters while excluding current portfolio members and respecting risk
   limits from `portfolio_risk`.  The results feed into `scan_trades` and
   `trade_plan` to suggest new trades that fit Alex's capital and risk
   appetite.

3. **Options‑Enhanced Fibonacci Strategies** – when a core holding shows a
   strong fib‑confluence signal, Alex opens the options sheet from
   `options_risk` to build a directional spread that caps risk and leverages
   the predicted price zone.

4. **Morning Brief + News‑Driven Revisits** – every morning the `morning_brief`
   pulls in overnight news sentiment, economic events, and highlights
   any portfolio symbols with new fib level crossings.  Alex tags three
   symbols for deeper analysis and runs `security_analyzer` on them.

5. **Stress‑Test Compliance Report** – before reallocating capital or
   adding a large new position, Alex uses `portfolio_risk` to run a 2008‑style
   stress scenario.  The report is exported to PDF and attached to the
   compliance log.

These five routines exemplify how the tools work together to deliver
coherent, actionable workflows rather than isolated calculations.

---

## 81 Actions a Power User Might Take

The following list enumerates possible tasks Alex executes across the nine
modules.  They are grouped by tool but often reference cross‑tool usage.

### Compare Securities (9 actions)
1. Normalise price charts for two biotech stocks and overlay fib levels.
2. Compute rolling 60‑day correlation among portfolio symbols.
3. Identify cointegrated pairs for mean‑reversion trades.
4. Generate an ETF vs. index volatility report.
5. Perform sector weighting analysis to check over‑exposure.
6. Run a sentiment comparison using news feeds imported via
   `security_analyzer`.
7. Export a PDF comparison of AAPL vs. MSFT for client review.
8. Use ML similarity scores to find closest peers to a thinly traded
   position.
9. Call the module from `morning_brief` to colour‑code movers.

### Security Analyzer (9 actions)
10. Generate AI‑written summary of quarterly results.
11. Pull fundamental ratios from API and compute a custom valuation metric.
12. Stream real‑time price data during earnings.
13. Overlay fib levels from `fibonacci` on the indicator chart.
14. Backtest a momentum strategy using the module's backtester.
15. Export the dataset for external ML training.
16. Trigger a risk‑alert when insider ownership drops.
17. Add ESG score to a watchlist filter in `scan_trades`.
18. Inject annotation of corporate events into `morning_brief` headlines.

### Morning Brief (9 actions)
19. View overnight gap analysis for SPY and QQQ.
20. Review pre‑market movers and tag those in the portfolio.
21. Scan the economic calendar for scheduled FOMC releases.
22. Read the audio briefing during morning coffee.
23. Create a custom template excluding cryptocurrency statistics.
24. Archive the day's brief for future research.
25. Push the brief to Slack using the API.
26. Automatically generate a list of symbols with new fib cross alerts.
27. Use brief data to seed `scan_trades` screens.

### Options Risk Analysis (9 actions)
28. Calculate Greeks for a 3‑leg iron condor.
29. Visualise delta risk surface for the entire options book.
30. Run a Monte‑Carlo stress test using fib‑based price paths.
31. Estimate assignment probability ahead of ex‑div date.
32. Scan chain for high IV rank opportunities.
33. Export a compliance risk report.
34. Trigger an alert when portfolio gamma exceeds threshold.
35. Re‑price held positions after a volatility shock.
36. Build a delta‑neutral synthetic position and test it via
   `portfolio_risk`.

### Portfolio Risk (9 actions)
37. Compute 95 % VaR using historical returns.
38. Model a simultaneous -30 % drop in all tech holdings.
39. Check concentration risk for a top‑weight security.
40. Generate a risk‑parity rebalance suggestion.
41. Produce a drawdown/recovery chart for the past 5 years.
42. Run an audit report for FRTB compliance.
43. Evaluate beta against S&P 500 monthly.
44. Correlate current holdings with macro risk factors.
45. Feed realized/unrealized risk data back into `trade_plan`.

### Scan Trades (9 actions)
46. Build a momentum screen that excludes current positions.
47. Backtest a breakout screen with historical data.
48. Run the screen overnight and email results.
49. Add social‑media sentiment filter via the plugin.
50. Launch an options‑aware screen during earnings week.
51. Use AI to suggest a new screen based on last week's winners.
52. Export results to the broker API for order routing.
53. Auto‑index screen results for quick retrieval.
54. Overlay portfolio risk limits to automatically prune matches.

### Screen Securities (9 actions)
55. Schedule a distributed scanning job every hour.
56. Edit a rule on‑the‑fly via CLI while a scan is running.
57. Cache quote history to speed repeated runs.
58. Publish scan results to Kafka for downstream consumption.
59. View the monitoring dashboard to check job health.
60. Run a multi‑tenant scan for a partner account.
61. Adjust scheduling to avoid maintenance windows.
62. Persist results into the database for future analysis.
63. Auto‑scale worker processes when the queue length spikes.

### Trade Plan (9 actions)
64. Create a new plan for AMZN using risk‑profile "moderate." 
65. Adjust the plan mid‑day after a fib level break.
66. Backtest the plan against the last 12 months of data.
67. Share the plan with a co‑trader via the collaboration feature.
68. Export the plan as JSON to the OMS.
69. Receive an alert when slippage exceeds 0.5 %. 
70. Version the plan before a big earnings trade.
71. Use portfolio risk output to set position size.
72. Visualise the planned trades on a timeline chart.

### Fibonacci Expansion (9 actions)
73. Load a custom ratio set from YAML and recalc levels.
74. Enable harmonic pattern recognition for selected symbols.
75. Register a new symbol set to be scanned for multi‑symbol confluence.
76. Stream real‑time level crossing alerts to a WebSocket client.
77. Run a bulk CLI job calculating levels for watchlist tickers.
78. Attach level confidence intervals to signals.
79. Animate historical fib levels for a play‑back review.
80. Generate export to Google Sheets for the research notebook.
81. Use machine‑learning model to up‑weight historically strong levels.

---

## Workflow Examples

Each of the nine workflows below strings together four to eight of the
MCP tools.  They demonstrate how a pro user like Alex might tackle common
trading challenges.

### Workflow 1 – New‑idea generation (tools 1, 5, 6, 8)
1. Run `screen_securities` overnight with custom filters.
2. Feed results into `scan_trades` for refined scoring and backtesting.
3. Compute portfolio risk implications of adding each candidate.
4. Pass top three proposals into `trade_plan` for final sizing and
   entry/exit rules.

### Workflow 2 – Pre‑market preparation (tools 3, 9, 2, 4)
1. Open `morning_brief` and review overnight headlines.
2. Highlight portfolio symbols with new fib level events.
3. Drill into those symbols with `security_analyzer` for fundamentals
   and news context.
4. Use `options_risk` to analyse existing option structures and decide
   whether to adjust or hedge.

### Workflow 3 – Earnings play (tools 1, 2, 9, 7, 4)
1. Use `compare_securities` to benchmark the target against peers.
2. Generate an AI narrative in `security_analyzer` focusing on past
   earnings surprises.
3. Calculate fib levels in `fibonacci` to identify key price zones.
4. Screen for corresponding option skew in `screen_securities`.
5. Construct a candidate trade plan and evaluate Greeks with `options_risk`.

### Workflow 4 – Risk audit (tools 5, 1, 6, 8)
1. Run `portfolio_risk` VaR and stress tests.
2. Compare portfolio risk to industry averages via
   `compare_securities`.
3. Scan trades for opportunities to hedge via short positions or options.
4. Draft a new trade plan that reduces concentration risk.

### Workflow 5 – Momentum rotation (tools 6, 1, 9, 2, 5)
1. Execute a momentum screen; export tickers.
2. Compare them against current holdings to identify rotation candidates.
3. For top candidates, compute fib levels to find entry points.
4. Analyze fundamentals with `security_analyzer` to avoid weak balance
   sheets.
5. Run a quick portfolio risk check before executing any new buying.

### Workflow 6 – Long‑term thesis validation (tools 2, 3, 1, 5, 9)
1. Read monthly `morning_brief` to gather macro news.
2. Use `security_analyzer` to revisit long‑term holdings’ fundamentals.
3. Compare those securities to sector leaders.
4. Update Fibonacci levels to see if the thesis aligns with current
   price structure.
5. Adjust portfolio risk metrics and possibly rebalance.

### Workflow 7 – Options hedge construction (tools 4, 5, 9, 1)
1. Identify a volatile position in `portfolio_risk` needing insurance.
2. Evaluate available option chains in `options_risk` for cost and IV.
3. Use fib levels to choose strike prices for a protective spread.
4. Validate the hedge’s effect on overall risk metrics.
5. Store the hedge plan in `trade_plan` for monitoring.

### Workflow 8 – Research session (tools 1, 6, 2, 7, 3)
1. Bulk‑calculate fib levels on watchlist via CLI.
2. Run an options‑aware scan for candidates forming classic patterns.
3. Analyze a short list of symbols in depth using `security_analyzer`.
4. Feed top picks to `trade_plan` for hypothetical orders.
5. Generate a mini‑brief summarizing the research and forward to an
   email group.

### Workflow 9 – End‑of‑day review (tools 3, 5, 8, 2)
1. Read the evening `morning_brief` archive to recap the day.
2. Update portfolio risk statistics and compare with morning values.
3. Review any open trade plans and mark those that executed successfully.
4. Ask `security_analyzer` to generate a quick sentiment summary of any
   price movers.

---

These nine workflows show how a pro user leverages **between four and eight
modules simultaneously** to make disciplined data‑driven decisions.  The
81 individual actions provide a granular view of what a power user might
actually click, run and automate as part of their daily cadence.