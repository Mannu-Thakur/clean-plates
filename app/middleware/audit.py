"""
Audit helpers — capture model state before/after mutations.

These are called explicitly within service functions, NOT as blanket middleware.

Ref: 04-middlewares.md §6
"""

from __future__ import annotations

from typing import Any


def capture_before(model_instance: Any) -> dict | None:
    """Serialize a model instance's current state before mutation.

    Returns a dict of column values, or None if the instance is None.
    """
    if model_instance is None:
        return None

    mapper = model_instance.__class__.__mapper__
    return {
        col.key: _serialize_value(getattr(model_instance, col.key, None))
        for col in mapper.column_attrs
    }


def capture_after(model_instance: Any) -> dict | None:
    """Serialize a model instance's current state after mutation."""
    return capture_before(model_instance)


def _serialize_value(value: Any) -> Any:
    """Convert non-serializable values to JSON-safe types."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    # datetime, uuid, etc.
    return str(value)
