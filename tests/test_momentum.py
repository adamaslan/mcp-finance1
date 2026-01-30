import yaml
import os
from scripts.backtests.momentum_backtest import run_momentum_backtest


def test_momentum_runs_and_writes_outputs(tmp_path):
    cfg = {
        'global': {
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'transaction_cost_bps': 1,
            'cache_dir': str(tmp_path / 'cache'),
            'random_seed': 123
        },
        'mcps': {
            'MCPTEST': {'universe': 'file://'+str(tmp_path / 'universe.csv')}
        },
        'backtests': [
            {'id': 'test_mom', 'type': 'momentum', 'apply_to': ['MCPTEST'], 'params': {'lookback': 20, 'top_n': 3, 'rebalance': 'monthly'}}
        ]
    }
    # write universe
    with open(str(tmp_path / 'universe.csv'),'w') as f:
        f.write('SPY\nQQQ\nDIA')

    cfg['backtests'][0]['params'].update({'starting_cash': 1000.0, 'fixed_fee': 1.0, 'max_position_pct': 0.5, 'slippage_pct': 0.001, 'save_plots': True})
    res = run_momentum_backtest(cfg, 'test_mom', 'MCPTEST')
    # ensure plot created
    outdir = res['outdir']
    assert os.path.exists(os.path.join(outdir, 'plots', 'equity.png'))
    assert 'run_id' in res
    outdir = res['outdir']
    assert os.path.exists(os.path.join(outdir, 'trades.csv'))
    assert os.path.exists(os.path.join(outdir, 'metrics.json'))


def test_transaction_cost_sweep_runs(tmp_path):
    import yaml
    from scripts.backtests.transaction_cost_sweep import run_transaction_cost_sweep
    cfg = {
        'global': {
            'start_date': '2020-01-01',
            'end_date': '2020-12-31',
            'transaction_cost_bps': 1,
            'random_seed': 42
        },
        'mcps': { 'MCPTEST': {'universe': 'file://'+str(tmp_path / 'universe.csv')}},
        'backtests': [ {'id': 'momentum_base', 'type':'momentum', 'apply_to':['MCPTEST'], 'params': {'lookback':20,'top_n':2, 'rebalance':'monthly'}},
                       {'id':'sweep','type':'sensitivity','apply_to':['MCPTEST'], 'params': {'base_test':'momentum_base','sweep_param':'transaction_cost_bps','values':[0,1]}}]
    }
    with open(str(tmp_path / 'universe.csv'),'w') as f:
        f.write('SPY\nQQQ')
    run_transaction_cost_sweep(cfg, 'sweep', 'MCPTEST')
    assert os.path.exists('outputs/transaction_cost_sweep_summary.csv')
