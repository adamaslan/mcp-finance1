#!/usr/bin/env python3
"""Generate economist-focused visualizations from industry performance data.

Creates 3 key graphs:
1. Sector Rotation Heatmap - Momentum across all industries
2. Economic Cycle Dashboard - Cyclical vs Defensive indicators
3. Correlation Matrix - Industry relationships

Usage:
    python scripts/visualize_industry_data.py --days 90

Output:
    - graphs/sector_rotation_heatmap.png
    - graphs/economic_cycle_dashboard.png
    - graphs/correlation_matrix.png
    - graphs/analysis_summary.md
"""

import asyncio
import logging
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent))  # For scripts
sys.path.insert(0, str(Path(__file__).parent.parent / "cloud-run" / "src"))  # For technical_analysis_mcp

from build_historical_industry_data import HistoricalDataBuilder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class IndustryDataVisualizer:
    """Generate economist-focused visualizations."""

    # Sector classifications
    CYCLICAL_INDUSTRIES = [
        "Software", "Semiconductors", "Cloud Computing", "Artificial Intelligence",
        "Automotive", "Construction", "Homebuilders", "Retail", "E-Commerce",
        "Restaurants", "Luxury Goods", "Aerospace & Defense", "Transportation",
    ]

    DEFENSIVE_INDUSTRIES = [
        "Utilities", "Consumer Staples", "Pharmaceuticals", "Healthcare Providers",
        "Managed Care", "Insurance", "REITs", "Telecommunications",
    ]

    FINANCIAL_INDUSTRIES = [
        "Banks", "Regional Banks", "Insurance", "Asset Management", "Fintech", "Payments",
    ]

    COMMODITY_INDUSTRIES = [
        "Oil & Gas", "Renewable Energy", "Mining", "Steel", "Chemicals", "Agriculture",
    ]

    def __init__(self, output_dir: str = "graphs"):
        """Initialize visualizer.

        Args:
            output_dir: Directory to save graphs.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams["figure.figsize"] = (14, 8)
        plt.rcParams["font.size"] = 10

    async def generate_all_graphs(
        self,
        data: dict[str, list[dict]],
    ) -> dict:
        """Generate all 3 economist-focused graphs.

        Args:
            data: Dict mapping date → list of industry performance dicts.

        Returns:
            Dict with file paths and analysis summary.
        """
        logger.info("Generating 3 economist-focused visualizations...")

        # Convert to DataFrame
        df = self._prepare_dataframe(data)

        if df.empty:
            logger.error("No data to visualize")
            return {"error": "No data"}

        logger.info("Data shape: %s", df.shape)

        # Generate graphs
        graph1 = await self._create_sector_rotation_heatmap(df)
        graph2 = await self._create_economic_cycle_dashboard(df)
        graph3 = await self._create_correlation_matrix(df)

        # Generate analysis summary
        analysis = self._generate_analysis_summary(df)

        return {
            "graphs": [graph1, graph2, graph3],
            "analysis_file": self.output_dir / "analysis_summary.md",
            "analysis": analysis,
        }

    def _prepare_dataframe(
        self,
        data: dict[str, list[dict]],
    ) -> pd.DataFrame:
        """Convert historical snapshots to DataFrame.

        Args:
            data: Dict mapping date → industry snapshots.

        Returns:
            DataFrame with columns: date, industry, 1m_return, 3m_return, etc.
        """
        records = []

        for date_str, industries in data.items():
            for ind_data in industries:
                industry = ind_data.get("industry")
                returns = ind_data.get("returns", {})

                # Extract key horizons
                record = {
                    "date": date_str,
                    "industry": industry,
                    "2w": returns.get("2w"),
                    "1m": returns.get("1m"),
                    "3m": returns.get("3m"),
                    "52w": returns.get("52w"),
                }

                records.append(record)

        df = pd.DataFrame(records)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date")

        logger.info("Prepared DataFrame with %d rows", len(df))
        return df

    async def _create_sector_rotation_heatmap(self, df: pd.DataFrame) -> str:
        """Graph 1: Sector Rotation Heatmap.

        Shows 1-month returns for all industries over time as a heatmap.
        Hot colors = outperforming, cold colors = underperforming.

        Args:
            df: Historical industry DataFrame.

        Returns:
            Path to saved graph.
        """
        logger.info("Creating sector rotation heatmap...")

        # Pivot data: industries x dates, values = 1m returns
        pivot = df.pivot_table(
            index="industry",
            columns="date",
            values="1m",
            aggfunc="mean",
        )

        # Sample dates (show weekly to avoid overcrowding)
        pivot_sampled = pivot.iloc[:, ::7]  # Every 7th day

        # Create heatmap
        fig, ax = plt.subplots(figsize=(16, 12))

        sns.heatmap(
            pivot_sampled,
            cmap="RdYlGn",
            center=0,
            vmin=-10,
            vmax=10,
            cbar_kws={"label": "1-Month Return (%)"},
            linewidths=0.5,
            ax=ax,
        )

        ax.set_title(
            "Sector Rotation Heatmap: 1-Month Performance Across 50 Industries",
            fontsize=16,
            fontweight="bold",
            pad=20,
        )
        ax.set_xlabel("Date (Weekly Snapshots)", fontsize=12)
        ax.set_ylabel("Industry", fontsize=12)

        # Format x-axis dates
        x_labels = [d.strftime("%m/%d") for d in pivot_sampled.columns]
        ax.set_xticklabels(x_labels, rotation=45, ha="right")

        plt.tight_layout()

        output_path = self.output_dir / "sector_rotation_heatmap.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("Saved: %s", output_path)
        return str(output_path)

    async def _create_economic_cycle_dashboard(self, df: pd.DataFrame) -> str:
        """Graph 2: Economic Cycle Dashboard.

        Tracks cyclical vs defensive sector performance to identify
        market regime (risk-on vs risk-off).

        Args:
            df: Historical industry DataFrame.

        Returns:
            Path to saved graph.
        """
        logger.info("Creating economic cycle dashboard...")

        # Calculate daily averages for each sector type
        df_cyclical = df[df["industry"].isin(self.CYCLICAL_INDUSTRIES)].copy()
        df_defensive = df[df["industry"].isin(self.DEFENSIVE_INDUSTRIES)].copy()
        df_financial = df[df["industry"].isin(self.FINANCIAL_INDUSTRIES)].copy()
        df_commodity = df[df["industry"].isin(self.COMMODITY_INDUSTRIES)].copy()

        # Group by date and calculate mean 1m return
        cyclical_avg = df_cyclical.groupby("date")["1m"].mean()
        defensive_avg = df_defensive.groupby("date")["1m"].mean()
        financial_avg = df_financial.groupby("date")["1m"].mean()
        commodity_avg = df_commodity.groupby("date")["1m"].mean()

        # Create figure with 2 subplots
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Plot 1: Sector performance trends
        ax1.plot(cyclical_avg.index, cyclical_avg.values, label="Cyclical", linewidth=2, color="#2E86AB")
        ax1.plot(defensive_avg.index, defensive_avg.values, label="Defensive", linewidth=2, color="#A23B72")
        ax1.plot(financial_avg.index, financial_avg.values, label="Financial", linewidth=2, color="#F18F01")
        ax1.plot(commodity_avg.index, commodity_avg.values, label="Commodity", linewidth=2, color="#C73E1D")

        ax1.axhline(0, color="black", linestyle="--", linewidth=1, alpha=0.5)
        ax1.set_title(
            "Economic Cycle Indicator: Sector Performance Trends",
            fontsize=14,
            fontweight="bold",
        )
        ax1.set_ylabel("Average 1-Month Return (%)", fontsize=11)
        ax1.legend(loc="best", fontsize=10)
        ax1.grid(True, alpha=0.3)

        # Plot 2: Cyclical vs Defensive spread (risk appetite)
        spread = cyclical_avg - defensive_avg

        ax2.fill_between(
            spread.index,
            0,
            spread.values,
            where=(spread.values >= 0),
            color="#2E86AB",
            alpha=0.6,
            label="Risk-On (Cyclical Outperforming)",
        )
        ax2.fill_between(
            spread.index,
            0,
            spread.values,
            where=(spread.values < 0),
            color="#A23B72",
            alpha=0.6,
            label="Risk-Off (Defensive Outperforming)",
        )

        ax2.axhline(0, color="black", linestyle="-", linewidth=1.5)
        ax2.set_title(
            "Risk Appetite: Cyclical - Defensive Spread",
            fontsize=14,
            fontweight="bold",
        )
        ax2.set_xlabel("Date", fontsize=11)
        ax2.set_ylabel("Spread (%)", fontsize=11)
        ax2.legend(loc="best", fontsize=10)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        output_path = self.output_dir / "economic_cycle_dashboard.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("Saved: %s", output_path)
        return str(output_path)

    async def _create_correlation_matrix(self, df: pd.DataFrame) -> str:
        """Graph 3: Industry Correlation Matrix.

        Shows which industries move together (useful for diversification).

        Args:
            df: Historical industry DataFrame.

        Returns:
            Path to saved graph.
        """
        logger.info("Creating correlation matrix...")

        # Pivot to wide format: dates x industries, values = 1m returns
        pivot = df.pivot_table(
            index="date",
            columns="industry",
            values="1m",
            aggfunc="mean",
        )

        # Calculate correlation matrix
        corr_matrix = pivot.corr()

        # Create clustered heatmap
        fig, ax = plt.subplots(figsize=(18, 16))

        # Use seaborn clustermap for better visualization
        g = sns.clustermap(
            corr_matrix,
            cmap="coolwarm",
            center=0,
            vmin=-1,
            vmax=1,
            linewidths=0.1,
            figsize=(18, 16),
            cbar_kws={"label": "Correlation Coefficient"},
            dendrogram_ratio=0.1,
        )

        g.fig.suptitle(
            "Industry Correlation Matrix (1-Month Returns)\nClustered by Similarity",
            fontsize=16,
            fontweight="bold",
            y=0.98,
        )

        output_path = self.output_dir / "correlation_matrix.png"
        g.savefig(output_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info("Saved: %s", output_path)
        return str(output_path)

    def _generate_analysis_summary(self, df: pd.DataFrame) -> str:
        """Generate markdown summary of key insights.

        Args:
            df: Historical industry DataFrame.

        Returns:
            Markdown text with analysis.
        """
        logger.info("Generating analysis summary...")

        # Latest data
        latest_date = df["date"].max()
        latest_df = df[df["date"] == latest_date].copy()

        # Top/bottom performers
        top_5 = latest_df.nlargest(5, "1m")[["industry", "1m"]]
        bottom_5 = latest_df.nsmallest(5, "1m")[["industry", "1m"]]

        # Sector averages
        cyclical_avg = latest_df[latest_df["industry"].isin(self.CYCLICAL_INDUSTRIES)]["1m"].mean()
        defensive_avg = latest_df[latest_df["industry"].isin(self.DEFENSIVE_INDUSTRIES)]["1m"].mean()
        spread = cyclical_avg - defensive_avg

        # Market breadth
        positive = (latest_df["1m"] > 0).sum()
        negative = (latest_df["1m"] < 0).sum()
        avg_return = latest_df["1m"].mean()

        # Generate markdown
        md = f"""# Industry Performance Analysis

**Analysis Date**: {latest_date.strftime('%Y-%m-%d')}
**Data Period**: 3 months (90 days)
**Industries Tracked**: {len(latest_df)}

---

## Market Summary

### Overall Performance
- **Average 1-Month Return**: {avg_return:.2f}%
- **Industries Advancing**: {positive} ({positive/len(latest_df)*100:.1f}%)
- **Industries Declining**: {negative} ({negative/len(latest_df)*100:.1f}%)

### Economic Cycle Indicator
- **Cyclical Sectors Average**: {cyclical_avg:.2f}%
- **Defensive Sectors Average**: {defensive_avg:.2f}%
- **Cyclical - Defensive Spread**: {spread:.2f}%
- **Market Regime**: {'**RISK-ON** (Cyclical outperforming)' if spread > 0 else '**RISK-OFF** (Defensive outperforming)'}

---

## Top 5 Performers (1-Month)

| Industry | 1M Return |
|----------|-----------|
"""

        for _, row in top_5.iterrows():
            md += f"| {row['industry']} | +{row['1m']:.2f}% |\n"

        md += """
---

## Bottom 5 Performers (1-Month)

| Industry | 1M Return |
|----------|-----------|
"""

        for _, row in bottom_5.iterrows():
            md += f"| {row['industry']} | {row['1m']:.2f}% |\n"

        md += f"""
---

## Key Insights from Visualizations

### 1. Sector Rotation Heatmap
- **Purpose**: Identify momentum shifts across all 50 industries
- **What to Look For**:
  - Hot streaks (consecutive green) = sustained outperformance
  - Cold streaks (consecutive red) = sustained underperformance
  - Sudden color changes = inflection points / rotation events

### 2. Economic Cycle Dashboard
- **Current Spread**: {spread:.2f}%
- **Interpretation**:
  - Spread > +3%: Strong risk-on environment
  - Spread -1% to +1%: Neutral/mixed
  - Spread < -3%: Risk-off / defensive rotation

- **Investment Implications**:
  - {'Favor growth stocks, small caps, emerging markets' if spread > 3 else ''}
  - {'Mixed signals - remain balanced' if -1 <= spread <= 1 else ''}
  - {'Favor quality, dividends, defensive sectors' if spread < -3 else ''}

### 3. Correlation Matrix (Clustered)
- **Purpose**: Identify industry relationships for diversification
- **What to Look For**:
  - Dark red clusters (high correlation) = industries that move together
  - Dark blue (negative correlation) = natural hedges
  - Dendrograms show sector groupings

---

## Economist's Perspective

### Market Regime Analysis
{'The positive cyclical-defensive spread indicates a **risk-on** market environment. Investors are rotating into growth-oriented sectors, suggesting optimism about economic acceleration.' if spread > 0 else 'The negative cyclical-defensive spread indicates a **risk-off** market environment. Investors are seeking safety in defensive sectors, suggesting concerns about economic slowdown or volatility.'}

### Breadth Analysis
{f'With {positive/len(latest_df)*100:.1f}% of industries advancing, market breadth is {"**strong**" if positive/len(latest_df) > 0.6 else "**weak**" if positive/len(latest_df) < 0.4 else "**moderate**"}. {"This confirms the strength of the current trend." if positive/len(latest_df) > 0.6 else "This suggests selective strength or rotation rather than broad participation." if positive/len(latest_df) < 0.6 else "This reflects a balanced market."}'}

### Correlation Insights
High correlation among technology sectors (Software, Semiconductors, AI) suggests these industries are driven by common factors (e.g., interest rates, growth expectations). Diversification within tech may not provide as much risk reduction as expected.

---

## Data Quality Notes

- **Source**: Alpha Vantage (daily adjusted close prices)
- **Calculation**: Returns calculated from ETF price changes
- **Frequency**: Daily snapshots stored in Firestore
- **Horizons**: 2w, 1m, 2m, 3m, 6m, 52w, 2y, 3y, 5y, 10y

---

**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""

        # Save markdown
        output_path = self.output_dir / "analysis_summary.md"
        output_path.write_text(md)

        logger.info("Saved: %s", output_path)
        return md


async def main():
    """Main execution."""
    parser = argparse.ArgumentParser(description="Visualize industry performance data")
    parser.add_argument("--days", type=int, default=90, help="Number of days to visualize")
    parser.add_argument("--output", type=str, default="graphs", help="Output directory")
    args = parser.parse_args()

    # Load environment
    av_key = os.getenv("ALPHA_VANTAGE_KEY")
    gcp_project = os.getenv("GCP_PROJECT_ID")

    if not av_key or not gcp_project:
        logger.error("ALPHA_VANTAGE_KEY and GCP_PROJECT_ID must be set")
        sys.exit(1)

    # Load historical data
    logger.info("Loading historical data for %d days...", args.days)
    builder = HistoricalDataBuilder(
        alpha_vantage_key=av_key,
        gcp_project_id=gcp_project,
        days=args.days,
    )

    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=args.days - 1)

    data = await builder.get_date_range(start_date, end_date)

    if not data:
        logger.error("No historical data found. Run build_historical_industry_data.py first.")
        sys.exit(1)

    logger.info("Loaded %d days of data", len(data))

    # Generate visualizations
    visualizer = IndustryDataVisualizer(output_dir=args.output)
    result = await visualizer.generate_all_graphs(data)

    # Print summary
    logger.info("=" * 60)
    logger.info("VISUALIZATION COMPLETE")
    logger.info("=" * 60)
    logger.info("Graphs saved to: %s/", args.output)
    for graph in result["graphs"]:
        logger.info("  - %s", graph)
    logger.info("Analysis: %s", result["analysis_file"])
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
