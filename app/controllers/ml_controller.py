"""
ML ingestion controller - API-key protected edge-device entrypoints.

Ref: docs/plans/02-controllers.md section 15.
"""

from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import DeviceModel
from app.schemas.common import LogoUrlSchema, MessageSchema
from app.schemas.waste import BulkWasteIngestSchema, DetectionPayload, HeartbeatPayload, SyncResultSchema, WasteEntrySchema
from app.services import waste_service


async def ingest_detection(
    db: AsyncSession,
    body: DetectionPayload,
    *,
    device: DeviceModel,
) -> WasteEntrySchema:
    return await waste_service.create_waste_entry(db, body, authenticated_device=device, source="ml")


async def bulk_ingest(
    db: AsyncSession,
    body: BulkWasteIngestSchema,
    *,
    device: DeviceModel,
) -> SyncResultSchema:
    return await waste_service.bulk_sync(db, body, authenticated_device=device)


async def ml_heartbeat(
    db: AsyncSession,
    body: HeartbeatPayload,
    *,
    device: DeviceModel,
) -> MessageSchema:
    await waste_service.ml_heartbeat(db, body, device=device)
    return MessageSchema(message="Heartbeat recorded")


async def upload_image(
    image_file: UploadFile,
    *,
    content_length: int | None = None,
) -> LogoUrlSchema:
    return await waste_service.upload_image(image_file, content_length=content_length)
