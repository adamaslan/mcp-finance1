"""Handlers for options risk analysis"""

async def options_risk_analysis(
    positions: list,
    market_conditions: str = "neutral",
    gcp_client=None,
) -> dict:
    """Analyze options portfolio risk"""
    if not gcp_client:
        raise Exception("GCP backend required for options risk analysis")
    
    return await gcp_client.options_risk_analysis(positions, market_conditions)
