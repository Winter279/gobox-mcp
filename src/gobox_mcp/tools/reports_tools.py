"""WMS report tools — 8 warehouse report endpoints.

== WORKFLOW GUIDE FOR AI ==

1. REPORT TYPES:
   - warehouse-import: Stock received into warehouse
   - warehouse-import-refund: Returned/refunded stock imports
   - warehouse-export-by-order: Stock exported grouped by order
   - warehouse-export-by-sku: Stock exported grouped by SKU
   - inventories: Inventory check (kiểm kho) report
   - warehouse-store: Current storage snapshot
   - warehouse-stock: Stock balance report (requires warehouse_id)
   - materials: Packaging/supplies usage report

2. COMMON FILTERS: start_date, end_date (YYYY-MM-DD), warehouse_id, sku_sku
   All reports are paginated (limit, page, sort).

3. USAGE:
   - "How much stock was imported last month?" → report_warehouse_import
   - "What's currently in warehouse X?" → report_warehouse_stock (requires warehouse_id)
   - "Show me export by order" → report_export_by_order
   - "Material usage report" → report_materials
"""
from ..client import api


def _report_params(
    start_date: str | None = None,
    end_date: str | None = None,
    warehouse_id: str | None = None,
    sku_sku: str | None = None,
    q: str | None = None,
    limit: int = 100,
    page: int = 1,
    sort: str = "done_at:1",
    extra: dict | None = None,
) -> dict:
    """Build common report param dict."""
    params: dict = {"limit": limit, "page": page, "sort": sort}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date
    if warehouse_id:
        params["warehouse_id"] = warehouse_id
    if sku_sku:
        params["sku_sku"] = sku_sku
    if q:
        params["q"] = q
    if extra:
        params.update(extra)
    return params


def register(mcp) -> None:
    """Register report tools onto the given FastMCP instance."""

    @mcp.tool()
    async def report_warehouse_import(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        sku_sku: str | None = None,
        is_consignment: bool | None = None,
        is_manual: bool | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Warehouse import (stock-in) report.

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            warehouse_id: Filter by warehouse
            sku_sku: Filter by SKU
            is_consignment: Filter consignment imports only
            is_manual: Filter manual imports only
            limit: Page size (default 100)
            page: Page number
        """
        extra = {}
        if is_consignment is not None:
            extra["is_consignment"] = is_consignment
        if is_manual is not None:
            extra["is_manual"] = is_manual
        return await api(
            "GET",
            "/open/api/reports/warehouse-import",
            params=_report_params(start_date, end_date, warehouse_id, sku_sku,
                                  limit=limit, page=page, extra=extra or None),
        )

    @mcp.tool()
    async def report_warehouse_import_refund(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        sku_sku: str | None = None,
        q: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Import report for refund/returned stock.

        Args:
            q: Search by order or shipping code
        """
        return await api(
            "GET",
            "/open/api/reports/warehouse-import-refund",
            params=_report_params(start_date, end_date, warehouse_id, sku_sku,
                                  q=q, limit=limit, page=page),
        )

    @mcp.tool()
    async def report_export_by_order(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        q: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Warehouse export report grouped by order.

        Args:
            q: Search by order or shipping code
        """
        return await api(
            "GET",
            "/open/api/reports/warehouse-export-by-order",
            params=_report_params(start_date, end_date, warehouse_id,
                                  q=q, limit=limit, page=page),
        )

    @mcp.tool()
    async def report_export_by_sku(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        sku_sku: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Warehouse export report grouped by SKU."""
        return await api(
            "GET",
            "/open/api/reports/warehouse-export-by-sku",
            params=_report_params(start_date, end_date, warehouse_id, sku_sku,
                                  limit=limit, page=page),
        )

    @mcp.tool()
    async def report_inventories(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        sku_sku: str | None = None,
        barcode: str | None = None,
        user_id: int | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Inventory check (kiểm kho) report.

        Args:
            barcode: Filter by barcode
            user_id: Filter by user who performed the check
        """
        extra = {}
        if barcode:
            extra["barcode"] = barcode
        if user_id is not None:
            extra["user_id"] = user_id
        return await api(
            "GET",
            "/open/api/reports/inventories",
            params=_report_params(start_date, end_date, warehouse_id, sku_sku,
                                  limit=limit, page=page, extra=extra or None),
        )

    @mcp.tool()
    async def report_warehouse_store(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        sku_sku: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Warehouse storage snapshot — what's currently stored."""
        return await api(
            "GET",
            "/open/api/reports/warehouse-store",
            params=_report_params(start_date, end_date, warehouse_id, sku_sku,
                                  limit=limit, page=page),
        )

    @mcp.tool()
    async def report_warehouse_stock(
        warehouse_id: str,
        start_date: str | None = None,
        end_date: str | None = None,
        sku_sku: str | None = None,
    ) -> dict:
        """Current stock balance per warehouse/SKU. warehouse_id is REQUIRED."""
        params: dict = {"warehouse_id": warehouse_id}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if sku_sku:
            params["sku_sku"] = sku_sku
        return await api(
            "GET", "/open/api/reports/warehouse-stock", params=params
        )

    @mcp.tool()
    async def report_materials(
        start_date: str | None = None,
        end_date: str | None = None,
        warehouse_id: str | None = None,
        q: str | None = None,
        limit: int = 100,
        page: int = 1,
    ) -> dict:
        """Materials (packaging, supplies) usage report.

        Args:
            q: Search by order, shipping, picking code, or GSKU
        """
        return await api(
            "GET",
            "/open/api/reports/materials",
            params=_report_params(start_date, end_date, warehouse_id,
                                  q=q, limit=limit, page=page),
        )
