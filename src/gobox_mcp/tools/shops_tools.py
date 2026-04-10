"""Shop integration tools (Shopee, Lazada, TikTok Shop, Tiki, Pancake, POS).

== WORKFLOW GUIDE FOR AI ==

Use list_shops to get shop_id for:
- Filtering products by shop (list_products shop_ids)
- Filtering orders by shop (list_orders shop_id)
- Creating orders linked to a specific sales channel
"""
import asyncio

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

    @mcp.tool()
    async def search_all_shops() -> dict:
        """Fetch ALL shops across all pages in parallel."""
        params: dict = {"limit": 50, "page": 1, "sort": "id:-1"}
        first = await api("GET", "/open/api/shops", params=params)
        meta = first.get("meta", {})
        total_pages = meta.get("total_page", 1)
        all_data = first.get("data", [])

        if total_pages > 1:
            tasks = [
                api("GET", "/open/api/shops", params={**params, "page": p})
                for p in range(2, total_pages + 1)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, dict) and "data" in res:
                    all_data.extend(res["data"])

        return {
            "total_found": meta.get("total", len(all_data)),
            "pages_fetched": total_pages,
            "data": all_data,
        }
