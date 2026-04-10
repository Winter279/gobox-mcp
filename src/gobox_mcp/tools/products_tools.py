"""Product catalog + SKU quantity tools.

Exposes Gobox's 5 distinct SKU inventory states:
- available: sellable stock (not held/picked)
- in_warehouse: physically present in warehouse
- keep_pick: reserved for outgoing orders
- wait_qc: awaiting quality check
- wait_incoming: expected from consignments

Composite tool `sku_full_status` aggregates all 5 in one AI-friendly call.
"""
import asyncio

from ..client import api


def register(mcp) -> None:
    """Register product + SKU tools onto the given FastMCP instance."""

    # === Product catalog ===
    @mcp.tool()
    async def list_products(
        category_id: str | None = None,
        brand_id: str | None = None,
        keyword: str | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List products with optional filters. Returns paginated results.

        IMPORTANT for AI: Response includes 'meta' with total, total_page, current.
        - ALWAYS use 'keyword' to search first instead of browsing all pages.
        - If needed results span multiple pages, call again with incremented 'page'.
        - Use 'limit' up to 50 to reduce number of page calls.
        """
        params: dict = {
            "limit": limit,
            "page": page,
        }
        if category_id:
            params["category_id"] = category_id
        if brand_id:
            params["brand_id"] = brand_id
        if keyword:
            params["keyword"] = keyword
        return await api("GET", "/open/api/products", params=params)

    @mcp.tool()
    async def search_all_products(
        keyword: str | None = None,
        category_id: str | None = None,
        brand_id: str | None = None,
    ) -> dict:
        """Fetch ALL products across all pages in parallel.

        Use this when you need a complete list, e.g. 'show all products of brand X'
        or 'how many products match keyword Y?'. Returns combined data + total count.
        ALWAYS use keyword/category/brand filters to narrow results when possible.
        """
        params: dict = {"limit": 50, "page": 1}
        if keyword:
            params["keyword"] = keyword
        if category_id:
            params["category_id"] = category_id
        if brand_id:
            params["brand_id"] = brand_id

        # First call to get total_page count
        first = await api("GET", "/open/api/products", params=params)
        meta = first.get("meta", {})
        total_pages = meta.get("total_page", 1)
        all_data = first.get("data", [])

        # Fetch all remaining pages in parallel
        if total_pages > 1:
            tasks = [
                api("GET", "/open/api/products", params={**params, "page": p})
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

    @mcp.tool()
    async def get_product(sku: str) -> dict:
        """Fetch product detail by SKU."""
        return await api("GET", f"/open/api/products/{sku}")

    @mcp.tool()
    async def list_categories() -> dict:
        """List all product categories."""
        return await api("GET", "/open/api/categories")

    @mcp.tool()
    async def list_brands() -> dict:
        """List all brands."""
        return await api("GET", "/open/api/brands")

    @mcp.tool()
    async def list_attributes() -> dict:
        """List product attributes (color, size, etc.)."""
        return await api("GET", "/open/api/attributes")

    # === SKU quantity states ===
    async def _quantity(endpoint: str, sku: str | None) -> dict:
        """Internal helper for quantity endpoints that accept optional sku filter."""
        params = {"sku": sku} if sku else {}
        return await api("GET", endpoint, params=params)

    @mcp.tool()
    async def sku_quantity_available(sku: str | None = None) -> dict:
        """Get AVAILABLE (sellable) quantity for SKU. Omit sku for all SKUs."""
        return await _quantity(
            "/open/api/product-skus/quantity-available", sku
        )

    @mcp.tool()
    async def sku_quantity_in_warehouse(sku: str | None = None) -> dict:
        """Get total quantity physically IN warehouse (includes held stock)."""
        return await _quantity(
            "/open/api/product-skus/quantity-in-warehouse", sku
        )

    @mcp.tool()
    async def sku_quantity_keep_pick(sku: str | None = None) -> dict:
        """Get quantity reserved for outgoing order picks (not available)."""
        return await _quantity(
            "/open/api/product-skus/quantity-keep-pick-in-warehouse", sku
        )

    @mcp.tool()
    async def sku_quantity_wait_qc(sku: str | None = None) -> dict:
        """Get quantity waiting for QC inspection (not yet sellable)."""
        return await _quantity(
            "/open/api/product-skus/quantity-wait-qc", sku
        )

    @mcp.tool()
    async def sku_quantity_wait_incoming(sku: str | None = None) -> dict:
        """Get quantity expected from incoming consignments."""
        return await _quantity(
            "/open/api/product-skus/quantity-wait-income-consigments", sku
        )

    @mcp.tool()
    async def sku_full_status(sku: str) -> dict:
        """Composite: fetch ALL 5 quantity states for a single SKU in parallel.

        Use this when answering 'How much of SKU X do we have?' — gives
        AI the full picture in one call instead of 5 sequential tool calls.
        """
        endpoints = [
            ("available", "/open/api/product-skus/quantity-available"),
            ("in_warehouse", "/open/api/product-skus/quantity-in-warehouse"),
            (
                "keep_pick",
                "/open/api/product-skus/quantity-keep-pick-in-warehouse",
            ),
            ("wait_qc", "/open/api/product-skus/quantity-wait-qc"),
            (
                "wait_incoming",
                "/open/api/product-skus/quantity-wait-income-consigments",
            ),
        ]
        tasks = [api("GET", ep, params={"sku": sku}) for _, ep in endpoints]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return {
            "sku": sku,
            **{
                name: (
                    {"error": str(res)} if isinstance(res, Exception) else res
                )
                for (name, _), res in zip(endpoints, results)
            },
        }
