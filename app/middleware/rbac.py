"""
Role-Based Access Control dependencies.

Ref: 04-middlewares.md §2
"""

from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status

from app.middleware.auth import get_current_user
from app.schemas.auth import UserSchema


def require_roles(*roles: str) -> Callable:
    """Factory that returns a FastAPI dependency checking user.role is in *roles*.

    Usage::

        @router.post("/rules", dependencies=[Depends(require_roles("super_admin", "institution_admin"))])
    """

    async def _check(current_user: UserSchema = Depends(get_current_user)) -> UserSchema:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' does not have access to this resource",
            )
        return current_user

    return _check


# ── Convenience shortcuts ────────────────────────────────────────────────────

require_admin = require_roles("super_admin", "institution_admin")
"""Shortcut — only super_admin and institution_admin."""

require_write_access = require_roles("super_admin", "institution_admin", "mess_admin", "staff_operator")
"""Blocks analytics_viewer from write routes."""
