"""Order management tools for Gobox MCP.

Wraps /open/api/orders/* endpoints.
Order identifier in Gobox is `transactionNo` (not numeric ID).
"""
import asyncio

from ..client import api


def register(mcp) -> None:
    """Register order tools onto the given FastMCP instance."""

    @mcp.tool()
    async def list_orders(
        status: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        is_fulfillment: bool = False,
        fulfilled_status: int | None = None,
        shop_id: str | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List orders with optional filters. Returns paginated results.

        IMPORTANT for AI: Response includes 'meta' with total, total_page, current.
        - Use filters (status, date range, shop_id) to narrow results.
        - If needed results span multiple pages, call again with incremented 'page'.
        - Use 'limit' up to 50 to reduce number of page calls.

        Args:
            status: Order status string (see sys/helpers for valid values)
            from_date: Filter start date in ISO 'YYYY-MM-DD'
            to_date: Filter end date in ISO 'YYYY-MM-DD'
            is_fulfillment: True = only fulfillment orders (warehouse-handled)
            fulfilled_status: Fulfillment status code (e.g. 180)
            shop_id: Filter by connected shop ID
            limit: Page size (default 20)
            page: Page number (1-indexed)
        """
        params: dict = {
            "limit": limit,
            "page": page,
        }
        if status:
            params["status"] = status
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if is_fulfillment:
            params["is_fulfillment"] = 1
        if fulfilled_status is not None:
            params["fulfilledStatus"] = fulfilled_status
        if shop_id:
            params["shop_id"] = shop_id
        return await api("GET", "/open/api/orders", params=params)

    @mcp.tool()
    async def get_order(transaction_no: str) -> dict:
        """Fetch single order detail by transactionNo."""
        return await api("GET", f"/open/api/orders/{transaction_no}")

    @mcp.tool()
    async def create_order(data: dict) -> dict:
        """Create a new order. `data` must match Gobox schema (see openapi.yaml)."""
        return await api("POST", "/open/api/orders", json=data)

    @mcp.tool()
    async def update_order(transaction_no: str, data: dict) -> dict:
        """Update order fields by transactionNo."""
        return await api(
            "PUT", f"/open/api/orders/{transaction_no}", json=data
        )

    @mcp.tool()
    async def update_order_status(transaction_no: str, status: str) -> dict:
        """Update order status (e.g. to 'shipping', 'delivered')."""
        return await api(
            "PUT",
            f"/open/api/orders/{transaction_no}/status",
            json={"status": status},
        )

    @mcp.tool()
    async def cancel_order(
        transaction_no: str, reason: str | None = None
    ) -> dict:
        """Cancel an order with optional reason."""
        body = {"reason": reason} if reason else {}
        return await api(
            "POST", f"/open/api/orders/{transaction_no}/cancel", json=body
        )

    @mcp.tool()
    async def send_order_to_goship(transaction_no: str) -> dict:
        """Push order to Goship for carrier pickup/delivery."""
        return await api(
            "POST", f"/open/api/orders/{transaction_no}/send-to-goship"
        )

    @mcp.tool()
    async def search_all_orders(
        status: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        shop_id: str | None = None,
    ) -> dict:
        """Fetch ALL orders across all pages in parallel.

        Use when you need a complete list, e.g. 'all orders from last week'
        or 'how many orders are pending?'.
        ALWAYS use filters (status, date range) to narrow results.
        """
        params: dict = {"limit": 50, "page": 1}
        if status:
            params["status"] = status
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        if shop_id:
            params["shop_id"] = shop_id

        first = await api("GET", "/open/api/orders", params=params)
        meta = first.get("meta", {})
        total_pages = meta.get("total_page", 1)
        all_data = first.get("data", [])

        if total_pages > 1:
            tasks = [
                api("GET", "/open/api/orders", params={**params, "page": p})
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
