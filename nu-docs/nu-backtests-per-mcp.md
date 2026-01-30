# 20 Robust Backtest Examples per MCP — nu-doc

This doc lists 20 different, robust and conceptually diverse backtests for each MCP. Each entry includes a short description and a parameter-rich YAML snippet you can drop into `backtests.yml` using `apply_to: [MCPx]`.

---

Format for each test:
- Short description
- Parameters (detailed) — think like a quant + risk manager
- Example YAML snippet

For brevity we show the per-MCP sections with template placeholders — replace MCP1..MCP9 and the universe path per-MCP.

## MCP1 — 20 robust backtests
1) Buy & Hold (benchmark)
   - Params: start_date, end_date, rebalance: none, transaction_cost_bps
   - YAML:
     id: mcp1_buy_hold
     type: buy_and_hold
     apply_to: [MCP1]
     params: { start_date: 2010-01-01 }

2) Momentum (top-n) — short-term momentum
   - Params: lookback: 60-120, top_n: 5-50, weighting: equal/risk_parity, rebalance: monthly/weekly, turnover_limit
   - YAML:
     id: mcp1_momentum_short
     type: momentum
     apply_to: [MCP1]
     params: { lookback: 90, top_n: 20, weighting: equal, rebalance: monthly }

3) Momentum — long-term
   - Params: lookback: 126-252, top_n: 10-50, rebalance: quarterly, combined with volatility_target

4) Mean Reversion — RSI
   - Params: rsi_period: 14, buy_thresh: 30, sell_thresh: 70, max_positions

5) Mean Reversion — Z-score on returns
   - Params: lookback: 20-60, z_entry: -2.0, z_exit: -0.5, max_hold_days

6) Trend Following — SMA crossover
   - Params: fast_window: 20, slow_window: 100, position_sizing: percent_of_equity, stop_loss

7) Breakout — Donchian channel
   - Params: lookback: 20, exit_lookback: 10, volume_filter

8) Pairs Trading — cointegration
   - Params: pair_selection: universe_filter, coint_pval_thresh: 0.05, z_entry: 2.0, z_exit: 0.5, max_positions

9) Volatility Targeting
   - Params: target_annual_vol: 0.12, vol_lookback: 60, leverage_limit: 2.0

10) ATR Position Sizing
    - Params: atr_period: 14, risk_per_trade_pct: 0.5, slippage_model

11) Stop-loss & Take-profit Sweeps
    - Params: stop_pct: [2,5,10], take_pct: [3,8,15], trailing_stop

12) Kelly Sizing
    - Params: fraction_cap: 0.75, historical_window

13) Equal-weight basket
    - Params: top_n, rebalance, max_turnover

14) Risk Parity
    - Params: vol_lookback: 63, rebalance: monthly, leverage_cap

15) Sector Rotation
    - Params: sector_mapping, lookback, election_method: top_k

16) Multi-factor scoring
    - Params: factors: [momentum, value, quality], weights, zscore_norm

17) Low-volatility tilt
    - Params: vol_lookback, vol_metric: std/realized_vol, top_n

18) Long-Short Market-Neutral
    - Params: top_n, bottom_n, net_exposure: 0, leverage

19) Transaction-cost & Slippage Sensitivity
    - Params: sweep values for transaction_cost_bps, slippage_models

20) Event-driven (earnings)
    - Params: event_feed, window_before, window_after, filter_quantiles

---

Repeat the above 20 for MCP2..MCP9: vary default parameters and universe filters. For each MCP, recommend tailoring:
- Universe size (small-cap vs large-cap)
- Max leverage and exposure caps
- Allowed assets (equities only, or ETFs, ADRs)

### Example full YAML entry (momentum + variants)
backtests:
  - id: mcp1_momentum_90_20_eq
    type: momentum
    apply_to: [MCP1]
    params:
      lookback: 90
      top_n: 20
      weighting: equal
      rebalance: monthly
      transaction_cost_bps: 5

---

## Implementation notes
- For each test include the following parameter groups: universe_filters, data_quality_filters (min_liquidity, min_history), risk_controls (max_position_pct, max_leverage), execution_params (transaction_cost_bps, slippage_model), and reporting flags (save_trades, save_plots).
- Save a canonical YAML snippet per test into `nu-docs/backtest-templates/` for quick reuse.

---

This doc is intentionally concise: if you'd like I can expand each MCP section into full, parameter-complete YAML files (one per test) and add these into `nu-docs/backtest-templates/` as individual files. Let me know if you want me to generate those files next.