"""Shop integration tools (Shopee, Lazada, TikTok Shop, Tiki, Pancake, POS).

== WORKFLOW GUIDE FOR AI ==

Use list_shops to get shop_id for:
- Filtering products by shop (list_products shop_ids)
- Filtering orders by shop (list_orders shop_id)
- Creating orders linked to a specific sales channel
"""
from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_shops(
        q: str | None = None,
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List all connected e-commerce shops.

        Args:
            q: Search by shop name
            limit: Page size
            page: Page number
        """
        params: dict = {"limit": limit, "page": page, "sort": "id:-1"}
        if q:
            params["q"] = q
        return await api("GET", "/open/api/shops", params=params)
