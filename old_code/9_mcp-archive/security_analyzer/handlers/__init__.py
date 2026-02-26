"""Handlers for security analysis"""

async def analyze_security(
    symbol: str,
    period: str = "1mo",
    use_ai: bool = True,
    gcp_client=None,
    get_from_local_cache=None,
    get_from_firestore=None,
    save_to_caches=None,
) -> dict:
    """
    Analyze stock/ETF with AI-powered insights.
    Smart routing: L1 (local cache) → L2 (Firestore) → L3 (GCP full pipeline)
    """
    symbol = symbol.upper()
    cache_key = f"{symbol}:{period}"

    # L1: Check local cache
    if get_from_local_cache:
        cached = get_from_local_cache(cache_key)
        if cached:
            cached['cache_level'] = 'L1_local'
            return cached

    # L2: Check Firestore
    if get_from_firestore:
        cached = get_from_firestore(symbol)
        if cached:
            if get_from_local_cache:
                get_from_local_cache(cache_key)
            cached['cache_level'] = 'L2_firestore'
            return cached

    # L3: Trigger GCP pipeline
    if not gcp_client:
        raise Exception("GCP backend not configured")

    print(f"🔄 L3 cache miss: {symbol} - triggering GCP pipeline")

    result = await gcp_client.analyze(symbol, period, use_ai)
    result['cache_level'] = 'L3_gcp_fresh'

    # Save to caches
    if save_to_caches:
        save_to_caches(cache_key, symbol, result)

    return result
