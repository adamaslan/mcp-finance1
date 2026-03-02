#!/usr/bin/env python3
"""Test script to run portfolio_risk with sector breakdown."""

import asyncio
import csv
import json
from pathlib import Path
from src.technical_analysis_mcp.portfolio.portfolio_risk import PortfolioRiskAssessor

async def load_portfolio(csv_path: str) -> list[dict]:
    """Load portfolio from CSV."""
    positions = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            positions.append({
                "symbol": row["Ticker"],
                "shares": float(row["Shares"]),
                "entry_price": float(row["Share Price ($)"]),
            })
    return positions

async def main():
    """Run portfolio risk assessment."""
    portfolio_path = Path("../portfolio.csv")
    if not portfolio_path.exists():
        print(f"❌ Portfolio not found at {portfolio_path}")
        return

    print("📊 Loading portfolio...")
    positions = await load_portfolio(portfolio_path)
    print(f"✓ Loaded {len(positions)} positions\n")

    print("⏳ Running portfolio risk assessment...")
    assessor = PortfolioRiskAssessor()
    result = await assessor.assess_positions(positions, period="1d")

    print("\n" + "=" * 80)
    print("PORTFOLIO RISK ASSESSMENT - SECTOR BREAKDOWN")
    print("=" * 80)

    print(f"\n📈 Portfolio Summary:")
    print(f"  Total Value:        ${result['total_value']:,.2f}")
    print(f"  Total Max Loss:     ${result['total_max_loss']:,.2f}")
    print(f"  Risk % of Portfolio: {result['risk_percent_of_portfolio']:.2f}%")
    print(f"  Overall Risk Level:  {result['overall_risk_level']}")
    print(f"  Timestamp:           {result['timestamp']}")

    print(f"\n🏦 SECTOR BREAKDOWN (11 SECTORS):\n")

    # Print sector-organized data
    sectors = result.get("sectors", {})
    for sector_name, sector_data in sectors.items():
        total_val = sector_data["total_value"]
        pct_portfolio = sector_data["percent_of_portfolio"]
        pos_count = sector_data["position_count"]
        hedge_etf = sector_data.get("hedge_etf", "N/A")

        metrics = sector_data.get("metrics", {})
        max_loss = metrics.get("total_max_loss_dollar", 0)
        max_loss_pct = metrics.get("max_loss_percent_of_sector", 0)
        avg_stop = metrics.get("avg_stop_loss_percent", 0)

        risk_dist = sector_data.get("risk_distribution", {})
        low = risk_dist.get("low_risk_count", 0)
        moderate = risk_dist.get("moderate_risk_count", 0)
        high = risk_dist.get("high_risk_count", 0)

        print(f"┌─ {sector_name}")
        print(f"│  Value: ${total_val:,.2f} ({pct_portfolio:.1f}% of portfolio)")
        print(f"│  Positions: {pos_count}")
        print(f"│  Max Loss: ${max_loss:,.2f} ({max_loss_pct:.2f}% of sector)")
        print(f"│  Avg Stop Loss: {avg_stop:.2f}%")
        print(f"│  Risk Distribution: {low} low / {moderate} moderate / {high} high")
        print(f"│  Hedge ETF: {hedge_etf}")

        # Show top 5 positions in this sector
        positions = sector_data.get("positions", [])[:5]
        for pos in positions:
            symbol = pos["symbol"]
            shares = pos["shares"]
            price = pos["current_price"]
            value = pos["current_value"]
            stop = pos["stop_level"]
            stop_pct = pos["stop_loss_percent"]
            risk = pos["risk_level"]

            print(f"│  • {symbol:6s} {shares:8.4f} sh @ ${price:8.2f} = ${value:10,.2f} [Stop: ${stop:8.2f} ({stop_pct:.1f}%) - {risk}]")

        if len(sector_data.get("positions", [])) > 5:
            extra = len(sector_data.get("positions", [])) - 5
            print(f"│  ... and {extra} more positions")

        print("└")
        print()

    # Sector concentration summary
    print(f"\n🎯 SECTOR CONCENTRATION:")
    concentration = result.get("sector_concentration", {})
    for sector, pct in sorted(concentration.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(pct / 2)
        print(f"  {sector:25s} {pct:6.2f}% {bar}")

    # Hedge suggestions
    suggestions = result.get("hedge_suggestions", [])
    if suggestions:
        print(f"\n🛡️  Hedge Suggestions:")
        for suggestion in suggestions:
            print(f"  • {suggestion}")

    # Save full results to JSON
    output_path = "portfolio_risk_sector_breakdown.json"
    with open(output_path, "w") as f:
        # Convert non-serializable items for JSON
        json.dump(result, f, indent=2, default=str)
    print(f"\n✓ Full results saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
