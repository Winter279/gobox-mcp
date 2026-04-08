"""OAuth2 token manager with in-memory cache + auto refresh.

Gobox uses OAuth2 client credentials flow via POST /oauth/token.
Token is cached until 60 seconds before expiry to avoid redundant calls.
"""
import os
import time
import httpx


# Module-level cache: single token per process lifetime
_cache: dict = {"token": None, "expires_at": 0}


def _cfg() -> tuple[str, str, str, str]:
    """Read required env vars lazily (so import doesn't fail in tests)."""
    return (
        os.environ["GOBOX_BASE_URL"],
        os.environ["GOBOX_CLIENT_ID"],
        os.environ["GOBOX_CLIENT_SECRET"],
        os.environ.get("GOBOX_GRANT_TYPE", "client_credentials"),
    )


async def get_access_token() -> str:
    """Return a valid access token, refreshing if near expiry.

    Refresh window: 60 seconds before `expires_at` to provide safety margin
    against clock drift and in-flight request latency.
    """
    now = time.time()
    if _cache["token"] and now < _cache["expires_at"] - 60:
        return _cache["token"]

    base_url, client_id, client_secret, grant_type = _cfg()

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(
            f"{base_url}/oauth/token",
            json={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": grant_type,
            },
        )
        response.raise_for_status()
        data = response.json()

    _cache["token"] = data["access_token"]
    # Default 1 hour if expires_in missing
    _cache["expires_at"] = now + data.get("expires_in", 3600)
    return _cache["token"]


def clear_cache() -> None:
    """Force next call to refetch token. Useful for testing/recovery."""
    _cache["token"] = None
    _cache["expires_at"] = 0
