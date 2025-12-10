"""Simple auth utilities (mock)."""

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException, status


async def get_current_user(authorization: Optional[str] = Header(default=None)) -> str:
    """
    Mock token validation:
    - Expects Authorization: Bearer <user_upn>
    - Returns user_upn
    """
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authorization_header_missing")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_authorization_header")
    user_upn = token.strip()
    return user_upn


CurrentUser = Annotated[str, Depends(get_current_user)]
