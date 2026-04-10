"""Goship shipping rate lookup tool.

== WORKFLOW GUIDE FOR AI ==

Use get_shipping_rates BEFORE creating an order to:
1. Get available carriers and their rates for a route
2. Let user choose the best carrier/price
3. Then create the order with the selected carrier info

Required: address (destination address string for Goship to map)
Optional: warehouse_id, cod, amount, weight, payer, shipping_carrier
"""
from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def get_shipping_rates(
        address: str,
        warehouse_id: str | None = None,
        cod: str | None = None,
        amount: str | None = None,
        weight: str | None = None,
        payer: str | None = None,
        user_id: str | None = None,
        shipping_carrier: str | None = None,
    ) -> dict:
        """Fetch Goship carrier rates for a delivery route.

        Args:
            address: Destination address (required, Goship maps it to location)
            warehouse_id: Origin warehouse ID
            cod: COD fee amount
            amount: Total order amount
            weight: Package weight
            payer: Who pays shipping (0=receiver, 1=sender)
            user_id: User ID
            shipping_carrier: Specific carrier (from get_sys_helpers)
        """
        body: dict = {"address": address}
        if warehouse_id:
            body["warehouse_id"] = warehouse_id
        if cod:
            body["cod"] = cod
        if amount:
            body["amount"] = amount
        if weight:
            body["weight"] = weight
        if payer:
            body["payer"] = payer
        if user_id:
            body["user_id"] = user_id
        if shipping_carrier:
            body["shipping_carrier"] = shipping_carrier
        return await api(
            "POST", "/open/api/user/get-rates", json=body
        )
