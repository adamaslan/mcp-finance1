#!/usr/bin/env python3
"""Demo: Portfolio sector breakdown with intelligent stop losses."""

import csv
from src.technical_analysis_mcp.portfolio.sector_mapping import get_sector, get_risk_level
from collections import defaultdict

def load_portfolio(csv_path: str) -> list[dict]:
    """Load portfolio from CSV."""
    positions = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            positions.append({
                "symbol": row["Ticker"],
                "shares": float(row["Shares"]),
                "current_price": float(row["Share Price ($)"]),
            })
    return positions

def calculate_stop_loss(current_price: float, risk_level: str) -> tuple[float, float]:
    """Calculate stop loss price and percentage based on risk level.

    Financial Risk Assessment:
    - LOW (2-3%): Blue-chip, stable earnings, long history
    - MODERATE (3-5%): Established with some volatility
    - HIGH (5-8%): Growth stocks, higher volatility
    """
    ranges = {
        "low": (2.0, 3.0),
        "moderate": (3.0, 5.0),
        "high": (5.0, 8.0),
    }

    min_pct, max_pct = ranges.get(risk_level, (3.0, 5.0))
    # Use mid-range for demo
    stop_pct = (min_pct + max_pct) / 2
    stop_price = current_price * (1 - stop_pct / 100)
    return stop_price, stop_pct

def main():
    """Run demo analysis."""
    print("Loading portfolio...")
    positions = load_portfolio("../portfolio.csv")
    print(f"✓ Loaded {len(positions)} positions\n")

    # Organize by sector
    sectors = defaultdict(list)
    total_value = 0
    total_max_loss = 0

    for pos in positions:
        sector = get_sector(pos["symbol"])
        risk_level = get_risk_level(pos["symbol"])

        current_price = pos["current_price"]
        shares = pos["shares"]
        current_value = current_price * shares

        stop_price, stop_pct = calculate_stop_loss(current_price, risk_level)
        max_loss = abs(current_price - stop_price) * shares

        sectors[sector].append({
            "symbol": pos["symbol"],
            "shares": shares,
            "current_price": current_price,
            "current_value": current_value,
            "risk_level": risk_level,
            "stop_price": stop_price,
            "stop_loss_percent": stop_pct,
            "max_loss_dollar": max_loss,
        })

        total_value += current_value
        total_max_loss += max_loss

    # Sort sectors
    sector_order = [
        "Information Technology",
        "Healthcare",
        "Financials",
        "Energy",
        "Consumer Discretionary",
        "Consumer Staples",
        "Industrials",
        "Materials",
        "Communication Services",
        "Utilities",
        "Real Estate",
        "Other",
    ]

    print("=" * 100)
    print("PORTFOLIO RISK ASSESSMENT - 11 SECTOR BREAKDOWN WITH INTELLIGENT STOPS")
    print("=" * 100)
    print(f"\n📊 PORTFOLIO SUMMARY")
    print(f"  Total Portfolio Value:  ${total_value:>15,.2f}")
    print(f"  Total Maximum Loss:     ${total_max_loss:>15,.2f}")
    print(f"  Risk as % of Portfolio:  {(total_max_loss/total_value*100) if total_value > 0 else 0:>14.2f}%")
    print()

    # Print each sector
    for sector_name in sector_order:
        if sector_name not in sectors:
            continue

        sector_positions = sectors[sector_name]
        sector_value = sum(p["current_value"] for p in sector_positions)
        sector_max_loss = sum(p["max_loss_dollar"] for p in sector_positions)
        sector_pct = (sector_value / total_value * 100) if total_value > 0 else 0

        # Risk distribution
        low_risk = sum(1 for p in sector_positions if p["risk_level"] == "low")
        moderate_risk = sum(1 for p in sector_positions if p["risk_level"] == "moderate")
        high_risk = sum(1 for p in sector_positions if p["risk_level"] == "high")

        print(f"┏━ {sector_name}")
        print(f"┃  💰 Value: ${sector_value:>12,.2f} ({sector_pct:>5.1f}% of portfolio)")
        print(f"┃  📍 Positions: {len(sector_positions):>2d}")
        print(f"┃  ⚠️  Max Loss: ${sector_max_loss:>11,.2f} ({(sector_max_loss/sector_value*100) if sector_value > 0 else 0:>5.2f}% of sector)")
        print(f"┃  🎯 Risk Mix: {low_risk} Low-Risk | {moderate_risk} Moderate-Risk | {high_risk} High-Risk")
        print(f"┃")

        # Show top 10 positions
        sorted_pos = sorted(sector_positions, key=lambda p: p["current_value"], reverse=True)
        for i, pos in enumerate(sorted_pos[:10], 1):
            symbol = pos["symbol"]
            shares = pos["shares"]
            price = pos["current_price"]
            value = pos["current_value"]
            stop = pos["stop_price"]
            stop_pct = pos["stop_loss_percent"]
            risk = pos["risk_level"].upper()

            pnl_per_stop = abs(price - stop) * shares

            print(f"┃  {i:2d}. {symbol:6s} {shares:8.2f} sh @ ${price:8.2f} = ${value:11,.2f}")
            print(f"┃      Stop: ${stop:8.2f} ({stop_pct:.1f}%) | Max Loss: ${pnl_per_stop:>10,.2f} | Risk: {risk:8s}")

        if len(sorted_pos) > 10:
            remaining = len(sorted_pos) - 10
            print(f"┃  ... and {remaining} more positions")

        print(f"┗━\n")

    # Summary table
    print("\n" + "=" * 100)
    print("SECTOR CONCENTRATION & RISK SUMMARY")
    print("=" * 100)
    print(f"{'Sector':<30} {'% Portfolio':>12} {'Positions':>10} {'Max Loss':>15} {'Avg Stop %':>12}")
    print("-" * 100)

    for sector_name in sector_order:
        if sector_name not in sectors:
            continue

        sector_positions = sectors[sector_name]
        sector_value = sum(p["current_value"] for p in sector_positions)
        sector_max_loss = sum(p["max_loss_dollar"] for p in sector_positions)
        sector_pct = (sector_value / total_value * 100) if total_value > 0 else 0
        avg_stop = sum(p["stop_loss_percent"] for p in sector_positions) / len(sector_positions)

        bar = "█" * int(sector_pct / 2)
        print(f"{sector_name:<30} {sector_pct:>11.2f}% {len(sector_positions):>10d} ${sector_max_loss:>14,.0f} {avg_stop:>11.1f}%  {bar}")

    print("-" * 100)
    print(f"{'TOTAL':<30} {100.0:>11.2f}% {len(positions):>10d} ${total_max_loss:>14,.0f}")
    print("=" * 100)

    # Risk level breakdown
    print(f"\n🎯 OVERALL RISK DISTRIBUTION:")
    all_positions_flat = [p for sector_pos in sectors.values() for p in sector_pos]
    low = sum(1 for p in all_positions_flat if p["risk_level"] == "low")
    moderate = sum(1 for p in all_positions_flat if p["risk_level"] == "moderate")
    high = sum(1 for p in all_positions_flat if p["risk_level"] == "high")

    total_pos = len(all_positions_flat)
    print(f"  Low-Risk:       {low:>3d} positions ({low/total_pos*100:>5.1f}%) - 2-3% stops")
    print(f"  Moderate-Risk:  {moderate:>3d} positions ({moderate/total_pos*100:>5.1f}%) - 3-5% stops")
    print(f"  High-Risk:      {high:>3d} positions ({high/total_pos*100:>5.1f}%) - 5-8% stops")

    print(f"\n✅ Analysis complete!")
    print(f"\nKey Insights:")
    print(f"  • Entry Price = Current Price (snapshot analysis)")
    print(f"  • Stop losses range from 2-8% based on financial risk assessment")
    print(f"  • Low-risk: Blue-chip, stable earnings (AAPL, MSFT, JNJ, etc.)")
    print(f"  • Moderate-risk: Established with volatility (ORCL, CSCO, etc.)")
    print(f"  • High-risk: Growth stocks, volatile (TSLA, META, NVDA, etc.)")

if __name__ == "__main__":
    main()
