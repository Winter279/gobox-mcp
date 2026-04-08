"""Webhook subscription management tools."""
from ..client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_webhooks() -> dict:
        """List all registered webhook subscriptions."""
        return await api("GET", "/open/api/webhooks")

    @mcp.tool()
    async def create_webhook(url: str, events: list[str]) -> dict:
        """Register a new webhook endpoint.

        Args:
            url: Public HTTPS URL to receive events
            events: List of event names (e.g. ['order.created', 'stock.changed'])
        """
        return await api(
            "POST",
            "/open/api/webhooks",
            json={"url": url, "events": events},
        )

    @mcp.tool()
    async def update_webhook(webhook_id: str, data: dict) -> dict:
        """Update webhook configuration."""
        return await api(
            "POST", f"/open/api/webhooks/{webhook_id}", json=data
        )

    @mcp.tool()
    async def delete_webhook(webhook_id: str) -> dict:
        """Delete a webhook subscription."""
        return await api("DELETE", f"/open/api/webhooks/{webhook_id}")

    @mcp.tool()
    async def toggle_webhook(webhook_id: str) -> dict:
        """Enable/disable a webhook."""
        return await api(
            "POST", f"/open/api/toggle-webhook-config/{webhook_id}"
        )
