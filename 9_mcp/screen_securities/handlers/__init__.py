"""Handlers for screening securities"""

async def screen_securities(
    symbols: list,
    criteria: dict,
    limit: int = 20,
    gcp_client=None,
) -> dict:
    """Screen securities via GCP parallel processing"""
    if not gcp_client:
        raise Exception("GCP backend required for screening")
    
    print(f"🔍 Screening {len(symbols)} symbols via GCP (parallel)")
    return await gcp_client.screen(symbols, criteria, limit)
