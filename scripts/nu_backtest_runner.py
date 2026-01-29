"""nu_backtest_runner.py — lightweight runner for backtests

Usage:
  python nu_backtest_runner.py run --config backtests.yml --id momentum_standard --mcp MCP1
  python nu_backtest_runner.py run-batch --config backtests.yml --ids momentum_standard,transaction_cost_sweep
"""
import argparse
import yaml
import os
from pathlib import Path
import sys
# ensure project package imports work when running the script directly
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.backtests.momentum_backtest import run_momentum_backtest
from scripts.backtests.transaction_cost_sweep import run_transaction_cost_sweep

OUT_DIR = Path('outputs')
OUT_DIR.mkdir(exist_ok=True)


def load_config(path):
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd')

    run = sub.add_parser('run')
    run.add_argument('--config', required=True)
    run.add_argument('--id', required=True)
    run.add_argument('--mcp', required=False)

    batch = sub.add_parser('run-batch')
    batch.add_argument('--config', required=True)
    batch.add_argument('--ids', required=True)

    args = p.parse_args()
    cfg = load_config(args.config)

    if args.cmd == 'run':
        bt_id = args.id
        # dispatch
        try:
            if bt_id.startswith('momentum'):
                res = run_momentum_backtest(cfg, bt_id, args.mcp)
            elif bt_id == 'transaction_cost_sweep':
                res = run_transaction_cost_sweep(cfg, bt_id, args.mcp)
            else:
                raise NotImplementedError(f'Backtest {bt_id} not implemented')
            if isinstance(res, dict):
                print(f"Run completed: {res.get('run_id')} -> {res.get('outdir')}")
        except Exception as e:
            print(f'Error running {bt_id}:', e)
            raise

    elif args.cmd == 'run-batch':
        for bt in args.ids.split(','):
            try:
                if bt.startswith('momentum'):
                    res = run_momentum_backtest(cfg, bt, None)
                elif bt == 'transaction_cost_sweep':
                    res = run_transaction_cost_sweep(cfg, bt, None)
                else:
                    print('skipping', bt)
                    continue
                if isinstance(res, dict):
                    print(f"Run completed: {res.get('run_id')} -> {res.get('outdir')}")
            except Exception as e:
                print(f"Backtest {bt} failed: {e}")
                # continue with next test
                continue

if __name__ == '__main__':
    main()
