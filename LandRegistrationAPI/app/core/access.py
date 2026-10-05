from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_staff_access(x_staff_key: str | None = Header(default=None)) -> None:
    """Enable staff endpoint protection by setting STAFF_API_KEY."""
    if settings.STAFF_API_KEY and x_staff_key != settings.STAFF_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid staff API key is required",
        )
