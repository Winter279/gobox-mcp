"""Order management tools for Gobox MCP.

== WORKFLOW GUIDE FOR AI ==

1. ORDER LIFECYCLE:
   Created → Confirmed → Sent to warehouse (gobox) → Packed → Sent to carrier (goship) → Shipping → Delivered
   At any point before shipping: can be Cancelled

2. FINDING ORDERS:
   - Use `list_orders(q="code")` to search by order code/transaction number/tracking
   - Use `get_order(transaction_no)` for full detail
   - Use `search_all_orders(...)` only when you need ALL matching results

3. CREATING AN ORDER:
   Step 1: list_shops → get shop_id
   Step 2: list_warehouses → get warehouse_id
   Step 3: get_product(sku) → verify product exists and has stock
   Step 4: sku_quantity_available(sku) → confirm stock
   Step 5: create_order(data) → create
   Step 6: send_order_to_gobox(transaction_no) → send to warehouse for packing
   Step 7: send_order_to_goship(transaction_no) → send to carrier for delivery

4. CANCELLING: cancel_order(transaction_no, reason) — only before shipping

5. STATUS CODES: Call get_sys_helpers() to see all valid status values.

Order identifier is `transactionNo` (string), NOT a numeric ID.
"""
import asyncio

from ..client import api


def register(mcp) -> None:
    """Register order tools onto the given FastMCP instance."""

    @mcp.tool()
    async def list_orders(
        q: str | None = None,
        status: str | None = None,
        shop_id: str | None = None,
        warehouse_id: str | None = None,
        platform: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
        sort: str = "id:-1",
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List orders with filters. Returns paginated results.

        IMPORTANT for AI:
        - Use 'q' to search by order code, transaction number, or tracking number.
        - Use date range filters to narrow results.
        - Response 'meta.pagination' has total, total_pages, current_page for pagination.

        Args:
            q: Search by order code, transaction number, or tracking number
            status: Order status (call get_sys_helpers for valid values)
            shop_id: Filter by shop ID
            warehouse_id: Filter by warehouse ID
            platform: Filter by platform (1=shopee, 2=lazada, 3=tiktokshop, 4=tiki, 5=pancake, 6=pos)
            start_create_date: Creation date range start (YYYY-MM-DD)
            end_create_date: Creation date range end (YYYY-MM-DD)
            sort: Sort order (default id:-1 = newest first)
            limit: Page size (default 25)
            page: Page number (1-indexed)
        """
        params: dict = {"limit": limit, "page": page, "sort": sort}
        if q:
            params["q"] = q
        if status:
            params["status"] = status
        if shop_id:
            params["shop_id"] = shop_id
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if platform:
            params["platform"] = platform
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        return await api("GET", "/open/api/orders", params=params)

    @mcp.tool()
    async def get_order(transaction_no: str) -> dict:
        """Fetch full order detail by transactionNo."""
        return await api("GET", f"/open/api/orders/{transaction_no}")

    @mcp.tool()
    async def create_order(data: dict) -> dict:
        """Create a new order.

        WORKFLOW: First verify product stock with sku_quantity_available.
        See WORKFLOW GUIDE in module docstring for full creation flow.
        """
        return await api("POST", "/open/api/orders", json=data)

    @mcp.tool()
    async def update_order(transaction_no: str, data: dict) -> dict:
        """Update order fields by transactionNo.

        WORKFLOW: Call get_order first to see current state.
        """
        return await api(
            "PUT", f"/open/api/orders/{transaction_no}", json=data
        )

    @mcp.tool()
    async def update_order_status(transaction_no: str, status: str) -> dict:
        """Update order status. Call get_sys_helpers() for valid status values."""
        return await api(
            "PUT",
            f"/open/api/orders/{transaction_no}/status",
            json={"status": status},
        )

    @mcp.tool()
    async def cancel_order(
        transaction_no: str, reason: str | None = None
    ) -> dict:
        """Cancel an order. Only works before shipping stage."""
        body = {"reason": reason} if reason else {}
        return await api(
            "POST", f"/open/api/orders/{transaction_no}/cancel", json=body
        )

    @mcp.tool()
    async def send_order_to_gobox(transaction_no: str) -> dict:
        """Send order to warehouse (Gobox) for packing.

        WORKFLOW: Call this AFTER create_order, BEFORE send_order_to_goship.
        This triggers the warehouse to start picking and packing the order.
        """
        return await api(
            "POST", f"/open/api/orders/{transaction_no}/send-to-gobox"
        )

    @mcp.tool()
    async def send_order_to_goship(transaction_no: str) -> dict:
        """Send order to carrier (Goship) for delivery.

        WORKFLOW: Call this AFTER send_order_to_gobox (order must be packed first).
        This triggers carrier pickup/delivery scheduling.
        """
        return await api(
            "POST", f"/open/api/orders/{transaction_no}/send-to-goship"
        )

    @mcp.tool()
    async def search_all_orders(
        q: str | None = None,
        status: str | None = None,
        shop_id: str | None = None,
        warehouse_id: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
    ) -> dict:
        """Fetch ALL orders across all pages in parallel.

        Use for reporting/counting, e.g. 'all orders from last week'.
        ALWAYS use filters to narrow results.
        """
        params: dict = {"limit": 50, "page": 1, "sort": "id:-1"}
        if q:
            params["q"] = q
        if status:
            params["status"] = status
        if shop_id:
            params["shop_id"] = shop_id
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date

        first = await api("GET", "/open/api/orders", params=params)
        pag = first.get("meta", {}).get("pagination", {})
        total_pages = pag.get("total_pages", 1)
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
            "total_found": pag.get("total", len(all_data)),
            "pages_fetched": total_pages,
            "data": all_data,
        }
