# Technical Analysis MCP — Source Overview & How to Change Values 🔧

This document explains every file under `mcp-finance1/src/technical_analysis_mcp/`, what it does, important classes/functions, and the easiest ways to change runtime values and configuration.

---

## Quick summary (TL;DR) ✅
- Primary configuration/constants: `config.py` (global constants) and `profiles/*` (user presets).
- Runtime per-user/per-session changes: use `profiles.config_manager.ConfigManager` session overrides or `get_profile_with_overrides()`.
- Temporary price simulations: `price_overrides.PriceOverrideManager` (set/clear/apply overrides).
- External secrets: `GEMINI_API_KEY` via environment variable.
- Easiest ways to change values: (1) session overrides via `ConfigManager`, (2) use existing risk profiles in `profiles/risk_profiles.py`, (3) set price overrides with `PriceOverrideManager`, (4) edit `config.py` for global, persistent changes.

---

## Files & directories (detailed) 📁

### Top-level package files

- `__init__.py` 🔹
  - Purpose: Public API and `TechnicalAnalyzer` facade for running complete analysis.
  - Key items: `TechnicalAnalyzer` class (simple `analyze()`, `compare()`, `screen()` wrappers), exports for major classes and helpers.
  - Where to change values: uses package defaults and `config.py`/profiles; change via `TechnicalAnalyzer` constructor (pass custom `DataFetcher` or `RankingStrategy`).

- `config.py` 🔸 (Primary constants)
  - Purpose: Central place for global constants and thresholds used across indicators, signals, ranking, and risk.
  - Key constants: moving average periods, RSI/MACD/Bollinger thresholds, TTL cache values (`CACHE_TTL_SECONDS`), ranking weights and thresholds (e.g., `RSI_OVERSOLD`, `ADX_TRENDING`, `MIN_DATA_POINTS`, `GEMINI_API_KEY` env read).
  - Where to change values: Edit `config.py` for global, persistent defaults OR prefer runtime overrides (see below) for non-code edits.
  - Note: `GEMINI_API_KEY` is read from the environment—set `GEMINI_API_KEY` to enable AI features.

- `price_overrides.py` 🔸
  - Purpose: What-if price simulation manager. Allows setting per-symbol synthetic prices for scenario planning and backtesting.
  - Key API: `PriceOverrideManager.set_override(symbol, price)`, `.get_override()`, `.apply_override(df, symbol)`, `.clear_override()`.
  - Where to change values: call the manager at runtime (no code change required). Persistent overrides are not saved by default.

- `data.py` 🔸
  - Purpose: Market data fetching (`YFinanceDataFetcher`) + caching (`CachedDataFetcher`), retry/backoff logic, and analysis result caching (`AnalysisResultCache`).
  - Key classes: `YFinanceDataFetcher`, `CachedDataFetcher`, `AnalysisResultCache` and factory `create_data_fetcher()`.
  - Where to change values: `MAX_RETRY_ATTEMPTS`, `CACHE_TTL_SECONDS`, `MIN_DATA_POINTS` live in `config.py` (change there for global effect). For runtime behavior, instantiate `YFinanceDataFetcher(max_retries=..., backoff_seconds=...)` directly.

- `exceptions.py` 🔹
  - Purpose: Domain-specific exceptions (e.g., `DataFetchError`, `InsufficientDataError`, `RankingError`, `ConfigurationError`).
  - Where to change: Add exception types here if you need new error classes.

- `formatting.py` 🔹
  - Purpose: Text formatters used by the MCP server to prepare human-friendly output for tools and briefing.
  - Key functions: `format_analysis`, `format_comparison`, `format_screening`, `format_risk_analysis`, etc.
  - Where to change values: Edit output templates inside the functions to change displayed text/emoji.

- `indicators.py` 🔸
  - Purpose: Indicator implementations (SMA/EMA, RSI, MACD, Bollinger Bands, Stochastic, ADX, ATR, OBV, etc.).
  - Key functions: `calculate_all_indicators()`, `calculate_rsi()`, `calculate_macd()`, `calculate_adx()`, `calculate_atr()`.
  - Where to change values: Default periods and parameters are imported from `config.py` (change there for global behavior). You can call these functions with different parameters (e.g., `calculate_rsi(df, period=10)`).

- `models.py` 🔹
  - Purpose: Pydantic models for `Signal`, `Indicators`, `AnalysisResult`, and mutable builder `MutableSignal` used during detection.
  - Where to change: Change model fields here if you need different schema or serialization format.

- `ranking.py` 🔸
  - Purpose: Strategy implementations to score and rank signals (`RuleBasedRanking` and `GeminiRanking`) and convenience helpers.
  - Key points: `RuleBasedRanking._calculate_score()` uses `STRENGTH_SCORES` and `CATEGORY_BONUSES` from `config.py`. `GeminiRanking` uses `GEMINI_API_KEY` env var.
  - Where to change values: Update scoring constants in `config.py` or override ranking by passing a custom `RankingStrategy` to the `TechnicalAnalyzer`.

- `signals.py` 🔸
  - Purpose: Signal detectors for MA crossovers, RSI, MACD, Bollinger, Stochastic, Volume, and Trend signals.
  - Key classes: `MovingAverageSignalDetector`, `RSISignalDetector`, `MACDSignalDetector`, `BollingerBandSignalDetector`, `StochasticSignalDetector`, `VolumeSignalDetector`, `TrendSignalDetector`.
  - Where to change values: Uses thresholds from `config.py` (e.g., `RSI_OVERSOLD`, `VOLUME_SPIKE_2X`). Modify `config.py` or change detector logic here.

- `universes.py` 🔹
  - Purpose: Hard-coded universes (SP500, NASDAQ100, sector ETFs, crypto, custom lists) used by screen/scan tools.
  - Where to change values: Edit `UNIVERSES` here or add a new lookup/load method (e.g., to fetch refreshed lists from data source).

- `server.py` 🔸 (MCP server definitions)
  - Purpose: MCP Server tool definitions and endpoints (tools such as `analyze_security`, `compare_securities`, `screen_securities`, `get_trade_plan`, `scan_trades`, `portfolio_risk`, `morning_brief`, `analyze_fibonacci`).
  - Key items: MCP `Tool` definitions, handler implementations, helper utilities like `calculate_adaptive_tolerance()`.
  - Where to change values: Default tool inputs (e.g., tool `inputSchema` defaults), default limits such as `MAX_SIGNALS_RETURNED` come from `config.py`. For quick changes use environment variables or modify the handler defaults.


### Subdirectories

- `briefing/` 🔹
  - Files: `economic_calendar.py`, `market_status.py`, `morning_briefer.py`
  - Purpose: Compose morning market brief with macro events and aggregated signals.
  - Where to change values: The brief generator may have thresholds/timeframes—edit the module to change templates or what it includes.

- `momentum/` 🔹
  - Files: `calculator.py`, `signal_integration.py`
  - Purpose: Momentum measures, grouping into scoring contributions.
  - Where to change values: `MomentumConfig` values in `profiles/base_config.py` or `config.py`.

- `portfolio/` 🔹
  - Files: `portfolio_risk.py`, `sector_mapping.py`
  - Purpose: Per-position analysis and sector-level aggregation.
  - Where to change values: Position-sizing limits in `profiles/base_config.py` (e.g., `max_position_risk_pct`), and mapping in `sector_mapping.py`.

- `profiles/` 🔸
  - Files: `base_config.py`, `config_manager.py`, `risk_profiles.py`
  - Purpose: Centralized user config dataclasses (`UserConfig`), presets for `risky`, `neutral`, `averse`, and runtime config manager with validation.
  - Key APIs: `get_profile()`, `get_profile_with_overrides()`, `ConfigManager.get_config()`, `ConfigManager.set_session_override()`.
  - Where to change values: Update `risk_profiles.py` for new presets, or use `ConfigManager` to set session/user overrides without editing code.

- `risk/` 🔹
  - Files: risk rules, option rules, stop distance, volatility regime detectors, suppression logic.
  - Purpose: Produce trade plans, apply suppression rules (why a trade is invalid), calculate stops and risk metrics.
  - Where to change values: Change thresholds in `profiles/base_config.py` or `config.py`, or tune logic within the risk modules.

- `scanners/` 🔹
  - Files: `trade_scanner.py`
  - Purpose: Parallel scanning across a universe and collection of qualified trade plans.
  - Where to change values: Concurrency or scan limits are parameterized in the scanner class.

- `testing/` 🔹
  - Files: `scenarios.py`, `test_config.py`
  - Purpose: Unit/integration tests and configurable test scenarios. Good place to try parameter changes safely.

- Other utility modules: (`formatting.py`, `exceptions.py`) — see above.

---

## Easiest ways to change values (practical guidance) 💡

1) Runtime, temporary (no code change) — Session overrides (recommended):

```py
from technical_analysis_mcp.profiles.config_manager import get_config_manager
cm = get_config_manager()
# Per-request/session override
cm.set_session_override("session-123", "rsi_oversold", 28.0)
# Or pass overrides directly when getting a config
config = cm.get_config(session_overrides={"rsi_oversold": 28.0})
```
- Pros: No code change, safe, immediate effect.
- Use-case: Testing new thresholds, A/B testing profiles.

2) Runtime, per-user persistent (in-memory but intended to persist later):

```py
cm.save_user_preferences(user_id="alice", preferences={"min_rr_ratio": 1.8})
# Later, cm.get_config(user_id="alice") will apply saved overrides
```
- Pros: Per-user preferences; once DB persistence added it will become persistent.

3) Quick one-off simulations — Price overrides:

```py
from technical_analysis_mcp.price_overrides import get_price_override_manager
pom = get_price_override_manager()
pom.set_override("AAPL", 150.00)
# Use Pom.apply_override(df, 'AAPL') when analyzing to simulate
```
- Pros: Perfect for what-if scenarios and testing trade plans without modifying historical data.

4) Environment variables (for secrets or AI):

```bash
export GEMINI_API_KEY="your_api_key_here"
```
- Pros: No code changes, secure for CI/CD and production.

5) Global/persistent changes — edit code defaults (less recommended for quick tests):
- Modify `mcp-finance1/src/technical_analysis_mcp/config.py` for global constants (e.g., `RSI_OVERSOLD`, `CACHE_TTL_SECONDS`).
- Modify `profiles/risk_profiles.py` to change the presets used by `ConfigManager.get_profile()`.
- Pros: Direct, understandable change for long-term tuning.
- Cons: Requires code change and redeploying service.

6) Add a config file loader (recommended improvement):
- Add a simple JSON/TOML/YAML loader + merge into `ConfigManager` to allow altering defaults without code changes. This repo already has a `ConfigManager` — adding a `load_from_file()` helper is low-effort and recommended.

---

## Quick code recipes 🧾

- Apply a session override for `min_rr_ratio` and analyze:
```py
from technical_analysis_mcp import TechnicalAnalyzer
from technical_analysis_mcp.profiles.config_manager import get_config_manager
cm = get_config_manager()
cm.set_session_override("dev-session", "min_rr_ratio", 1.8)
# Analyze using TechnicalAnalyzer (ranking will pick up overrides when risk assessor uses the manager)
analyzer = TechnicalAnalyzer()
res = analyzer.analyze("AAPL")
```

- Simulate price and evaluate signals:
```py
from technical_analysis_mcp.price_overrides import get_price_override_manager
pom = get_price_override_manager()
pom.set_override("AAPL", 175.00)
# When fetching, call pom.apply_override(df, "AAPL") after receiving df
```

---

## Notes & recommendations (next steps) 🔭

- For non-developers, the most user-friendly approach is to expose a small API endpoint or a small admin CLI that uses `ConfigManager.set_session_override()` and `save_user_preferences()` so non-devs can tweak settings safely.
- Add a `config.yaml` loader and merge into default `UserConfig` on startup to avoid direct edits to `config.py`.
- Consider persisting `PriceOverrideManager` state to a small JSON file or Redis cache when users want persistent scenario sets.

---

If you'd like, I can:
1. Add a `docs/` improvements PR with `README` examples and a `config.yaml` loader, or
2. Create a short CLI `scripts/set-config` to set session overrides, or
3. Generate unit tests that demonstrate changing the most common thresholds (RSI, ATR, stop distances).

Which of the above would you like me to do next? ✅
