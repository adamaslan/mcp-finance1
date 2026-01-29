"""Momentum backtest reference implementation using yfinance + caching.

Features:
- yfinance price loader with parquet cache
- simple monthly rebalancing momentum (top-n)
- supports weighting modes: equal, risk_parity
- transaction cost bps and slippage
- outputs: prices.parquet, trades.csv, metrics.json
"""
import os
from pathlib import Path
import pandas as pd
import numpy as np
import yfinance as yf
import json
from datetime import datetime

CACHE_DIR = Path('data/cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR = Path('outputs')
OUT_DIR.mkdir(exist_ok=True)


def cache_path_for_ticker(ticker):
    return CACHE_DIR / f"{ticker}.parquet"


def fetch_prices(tickers, start, end, interval='1d'):
    # fetch and cache per ticker
    prices = {}
    for t in tickers:
        pfile = cache_path_for_ticker(t)
        if pfile.exists():
            df = pd.read_parquet(pfile)
            # if cached range doesn't cover, fetch missing
            if df.index.min() <= pd.to_datetime(start) and df.index.max() >= pd.to_datetime(end):
                prices[t] = df.loc[start:end]['Adj Close']
                continue
        # download fresh
        df = yf.download(t, start=start, end=end, progress=False, threads=False)
        if df.empty:
            continue
        df = df[['Adj Close']]
        df.to_parquet(pfile)
        prices[t] = df['Adj Close']
    if not prices:
        raise RuntimeError('no prices fetched')
    panel = pd.concat(prices, axis=1)
    panel.columns = [c for c in panel.columns]
    panel = panel.sort_index()
    return panel


def compute_metrics(wealth_series):
    # wealth_series is a pd.Series of portfolio equity values indexed by date
    returns = wealth_series.pct_change().dropna()
    total_return = wealth_series.iloc[-1] / wealth_series.iloc[0] - 1
    years = (wealth_series.index[-1] - wealth_series.index[0]).days / 365.25
    cagr = (wealth_series.iloc[-1] / wealth_series.iloc[0]) ** (1/years) - 1
    ann_vol = returns.std() * np.sqrt(252)
    sharpe = returns.mean()/returns.std() * np.sqrt(252) if returns.std() > 0 else np.nan
    drawdown = (wealth_series / wealth_series.cummax() - 1).min()
    return dict(total_return=total_return, cagr=cagr, ann_vol=ann_vol, sharpe=sharpe, max_drawdown=drawdown)


def run_momentum_backtest(cfg, bt_id, mcp=None):
    # read config
    backtest_cfg = None
    for bt in cfg.get('backtests', []):
        if bt['id'] == bt_id:
            backtest_cfg = bt
            break
    if backtest_cfg is None:
        raise KeyError(bt_id)

    params = backtest_cfg.get('params', {})
    lookback = params.get('lookback', 90)
    top_n = params.get('top_n', 10)
    weighting = params.get('weighting', 'equal')
    rebalance = params.get('rebalance', 'monthly')
    start = cfg['global']['start_date']
    end = cfg['global']['end_date']
    transaction_cost_bps = cfg['global'].get('transaction_cost_bps', 5)

    # resolve universe
    mcps = cfg.get('mcps', {})
    if mcp is None:
        # choose first apply_to
        mcp = backtest_cfg.get('apply_to', [list(mcps.keys())[0]])[0]
    uni_spec = mcps[mcp]['universe']
    if uni_spec.startswith('file://'):
        ufile = uni_spec[len('file://'):]
        tickers = pd.read_csv(ufile, header=None).iloc[:,0].astype(str).tolist()
    else:
        # assume list
        tickers = params.get('tickers') or ['SPY','QQQ','DIA','IWM']

    print(f'Running {bt_id} for {mcp} on {len(tickers)} tickers')

    prices = fetch_prices(tickers, start, end)
    prices = prices.dropna(how='all', axis=1).ffill().dropna(axis=0, how='all')

    # build monthly rebalancing dates
    if rebalance == 'monthly':
        rebal_dates = prices.resample('M').apply(lambda x: x.index[-1])
        rebal_dates = rebal_dates.index
    elif rebalance == 'weekly':
        rebal_dates = prices.resample('W').apply(lambda x: x.index[-1]).index
    else:
        rebal_dates = prices.index

    # compute lookback returns per rebal date
    adj = prices
    returns = adj.pct_change(periods=lookback)

    trades = []
    cash = 1.0
    positions = {}
    equity = []
    current_weights = {}

    for i, d in enumerate(prices.index):
        if d not in rebal_dates and i != 0:
            # mark-to-market
            total = cash + sum(positions.get(t,0) * prices.loc[d, t] for t in positions)
            equity.append((d, total))
            continue
        # rebalance
        if d not in returns.index:
            continue
        todays = returns.loc[d].dropna().sort_values(ascending=False)
        longs = todays.index[:top_n].tolist()
        # compute weights
        if weighting == 'equal':
            w = {t: 1/top_n for t in longs}
        elif weighting == 'risk_parity':
            vol = adj.pct_change().rolling(lookback).std().loc[d, longs]
            inv_vol = 1/vol
            wvals = inv_vol / inv_vol.sum()
            w = dict(zip(longs, wvals))
        else:
            w = {t: 1/top_n for t in longs}

        # compute target positions (number of shares)
        total_nav = cash + sum(positions.get(t,0) * prices.loc[d, t] for t in positions)
        target_positions = {t: (w[t] * total_nav) / prices.loc[d, t] for t in w}

        # compute trades
        # sell everything not in targets
        for t in list(positions.keys()):
            if t not in target_positions:
                proceeds = positions[t] * prices.loc[d, t]
                cost = proceeds * (transaction_cost_bps/10000)
                cash += proceeds - cost
                trades.append(dict(date=str(d.date()), ticker=t, action='sell', shares=positions[t], price=float(prices.loc[d,t]), proceeds=float(proceeds-cost)))
                del positions[t]

        # buy/update
        for t, shares in target_positions.items():
            prev = positions.get(t, 0)
            delta = shares - prev
            if delta > 0:
                spend = delta * prices.loc[d, t]
                cost = spend * (transaction_cost_bps/10000)
                cash -= (spend + cost)
                trades.append(dict(date=str(d.date()), ticker=t, action='buy', shares=float(delta), price=float(prices.loc[d,t]), cost=float(cost)))
            elif delta < 0:
                proceeds = -delta * prices.loc[d,t]
                cost = proceeds * (transaction_cost_bps/10000)
                cash += (proceeds - cost)
                trades.append(dict(date=str(d.date()), ticker=t, action='sell', shares=float(-delta), price=float(prices.loc[d,t]), proceeds=float(proceeds-cost)))
            positions[t] = shares

        total = cash + sum(positions.get(t,0) * prices.loc[d,t] for t in positions)
        equity.append((d, total))

    equity_series = pd.Series({d: val for d, val in equity}).sort_index()

    metrics = compute_metrics(equity_series)

    run_id = f"{bt_id}_{mcp}_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    outdir = OUT_DIR / run_id
    outdir.mkdir(exist_ok=True)

    prices.to_parquet(outdir / 'prices.parquet')
    pd.DataFrame(trades).to_csv(outdir / 'trades.csv', index=False)
    with open(outdir / 'metrics.json','w') as f:
        json.dump(metrics, f, indent=2)

    print('Done. Metrics:', metrics)
    return dict(run_id=run_id, outdir=str(outdir))


if __name__ == '__main__':
    import yaml
    cfg = yaml.safe_load(open('backtests.yml'))
    run_momentum_backtest(cfg, 'momentum_standard', 'MCP1')
