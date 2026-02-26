"""Cluster signal generators."""

from typing import List, Dict, Tuple

from .base import SignalGenerator
from ..core.models import FibonacciSignal, FibonacciLevel
from ..analysis.context import FibonacciContext


class ClusterSignals(SignalGenerator):
    """Detects Fibonacci level clusters and confluence zones."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        swing_data = ctx.get_swing_data()
        if not swing_data:
            return signals

        swing_range = swing_data['range']
        cluster_tolerance = swing_range * 0.02

        levels = ctx.get_fib_levels()

        # Group levels by price cluster
        price_clusters: Dict[float, List[FibonacciLevel]] = {}

        for level in levels.values():
            cluster_key = round(level.price / cluster_tolerance) * cluster_tolerance

            if cluster_key not in price_clusters:
                price_clusters[cluster_key] = []
            price_clusters[cluster_key].append(level)

        # Find clusters near current price
        tolerance = ctx.get_tolerance('wide')

        for cluster_price, cluster_levels in price_clusters.items():
            if len(cluster_levels) >= 2:
                if abs(ctx.close - cluster_price) / ctx.close < tolerance:
                    level_names = [l.name for l in cluster_levels]
                    level_types = set(l.fib_type.value for l in cluster_levels)

                    strength = (
                        'EXTREME' if len(cluster_levels) >= 4 else
                        'STRONG' if len(cluster_levels) >= 3 else
                        'SIGNIFICANT'
                    )

                    signals.append(FibonacciSignal(
                        signal=f"FIB CLUSTER {len(cluster_levels)} LEVELS",
                        description=f"Fibonacci confluence: {', '.join(level_names)}",
                        strength=strength,
                        category='FIB_CLUSTER',
                        timeframe=ctx.interval,
                        value=cluster_price,
                        metadata={
                            'cluster_count': len(cluster_levels),
                            'level_names': level_names,
                            'level_types': list(level_types)
                        }
                    ))

        return signals


class MultiTimeframeClusterSignals(SignalGenerator):
    """Detects clusters across multiple lookback windows."""

    def generate(self, ctx: FibonacciContext) -> List[FibonacciSignal]:
        signals = []

        if ctx.close is None:
            return signals

        windows = [20, 50, 100, 200]
        all_levels: List[Tuple[int, FibonacciLevel]] = []

        # Collect levels from all windows
        for window in windows:
            if window > len(ctx.df):
                continue
            levels = ctx.get_fib_levels(window)
            for level in levels.values():
                all_levels.append((window, level))

        # Find price levels that appear across multiple windows
        tolerance = ctx.get_tolerance('standard')
        price_groups: Dict[float, List[Tuple[int, FibonacciLevel]]] = {}

        for window, level in all_levels:
            # Round to cluster
            cluster_key = round(level.price / (ctx.close * tolerance)) * (ctx.close * tolerance)

            if cluster_key not in price_groups:
                price_groups[cluster_key] = []
            price_groups[cluster_key].append((window, level))

        # Find multi-window confluences near current price
        for cluster_price, group in price_groups.items():
            windows_in_cluster = set(w for w, _ in group)

            if len(windows_in_cluster) >= 2 and abs(ctx.close - cluster_price) / ctx.close < tolerance * 2:
                level_desc = [f"{l.name}({w}P)" for w, l in group[:5]]  # Limit description

                strength = (
                    'EXTREME' if len(windows_in_cluster) >= 3 else
                    'SIGNIFICANT'
                )

                signals.append(FibonacciSignal(
                    signal=f"FIB MTF CONFLUENCE {len(windows_in_cluster)} WINDOWS",
                    description=f"Multi-timeframe confluence: {', '.join(level_desc)}",
                    strength=strength,
                    category='FIB_MTF_CLUSTER',
                    timeframe=ctx.interval,
                    value=cluster_price,
                    metadata={
                        'windows': list(windows_in_cluster),
                        'total_levels': len(group)
                    }
                ))

        return signals
