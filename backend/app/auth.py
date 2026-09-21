from fastapi import Header, HTTPException, status

from .config import get_settings


def require_founder_auth(authorization: str | None = Header(default=None)) -> None:
    """Require the configured founder API key as an HTTP Bearer token."""
    configured = get_settings().founder_api_key
    if not configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Founder API key is not configured.")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required. Use: Bearer <founder API key>.")
    supplied = authorization.removeprefix("Bearer ").strip()
    if supplied != configured:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid founder API key.")
