"""WMS report tools — 8 warehouse report endpoints.

All reports accept optional date range + warehouse filter.
"""
from ..client import api


def _date_params(
    from_date: str | None = None,
    to_date: str | None = None,
    warehouse_id: str | None = None,
    extra: dict | None = None,
) -> dict:
    """Build common date/warehouse param dict shared across reports."""
    params: dict = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    if warehouse_id:
        params["warehouse_id"] = warehouse_id
    if extra:
        params.update(extra)
    return params


def register(mcp) -> None:
    """Register report tools onto the given FastMCP instance."""

    @mcp.tool()
    async def report_warehouse_import(
        from_date: str | None = None,
        to_date: str | None = None,
        warehouse_id: str | None = None,
    ) -> dict:
        """Warehouse import (stock-in) report for date range."""
        return await api(
            "GET",
            "/open/api/reports/warehouse-import",
            params=_date_params(from_date, to_date, warehouse_id),
        )

    @mcp.tool()
    async def report_warehouse_import_refund(
        from_date: str | None = None,
        to_date: str | None = None,
        warehouse_id: str | None = None,
    ) -> dict:
        """Import report for refund/returned stock."""
        return await api(
            "GET",
            "/open/api/reports/warehouse-import-refund",
            params=_date_params(from_date, to_date, warehouse_id),
        )

    @mcp.tool()
    async def report_export_by_order(
        from_date: str | None = None,
        to_date: str | None = None,
        warehouse_id: str | None = None,
    ) -> dict:
        """Warehouse export report grouped by order."""
        return await api(
            "GET",
            "/open/api/reports/warehouse-export-by-order",
            params=_date_params(from_date, to_date, warehouse_id),
        )

    @mcp.tool()
    async def report_export_by_sku(
        from_date: str | None = None,
        to_date: str | None = None,
        warehouse_id: str | None = None,
        sku: str | None = None,
    ) -> dict:
        """Warehouse export report grouped by SKU (optionally filter 1 SKU)."""
        extra = {"sku": sku} if sku else None
        return await api(
            "GET",
            "/open/api/reports/warehouse-export-by-sku",
            params=_date_params(from_date, to_date, warehouse_id, extra),
        )

    @mcp.tool()
    async def report_inventories(
        from_date: str | None = None,
        to_date: str | None = None,
        warehouse_id: str | None = None,
    ) -> dict:
        """Inventory check (stock count) aggregated report."""
        return await api(
            "GET",
            "/open/api/reports/inventories",
            params=_date_params(from_date, to_date, warehouse_id),
        )

    @mcp.tool()
    async def report_warehouse_store(
        warehouse_id: str | None = None,
    ) -> dict:
        """Warehouse storage snapshot — what's currently stored."""
        params = {"warehouse_id": warehouse_id} if warehouse_id else {}
        return await api(
            "GET", "/open/api/reports/warehouse-store", params=params
        )

    @mcp.tool()
    async def report_warehouse_stock(
        warehouse_id: str | None = None,
        sku: str | None = None,
    ) -> dict:
        """Current stock snapshot per warehouse/SKU."""
        params: dict = {}
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if sku:
            params["sku"] = sku
        return await api(
            "GET", "/open/api/reports/warehouse-stock", params=params
        )

    @mcp.tool()
    async def report_materials(
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> dict:
        """Materials (packaging, supplies) report."""
        return await api(
            "GET",
            "/open/api/reports/materials",
            params=_date_params(from_date, to_date),
        )
