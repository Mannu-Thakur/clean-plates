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
from app.models.device import DeviceModel, DeviceHealthModel
from app.models.student import StudentModel, StudentMappingModel
from app.models.food import FoodItemModel
from app.models.rule import RuleExecutionModel, RuleModel
from app.models.warning import EscalationModel, PenaltyModel, WarningModel
from app.models.waste import WasteEntryModel
from app.models.aggregated_waste import AggregatedWasteModel
from app.models.filter_preset import FilterPresetModel

__all__ = [
    "Base",
    "UserModel",
    "RefreshTokenModel",
    "RoleModel",
    "ConfigModel",
    "AuditEventModel",
    "DeviceModel",
    "DeviceHealthModel",
    "StudentModel",
    "StudentMappingModel",
    "FoodItemModel",
    "RuleModel",
    "RuleExecutionModel",
    "WasteEntryModel",
    "WarningModel",
    "EscalationModel",
    "PenaltyModel",
    "AggregatedWasteModel",
    "FilterPresetModel",
]
