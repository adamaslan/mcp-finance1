# Backtesting with yfinance — nu-MCP guide 🔧📈

## Summary
A compact, centralized backtesting design for all nine MCPs using `yfinance` for data ingestion. Focus: flexible, easily configurable tests, reusable templates, and clear per-MCP mappings so experiments are reproducible and parameterizable.

---

## Design principles ✅
- **Centralized config**: one YAML file controls global settings, per-MCP overrides, and a list of backtests to run.
- **Modular tests**: each backtest is a small, parameterized template (strategy type + params + execution model + risk rules).
- **Pluggable data**: default `yfinance` loader with local caching (Parquet) and optional alternative sources.
- **Simple CLI / API runner**: run single test, sweep many, or run suites across multiple MCPs.
- **Deterministic outputs**: deterministic seeding, versioned config, and full run metadata in outputs.

---

## Global configuration (example)
```yaml
global:
  data_source: yfinance
  cache_dir: data/cache
  start_date: 2010-01-01
  end_date: 2025-01-01
  frequency: daily  # daily | weekly | monthly
  transaction_cost_bps: 5
  slippage_model: pct_of_spread

mcps:
  MCP1:
    universe: file://mcp1_universe.csv
  MCP2:
    universe: query:select tickers from universe where signal_group=2

backtests:
  - id: m1_momentum
    type: momentum
    apply_to: [MCP1, MCP2]
    params:
      lookback: 90
      top_n: 20
      weighting: equal
      rebalance: monthly
```

> Note: Use `apply_to` to run a test for any subset of the nine MCPs.

---

## 20 concise, very-different backtest types (apply across any MCP) 🧪
For each test we list a short description and minimal config parameters to make it trivial to instantiate and run.

1) **Buy & Hold** — baseline, low complexity.
   - Key params: hold_universe (true/false), start_date
   - Metrics: total return, max drawdown

2) **Periodic Rebalance (equal-weight)** — rebalancing every N period.
   - Params: rebalance_frequency, top_n, weighting

3) **Momentum (top-n)** — rank by returns over lookback, long-only.
   - Params: lookback, top_n, rebalance

4) **Mean Reversion (RSI/Threshold)** — buy when oversold.
   - Params: rsi_period, buy_thresh, sell_thresh, lookback

5) **Moving Avg Crossover (trend-following)** — SMA fast/slow crossover.
   - Params: fast_window, slow_window, position_sizing

6) **Breakout (Donchian / Channel)** — enter on breakout, exit on channel break.
   - Params: lookback, exit_lookback, breakout_type

7) **Pairs Trading (cointegration/stat arb)** — market-neutral pair trades.
   - Params: pair_selection: cointegration_p_value, zscore_entry, zscore_exit

8) **Volatility Targeting / Volatility parity** — scale exposure to target vol.
   - Params: target_annual_vol, lookback_vol, max_leverage

9) **ATR Position Sizing** — size by ATR to equalize risk per trade.
   - Params: atr_period, risk_per_trade_pct

10) **Stop-loss & Take-profit analysis** — test fixed thresholds and trailing stops.
    - Params: stop_pct, take_pct, trailing=True/False

11) **Kelly / Optimal f sizing** — position size via Kelly fraction.
    - Params: fraction_cap, min_trade_size

12) **Equal-weight basket** — long top-N equally weighted.
    - Params: top_n, rebalance

13) **Risk Parity** — allocate by inverse vol or risk contribution.
    - Params: vol_lookback, leverage_limit

14) **Sector Rotation** — rank sectors and rotate.
    - Params: sector_mapping, lookback, top_sector_count

15) **Factor-based (value / momentum / quality)** — scoring and multi-factor weights.
    - Params: factor_list, factor_weights, zscore_normalize

16) **Low-volatility tilt** — bias to low-vol stocks.
    - Params: vol_lookback, top_n

17) **Long-Short Market-Neutral** — long top & short bottom by signal.
    - Params: top_n, bottom_n, net_exposure=0

18) **Seasonality / Calendar effects** — monthly/weekday seasonality tests.
    - Params: season_pattern (e.g., month=[11,12]), compare_periods

19) **Transaction-cost & slippage sensitivity** — sweep costs to measure robustness.
    - Params: transaction_cost_bps (list), slippage_model (list)

20) **Event-driven (earnings, splits)** — trade on event triggers.
    - Params: event_type (earnings), window_before, window_after, filter

---

## Easy configuration approach (templates) ⚙️
- Provide one YAML template per `type` above. A minimal engine will load a template and merge user params.
- Standardize parameter names across templates where possible (e.g., `rebalance`, `lookback`, `top_n`, `weighting`).

Example template for `momentum`:
```yaml
id: momentum_template
type: momentum
params:
  lookback: 90
  top_n: 10
  weighting: risk_parity
  rebalance: monthly
```

Example template for `pairs`:
```yaml
id: pairs_basic
type: pairs
params:
  cointegration_p_value: 0.05
  zscore_entry: 2.0
  zscore_exit: 0.5
  max_positions: 10
```

---

## Runner & API suggestions
- CLI: `nu-backtest run --config config.yml --mcp MCP1 --backtest m1_momentum` ✅
- Batch: `nu-backtest run-batch --config config.yml --preset quarterly-scan`
- Store each run in `outputs/<run_id>/` with `prices.parquet`, `trades.csv`, `report.json`, and `plots/`.

---

## Data & implementation notes
- Use `yfinance` for daily OHLCV: add a caching layer (`to_parquet`) to avoid repeated downloads.
- For performance consider `vectorbt` or `fastparquet + numba` for heavy simulations.
- Emulate execution with realistic costs: per-trade cost, bps, fixed fees, and slippage models.
- Add a `simulate_partial_fill` flag to study market impact (use synthetic slippage functions).

---

## Reporting and metrics (per test)
- Benchmarks: raw return vs buy&hold, Sharpe, Sortino, max drawdown, CAGR, hit rate, turnover.
- Risk decomposition: factor exposures, concentration, period-wise drawdowns.
- Config and metadata must be saved with each run for reproducibility.

---

## How to apply to the nine MCPs
1. Create a single `backtests.yml` with `apply_to` lists that map tests to MCPs.
2. Use per-MCP overrides for universe and risk limits.
3. Run the same test across all MCPs to compare signal portability and robustness.

Example mapping stub:
```yaml
backtests:
  - id: momentum_global
    type: momentum
    apply_to: [MCP1, MCP2, MCP3, MCP4, MCP5, MCP6, MCP7, MCP8, MCP9]
    params: { lookback: 120, top_n: 20 }
```

---

## Quick tips 💡
- Start with low-cost baselines (Buy & Hold) and add complexity incrementally.
- Always run transaction-cost sensitivity sweeps (test #19) before trusting high-turnover strategies.
- Use small synthetic experiments on a subset of the universe to validate correctness before large runs.

---

## Next steps
- Add an example runner script `scripts/nu_backtest_runner.py` and a sample `backtests.yml` in the repo.
- Create a minimal notebook `notebooks/backtest-demo.ipynb` that runs 3 representative tests across MCP1-3 for quick verification.

> If you want, I can add the `backtests.yml` template and implement the `nu_backtest_runner.py` scaffold next. 👇

---

*Doc generated: concise blueprint to run, compare and scale backtests across nine MCPs using yfinance.*
