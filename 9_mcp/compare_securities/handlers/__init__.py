"""Handlers for comparing securities"""

async def compare_securities(
    symbols: list,
    period: str = "1mo",
    gcp_client=None,
) -> dict:
    """Compare multiple securities with historical context"""
    if not gcp_client:
        raise Exception("GCP backend required for comparison")
    
    return await gcp_client.compare(symbols, period)
