"""Warehouse + inventory operation tools."""
from gobox_client import api


def register(mcp) -> None:
    """Register warehouse tools onto the given FastMCP instance."""

    @mcp.tool()
    async def list_warehouses() -> dict:
        """List all warehouses registered in Gobox."""
        return await api("GET", "/open/api/warehouses")

    @mcp.tool()
    async def list_inventories(
        warehouse_id: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 20,
    ) -> dict:
        """List inventory check (stock count) documents."""
        params: dict = {"limit": limit, "simple_paginate_meta": 1}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date
        return await api("GET", "/open/api/inventories", params=params)

    @mcp.tool()
    async def list_warehouse_pickings(
        warehouse_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
    ) -> dict:
        """List warehouse picking documents (import/export/transfer)."""
        params: dict = {"limit": limit, "simple_paginate_meta": 1}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if status:
            params["status"] = status
        return await api(
            "GET", "/open/api/warehouse-pickings", params=params
        )
