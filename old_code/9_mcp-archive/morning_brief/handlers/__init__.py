"""Handlers for morning brief generation"""

async def morning_brief(
    date: str = "today",
    gcp_client=None,
    db=None,
) -> dict:
    """Get automated daily market summary"""
    if not gcp_client and not db:
        raise Exception("GCP backend required for daily briefs")

    return await gcp_client.morning_brief(date)
