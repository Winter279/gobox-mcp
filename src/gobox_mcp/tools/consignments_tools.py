"""Consignment (phiếu ký gửi / nhập hàng) management tools.

== WORKFLOW GUIDE FOR AI ==

1. CONSIGNMENT LIFECYCLE:
   Draft (0) → Confirmed (2) → Received (3) → Partially Imported (4) → Imported (5)
   Can be Cancelled (49) at draft/confirmed stage.

2. CREATING A CONSIGNMENT (nhập hàng vào kho):
   Step 1: list_warehouses → pick warehouse_id
   Step 2: get_product(sku) → verify SKU exists
   Step 3: create_consignment with status=0 (draft) or status=2 (confirmed)
   Step 4: (optional) add_consignment_attachments for supporting documents

3. INCLUDE RELATIONS: warehouse, skus, attachments
   — Use include when you need full consignment detail

4. STATUS CODES:
   0=draft, 2=confirmed, 3=received, 4=partially imported, 5=imported, 49=cancelled

5. QC TYPES: 1=basic, 2=advanced (advanced requires qc_note per product)

6. PRIORITY: 50=normal, 25=fast, 10=rush
"""
import asyncio

from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_consignments(
        q: str | None = None,
        status: int | None = None,
        warehouse_id: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
        quality_control_types: list[str] | None = None,
        include: str | None = None,
        sort: str = "id:-1",
        limit: int = 25,
        page: int = 1,
    ) -> dict:
        """List consignment documents. Returns paginated results.

        IMPORTANT for AI:
        - Use 'q' to search by consignment code.
        - Use 'include' for relations: warehouse,skus,attachments
        - Status: 0=draft, 2=confirmed, 3=received, 4=partially imported, 5=imported, 49=cancelled

        Args:
            q: Search by consignment code
            status: Status filter (0/2/3/4/5/49)
            warehouse_id: Filter by warehouse
            start_create_date: Creation date start (YYYY-MM-DD)
            end_create_date: Creation date end (YYYY-MM-DD)
            quality_control_types: QC type filter (1=basic, 2=advanced)
            include: Comma-separated relations: warehouse,skus,attachments
            sort: Sort order (default id:-1)
            limit: Page size (default 25)
            page: Page number
        """
        params: dict = {"limit": limit, "page": page, "sort": sort}
        if q:
            params["q"] = q
        if status is not None:
            params["status"] = status
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        if quality_control_types:
            params["quality_control_types[]"] = quality_control_types
        if include:
            params["include[]"] = include.split(",")
        return await api("GET", "/open/api/consignments", params=params)

    @mcp.tool()
    async def get_consignment(code: str, include: str | None = None) -> dict:
        """Fetch full consignment detail by code.

        Args:
            code: Consignment code
            include: Comma-separated relations: warehouse,skus,attachments (default: all)
        """
        inc = include or "warehouse,skus,attachments"
        return await api(
            "GET",
            f"/open/api/consignments/{code}",
            params={"include[]": inc.split(",")},
        )

    @mcp.tool()
    async def create_consignment(
        warehouse_id: int,
        status: int,
        products: list[dict],
        qc_type: int = 1,
        priority: int = 50,
        note: str | None = None,
        is_inspection: bool = False,
        is_authorized_seller: bool = False,
    ) -> dict:
        """Create a new consignment (nhập hàng vào kho).

        WORKFLOW: First call list_warehouses to get warehouse_id, then get_product to verify SKUs.

        Args:
            warehouse_id: Target warehouse ID
            status: 0=draft, 2=confirmed
            products: List of products, each with:
                - sku (str, required): Product SKU
                - quantity (int, required): Quantity
                - specification (str, required): Specification
                - unit (str, required): Unit of measure
                - pack (str, required): Packing info
                - qc_description (str, optional): QC description
                - qc_note (str, optional): QC note (required if qc_type=2)
            qc_type: 1=basic (default), 2=advanced
            priority: 50=normal (default), 25=fast, 10=rush
            note: Optional note
            is_inspection: Co-inspection flag
            is_authorized_seller: Authorized seller flag
        """
        body: dict = {
            "warehouse_id": warehouse_id,
            "status": status,
            "qc_type": qc_type,
            "priority": priority,
            "products": products,
        }
        if note:
            body["note"] = note
        if is_inspection:
            body["is_inspection"] = is_inspection
        if is_authorized_seller:
            body["is_authorized_seller"] = is_authorized_seller
        return await api("POST", "/open/api/consignments", json=body)

    @mcp.tool()
    async def cancel_consignment(
        code: str, reason: str | None = None
    ) -> dict:
        """Cancel a consignment. Only works for draft/confirmed status."""
        body = {"reason": reason} if reason else {}
        return await api(
            "POST", f"/open/api/consignments/{code}/cancel", json=body
        )

    @mcp.tool()
    async def add_consignment_attachments(code: str, files: list[dict]) -> dict:
        """Add attachment files to a consignment.

        Args:
            code: Consignment code
            files: List of file objects [{file: ...}]
        """
        return await api(
            "POST",
            f"/open/api/consignments/{code}/attachments-create",
            json={"files": files},
        )

    @mcp.tool()
    async def search_all_consignments(
        q: str | None = None,
        status: int | None = None,
        warehouse_id: str | None = None,
        start_create_date: str | None = None,
        end_create_date: str | None = None,
        include: str | None = None,
    ) -> dict:
        """Fetch ALL consignments across all pages in parallel.

        ALWAYS use filters to narrow results.
        """
        params: dict = {"limit": 50, "page": 1, "sort": "id:-1"}
        if q:
            params["q"] = q
        if status is not None:
            params["status"] = status
        if warehouse_id:
            params["warehouse_id"] = warehouse_id
        if start_create_date:
            params["start_create_date"] = start_create_date
        if end_create_date:
            params["end_create_date"] = end_create_date
        if include:
            params["include[]"] = include.split(",")

        first = await api("GET", "/open/api/consignments", params=params)
        meta = first.get("meta", {})
        total_pages = meta.get("total_page", 1)
        all_data = first.get("data", [])

        if total_pages > 1:
            tasks = [
                api("GET", "/open/api/consignments", params={**params, "page": p})
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
