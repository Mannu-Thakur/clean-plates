"""
ML ingestion controller - API-key protected edge-device entrypoints.

Ref: docs/plans/02-controllers.md section 15.
"""

from __future__ import annotations

from arq.connections import ArqRedis
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.device import DeviceModel
from app.schemas.common import LogoUrlSchema, MessageSchema
from app.schemas.waste import (
    BulkWasteIngestSchema,
    DetectionPayload,
    HeartbeatPayload,
    SyncResultSchema,
    WasteEntrySchema,
)
from app.services import waste_service


async def ingest_detection(
    db: AsyncSession,
    body: DetectionPayload,
    *,
    device: DeviceModel,
    arq_pool: ArqRedis | None = None,
) -> WasteEntrySchema:
    return await waste_service.create_waste_entry(db, body, authenticated_device=device, source="ml", arq_pool=arq_pool)


async def bulk_ingest(
    db: AsyncSession,
    body: BulkWasteIngestSchema,
    *,
    device: DeviceModel,
    arq_pool: ArqRedis | None = None,
) -> SyncResultSchema:
    return await waste_service.bulk_sync(db, body, authenticated_device=device, arq_pool=arq_pool)


async def ml_heartbeat(
    db: AsyncSession,
    body: HeartbeatPayload,
    *,
    device: DeviceModel,
    arq_pool: ArqRedis | None = None,
) -> MessageSchema:
    await waste_service.ml_heartbeat(db, body, device=device, arq_pool=arq_pool)
    return MessageSchema(message="Heartbeat recorded")


async def upload_image(
    image_file: UploadFile,
    *,
    content_length: int | None = None,
) -> LogoUrlSchema:
    return await waste_service.upload_image(image_file, content_length=content_length)
