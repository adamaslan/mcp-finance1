# Technical Indicators & Signals Review

This document reviews the current indicator and signal architecture in this repository and proposes concrete improvements and additional signals/events, with emphasis on Fibonacci-, MACD-, RSI-, and Bollinger Band–based logic.

## 1. Architecture Overview

- **Indicator engine**: `mcp-finance1/src/technical_analysis_mcp/indicators.py`
  - Pure pandas/NumPy functions that compute all indicators and orchestrate them via `calculate_all_indicators` and `calculate_indicators_dict` (`indicators.py:322` and `indicators.py:352`).
- **Signal engine**: `mcp-finance1/src/technical_analysis_mcp/signals.py`
  - A set of detector classes (MA, RSI, MACD, Bollinger, Stochastic, Volume, Trend/ADX, Price Action) implementing a `SignalDetector` protocol and orchestrated by `detect_all_signals` (`signals.py:456`).
- **CLI-style skills**:
  - `/indicators` skill: `.claude/skills/indicators.md` – dashboard-style indicator display.
  - `/signals` skill: `.claude/skills/signals.md` – watchlist-wide signal report using `detect_all_signals`.

Overall, the split between **calculation**, **signal detection**, and **presentation** is clean and extensible.

---

## 2. Existing Indicator Set

All indicators are calculated from OHLCV data via `calculate_all_indicators(df)` (`indicators.py:322`). Below is a categorized review.

### 2.1 Moving Averages & Distance

- **Functions**:
  - `calculate_sma` / `calculate_ema` (`indicators.py:31`, `indicators.py:44`)
  - `calculate_moving_averages` (`indicators.py:57`) for `MA_PERIODS = (5, 10, 20, 50, 100, 200)` (`config.py:24`)
  - `calculate_distance_from_ma` (`indicators.py:299`)
- **Strengths**:
  - Broad MA set (short → long term) suitable for multi-horizon analysis.
  - Distance-from-MA (% terms) enables normalized overextension measures.
- **Improvement ideas**:
  - Add **EMA-only distance metrics** (e.g., `Dist_EMA_20`) for faster reaction in momentum names.
  - Add **relative MA slope** (e.g., 10-day slope of SMA20/SMA50) to quantify trend steepness instead of just alignment.
  - Support **configurable MA sets per use-case** (swing vs position vs intraday) via an optional parameter or configuration profile rather than a fixed global tuple.

### 2.2 RSI

- **Function**: `calculate_rsi` (`indicators.py:77`), period from `RSI_PERIOD` (`config.py:25`).
- **Implementation**:
  - Uses price differences, separating positive/negative moves, with rolling means and a small epsilon to avoid divide-by-zero in strong uptrends.
- **Strengths**:
  - Robust to zero-loss periods.
  - Standard 14-period setting with clear thresholds in config (`config.py:98–102`).
- **Improvement ideas**:
  - Add **RSI moving average** (e.g., 5-period SMA of RSI) to smooth choppy names.
  - Track **RSI range regime** (e.g., `RSI > 40` and `< 80` for bull ranges, `RSI < 60`/`> 20` for bear ranges) to distinguish trend states instead of using only static 30/70 thresholds.
  - Pre-compute **RSI 50-line cross flags** (above/below 50) to simplify trend confirmation signals.

### 2.3 MACD

- **Function**: `calculate_macd` (`indicators.py:104`) with `MACD_FAST`, `MACD_SLOW`, `MACD_SIGNAL` (`config.py:26–28`).
- **Outputs**: `MACD`, `MACD_Signal`, `MACD_Hist` (`indicators.py:126–128`).
- **Strengths**:
  - Standard MACD implementation with histogram, suitable for momentum and trend strength analysis.
  - MACD values are exported via `calculate_indicators_dict` (`indicators.py:373–378`).
- **Improvement ideas**:
  - Pre-compute **MACD histogram slope** (e.g., 3-period difference of `MACD_Hist`) for early momentum inflection detection.
  - Optionally expose **MACD as a z-score** of its own 6–12 bar history to standardize across symbols.
  - Consider a **“fast MACD” profile** (e.g., 6/13/5) for more aggressive, short-term scanning.

### 2.4 Bollinger Bands

- **Function**: `calculate_bollinger_bands` (`indicators.py:134`) using `BOLLINGER_PERIOD`, `BOLLINGER_STD` (`config.py:29–30`).
- **Outputs**: `BB_Middle`, `BB_Upper`, `BB_Lower`, `BB_Width` (`indicators.py:151–157`).
- **Strengths**:
  - Standard implementation with width metric for volatility/squeeze analyses.
  - Used by Bollinger signal detector for band touches.
- **Notable issue**:
  - In `calculate_indicators_dict`, the mid-band is referenced as `BB_Mid` (`indicators.py:391–392`), but the column name is `BB_Middle`. This means `bb_mid` is never set in the exported dictionary. Harmonizing this naming would fix downstream dashboards.
- **Improvement ideas**:
  - Add **Bollinger %b** (`(Close - BB_Lower) / (BB_Upper - BB_Lower)`) as a normalized location metric.
  - Add **BB_Width percentile** vs its own 6–12 month history to objectively define “squeeze” vs “normal” vs “expanded” regimes.

### 2.5 Stochastic Oscillator

- **Function**: `calculate_stochastic` (`indicators.py:162`), with `Stoch_K` and `Stoch_D` outputs (`indicators.py:182–183`).
- **Strengths**:
  - Classic high/low channel-based oscillator with smoothing.
- **Improvement ideas**:
  - Add **%K vs %D cross flags** (e.g., boolean columns for `k_cross_up`, `k_cross_down`) to simplify signal layer logic.
  - Consider a **slow stochastic variant** (3-period smoothed %K before %D) for less noisy signals.

### 2.6 ADX, ATR, and Trend/Volatility Metrics

- **Functions**:
  - `calculate_adx` (`indicators.py:189`) gives `ADX`, `Plus_DI`, `Minus_DI`.
  - `calculate_atr` (`indicators.py:226`) gives `ATR`.
- **Strengths**:
  - ADX/DI and ATR are correctly computed from true ranges and directional moves.
  - Config exposes thresholds for trend regimes (`ADX_TRENDING`, `ADX_STRONG_TREND`, `config.py:113–115`) and for volatility regimes in the risk layer (`config.py:123–125`).
- **Improvement ideas**:
  - Use **Wilder-style smoothing** (EMA on ranges and DM) to better match canonical ADX behavior.
  - Pre-compute **ATR% of price** and/or **volatility regime flags** (LOW/NORMAL/HIGH) directly in `indicators.py` so they can be used by signals without duplicating logic.

### 2.7 Volume Indicators

- **Function**: `calculate_volume_indicators` (`indicators.py:251`).
- **Outputs**: `Volume_MA_20`, `Volume_MA_50`, `OBV` (`indicators.py:268–272`).
- **Strengths**:
  - Provides short and long volume averages plus OBV for accumulation/distribution.
- **Improvement ideas**:
  - Add **relative volume** columns (e.g., `Vol_Ratio_20 = Volume / Volume_MA_20`) instead of computing that ad hoc only inside `calculate_indicators_dict` (`indicators.py:415–420`).
  - Add **OBV moving average** and **OBV slope** to explicitly label accumulation/ distribution trends.

### 2.8 Price Change & Volatility

- **Function**: `calculate_price_changes` (`indicators.py:277`).
- **Outputs**: `Price_Change` (1-day), `Price_Change_5d`, and annualized `Volatility` (`indicators.py:288–293`).
- **Strengths**:
  - Provides both single-day and 5-day percentage moves, plus annualized volatility.
- **Improvement ideas**:
  - Add **gap size** (today’s open vs prior close) and classify gap up/down/magnitude.
  - Provide **rolling max/min 20–50d returns** to contextualize current moves.

---

## 3. Existing Signal Detectors

Signals are detected via dedicated detector classes and orchestrated with `detect_all_signals(df)` (`signals.py:456`). Each detector consumes the indicator DataFrame and returns `MutableSignal` objects (`signals.py:33`, `signals.py:438–452`).

### 3.1 Moving Average Signals

- **Detector**: `MovingAverageSignalDetector` (`signals.py:45`).
- **Signals**:
  - **Golden Cross / Death Cross**: 50 SMA vs 200 SMA (`signals.py:75–93`).
  - **Price cross vs SMA20**: price crossing above/below SMA20 (`signals.py:106–124`).
  - **MA alignment**: 10 > 20 > 50 bullish, 10 < 20 < 50 bearish (`signals.py:132–154`).
- **Strengths**:
  - Captures both major regime shifts (50/200 cross) and shorter-term price/MA interactions.
  - MA alignment acts as a concise proxy for trend quality.
- **Improvement ideas**:
  - Add **20/50 cross** signals (faster than 50/200) and classify them as “intermediate trend shift”.
  - Require a **minimum separation** (e.g., percentage distance between MAs) to avoid whipsaws during chop.
  - Combine with **ADX filter** (e.g., only flag new MA trend signals when ADX is below 20 and then rising through 25) to identify genuine new trends.

### 3.2 RSI Signals

- **Detector**: `RSISignalDetector` (`signals.py:159`).
- **Signals**:
  - `RSI EXTREME OVERSOLD` when `RSI < RSI_EXTREME_OVERSOLD` (`signals.py:171–179`).
  - `RSI OVERSOLD` when `RSI < RSI_OVERSOLD` (`signals.py:180–188`).
  - `RSI OVERBOUGHT` when `RSI > RSI_OVERBOUGHT` (`signals.py:190–198`).
- **Strengths**:
  - Clean separation between “oversold” and “extreme oversold” for position sizing/priority.
- **Improvement ideas (RSI-focused)**:
  - Add **RSI 50-line cross** events (up/down) as trend confirmation/negation.
  - Track **RSI range shift** (e.g., prior 50 bars mostly above 40 vs mostly below 60) to distinguish bull vs bear regimes and filter oversold/overbought signals accordingly.
  - Add **RSI exit events**: oversold → back above 30, overbought → back below 70, which often mark more actionable entries than the extreme itself.

### 3.3 MACD Signals

- **Detector**: `MACDSignalDetector` (`signals.py:203`).
- **Signals**:
  - `MACD BULL CROSS` / `MACD BEAR CROSS` when MACD crosses its signal line (`signals.py:219–237`).
  - `MACD ZERO CROSS UP` / `MACD ZERO CROSS DOWN` when MACD crosses the zero line (`signals.py:239–257`).
- **Strengths**:
  - Covers the canonical MACD signal set: signal-line crossovers and zero-line transitions.
- **Improvement ideas (MACD-focused)**:
  - Add **MACD histogram momentum** events: histogram turning positive/negative and/or its slope turning up/down after extended moves.
  - Introduce **“MACD + trend filter”** events where bullish MACD crosses only fire when price is above SMA50/200 and ADX is in a trending regime.
  - Implement **MACD “zero-line rejection”** events (MACD approaches but fails to cross zero and turns back in trend direction).

### 3.4 Bollinger Band Signals

- **Detector**: `BollingerBandSignalDetector` (`signals.py:262`).
- **Signals**:
  - `AT LOWER BB` when price is at or slightly below the lower band (`signals.py:277–285`).
  - `AT UPPER BB` when price is at or slightly above the upper band (`signals.py:287–295`).
- **Strengths**:
  - Implements straightforward mean-reversion style triggers at band extremes.
- **Gap vs documentation**:
  - Skill docs mention **squeeze** detection (`.claude/skills/signals.md:98`), but the current detector does not yet implement squeezes.
- **Improvement ideas (Bollinger-focused)**:
  - Implement **Bollinger Squeeze** events where `BB_Width` is in, for example, the lowest 10–20% percentile of its 6–12 month history.
  - Implement **Squeeze Breakout** events: squeeze regime followed by a decisive close outside the bands (optionally with a volume spike and ADX increasing).
  - Add **Band Walk** events (price hugging upper or lower band for multiple bars in a strong trend) as continuation signals, filtered by ADX.
  - Incorporate **Bollinger %b** in signals to make rules robust across symbols with different volatility.

### 3.5 Stochastic Signals

- **Detector**: `StochasticSignalDetector` (`signals.py:300`).
- **Signals**:
  - `STOCHASTIC OVERSOLD` for `Stoch_K < STOCH_OVERSOLD` (`signals.py:312–320`).
  - `STOCHASTIC OVERBOUGHT` for `Stoch_K > STOCH_OVERBOUGHT` (`signals.py:322–330`).
- **Strengths**:
  - Captures classic overbought/oversold readings.
- **Improvement ideas**:
  - Add **K/D cross** signals with zone context (e.g., `K` crossing above `D` while both are below 20 as a higher-quality oversold reversal trigger).
  - Filter signals by **trend regime** (e.g., only take oversold signals in uptrends where price above SMA50 and ADX trending).

### 3.6 Volume Signals

- **Detector**: `VolumeSignalDetector` (`signals.py:335`).
- **Signals**:
  - `EXTREME VOLUME 3X` for volume > 3× 20-day average (`signals.py:352–360`).
  - `VOLUME SPIKE 2X` for volume > 2× 20-day average (`signals.py:361–369`).
- **Strengths**:
  - Differentiates between strong and very strong volume anomalies.
- **Gap vs documentation**:
  - Skill docs reference **“Drying Up”** volume (`signals.md:100`), but this condition is not implemented yet.
- **Improvement ideas**:
  - Add **Low Volume / Dry-Up** signals when volume < 0.5× average (`MIN_VOLUME_RATIO`, `config.py:152`).
  - Add **climactic volume** detection where volume is, for example, > 4–5× average and the bar is a reversal candle (large tail vs body), as potential exhaustion signals.
  - Incorporate **OBV trend** (rising/falling) into volume-based confirmation signals.

### 3.7 Trend (ADX) Signals

- **Detector**: `TrendSignalDetector` (`signals.py:374`).
- **Signals**:
  - `STRONG UPTREND` / `STRONG DOWNTREND` when `ADX > ADX_TRENDING` and price relative to SMA50 determines direction (`signals.py:389–397`).
- **Strengths**:
  - Provides a clean “trending vs non-trending” label.
- **Gaps & improvements**:
  - Config defines **multiple ADX thresholds** (`ADX_TRENDING`, `ADX_STRONG_TREND`, `config.py:113–115`; and risk-layer thresholds `config.py:141–143`), but only one threshold is used. Consider differentiating **emerging trend**, **strong trend**, and **no trend**.
  - Add **DI+/- crossover-based signals** (trend direction transitions) and categorize them under `SignalCategory.ADX` instead of or in addition to `TREND`.

### 3.8 Price Action Signals

- **Detector**: `PriceActionSignalDetector` (`signals.py:403`).
- **Signals**:
  - `LARGE GAIN` for 1-day move > `LARGE_MOVE_PERCENT` (`signals.py:415–423`).
  - `LARGE LOSS` for 1-day move < `-LARGE_MOVE_PERCENT` (`signals.py:425–433`).
- **Strengths**:
  - Captures single-bar momentum/extreme moves.
- **Gap vs documentation**:
  - Skill docs advertise **gap up/down** and **other price patterns** (`signals.md:100–101`), but current implementation only checks percentage moves.
- **Improvement ideas**:
  - Add **gap detection** using open vs prior close; classify gap up/down and large gap thresholds.
  - Add **multi-day breakout/breakdown** events: closes above recent 20/50-day highs or below recent lows.
  - Add **inside bars / NR4–NR7** patterns to identify contraction before expansion.

---

## 4. Inconsistencies vs Documentation

The `.claude/skills` docs describe a richer signal set than is currently implemented.

- **Bollinger Squeeze**: Mentioned as a signal type (`signals.md:98`), but not yet implemented in `BollingerBandSignalDetector`.
- **RSI / MACD Divergence**: Docs list divergence for RSI/MACD, but there is no divergence logic in `signals.py`.
- **Volume Dry-Up**: Listed in docs (`signals.md:100`), but only spikes are implemented.
- **Gap Up / Gap Down**: Listed in docs (`signals.md:101–102`), but current `PriceActionSignalDetector` only checks `Price_Change`.
- **Bollinger Middle Band Naming**: `BB_Middle` vs `BB_Mid` mismatch in `calculate_indicators_dict` (see §2.4) leads to missing mid-band in exported indicator dict.

Addressing these gaps will align the implementation with the advertised feature set.

---

## 5. Proposed New Signals & Events

This section focuses on concrete, high-value additions around Fibonacci, MACD, RSI, and Bollinger Bands, plus cross-indicator composites. All proposals are formulated so they can be implemented as new `SignalDetector` classes without breaking existing behavior.

### 5.1 Fibonacci-Based Signals

**Goal**: Capture pullbacks to key retracement levels and breakout/extension behavior.

**Inputs**:

- Recent swing high/low over a configurable lookback (e.g., 20–60 bars).
- Close price and optionally volume and trend context (ADX/MA alignment).

**Proposed logic**:

1. **Swing detection** (simplified):
   - For a lookback window `N`, compute `swing_low = rolling_min(Low, N)` and `swing_high = rolling_max(High, N)`.
   - Determine whether current context is more “up-leg” or “down-leg” based on price relative to MAs and/or DI+/-.
2. **Retracement levels**:
   - For an up-leg: levels at 38.2%, 50%, 61.8% of `swing_low → swing_high`.
   - For a down-leg: levels at 38.2%, 50%, 61.8% of `swing_high → swing_low`.
3. **Signals**:
   - **FIBONACCI RETRACEMENT HOLD (BULLISH)**
     - Price pulls back into 38.2–61.8% zone and shows:
       - Close above level, or
       - Long lower wick (close near high of day) with volume spike.
   - **FIBONACCI RETRACEMENT BREAK (BEARISH)**
     - Price closes decisively below 61.8% after an up-leg (or above 61.8% after a down-leg) – potential trend failure.
   - **FIBONACCI EXTENSION TARGET HIT**
     - Price reaches 100% or 161.8% extension from prior swing; use as profit-taking or risk-management events.

**Implementation notes**:

- Implement as `FibonacciSignalDetector`, using precomputed swing/level columns (added in `indicators.py`) to keep detectors simple.
- Optional filters:
  - Only fire retracement signals when ADX is already in a trending regime and `Price_Change_5d` is aligned with the trend.
  - Require confirmation from MACD histogram (e.g., turning back in trend direction) or RSI (staying in bull/bear range).

### 5.2 Enhanced MACD Signals

**Goal**: Turn MACD from simple crossovers into a richer momentum regime detector.

**Additional events**:

- **MACD MOMENTUM SURGE**
  - `MACD_Hist` crosses above a small positive threshold and its slope (difference vs prior bar) is positive for 2–3 bars.
  - Filter: price above SMA50 and ADX trending.
- **MACD MOMENTUM FADE / EXHAUSTION**
  - `MACD_Hist` has been positive and rising, then turns down and makes a lower high while price makes a higher high.
  - This approximates **bearish momentum divergence**.
- **MACD ZERO-LINE REJECTION**
  - MACD approaches zero but turns back in the direction of the prevailing trend without crossing zero.
  - Useful for identifying **trend continuation** entries.

**Implementation notes**:

- Add small helper columns in `indicators.py` (e.g., `MACD_Hist_Diff`) and then implement new events in a `MACDAdvancedSignalDetector` while keeping the existing `MACDSignalDetector` intact for backwards compatibility.

### 5.3 Enhanced RSI Signals

**Goal**: Use RSI as a **trend regime and reversal-quality** tool, not just an overbought/oversold flag.

**Additional events**:

- **RSI RANGE SHIFT (BULLISH/BEARISH)**
  - Bullish range: majority of last 50 bars have `RSI > 40` and peaks near 80.
  - Bearish range: majority of last 50 bars have `RSI < 60` and troughs near 20.
- **RSI 50-LINE CROSS (TREND CONFIRMATION)**
  - RSI crosses above 50 after exiting oversold; label as **trend confirmation** rather than initial signal.
- **RSI EXIT OVERSOLD / EXIT OVERBOUGHT**
  - RSI moves back above 30 from below, or back below 70 from above; often better-timed entries/exits than initial extremes.
- **RSI SIMPLE DIVERGENCE** (optional advanced feature)
  - Price makes a lower low while RSI makes a higher low (bullish divergence) or vice versa.

**Implementation notes**:

- Add smoothed RSI or rolling stats (e.g., proportion of bars > 50) in `indicators.py` to avoid recalculating via loops inside detectors.
- Implement a new `RSIAdvancedSignalDetector` that consumes these columns and outputs higher-confidence regime and divergence events.

### 5.4 Enhanced Bollinger Band Signals

**Goal**: Leverage bands for both **mean reversion** and **volatility regime** detection.

**Additional events**:

- **BOLLINGER SQUEEZE**
  - `BB_Width` below a percentile threshold (e.g., 10–20%) of its historical distribution.
  - Optional flag for **“squeeze duration”** (number of bars in low-width regime).
- **SQUEEZE BREAKOUT (BULLISH/BEARISH)**
  - A breakout close outside bands following a squeeze, confirmed by:
    - Volume spike (e.g., > 1.5–2× average), and
    - ADX rising through 20–25.
- **BAND WALK CONTINUATION**
  - Multiple closes near or above the upper band (or near/below the lower band) with ADX in strong trend territory.
  - Label as **trend continuation signals** rather than reversals.
- **MEAN-REVERSION + TREND FILTER**
  - Only flag `AT LOWER BB` buy signals when price is above SMA200 (pullback in an uptrend).
  - Only flag `AT UPPER BB` sell signals when price is below SMA200 (rallies in downtrends).

**Implementation notes**:

- Add `BB_Width_PctRank` or similar metric in `indicators.py` using a rolling-window percentile.
- Extend `BollingerBandSignalDetector` or introduce `BollingerAdvancedSignalDetector` to handle squeeze and breakout logic separately.

### 5.5 Composite Multi-Indicator Signals

Beyond individual indicator enhancements, the existing infrastructure and `SignalStrength`/`SignalCategory` enums (`config.py:52–78`) support higher-level **composite signals**.

Examples:

- **TREND + MOMENTUM ALIGNMENT (BULLISH)**
  - Conditions:
    - Price above SMA50 and SMA200.
    - ADX > 25 (trending) and rising.
    - MACD > 0 and MACD histogram positive.
    - RSI between 50 and 70 (bullish, but not overbought).
  - Use as a high-confidence **trend continuation** signal with `SignalStrength.STRONG_BULLISH`.

- **REVERSAL WITH CONFIRMATION (BULLISH)**
  - Conditions:
    - Price touches/breaks slightly below lower Bollinger band.
    - RSI exiting oversold area (> 30) and curling up.
    - Volume spike > 1.5–2× average.
  - This can be categorized under a new composite category (e.g., `SignalCategory.PRICE_ACTION` or a dedicated composite enum).

- **EXHAUSTION TOP/BOTTOM**
  - Conditions (top example):
    - Large positive day (`Price_Change` >> `LARGE_MOVE_PERCENT`).
    - Price closing above upper Bollinger band.
    - Volume extreme (3–4× average).
    - MACD histogram flattening or turning down.
  - Label as high-risk **exhaustion** setup; primarily for risk trimming, not shorting in isolation.

These composite conditions can be implemented as additional detectors that simply read existing indicator columns, without changing the calculation layer.

---

## 6. Prioritized Implementation Roadmap

To incrementally enhance the system while maintaining stability:

1. **Fix naming and documentation gaps**
   - Harmonize `BB_Middle` vs `BB_Mid` in `calculate_indicators_dict`.
   - Align signal categories and types between `signals.py` and `.claude/skills/signals.md` (e.g., add missing types or adjust docs).

2. **Extend existing detectors with low-risk enhancements**
   - Add volume dry-up, basic gap detection, and simple ADX multi-threshold logic.
   - Introduce RSI 50-line cross and Bollinger mean-reversion + trend filter rules.

3. **Add advanced detectors for new capabilities**
   - Implement separate `*AdvancedSignalDetector` classes for RSI, MACD, Bollinger, and Fibonacci to keep the base detectors simple and backwards compatible.

4. **Introduce composite signals and scoring refinements**
   - Leverage `STRENGTH_SCORES` and `CATEGORY_BONUSES` (`config.py:80–94`) to assign higher scores to composite, well-confirmed setups.

5. **Optional future work**
   - Add multi-timeframe variants (daily vs weekly) by running the same indicator/signal engine on multiple datasets and detecting alignment or conflict.

Implementing the above will significantly improve the **depth**, **reliability**, and **expressiveness** of the technical signals while staying consistent with the existing architecture and documentation.

