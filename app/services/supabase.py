"""Small Supabase REST client used for user verification and enrichment history."""

from typing import Any, Optional
import httpx
from fastapi import Header, HTTPException

from app.config import settings


def is_configured() -> bool:
    return bool(settings.SUPABASE_URL and settings.SUPABASE_ANON_KEY)


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> Optional[dict[str, Any]]:
    """Validate a Supabase access token and return the authenticated user."""
    if not is_configured():
        return None
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Sign in is required to use the intelligence pipeline.")

    token = authorization.removeprefix("Bearer ").strip()
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={"apikey": settings.SUPABASE_ANON_KEY, "Authorization": f"Bearer {token}"},
        )
    if response.is_error:
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")
    return response.json()


async def save_enrichment(user: Optional[dict[str, Any]], request: Any, result: Any, authorization: Optional[str]) -> None:
    """Persist a run using the caller's token so Supabase RLS remains authoritative."""
    if not is_configured() or not user or not authorization:
        return
    payload = {
        "user_id": user["id"],
        "brand": request.brand,
        "mpn": request.mpn,
        "description": request.description,
        "result": result.model_dump(mode="json") if hasattr(result, "model_dump") else result,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(
            f"{settings.SUPABASE_URL}/rest/v1/enrichment_runs",
            headers={
                "apikey": settings.SUPABASE_ANON_KEY,
                "Authorization": authorization,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=payload,
        )
    if response.is_error:
        # A completed enrichment remains useful even if history persistence fails.
        return
