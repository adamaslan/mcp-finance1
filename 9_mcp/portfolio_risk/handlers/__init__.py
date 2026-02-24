"""Handlers for portfolio risk analysis"""

async def portfolio_risk(
    holdings: list,
    weights: list = None,
    gcp_client=None,
) -> dict:
    """Analyze portfolio risk metrics"""
    if not gcp_client:
        raise Exception("GCP backend required for portfolio risk analysis")
    
    return await gcp_client.portfolio_risk(holdings, weights)
