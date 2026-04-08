# gobox-mcp

MCP server wrapping the Gobox Open API (`dev-api.gobox.asia/open/api/*`) for AI agents, Claude Desktop, and CLI automation.

## Features

- **~40 tools** covering orders, products, SKU quantities, warehouses, reports, shops, locations, consignments, Goship rates, webhooks
- **5 SKU quantity states**: available, in_warehouse, keep_pick, wait_qc, wait_incoming (+ composite `sku_full_status`)
- **Dual transport**: stdio (Claude Desktop local) or SSE (Docker shared for bot/team)
- **Auto token refresh** with in-memory cache
- **Modular**: each tool group in its own file under `tools/`

## Setup

### 1. Credentials

Contact Gobox admin for `client_id` + `client_secret`.

### 2. Install

```bash
cd gobox-mcp
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
```

### 3. Run locally (stdio)

```bash
python gobox_mcp.py
```

### 4. Run in Docker (SSE)

```bash
docker compose up -d
# Test: curl http://localhost:8000/sse
```

## Connect to Claude Desktop

### Stdio mode (local)
Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gobox": {
      "command": "/absolute/path/to/gobox-mcp/.venv/bin/python",
      "args": ["/absolute/path/to/gobox-mcp/gobox_mcp.py"],
      "env": {
        "GOBOX_BASE_URL": "https://dev-api.gobox.asia",
        "GOBOX_CLIENT_ID": "xxx",
        "GOBOX_CLIENT_SECRET": "xxx"
      }
    }
  }
}
```

### SSE mode (Docker)
```json
{
  "mcpServers": {
    "gobox": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Connect to Claude Code

```bash
claude mcp add gobox \
  /absolute/path/.venv/bin/python \
  /absolute/path/gobox_mcp.py \
  -e GOBOX_BASE_URL=https://dev-api.gobox.asia \
  -e GOBOX_CLIENT_ID=xxx \
  -e GOBOX_CLIENT_SECRET=xxx
```

## Environment switching (dev/prod)

Set `GOBOX_BASE_URL` to switch:
- Dev: `https://dev-api.gobox.asia`
- Prod: `https://api.gobox.asia` (verify actual prod URL)

## Tool catalog

| Module | Tools |
|---|---|
| `orders_tools` | `list_orders`, `get_order`, `create_order`, `update_order`, `update_order_status`, `cancel_order`, `send_order_to_goship` |
| `products_tools` | `list_products`, `get_product`, `list_categories`, `list_brands`, `list_attributes`, `sku_quantity_available`, `sku_quantity_in_warehouse`, `sku_quantity_keep_pick`, `sku_quantity_wait_qc`, `sku_quantity_wait_incoming`, `sku_full_status` |
| `warehouses_tools` | `list_warehouses`, `list_inventories`, `list_warehouse_pickings` |
| `reports_tools` | `report_warehouse_import`, `report_warehouse_import_refund`, `report_export_by_order`, `report_export_by_sku`, `report_inventories`, `report_warehouse_store`, `report_warehouse_stock`, `report_materials` |
| `shops_tools` | `list_shops` |
| `locations_tools` | `list_cities`, `list_districts`, `list_wards`, `list_countries`, `get_sys_helpers` |
| `consignments_tools` | `list_consignments`, `get_consignment`, `create_consignment`, `cancel_consignment` |
| `goship_tools` | `get_shipping_rates` |
| `webhooks_tools` | `list_webhooks`, `create_webhook`, `update_webhook`, `delete_webhook`, `toggle_webhook` |

## Example AI queries

> "List all Gobox warehouses"
> "Check stock for SKU ABC123" → calls `sku_full_status("ABC123")`
> "Có bao nhiêu đơn Shopee chưa giao hôm nay?"
> "Báo cáo nhập kho tháng này"

## Troubleshooting

**OAuth fails**: Verify `GOBOX_GRANT_TYPE` (default `client_credentials`). Contact admin if unsure.

**FastMCP SSE DNS rebinding error**: Add `transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False)` to `mcp.run()` call.

**Token expired mid-call**: Auto-refresh handles this. If persists, call `gobox_auth.clear_cache()`.

## Project structure

```
gobox-mcp/
├── gobox_mcp.py              # Main entry
├── gobox_auth.py             # OAuth token cache
├── gobox_client.py           # HTTP helper
├── tools/
│   ├── orders_tools.py
│   ├── products_tools.py
│   ├── warehouses_tools.py
│   ├── reports_tools.py
│   ├── shops_tools.py
│   ├── locations_tools.py
│   ├── consignments_tools.py
│   ├── goship_tools.py
│   └── webhooks_tools.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```
