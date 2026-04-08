"""Vietnamese administrative divisions + system helpers.

Provides cities/districts/wards lookup for address validation,
plus /sys/helpers which returns enum/status code reference data
used across other endpoints.
"""
from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_cities() -> dict:
        """List all Vietnamese provinces/cities."""
        return await api("GET", "/open/api/cities")

    @mcp.tool()
    async def list_districts(city_id: str | None = None) -> dict:
        """List districts, optionally filtered by city_id."""
        params = {"city_id": city_id} if city_id else {}
        return await api("GET", "/open/api/districts", params=params)

    @mcp.tool()
    async def list_wards(district_id: str | None = None) -> dict:
        """List wards, optionally filtered by district_id."""
        params = {"district_id": district_id} if district_id else {}
        return await api("GET", "/open/api/wards", params=params)

    @mcp.tool()
    async def list_countries() -> dict:
        """List all countries supported by Gobox."""
        return await api("GET", "/open/api/countries")

    @mcp.tool()
    async def get_sys_helpers() -> dict:
        """Fetch system enum/status reference (order statuses, types, etc.).

        Call this once to let AI understand what status codes mean
        when interpreting order/inventory responses.
        """
        return await api("GET", "/open/api/sys/helpers")
