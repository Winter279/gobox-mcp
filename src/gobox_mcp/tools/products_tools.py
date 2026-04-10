"""Product catalog, SKU variants, and inventory quantity tools.

== WORKFLOW GUIDE FOR AI ==

1. FINDING PRODUCTS:
   - Use `list_products(q="keyword")` to search by name/SKU
   - Use `get_product(sku)` with include to get FULL detail (skus, variants, images, etc.)
   - Use `search_all_products(q="keyword")` only when you need ALL matching results

2. CHECKING STOCK:
   - Use `sku_full_status(sku)` to get ALL 5 quantity states in one call
   - Individual quantity tools only when you need just one specific state

3. PRODUCT MANAGEMENT:
   - Create: first call `list_categories` → get category_id → then `list_brands(category_id)` + `list_attributes(category_id)`
   - Update: call `get_product(sku)` first to see current state
   - Delete: confirm with user before calling

4. QUANTITY STATES EXPLAINED:
   - available: sellable stock (not held/picked) — what can be sold NOW
   - in_warehouse: physically present (includes held stock)
   - keep_pick: reserved for outgoing order picks (not available for sale)
   - wait_qc: awaiting quality check (from consignment, not yet sellable)
   - wait_incoming: expected from incoming consignments (not yet in warehouse)

5. INCLUDE RELATIONS (for list_products / get_product):
   skus, variants, images, attributes, brand, shops, combos
   — ALWAYS use include when you need full product info
"""
import asyncio

from ..client import api

# Default include for full product detail
_PRODUCT_INCLUDES = "skus,variants,images,attributes,brand,shops,combos"


def register(mcp) -> None:
    """Register product + SKU tools onto the given FastMCP instance."""

    # === Product catalog ===
    @mcp.tool()
    async def list_products(
        q: str | None = None,
        category_id: str | None = None,
        brand_id: str | None = None,
        shop_ids: list[str] | None = None,
        platform: str | None = None,
        product_sku: str | None = None,
        sku_sku: str | None = None,
        include: str | None = None,
        sort: str = "id:-1",
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List products with filters. Returns paginated results.

        IMPORTANT for AI:
        - ALWAYS use 'q' to search by name/SKU first instead of browsing all pages.
        - Use 'include' to get relations: skus,variants,images,attributes,brand,shops,combos
        - Response 'meta.pagination' has total, total_pages, current_page for pagination.
        - Platform codes: 1=shopee, 2=lazada, 3=tiktokshop, 4=tiki, 5=pancake, 6=pos

        Args:
            q: Search by product name or SKU
            category_id: Filter by category ID
            brand_id: Filter by brand ID
            shop_ids: Filter by shop IDs (list)
            platform: Filter by platform (1=shopee, 2=lazada, 3=tiktokshop, 4=tiki, 5=pancake, 6=pos)
            product_sku: Search by product SKU specifically
            sku_sku: Search by variant SKU specifically
            include: Comma-separated relations: skus,variants,images,attributes,brand,shops,combos
            sort: Sort order (default id:-1 = newest first)
            limit: Page size (default 25)
            page: Page number (1-indexed)
        """
        params: dict = {"limit": limit, "page": page, "sort": sort}
        if q:
            params["q"] = q
        if category_id:
            params["category_id"] = category_id
        if brand_id:
            params["brand_id"] = brand_id
        if shop_ids:
            params["shop_ids[]"] = shop_ids
        if platform:
            params["platform"] = platform
        if product_sku:
            params["product_sku"] = product_sku
        if sku_sku:
            params["sku_sku"] = sku_sku
        if include:
            params["include[]"] = include.split(",")
        return await api("GET", "/open/api/products", params=params)

    @mcp.tool()
    async def get_product(sku: str, include: str | None = None) -> dict:
        """Fetch FULL product detail by SKU with all relations.

        Args:
            sku: Product SKU
            include: Comma-separated relations (default: skus,variants,images,attributes,brand,shops,combos)
        """
        inc = include or _PRODUCT_INCLUDES
        return await api(
            "GET",
            f"/open/api/products/{sku}",
            params={"include[]": inc.split(",")},
        )

    @mcp.tool()
    async def create_product(data: dict) -> dict:
        """Create a new product.

        WORKFLOW: First call list_categories + list_brands to get valid IDs.

        Required body fields:
            category_id (int): Category ID (from list_categories)
        Optional fields:
            name (str), sku (str), description (str),
            brand_id (int), weight (int, grams), length/width/height (int),
            is_combo (bool), total_price (number, required if is_combo=1),
            product_combos: [{sku_name, quantity}] (if combo),
            variants: [{name, value}],
            skus: [{sku, price, supplier_price, variants}],
            images: [{image, variant_name, variant_value}],
            attributes: [{attribute_id, value, platform, values[], unit}]
        """
        return await api("POST", "/open/api/products", json=data)

    @mcp.tool()
    async def update_product(sku: str, data: dict) -> dict:
        """Update product by SKU.

        WORKFLOW: Call get_product(sku) first to see current state before updating.
        Body fields same as create_product.
        """
        return await api("POST", f"/open/api/products/{sku}", json=data)

    @mcp.tool()
    async def delete_product(sku: str) -> dict:
        """Delete product by SKU. WARNING: This is irreversible."""
        return await api("DELETE", f"/open/api/products/{sku}")

    @mcp.tool()
    async def search_all_products(
        q: str | None = None,
        category_id: str | None = None,
        brand_id: str | None = None,
        include: str | None = None,
    ) -> dict:
        """Fetch ALL products across all pages in parallel.

        Use when you need a complete list, e.g. 'show all products of brand X'.
        ALWAYS use q/category/brand filters to narrow results when possible.

        """
        params: dict = {"limit": 50, "page": 1, "sort": "id:-1"}
        if q:
            params["q"] = q
        if category_id:
            params["category_id"] = category_id
        if brand_id:
            params["brand_id"] = brand_id
        if include:
            params["include[]"] = include.split(",")

        first = await api("GET", "/open/api/products", params=params)
        pag = first.get("meta", {}).get("pagination", {})
        total_pages = pag.get("total_pages", 1)
        all_data = first.get("data", [])

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
            "total_found": pag.get("total", len(all_data)),
            "pages_fetched": total_pages,
            "data": all_data,
        }

    @mcp.tool()
    async def list_categories() -> dict:
        """List all product categories. Use to get category_id for product creation.

        WORKFLOW: Call this FIRST, then use category_id for list_brands and list_attributes.
        """
        return await api("GET", "/open/api/categories")

    @mcp.tool()
    async def list_brands(category_id: int) -> dict:
        """List brands for a category. category_id is REQUIRED.

        WORKFLOW: Call list_categories first to get category_id.

        Args:
            category_id: Category ID (from list_categories) — required
        """
        return await api(
            "GET", "/open/api/brands", params={"category_id": category_id}
        )

    @mcp.tool()
    async def list_attributes(category_id: int) -> dict:
        """List product attributes for a category. category_id is REQUIRED.

        WORKFLOW: Call list_categories first to get category_id.

        Args:
            category_id: Category ID (from list_categories) — required
        """
        return await api(
            "GET", "/open/api/attributes", params={"category_id": category_id}
        )

    @mcp.tool()
    async def list_product_skus(
        q: str | None = None,
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List all product SKU variants.

        Args:
            q: Search by SKU code
            limit: Page size
            page: Page number
        """
        params: dict = {"limit": limit, "page": page}
        if q:
            params["q"] = q
        return await api("GET", "/open/api/product-skus", params=params)

    @mcp.tool()
    async def search_all_product_skus(
        q: str | None = None,
    ) -> dict:
        """Fetch ALL product SKU variants across all pages in parallel."""
        params: dict = {"limit": 50, "page": 1}
        if q:
            params["q"] = q

        first = await api("GET", "/open/api/product-skus", params=params)
        pag = first.get("meta", {}).get("pagination", {})
        total_pages = pag.get("total_pages", 1)
        all_data = first.get("data", [])

        if total_pages > 1:
            tasks = [
                api("GET", "/open/api/product-skus", params={**params, "page": p})
                for p in range(2, total_pages + 1)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, dict) and "data" in res:
                    all_data.extend(res["data"])

        return {
            "total_found": pag.get("total", len(all_data)),
            "pages_fetched": total_pages,
            "data": all_data,
        }

    # === SKU quantity states ===
    async def _quantity(endpoint: str, sku: str | None) -> dict:
        """Internal helper for quantity endpoints."""
        params = {"sku": sku} if sku else {}
        return await api("GET", endpoint, params=params)

    @mcp.tool()
    async def sku_quantity_available(sku: str | None = None) -> dict:
        """Get AVAILABLE (sellable) quantity. This is what can be sold NOW."""
        return await _quantity(
            "/open/api/product-skus-quantity-available", sku
        )

    @mcp.tool()
    async def sku_quantity_in_warehouse(sku: str | None = None) -> dict:
        """Get total quantity physically IN warehouse (includes held stock)."""
        return await _quantity(
            "/open/api/product-skus-quantity-in-warehouse", sku
        )

    @mcp.tool()
    async def sku_quantity_keep_pick(sku: str | None = None) -> dict:
        """Get quantity reserved for outgoing order picks (not available for sale)."""
        return await _quantity(
            "/open/api/product-skus-quantity-keep-pick-in-warehouse", sku
        )

    @mcp.tool()
    async def sku_quantity_wait_qc(sku: str | None = None) -> dict:
        """Get quantity waiting for QC inspection (not yet sellable)."""
        return await _quantity(
            "/open/api/product-skus-quantity-wait-qc", sku
        )

    @mcp.tool()
    async def sku_quantity_wait_incoming(sku: str | None = None) -> dict:
        """Get quantity expected from incoming consignments (not yet in warehouse)."""
        return await _quantity(
            "/open/api/product-skus-quantity-wait-income-consigments", sku
        )

    @mcp.tool()
    async def sku_full_status(sku: str) -> dict:
        """Composite: fetch ALL 5 quantity states for a single SKU in parallel.

        PREFERRED tool for answering 'How much of SKU X do we have?'
        Returns all states in one call instead of 5 sequential calls.
        """
        endpoints = [
            ("available", "/open/api/product-skus-quantity-available"),
            ("in_warehouse", "/open/api/product-skus-quantity-in-warehouse"),
            ("keep_pick", "/open/api/product-skus-quantity-keep-pick-in-warehouse"),
            ("wait_qc", "/open/api/product-skus-quantity-wait-qc"),
            ("wait_incoming", "/open/api/product-skus-quantity-wait-income-consigments"),
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
