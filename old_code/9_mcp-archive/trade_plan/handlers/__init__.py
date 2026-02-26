"""Handlers for trade planning"""

async def get_trade_plan(
    symbol: str,
    risk_profile: str = "neutral",
    timeframe: str = "1d",
    gcp_client=None,
) -> dict:
    """Generate trading strategies based on technical analysis"""
    if not gcp_client:
        raise Exception("GCP backend required for trade planning")
    
    return await gcp_client.get_trade_plan(symbol, risk_profile, timeframe)
