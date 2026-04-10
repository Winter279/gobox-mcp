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
    async def list_districts(city_id: int) -> dict:
        """List districts for a city. city_id is REQUIRED.

        WORKFLOW: Call list_cities first to get city_id.

        Args:
            city_id: City/province ID (required, from list_cities)
        """
        return await api(
            "GET", "/open/api/districts", params={"city_id": city_id}
        )

    @mcp.tool()
    async def list_wards(district_id: int) -> dict:
        """List wards for a district. district_id is REQUIRED.

        WORKFLOW: Call list_cities → list_districts(city_id) → list_wards(district_id).

        Args:
            district_id: District ID (required, from list_districts)
        """
        return await api(
            "GET", "/open/api/wards", params={"district_id": district_id}
        )

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
