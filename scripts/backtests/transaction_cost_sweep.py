"""Transaction cost sweep script — runs a base test across a set of transaction cost values and outputs a summary CSV"""
import yaml
import pandas as pd
from .momentum_backtest import run_momentum_backtest


def run_transaction_cost_sweep(cfg, bt_id, mcp=None):
    # find sweep params in backtests config
    bt = None
    for b in cfg.get('backtests', []):
        if b['id'] == bt_id:
            bt = b
            break
    if bt is None:
        raise KeyError(bt_id)
    params = bt.get('params', {})
    values = params.get('values', [0,1,5,10,20])
    base_test = params.get('base_test', 'momentum_standard')

    results = []
    for v in values:
        cfg2 = cfg.copy()
        cfg2['global'] = dict(cfg['global'])
        cfg2['global']['transaction_cost_bps'] = v
        out = run_momentum_backtest(cfg2, base_test, mcp or (cfg.get('mcps') and list(cfg['mcps'].keys())[0]))
        # load metrics
        import json
        with open(f"{out['outdir']}/metrics.json") as f:
            m = json.load(f)
        m['transaction_cost_bps'] = v
        m['run_id'] = out['run_id']
        results.append(m)

    df = pd.DataFrame(results)
    df.to_csv('outputs/transaction_cost_sweep_summary.csv', index=False)
    print('Sweep complete. results in outputs/transaction_cost_sweep_summary.csv')
