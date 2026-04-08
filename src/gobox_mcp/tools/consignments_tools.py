"""Consignment (phiếu ký gửi) management tools."""
from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_consignments(
        status: str | None = None,
        from_date: str | None = None,
        limit: int = 20,
    ) -> dict:
        """List consignment documents."""
        params: dict = {"limit": limit, "simple_paginate_meta": 1}
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
