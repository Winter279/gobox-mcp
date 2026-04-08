"""Gobox MCP server — unified access to Gobox Open API for AI agents.

Runs in either stdio mode (Claude Desktop/Code local) or SSE mode (Docker shared).
Controlled via MCP_TRANSPORT env var (default: stdio).

Registers ~40 tools across 9 modules:
- orders, products, warehouses, reports, shops,
  locations, consignments, goship, webhooks
"""
import os
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env before importing tool modules (they read env at function call time)
load_dotenv()

# Fail fast if core config missing
_REQUIRED_ENV = ("GOBOX_BASE_URL", "GOBOX_CLIENT_ID", "GOBOX_CLIENT_SECRET")
for _key in _REQUIRED_ENV:
    if not os.environ.get(_key):
        raise RuntimeError(
            f"Missing required env var: {_key} "
            f"(see .env.example)"
        )


mcp = FastMCP("gobox-mcp")

# Register all tool modules
from tools import (  # noqa: E402
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

orders_tools.register(mcp)
products_tools.register(mcp)
warehouses_tools.register(mcp)
reports_tools.register(mcp)
shops_tools.register(mcp)
locations_tools.register(mcp)
consignments_tools.register(mcp)
goship_tools.register(mcp)
webhooks_tools.register(mcp)


if __name__ == "__main__":
    transport = os.environ.get("MCP_TRANSPORT", "stdio").lower()
    if transport == "sse":
        port = int(os.environ.get("PORT", 8000))
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        mcp.run()  # stdio default
