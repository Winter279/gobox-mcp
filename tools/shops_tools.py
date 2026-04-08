"""Shop integration tools (Shopee, Lazada, TikTok Shop, Tiki)."""
from gobox_client import api


def register(mcp) -> None:
    @mcp.tool()
    async def list_shops() -> dict:
        """List all connected e-commerce shops (Shopee/Lazada/TikTok/Tiki)."""
        return await api("GET", "/open/api/shops")
