"""Consignment (phiếu ký gửi) management tools."""
import asyncio

from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_consignments(
        status: str | None = None,
        from_date: str | None = None,
        limit: int = 20,
        page: int = 1,
    ) -> dict:
        """List consignment documents. Returns paginated results.

        IMPORTANT for AI: Response includes 'meta' with total, total_page, current.
        - Use filters (status, from_date) to narrow results.
        - If needed results span multiple pages, call again with incremented 'page'.
        """
        params: dict = {"limit": limit, "page": page}
        if status:
            params["status"] = status
        if from_date:
            params["from_date"] = from_date
        return await api("GET", "/open/api/consignments", params=params)

    @mcp.tool()
    async def get_consignment(code: str) -> dict:
        """Fetch consignment detail by code."""
        return await api("GET", f"/open/api/consignments/{code}")

    @mcp.tool()
    async def create_consignment(data: dict) -> dict:
        """Create a new consignment. `data` must match Gobox schema."""
        return await api("POST", "/open/api/consignments", json=data)

    @mcp.tool()
    async def cancel_consignment(
        code: str, reason: str | None = None
    ) -> dict:
        """Cancel a consignment with optional reason."""
        body = {"reason": reason} if reason else {}
        return await api(
            "POST", f"/open/api/consignments/{code}/cancel", json=body
        )

    @mcp.tool()
    async def search_all_consignments(
        status: str | None = None,
        from_date: str | None = None,
    ) -> dict:
        """Fetch ALL consignments across all pages in parallel.

        Use when you need a complete list.
        ALWAYS use filters (status, from_date) to narrow results.
        """
        params: dict = {"limit": 50, "page": 1}
        if status:
            params["status"] = status
        if from_date:
            params["from_date"] = from_date

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
