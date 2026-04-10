"""Warehouse, inventory check, and warehouse picking tools.

== WORKFLOW GUIDE FOR AI ==

1. WAREHOUSES:
   - list_warehouses → get warehouse_id for use in orders, consignments, reports
   - include 'address' relation to get warehouse location

2. INVENTORY CHECKS (kiểm kho):
   Used to verify physical stock matches system records.
   Status: 1=pending, 10=awaiting confirmation, 200=completed
   Done status: 1=matched, 2=discrepancy, 3=excess, 4=shortage

3. WAREHOUSE PICKINGS (nhập/xuất/chuyển kho):
   Type: 1=shelf transfer, 2=import, 3=export, 4=warehouse transfer
   Used for all physical stock movements between locations.

4. COMMON FLOW:
   - Check stock: use sku_full_status (in products_tools)
   - Import stock: create consignment → warehouse receives → inventory updated
   - Export stock: create order → send to gobox → picking created → exported
   - Transfer: warehouse picking type=4 between warehouses
"""
import asyncio

from ..client import api


async def _fetch_all_pages(endpoint: str, params: dict) -> dict:
    """Fetch all pages in parallel for any paginated endpoint."""
    first = await api("GET", endpoint, params={**params, "page": 1})
    pag = first.get("meta", {}).get("pagination", {})
    total_pages = pag.get("total_pages", 1)
    all_data = first.get("data", [])

    if total_pages > 1:
        tasks = [
            api("GET", endpoint, params={**params, "page": p})
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


def register(mcp) -> None:
    """Register warehouse tools onto the given FastMCP instance."""

    @mcp.tool()
    async def list_warehouses(
        q: str | None = None,
        include: str | None = None,
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List all warehouses.

        Args:
            q: Search by warehouse name
            include: Relations: address
            limit: Page size
            page: Page number
        """
        params: dict = {"limit": limit, "page": page, "sort": "id:-1"}
        if q:
            params["q"] = q
        if include:
            params["include[]"] = include.split(",")
        return await api("GET", "/open/api/warehouses", params=params)

    @mcp.tool()
    async def list_inventories(
        q: str | None = None,
        warehouse_id: str | None = None,
        status: int | None = None,
        done_status: int | None = None,
        sku_sku: str | None = None,
        include: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
        start_done_date: str | None = None,
        end_done_date: str | None = None,
        sort: str = "id:-1",
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List inventory check (kiểm kho) documents. Paginated.

        IMPORTANT for AI:
        - Status: 1=pending, 10=awaiting confirmation, 200=completed
        - Done status: 1=matched, 2=discrepancy, 3=excess, 4=shortage
        - Use date filters + warehouse_id to narrow results.
        - Include: location,confirmer,creator,processer,sku

        Args:
            q: Search by inventory code
            warehouse_id: Filter by warehouse
            status: 1=pending, 10=awaiting confirmation, 200=completed
            done_status: 1=matched, 2=discrepancy, 3=excess, 4=shortage
            sku_sku: Filter by SKU
            include: Relations: location,confirmer,creator,processer,sku
            start_create_date: Creation date start (YYYY-MM-DD)
            end_create_date: Creation date end (YYYY-MM-DD)
            start_done_date: Completion date start (YYYY-MM-DD)
            end_done_date: Completion date end (YYYY-MM-DD)
            sort: Sort order (default id:-1)
            limit: Page size
            page: Page number
        """
        params: dict = {"limit": limit, "page": page, "sort": sort}
        if q:
            params["q"] = q
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if status is not None:
            params["status"] = status
        if done_status is not None:
            params["done_status"] = done_status
        if sku_sku:
            params["sku_sku"] = sku_sku
        if include:
            params["include[]"] = include.split(",")
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        if start_done_date:
            params["start_done_date"] = start_done_date
        if end_done_date:
            params["end_done_date"] = end_done_date
        return await api("GET", "/open/api/inventories", params=params)

    @mcp.tool()
    async def list_warehouse_pickings(
        q: str | None = None,
        warehouse_id: str | None = None,
        warehouse_dest_id: str | None = None,
        type: int | None = None,
        status: str | None = None,
        sku_sku: str | None = None,
        include: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
        start_done_date: str | None = None,
        end_done_date: str | None = None,
        sort: str = "id:-1",
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List warehouse picking documents (nhập/xuất/chuyển kho). Paginated.

        IMPORTANT for AI:
        - Type: 1=shelf transfer, 2=import, 3=export, 4=warehouse transfer
        - Use 'q' to search by code, order number, or shipping code.
        - Include: moves.sku,order,processer,doner,handoverer,handover,assigner,waiting_revoker,revoker

        Args:
            q: Search by code, order, shipping, picking code
            warehouse_id: Source warehouse filter
            warehouse_dest_id: Destination warehouse (for transfers)
            type: 1=shelf transfer, 2=import, 3=export, 4=warehouse transfer
            status: Status filter
            sku_sku: Filter by SKU
            include: Relations: moves.sku,order,processer,doner,handoverer,handover,assigner,waiting_revoker,revoker
            start_create_date: Creation date start (YYYY-MM-DD)
            end_create_date: Creation date end (YYYY-MM-DD)
            start_done_date: Completion date start (YYYY-MM-DD)
            end_done_date: Completion date end (YYYY-MM-DD)
            sort: Sort order (default id:-1)
            limit: Page size
            page: Page number
        """
        params: dict = {"limit": limit, "page": page, "sort": sort}
        if q:
            params["q"] = q
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if warehouse_dest_id:
            params["warehouse_dest_id"] = warehouse_dest_id
        if type is not None:
            params["type"] = type
        if status:
            params["status"] = status
        if sku_sku:
            params["sku_sku"] = sku_sku
        if include:
            params["include[]"] = include.split(",")
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        if start_done_date:
            params["start_done_date"] = start_done_date
        if end_done_date:
            params["end_done_date"] = end_done_date
        return await api(
            "GET", "/open/api/warehouse-pickings", params=params
        )

    @mcp.tool()
    async def search_all_warehouses(
        include: str | None = None,
    ) -> dict:
        """Fetch ALL warehouses across all pages in parallel."""
        params: dict = {"limit": 50, "sort": "id:-1"}
        if include:
            params["include[]"] = include.split(",")
        return await _fetch_all_pages("/open/api/warehouses", params)

    @mcp.tool()
    async def search_all_inventories(
        warehouse_id: str | None = None,
        status: int | None = None,
        done_status: int | None = None,
        include: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
    ) -> dict:
        """Fetch ALL inventory checks across all pages in parallel.

        ALWAYS use filters to narrow results.
        """
        params: dict = {"limit": 50, "sort": "id:-1"}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if status is not None:
            params["status"] = status
        if done_status is not None:
            params["done_status"] = done_status
        if include:
            params["include[]"] = include.split(",")
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        return await _fetch_all_pages("/open/api/inventories", params)

    @mcp.tool()
    async def search_all_warehouse_pickings(
        warehouse_id: str | None = None,
        type: int | None = None,
        status: str | None = None,
        include: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
    ) -> dict:
        """Fetch ALL warehouse pickings across all pages in parallel.

        ALWAYS use filters to narrow results.
        """
        params: dict = {"limit": 50, "sort": "id:-1"}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if type is not None:
            params["type"] = type
        if status:
            params["status"] = status
        if include:
            params["include[]"] = include.split(",")
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        return await _fetch_all_pages("/open/api/warehouse-pickings", params)
