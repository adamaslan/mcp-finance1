"""Handlers for scanning trades"""

async def scan_trades(
    symbols: list,
    scan_type: str = "momentum",
    gcp_client=None,
) -> dict:
    """Scan for trading opportunities"""
    if not gcp_client:
        raise Exception("GCP backend required for trade scanning")
    
    return await gcp_client.scan_trades(symbols, scan_type)
