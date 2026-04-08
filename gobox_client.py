"""Shared async HTTP helper for all Gobox API tool calls.

Wraps httpx.AsyncClient with:
- Automatic Bearer token injection via gobox_auth
- Default `lang=vn` query param for Vietnamese responses
- Safe JSON parsing (returns error dict instead of raising)
"""
import os
import httpx

from gobox_auth import get_access_token


def _base_url() -> str:
    return os.environ["GOBOX_BASE_URL"]


def _default_lang() -> str:
    return os.environ.get("GOBOX_DEFAULT_LANG", "vn")


async def api(
    method: str,
    path: str,
    *,
    params: dict | None = None,
    json: dict | None = None,
) -> dict:
    """Call a Gobox Open API endpoint with auth + default lang.

    Args:
        method: HTTP verb ('GET', 'POST', 'PUT', 'DELETE')
        path: Endpoint path, e.g. '/open/api/orders'
        params: Query params (auto-merged with lang=vn for GET)
        json: Request body for POST/PUT

    Returns:
        Parsed JSON dict on success.
        On non-JSON response: {'status_code': int, 'text': str}
        On auth/network error: {'error': str, 'details': ...}
    """
    try:
        token = await get_access_token()
    except Exception as exc:  # noqa: BLE001
        return {"error": "auth_failed", "details": str(exc)}

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }

    # Inject lang=vn into GET params by default
    if method.upper() == "GET":
        merged_params = {"lang": _default_lang()}
        if params:
            merged_params.update(params)
    else:
        merged_params = params

    try:
        async with httpx.AsyncClient(base_url=_base_url(), timeout=30) as client:
            response = await client.request(
                method,
                path,
                headers=headers,
                params=merged_params,
                json=json,
            )
    except httpx.HTTPError as exc:
        return {"error": "http_error", "details": str(exc)}

    # Attempt JSON parse, fallback to raw text metadata
    try:
        return response.json()
    except ValueError:
        return {
            "status_code": response.status_code,
            "text": response.text[:500],
        }
