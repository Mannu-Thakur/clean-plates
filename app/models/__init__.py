"""
Models package — re-exports all models for Alembic and general convenience.

Alembic's env.py imports ``from app.models import Base`` so that autogenerate
discovers every table via Base.metadata.
"""

from app.models.base import Base
from app.models.user import UserModel, RefreshTokenModel
from app.models.role import RoleModel
from app.models.config import ConfigModel
from app.models.audit import AuditEventModel

__all__ = [
    "Base",
    "UserModel",
    "RefreshTokenModel",
    "RoleModel",
    "ConfigModel",
    "AuditEventModel",
]
