"""Gobox MCP server — unified access to Gobox Open API for AI agents.

Runs in either stdio mode (Claude Desktop/Code local) or SSE mode (Docker shared).
Controlled via MCP_TRANSPORT env var (default: stdio).

Registers ~45 tools across 9 modules:
- orders, products, warehouses, reports, shops,
  locations, consignments, goship, webhooks
"""
import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from .tools import (
    orders_tools,
    products_tools,
    warehouses_tools,
    reports_tools,
    shops_tools,
    locations_tools,
    consignments_tools,
    goship_tools,
    webhooks_tools,
)


def build_server() -> FastMCP:
    """Instantiate FastMCP and register all tool modules.

    Validates required env vars before registering so missing credentials
    fail fast with a clear error instead of on first API call.
    """
    # Load .env if present (silent no-op if missing)
    load_dotenv()

    for key in ("GOBOX_BASE_URL", "GOBOX_CLIENT_ID", "GOBOX_CLIENT_SECRET"):
        if not os.environ.get(key):
            raise RuntimeError(
                f"Missing required env var: {key} (see .env.example)"
            )

    mcp = FastMCP("gobox-mcp")

    orders_tools.register(mcp)
    products_tools.register(mcp)
    warehouses_tools.register(mcp)
    reports_tools.register(mcp)
    shops_tools.register(mcp)
    locations_tools.register(mcp)
    consignments_tools.register(mcp)
    goship_tools.register(mcp)
    webhooks_tools.register(mcp)

    return mcp


def main() -> None:
    """Entry point for `gobox-mcp` console script.

    Selects transport from MCP_TRANSPORT env var:
    - stdio (default): for Claude Desktop/Code spawning via uvx/pipx
    - sse: for Docker/remote deployments
    """
    mcp = build_server()
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()

    if transport == "sse":
        port = int(os.environ.get("PORT", 8000))
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run()  # stdio default


if __name__ == "__main__":
    main()
