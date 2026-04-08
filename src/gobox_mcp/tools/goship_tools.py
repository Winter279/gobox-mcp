"""Goship shipping rate lookup tool."""
from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def get_shipping_rates(
        from_city_id: str,
        to_city_id: str,
        weight: int,
        value: int | None = None,
    ) -> dict:
        """Fetch Goship carrier rates for a route.

        Args:
            from_city_id: Origin city ID (see list_cities)
            to_city_id: Destination city ID
            weight: Package weight in grams
            value: Declared order value in VND (optional)
        """
        body: dict = {
            "from_city_id": from_city_id,
            "to_city_id": to_city_id,
            "weight": weight,
        }
        if value is not None:
            body["value"] = value
        return await api(
            "POST", "/open/api/user/get-rates", json=body
        )
